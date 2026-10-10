import {UawClient,ApiFailure,TransportError,requestMeta,type WebSession} from '../../lib/api/client';
import type {Conversation,Schema,Approval,Run,DisplayItem} from '../../lib/api/types';
import {Projection,SnapshotRequired,terminal} from '../../lib/events/projection';
import {DraftStore,type Recovery} from '../../lib/cache/drafts';
export interface RecoveryPort { find(conversationId:string,requestId:string,signal:AbortSignal):Promise<Run|undefined>; }
export type WorkspaceHost={session:()=>WebSession|null; subscribe?:(callback:()=>void)=>()=>void;
 unavailableReason?:()=>string;logout?:()=>Promise<void>;recovery?:RecoveryPort};
export type View={connected:boolean;loading:boolean;busy:boolean;error:string;conversations:Conversation[];
 active?:Conversation;models:Schema['ModelCatalogEntry'][];items:ReturnType<Projection['sorted']>;
 run?:Run;frame?:Schema['TaskFrame'];approvals:Approval[];draft:string;draftRevision:number;
 recovery?:Recovery;stopping:boolean;transport:'分页轮询';};
const initial=():View=>({connected:false,loading:false,busy:false,error:'',conversations:[],models:[],items:[],approvals:[],draft:'',draftRevision:1,stopping:false,transport:'分页轮询'});
export class WorkspaceController {
 private value=initial();private listeners=new Set<()=>void>();private identity:string|null=null;
 private abort=new AbortController();private timer:ReturnType<typeof setTimeout>|undefined;
 private reads:Promise<void>|undefined;private generation=0;private stopped=true;private projection=new Projection();
 private unknownActions=new Set<string>();private mutation:symbol|undefined;
 constructor(readonly client:UawClient,readonly host:WorkspaceHost,private drafts=new DraftStore(),private pollMs=3000){}
 snapshot=()=>this.value;
 subscribe=(f:()=>void)=>{this.listeners.add(f);return()=>{this.listeners.delete(f);};};
 private patch(p:Partial<View>){this.value={...this.value,...p};for(const f of this.listeners)f();}
 private guard(generation:number){if(generation!==this.generation||this.stopped)throw new DOMException('操作已取消','AbortError');if(this.host.session()?.identityKey!==this.identity){void this.start();throw new DOMException('身份已变化','AbortError');}}
 private sameIdentity(){if(this.host.session()?.identityKey!==this.identity){void this.start();return false;}return true;}
 private reset(){this.mutation=undefined;this.abort.abort();this.abort=new AbortController();clearTimeout(this.timer);this.generation++;this.projection.clear();this.unknownActions.clear();this.reads=undefined;this.patch(initial());}
 async start(initialId?:string){this.stopped=false;const identity=this.host.session()?.identityKey??null;
  if(identity!==this.identity||this.abort.signal.aborted){this.reset();this.identity=identity;this.drafts.bind(identity);}
  if(!identity){this.patch({error:this.host.unavailableReason?.()??'浏览器身份入口尚未接入，请等待服务端会话。'});return;}
  const generation=this.generation;
  try{this.patch({loading:true});const page=await this.client.models(this.abort.signal);this.guard(generation);
   this.patch({models:page.items.filter(m=>m.status==='active'),connected:true,error:''});
   const saved=this.drafts.read();await this.list(generation);this.guard(generation);const conversations=this.value.conversations;
   this.patch({recovery:saved.recovery});
   if(saved.recovery)await this.open(saved.recovery.conversationId);else if(initialId)await this.open(initialId);else if(conversations[0])await this.open(conversations[0].id);
  }catch(e){if(generation===this.generation)this.fail(e);}finally{if(generation===this.generation)this.patch({loading:false});}
 }
 async list(g=this.generation){const load=async()=>{const page=await this.pages(c=>this.client.conversations(c,this.abort.signal));this.guard(g);
   const newest=new Map<string,Conversation>();for(const c of page.items as Conversation[]){const old=newest.get(c.id);if(!old||c.revision>old.revision)newest.set(c.id,c);}
   this.patch({conversations:[...newest.values()]});};
  try{await load();}catch(e){if(e instanceof SnapshotRequired||e instanceof ApiFailure&&['cursor_invalid','snapshot_required'].includes(e.result.failure?.code??'')){await load();}else throw e;}
 }
 stop(){this.stopped=true;this.abort.abort();clearTimeout(this.timer);this.generation++;}
 async logout(){this.stop();this.identity=null;this.drafts.clear();this.reset();await this.host.logout?.();}
 private fail(e:unknown){if(e instanceof DOMException&&e.name==='AbortError')return;
  this.patch({connected:false,error:e instanceof Error?e.message:'读取失败，请重新连接。'});}
 edit(text:string){this.patch({draft:text,draftRevision:this.value.draftRevision+1});if(this.value.active)this.drafts.draft(this.value.active.id,text);}
 async create(title:string,modelId:string){if(!this.sameIdentity()||!this.value.connected||this.mutation)return;
  const operation=Symbol('mutation');this.mutation=operation;this.patch({busy:true});const g=this.generation;
  try{const result=await this.client.create({title,model_choice:{mode:'explicit',model_id:modelId},
   memory_policy:{revision:1,read_enabled:false,contribute_enabled:false,scope:{resource_refs:[]}},approval_mode:'manual'},requestMeta(0),this.abort.signal);
   this.guard(g);this.drafts.remember(result.id);this.patch({conversations:[result,...this.value.conversations]});await this.open(result.id);
  }catch(e){if(g===this.generation)this.fail(e);}finally{if(this.mutation===operation){this.mutation=undefined;this.patch({busy:false});}}
 }
 async open(id:string){
  this.mutation=undefined;this.abort.abort();this.abort=new AbortController();clearTimeout(this.timer);const g=++this.generation;
  this.projection.clear();this.patch({loading:true,busy:false,active:undefined,items:[],run:undefined,frame:undefined,approvals:[],error:'',stopping:false});
  try{const active=await this.client.conversation(id,this.abort.signal);this.guard(g);this.drafts.remember(id);
   this.patch({active,conversations:[active,...this.value.conversations.filter(c=>c.id!==id)],draft:this.drafts.read().drafts[id]??'',draftRevision:1,connected:true});await this.refresh(g);
  }catch(e){if(g===this.generation)this.fail(e);}finally{if(g===this.generation){this.patch({loading:false});this.schedule(g);}}
 }
 private schedule(g:number){if(this.stopped||g!==this.generation)return;clearTimeout(this.timer);
  this.timer=setTimeout(async()=>{try{await this.refresh(g);}catch(e){if(g===this.generation)this.fail(e);}finally{this.schedule(g);}},this.pollMs);}
 private async pages<T extends {items:unknown[];next_cursor?:string;snapshot_revision:number}>(load:(cursor?:string)=>Promise<T>){
  let cursor:string|undefined,revision:number|undefined;const cursors=new Set<string>();const items:T['items']=[];
  for(let n=0;n<64;n++){const page=await load(cursor);if(revision!==undefined&&revision!==page.snapshot_revision)throw new SnapshotRequired('分页快照版本变化');
   revision=page.snapshot_revision;items.push(...page.items);if(!page.next_cursor)return{items,revision};
   if(cursors.has(page.next_cursor))throw new SnapshotRequired('分页游标循环');cursors.add(page.next_cursor);cursor=page.next_cursor;}
  throw new Error('历史分页超过本次读取上限，请缩小会话范围。');
 }
 private async refresh(g:number){
  const previous=this.reads;if(previous){try{await previous;}catch{/* fresh read follows */}}
  this.guard(g);const current=this.readFresh(g);this.reads=current;
  try{await current;}finally{if(this.reads===current)this.reads=undefined;}
 }
 private async readFresh(g:number){const active=this.value.active;if(!active)return;const signal=this.abort.signal;
  const load=async()=>{
   const current=await this.client.conversation(active.id,signal);this.guard(g);
   const page=await this.pages(c=>this.client.items(active.id,c,signal));this.guard(g);
   if(page.items.some(i=>(i as DisplayItem).conversation_id!==active.id))throw new SnapshotRequired('条目会话不一致');
   this.projection.replaceItems(page.items as DisplayItem[],page.revision!);
   const history=await this.pages(c=>this.client.events(active.id,c,signal));this.guard(g);
   for(const event of history.items as Schema['EventEnvelope'][]){if(event.stream_id!==active.id)throw new SnapshotRequired('事件会话不一致');if(event.seq<=this.projection.lastSeq){const previous=this.projection.events.get(event.seq);if(previous&&previous!==event.event_id)throw new SnapshotRequired('相同seq出现不同事件');continue;}
    const payload=await this.client.payload(event.event_id,signal);this.guard(g);this.projection.apply(event,payload);}
   let rec=this.drafts.read().recovery;
   if(rec && rec.conversationId===active.id){
    if(rec.runId)this.projection.run=await this.client.run(rec.runId,signal);
    else if(this.host.recovery){const run=await this.host.recovery.find(rec.conversationId,rec.requestId,signal);this.guard(g);
      if(run){if(run.conversation_id!==rec.conversationId)throw new Error('原请求Run归属不匹配');rec={...rec,runId:run.id};this.drafts.recovery(rec);this.projection.run=run;}}
   }
   this.guard(g);
   if(this.projection.run){const run=await this.client.run(this.projection.run.id,signal);this.guard(g);if(run.conversation_id!==active.id)throw new SnapshotRequired('Run会话不一致');this.projection.run=run;
    try{this.projection.frame=await this.client.frame(run.task_id,signal);}catch(e){if(!(e instanceof ApiFailure&&['missing','waiting'].includes(e.result.kind)))throw e;}
    this.guard(g);if(this.projection.frame&&this.projection.frame.task_id!==run.task_id)throw new SnapshotRequired('任务理解归属不一致');
    if(terminal(run.status)){this.patch({stopping:false});if(rec?.runId===run.id){this.drafts.recovery();rec=undefined;}}
   }
   const approvalIds=new Set([...this.projection.approvals.keys(),...this.projection.sorted().flatMap(i=>i.type==='approval'?i.resource_refs.filter(r=>r.kind==='approval').map(r=>r.id):[])]);
   for(const id of approvalIds){const approval=await this.client.approval(id,signal);this.guard(g);this.projection.approvals.set(id,approval);}
   this.patch({active:current,connected:true,error:rec&&!rec.runId?'发送结果待对账：尚无原请求Run回执，不会重发。':'',recovery:rec,
    items:this.projection.sorted(),run:this.projection.run,frame:this.projection.frame,approvals:[...this.projection.approvals.values()]});
  };
  try{await load();}catch(e){if(e instanceof SnapshotRequired || e instanceof ApiFailure&&['cursor_invalid','snapshot_required'].includes(e.result.failure?.code??'')){
    this.projection.clear();await load();}else throw e;}
 }
 async reconnect(){if(!this.sameIdentity())return;if(this.value.active){const g=this.generation;try{await this.list(g);await this.refresh(g);}catch(e){if(g===this.generation)this.fail(e);}}else await this.start();}
 async send(){const active=this.value.active,text=this.value.draft;
  if(!this.sameIdentity()||!active||!text.trim()||!this.value.connected||this.mutation||this.value.recovery)return;
  const operation=Symbol('mutation');this.mutation=operation;this.patch({busy:true,error:''});const g=this.generation;
  try{const meta=requestMeta(active.revision);
   // Persist lookup only BEFORE dispatch; never persist permission or Run status.
   const rec:Recovery={requestId:meta.request_id,conversationId:active.id};this.drafts.recovery(rec);this.patch({recovery:rec});
   const run=await this.client.submit(active.id,{text,attachment_refs:[]},meta,this.abort.signal);this.guard(g);
   this.drafts.recovery({...rec,runId:run.id});this.projection.run=run;this.edit('');this.patch({run,recovery:{...rec,runId:run.id}});await this.refresh(g);
  }catch(e){if(g===this.generation){if(!(e instanceof TransportError) && !(e instanceof DOMException&&e.name==='AbortError') && !(e instanceof ApiFailure&&e.result.kind==='waiting')){this.drafts.recovery();this.patch({recovery:undefined});}this.fail(e);}}
  finally{if(this.mutation===operation){this.mutation=undefined;this.patch({busy:false});}}
 }
 async cancel(){const old=this.value.run;if(!this.sameIdentity()||!old||terminal(old.status)||this.mutation||!this.value.connected||this.unknownActions.has(old.id))return;
  const operation=Symbol('mutation');this.mutation=operation;this.patch({busy:true,stopping:true});const g=this.generation;
  try{const current=await this.client.run(old.id,this.abort.signal);this.guard(g);
   if(current.id!==old.id||current.conversation_id!==old.conversation_id||current.revision!==old.revision)throw new Error('运行版本已变化，请重新读取后操作。');
   await this.client.control(current.id,{mode:'cancel',preserve_refs:[],reason:'用户请求停止'},requestMeta(current.revision),this.abort.signal);this.guard(g);
   await this.refresh(g); // Acknowledgement never means cancelled.
  }catch(e){if(g===this.generation){if(e instanceof TransportError)this.unknownActions.add(old.id);this.fail(e);}}
  finally{if(this.mutation===operation){this.mutation=undefined;this.patch({busy:false});}}
 }
 async decide(old:Approval,decision:'approve_once'|'decline'){
  if(!this.sameIdentity()||this.mutation||!this.value.connected||this.unknownActions.has(old.id))return;const operation=Symbol('mutation');this.mutation=operation;this.patch({busy:true});const g=this.generation;
  try{const current=await this.client.approval(old.id,this.abort.signal);this.guard(g);
   if(current.id!==old.id||current.status!=='pending'||Date.parse(current.expires_at)<=Date.now()||current.revision!==old.revision||current.arguments_hash!==old.arguments_hash||JSON.stringify(current.resource_refs)!==JSON.stringify(old.resource_refs))throw new Error('审批已过期或版本变化，请重新读取。');
   await this.client.decide(current.id,{decision,expected_arguments_hash:current.arguments_hash,expected_resource_refs:current.resource_refs,reason:decision==='decline'?'用户拒绝本次动作':'用户批准本次动作'},requestMeta(current.revision),this.abort.signal);this.guard(g);await this.refresh(g);
  }catch(e){if(g===this.generation){if(e instanceof TransportError)this.unknownActions.add(old.id);this.fail(e);}}finally{if(this.mutation===operation){this.mutation=undefined;this.patch({busy:false});}}
 }
}
