import {beforeEach,it,expect,vi} from 'vitest';
import {WorkspaceController} from '../../src/features/workspace/controller';
import {UawClient} from '../../src/lib/api/client';
import {conversation,models,ok,makeRun,frame,now,ref,approval} from '../fixtures';
import type {Approval,Schema} from '../../src/lib/api/types';
function setup(){let run=makeRun();let hasRun=false;let pending=structuredClone(approval);const posts:RequestInit[]=[];
 const transport=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
  const path=String(input).split('?')[0];let data:unknown;
  if(options?.method==='POST'){posts.push(options);if(path.endsWith('/turns')){hasRun=true;data=run;}
   else if(path.endsWith('/control')){data={operation_id:'control-one',status:'accepted'};}
   else if(path.endsWith('/decisions')){const decision=JSON.parse(String(options.body)).payload.decision;pending={...pending,status:decision.decision==='decline'?'declined':'approved',revision:2};
    data={id:'grant-one',approval_ref:ref('approval',pending.id,'2'),actor:{id:'user-one',kind:'user',auth_session_id:'session-one'},decision,issued_at:now};}
   else data=conversation;
  }else if(path==='/v1/models')data=models;
  else if(path==='/v1/conversations/conv-one')data=conversation;
  else if(path.endsWith('/items'))data={items:[],snapshot_revision:hasRun?1:0};
  else if(path.endsWith('/events'))data={items:hasRun?[{event_id:'event-one',stream_id:'conv-one',seq:1,type:'run.updated',schema_version:'0.1',occurred_at:now,payload_ref:ref('event','event-one')}]:[],snapshot_revision:hasRun?1:0};
  else if(path.endsWith('/payload'))data={action:'run.updated',parameters:run};
  else if(path.endsWith('/frame'))data=frame;
  else if(path.includes('/approvals/'))data=pending;
  else data=run;
  return new Response(JSON.stringify(ok(data)),{status:200});
 });
 const c=new WorkspaceController(new UawClient(()=>({identityKey:'user-one'}),transport),{session:()=>({identityKey:'user-one'})},undefined,60000);
 return{c,transport,posts,setRun:(v:Schema['RunRecord'])=>{run=v;},setApproval:(a:Approval)=>{pending=a;}};
}
beforeEach(()=>localStorage.clear());
it('sends exact original once, refreshes known Run and does not treat cancellation acknowledgement as terminal',async()=>{
 const x=setup();await x.c.start('conv-one');x.c.edit('  保留原文\n  ');await x.c.send();
 expect(x.posts).toHaveLength(1);expect(JSON.parse(String(x.posts[0].body)).payload.text).toBe('  保留原文\n  ');
 expect(x.c.snapshot().run?.status).toBe('running');await x.c.cancel();expect(x.c.snapshot().stopping).toBe(true);expect(x.c.snapshot().run?.status).toBe('running');
 x.setRun(makeRun('cancelled',2));await x.c.reconnect();expect(x.c.snapshot().stopping).toBe(false);expect(x.c.snapshot().run?.status).toBe('cancelled');x.c.stop();
});
it('uncertain dispatch persists lookup only and refresh never resubmits',async()=>{
 const x=setup();await x.c.start('conv-one');x.transport.mockImplementationOnce(async()=>{throw new TypeError('lost');});x.c.edit('task');await x.c.send();
 expect(x.c.snapshot().recovery?.requestId).toBeTruthy();expect(x.c.snapshot().recovery?.runId).toBeUndefined();
 await x.c.reconnect();await x.c.send();expect(x.posts).toHaveLength(0);expect(x.c.snapshot().error).toContain('待对账');x.c.stop();
});
it('decision binds fresh hash/refs/revision, rejects changed approval',async()=>{
 const x=setup();await x.c.start('conv-one');await x.c.decide(approval,'approve_once');expect(x.posts).toHaveLength(1);
 const body=JSON.parse(String(x.posts[0].body));expect(body.meta.expected_revision).toBe(1);expect(body.payload.decision.expected_arguments_hash).toBe(approval.arguments_hash);
 x.setApproval({...approval,revision:2,arguments_hash:'b'.repeat(64)});await x.c.decide(approval,'decline');expect(x.posts).toHaveLength(1);x.c.stop();
});

it('creating a conversation releases busy state and records an opened URL in the sidebar',async()=>{
 const x=setup();await x.c.start('conv-one');expect(x.c.snapshot().conversations.map(c=>c.id)).toEqual(['conv-one']);
 await x.c.create('new','model-one');expect(x.c.snapshot().busy).toBe(false);x.c.edit('next');await x.c.send();expect(x.posts).toHaveLength(2);x.c.stop();
});
it('new controller restores original Run by GET without dispatching a turn',async()=>{
 const x=setup();await x.c.start('conv-one');x.c.edit('original');await x.c.send();x.c.stop();
 const y=setup();await y.c.start();expect(y.c.snapshot().run?.id).toBe('run-one');expect(y.posts).toHaveLength(0);y.c.stop();
});
it('aborted identity read cannot restore old data or a connected state',async()=>{
 const x=setup();let release!:(response:Response)=>void;x.transport.mockImplementationOnce(()=>new Promise(resolve=>{release=resolve;}));
 const starting=x.c.start('conv-one');x.c.stop();release(new Response(JSON.stringify(ok(models))));await starting;
 expect(x.c.snapshot().connected).toBe(false);expect(x.c.snapshot().active).toBeUndefined();
});

it('cursor-invalid responses resnapshot without sending and cursor loops fail explicitly',async()=>{
 const x=setup();const actual=x.transport.getMockImplementation()!;let stale=true,reads=0;
 x.transport.mockImplementation(async(input,options)=>{if(String(input).includes('/items')){reads++;if(stale){stale=false;return new Response(JSON.stringify({kind:'stale',failure:{code:'cursor_invalid',category:'conflict',message:'cursor expired',retryable:false,failed_phase:'read'},output_refs:[]}));}}return actual(input,options);});
 await x.c.start('conv-one');expect(x.c.snapshot().connected).toBe(true);expect(reads).toBe(2);expect(x.posts).toHaveLength(0);x.c.stop();
 const y=setup();const normal=y.transport.getMockImplementation()!;y.transport.mockImplementation(async(input,options)=>String(input).includes('/items')?new Response(JSON.stringify(ok({items:[],snapshot_revision:1,next_cursor:'loop'}))):normal(input,options));
 await y.c.start('conv-one');expect(y.c.snapshot().connected).toBe(false);expect(y.c.snapshot().error).toContain('游标循环');expect(y.posts).toHaveLength(0);y.c.stop();
});
