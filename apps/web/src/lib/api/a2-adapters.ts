import {AcceptanceLookups} from '../cache/acceptance-lookups';
import {ApiFailure,UawClient} from './client';
import type {RecoveryPort} from '../../features/workspace/controller';
import type {ReviewPort,ReviewSnapshot} from '../../features/review/port';
import {checkReview,matchesPin} from '../../features/review/port';
import type {Ref,Schema} from './types';
// Only the six A2 handlers published in ms-i2k-start. No fallback execution.
export class HttpRecoveryPort implements RecoveryPort {
 constructor(private client:UawClient){}
 async find(conversationId:string,requestId:string,signal:AbortSignal){
  try{const run=await this.client.lookup(conversationId,requestId,signal);if(run.conversation_id!==conversationId)throw new Error('原请求Run归属不匹配');return run;}
  catch(e){if(e instanceof ApiFailure&&e.result.kind==='missing')return undefined;throw e;}
 }
}
export class HttpReviewPort implements ReviewPort {
 constructor(private client:UawClient,private lookups=new AcceptanceLookups()){}
 private scope(){const key=this.client.currentSession()?.identityKey;if(!key)throw new Error('当前浏览器会话不可用');this.lookups.bind(key);return key;}
 private current(key:string,signal:AbortSignal){signal.throwIfAborted();if(this.client.currentSession()?.identityKey!==key)throw new Error('接受等待期间身份已变化');}
 async read(requested:Ref|undefined,runId:string,signal:AbortSignal):Promise<ReviewSnapshot>{
  const key=this.scope();const view=await this.client.delivery(runId,signal);this.current(key,signal);if(view.run_id!==runId)throw new Error('成果Run归属不匹配');
  if(requested&&!matchesPin(view.artifact_ref,requested))throw new Error('成果与条目固定版本不匹配');
  await checkDelivery(view);
  const value:ReviewSnapshot={artifact:view.artifact,content:view.content,report:view.report,bundleRef:view.bundle_ref,contractRef:view.contract_ref,requiresAcceptance:view.requires_acceptance,delivery:view};
  await checkReview(value,view.artifact_ref);this.current(key,signal);const pending=this.lookups.find(runId);if(pending&&view.acceptance&&pending.bundleId===view.bundle_ref.id&&pending.artifactId===view.artifact_ref.id)this.lookups.clear(runId);value.decisionUncertain=!!this.lookups.find(runId);return value;
 }
 async accept(value:ReviewSnapshot,meta:Schema['RequestMeta'],signal:AbortSignal){
  const key=this.scope();const v=value.delivery;if(!v)throw new Error('缺实际RunDeliveryView');
  if(v.stale||v.acceptance||!v.requires_acceptance)throw new Error('当前成果已过时、已有决定或不要求接受');
  if(this.lookups.find(v.run_id))throw new Error('接受结果尚未对账，不会换request_id重发。');
  this.current(key,signal);this.lookups.mark({runId:v.run_id,requestId:meta.request_id,bundleId:v.bundle_ref.id,artifactId:v.artifact_ref.id});
  try{const receipt=await this.client.acceptDelivery(v.run_id,{bundle_ref:v.bundle_ref,artifact_ref:v.artifact_ref,decision:'accept'},meta,signal);this.current(key,signal);
   const principal=this.client.currentSession()?.principal;
   if(!matchesPin(receipt.bundle_ref,v.bundle_ref)||receipt.decision!=='accept'||principal&&JSON.stringify(receipt.principal)!==JSON.stringify(principal))throw new Error('接受回执版本或主体不匹配');
   // Keep lookup until authoritative GET delivery reconciles the receipt.
   return{kind:'ok' as const,payload:receipt,output_refs:[]};
  }catch(e){if(e instanceof ApiFailure&&e.result.kind!=='waiting'&&this.client.currentSession()?.identityKey===key)this.lookups.clear(v.run_id);throw e;}

 }
}
export async function checkDelivery(v:Schema['RunDeliveryView']){
 const a=v.artifact_ref;
 if(a.kind!=='artifact'||a.id!==v.artifact.id||a.version!==v.artifact.version||v.bundle_ref.kind!=='content'||v.contract_ref.kind!=='content'||v.report_ref.kind!=='verification'||v.report_ref.id!==v.report.id||v.proposal_ref.kind!=='content'||
  !matchesPin(v.report.contract_ref,v.contract_ref)||!v.report.target_refs.some(p=>matchesPin(p,a))||!matchesPin(v.proposal.contract_ref,v.contract_ref)||!matchesPin(v.proposal.report_ref,v.report_ref)||v.proposal.artifact_refs.length!==1||!matchesPin(v.proposal.artifact_refs[0],a)||v.proposal.run_ref.kind!=='run'||v.proposal.run_ref.id!==v.run_id||v.requires_acceptance!==(v.contract.acceptance_required??false)||v.acceptance&&!matchesPin(v.acceptance.bundle_ref,v.bundle_ref))throw new Error('成果、合同、核验与提案固定关联不匹配');
}
