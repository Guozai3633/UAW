import {ApiFailure,UawClient,requestMeta} from '../../lib/api/client';
import {canonical} from '../../lib/api/canonical';
import type {Schema} from '../../lib/api/types';
type Enrollment=Schema['RunnerEnrollmentRecord'];
export interface EnrollmentSourcePort { current(signal:AbortSignal):Promise<{candidateId?:string;enrollmentId?:string}>; }
export interface EnrollmentPort {
 locate(signal:AbortSignal):Promise<{candidateId?:string;enrollmentId?:string}>;
 read(id:string,signal:AbortSignal):Promise<Enrollment>;
 begin(signal:AbortSignal):Promise<Enrollment>;
 decide(value:Enrollment,action:'confirmation'|'revocation',signal:AbortSignal):Promise<Enrollment>;
 uncertain():boolean;
}
// Lookup metadata only, never an enrollment, proof, status, permission or token.
type Pending={requestId:string;enrollmentId?:string;candidateId?:string;revision?:number};
const key='uaw.web.enrollment-lookup.v1';
const id=(v:unknown):v is string=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(v);
export function clearEnrollmentLookup(){try{localStorage.removeItem(key);}catch{/* local view remains unavailable */}}
export class HttpEnrollmentPort implements EnrollmentPort {
 private pending:Pending|undefined;private identity:string|undefined;
 constructor(private client:UawClient,private source?:EnrollmentSourcePort,private storage:Storage=localStorage){}
 private bind(){const current=this.client.currentSession()?.identityKey;if(!current)throw Error('当前用户会话不可用');
  if(current!==this.identity){let saved:unknown;try{saved=JSON.parse(this.storage.getItem(key)??'null');}catch{/* ignored */}
   const s=saved as {identity?:string;lookup?:Pending}|null;
   const value=this.identity===undefined&&s?.identity===current?s.lookup:undefined;
   this.pending=value&&id(value.requestId)&&(id(value.enrollmentId)||id(value.candidateId))&&(value.revision===undefined||Number.isSafeInteger(value.revision)&&value.revision>0)?{requestId:value.requestId,...(id(value.enrollmentId)?{enrollmentId:value.enrollmentId,revision:value.revision}:{}),...(id(value.candidateId)?{candidateId:value.candidateId}:{})}:undefined;this.identity=current;this.save();
  }return current;
 }
 private save(){try{if(this.pending)this.storage.setItem(key,JSON.stringify({identity:this.identity,lookup:this.pending}));else this.storage.removeItem(key);}catch{throw Error('无法保存原登记查找ID，设备写入不可用。');}}
 private guard(identity:string,signal:AbortSignal){signal.throwIfAborted();if(identity!==this.client.currentSession()?.identityKey)throw Error('设备读取期间身份已变化');}
 private check(v:Enrollment,id?:string){const owner=this.client.currentSession()?.principal;
  if(v.proof_document.enrollment_id!==v.id||id&&v.id!==id||owner&&canonical(v.proof_document.owner)!==canonical(owner))throw Error('登记与当前原身份不匹配');
 }
 uncertain(){this.bind();return !!this.pending;}
 async locate(signal:AbortSignal){const identity=this.bind();if(!this.source&&this.pending?.enrollmentId)return{enrollmentId:this.pending.enrollmentId};if(!this.source)throw Error('可信本机候选来源尚未接入；首次登记不可用。');const value=await this.source.current(signal);this.guard(identity,signal);return value;}
 async read(id:string,signal:AbortSignal){const identity=this.bind();if(!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(id))throw Error('原登记ID格式不匹配');const value=await this.client.enrollment(id,signal);this.guard(identity,signal);this.check(value,id);
  if(this.pending&&(this.pending.enrollmentId===id&&value.revision>(this.pending.revision??0)||!this.pending.enrollmentId&&this.pending.candidateId===value.proof_document.candidate_ref.id)){this.pending=undefined;this.save();}return value;
 }
 async begin(signal:AbortSignal){const identity=this.bind();if(this.pending)throw Error('原登记请求结果未知；先查询原登记，不会换请求ID。');
  const locator=await this.locate(signal);this.guard(identity,signal);if(!locator.candidateId)throw Error('缺实际可信候选；不能由网页自造设备。');
  const meta=requestMeta();this.pending={requestId:meta.request_id,candidateId:locator.candidateId};this.save();
  try{const value=await this.client.beginEnrollment(locator.candidateId,meta,signal);this.guard(identity,signal);this.check(value);this.pending=undefined;this.save();return value;}
  catch(e){if(e instanceof ApiFailure&&e.result.kind!=='waiting'&&this.client.currentSession()?.identityKey===identity){this.pending=undefined;this.save();}throw e;}
 }
 async decide(old:Enrollment,action:'confirmation'|'revocation',signal:AbortSignal){const identity=this.bind();if(this.pending)throw Error('原设备决定结果未知；只查询原登记，不会重发。');
  const value=await this.read(old.id,signal);this.guard(identity,signal);
  if(value.revision!==old.revision||canonical(value.proof_document)!==canonical(old.proof_document)||value.state==='revoked'||value.state==='expired'||Date.parse(value.proof_document.expires_at)<=Date.now()||action==='confirmation'&&value.state!=='pending')throw Error('设备版本或当前状态已变化，请重新读取。');
  const meta=requestMeta(value.revision);this.pending={requestId:meta.request_id,enrollmentId:value.id,revision:value.revision};this.save();
  try{const result=await (action==='confirmation'?this.client.confirmEnrollment(value.id,meta,signal):this.client.revokeEnrollment(value.id,meta,signal));this.guard(identity,signal);this.check(result,value.id);this.pending=undefined;this.save();return result;}
  catch(e){if(e instanceof ApiFailure&&e.result.kind!=='waiting'&&this.client.currentSession()?.identityKey===identity){this.pending=undefined;this.save();}throw e;}
 }
}
