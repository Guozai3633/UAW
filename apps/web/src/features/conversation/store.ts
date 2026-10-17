import type {ControlKind,ControlScope,ContinuationReceipt} from './port';
import {checkReceipt} from './port';
export type PendingContinuation={requestId:string;kind:ControlKind;runRevision:number;inputRevision:number;questionId?:string;questionRevision?:number};
const draftsKey='uaw.web.continuation.drafts.v1',pendingPrefix='uaw.web.continuation.pending.v1.';
const id=(v:unknown):v is string=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(v);
const revision=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=1;
const validScope=(v:ControlScope|undefined):v is ControlScope=>!!v&&id(v.conversationId)&&id(v.runId);
const validPending=(p:PendingContinuation|undefined):p is PendingContinuation=>!!p&&id(p.requestId)&&revision(p.runRevision)&&revision(p.inputRevision)&&(p.kind==='clarification_answer'?id(p.questionId)&&revision(p.questionRevision):p.kind==='correction'&&p.questionId===undefined&&p.questionRevision===undefined);
const scopeKey=(s:ControlScope)=>JSON.stringify([s.conversationId,s.runId]);
type DraftEntry={scope:ControlScope;drafts:Record<string,string>};
// Only user drafts and per-request lookup/CAS metadata. No cached graph/receipt/permission or secret.
export class ContinuationStore {
 private identity:string|undefined;private entries:DraftEntry[]=[];
 constructor(private storage:Storage=localStorage){}
 bind(identity:string){if(!identity)throw Error('当前对话身份不可用');if(this.identity===identity)return;let data:unknown;try{data=JSON.parse(this.storage.getItem(draftsKey)??'null');}catch{/* corrupt drafts are discarded */}
  const saved=data as {identity?:string;entries?:DraftEntry[]}|null;this.entries=[];
  if(this.identity===undefined&&saved?.identity===identity&&Array.isArray(saved.entries))for(const row of saved.entries.slice(-50)){if(!validScope(row?.scope))continue;const drafts=Object.fromEntries(Object.entries(row.drafts??{}).filter(([k,v])=>(k==='correction'||k.startsWith('answer:')&&id(k.slice(7)))&&typeof v==='string'&&v.length<=131072));this.entries.push({scope:{conversationId:row.scope.conversationId,runId:row.scope.runId},drafts});}
  this.identity=identity;
 }
 private keys(){if(this.storage.length>4096)throw Error('本地恢复索引超过上限，当前不能安全提交。');return Array.from({length:this.storage.length},(_,n)=>this.storage.key(n)).filter((k):k is string=>!!k&&k.startsWith(pendingPrefix));}
 draft(scope:ControlScope,key:string,value?:string){if(!this.identity||!validScope(scope))throw Error('当前对话身份或原Run不可用');let entry=this.entries.find(e=>scopeKey(e.scope)===scopeKey(scope));
  if(value===undefined)return entry?.drafts[key]??'';if(value.length>131072)throw Error('草稿超过当前上限。');if(!entry){entry={scope:structuredClone(scope),drafts:{}};this.entries.push(entry);this.entries=this.entries.slice(-50);}entry.drafts[key]=value;
  try{this.storage.setItem(draftsKey,JSON.stringify({identity:this.identity,entries:this.entries}));}catch{throw Error('草稿未能持久保存；提交前必须先保存原请求ID。');}return value;
 }
 pending(scope:ControlScope):PendingContinuation[]{if(!this.identity||!validScope(scope))throw Error('当前对话身份或原Run不可用');const found:PendingContinuation[]=[];for(const key of this.keys()){let data:unknown;try{data=JSON.parse(this.storage.getItem(key)??'null');}catch{throw Error('原补充请求查找记录损坏，不能自动重发。');}const v=data as {identity?:string;scope?:ControlScope;pending?:PendingContinuation}|null;if(!v||typeof v.identity!=='string'||!v.identity)throw Error('原补充请求查找记录损坏，不能自动重发。');if(v.identity!==this.identity)continue;if(!validScope(v.scope))throw Error('原补充请求查找记录损坏，不能自动重发。');if(scopeKey(v.scope)!==scopeKey(scope))continue;const p=v.pending;
   if(!validPending(p)||key!==pendingPrefix+p.requestId)throw Error('原补充请求查找记录损坏，不能自动重发。');
   found.push({requestId:p.requestId,kind:p.kind,runRevision:p.runRevision,inputRevision:p.inputRevision,...(p.kind==='clarification_answer'?{questionId:p.questionId,questionRevision:p.questionRevision}:{})});
  }if(found.length>64)throw Error('原补充请求超过恢复上限。');return found;
 }
 mark(scope:ControlScope,p:PendingContinuation){if(!this.identity||!validScope(scope)||!validPending(p))throw Error('原补充请求元数据不可用；没有发送。');const key=pendingPrefix+p.requestId,wire=JSON.stringify({identity:this.identity,scope,pending:p});try{const old=this.storage.getItem(key);if(old!==null&&old!==wire)throw Error();this.storage.setItem(key,wire);if(this.storage.getItem(key)!==wire)throw Error();}catch{throw Error('无法保存原补充请求ID；没有发送。');}}
 forget(requestId:string){try{this.storage.removeItem(pendingPrefix+requestId);}catch{throw Error('原补充查找尚未清理；先查询，不要重发。');}}
 resolve(scope:ControlScope,r:ContinuationReceipt){const pending=this.pending(scope).find(p=>p.requestId===r.patch.request_id);if(!pending)return;checkReceipt(r,scope,pending.requestId);if(r.patch.kind!==pending.kind||r.patch.base_input_revision!==pending.inputRevision||pending.kind==='clarification_answer'&&(r.patch.question_item_id!==pending.questionId||r.patch.question_revision!==pending.questionRevision))throw Error('回执不匹配原补充版本；不会换ID重发。');this.forget(pending.requestId);}
 clear(){this.identity=undefined;this.entries=[];try{this.storage.removeItem(draftsKey);for(const key of this.keys())this.storage.removeItem(key);}catch{/* server still owns auth; no cached authority is used */}}
}
