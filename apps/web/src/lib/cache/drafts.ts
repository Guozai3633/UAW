// Persistent storage contains only the explicitly permitted draft and lookup IDs.
// No Run status, event payload, approval, token, model secret or acceptance is stored.
export type Recovery = {requestId:string;conversationId:string;runId?:string};
export type LocalData = {version:1;drafts:Record<string,string>;conversationIds:string[];recovery?:Recovery};
const key='uaw.web.local.v1';
const empty=():LocalData=>({version:1,drafts:{},conversationIds:[]});
export class DraftStore {
 private value=empty();private identity:string|null=null;
 constructor(private storage:Storage=localStorage){}
 bind(identity:string|null){if(identity===this.identity)return;
  let previous:string|null=null;try{previous=this.storage.getItem(key);}catch{/* unavailable storage: memory only */}this.value=empty();
  if(identity && this.identity===null && previous){try{const data=JSON.parse(previous);
   if(data.identity===identity && data.value?.version===1){
    const v=data.value;
    this.value={version:1,drafts:Object.fromEntries(Object.entries(v.drafts??{}).filter((pair):pair is [string,string]=>validId(pair[0])&&typeof pair[1]==='string'&&pair[1].length<=131072)),
     conversationIds:Array.isArray(v.conversationIds)?v.conversationIds.filter(validId).slice(-50):[]};
    const rec=v.recovery;if(rec&&validId(rec.requestId)&&validId(rec.conversationId)&&(!rec.runId||validId(rec.runId)))this.value.recovery=rec;
   }}catch{/* corrupt storage is discarded */}}
  this.identity=identity;this.flush();return this.read();
 }
 read():LocalData{return structuredClone(this.value);}
 draft(id:string,text:string){if(text.length<=131072)this.value.drafts[id]=text;this.flush();}
 remember(id:string){if(validId(id)){this.value.conversationIds=[...new Set([...this.value.conversationIds,id])].slice(-50);this.flush();}}
 recovery(value?:Recovery){if(value)this.value.recovery=structuredClone(value);else delete this.value.recovery;this.flush();}
 clear(){this.identity=null;this.value=empty();try{this.storage.removeItem(key);}catch{/* memory already cleared */}}
 private flush(){try{if(this.identity)this.storage.setItem(key,JSON.stringify({identity:this.identity,value:this.value}));else this.storage.removeItem(key);}catch{/* storage unavailable: memory only, no resubmission */}}
}
const validId=(v:unknown):v is string=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(v);
