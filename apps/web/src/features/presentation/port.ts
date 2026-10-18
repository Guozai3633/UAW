import {ApiFailure,UawClient} from '../../lib/api/client';
import {canonical} from '../../lib/api/canonical';
import type {Run,Schema} from '../../lib/api/types';
import {terminal} from '../../lib/events/projection';
import type {ConversationPort,ConversationView,ContinuationReceipt} from '../conversation/port';
import {ContinuationStore,type PendingContinuation} from '../conversation/store';
export type Presentation=Schema['RunPresentationView'];
export interface PresentationPort {read(run:Run,signal:AbortSignal):Promise<Presentation>}
export const phaseLabels:Record<Presentation['phase'],string>={preparing:'正在准备任务',working:'正在处理任务',verifying:'正在核验成果',waiting_for_user:'任务等待处理',awaiting_acceptance:'成果已就绪，等待你审阅',finalizing:'正在收尾',needs_revision:'成果需要修改，请查看核验',stopping:'正在停止',completed:'已完成',failed:'运行失败',cancelled:'已取消',unavailable:'当前任务展示来源不可用'};
export function checkPresentation(p:Presentation,run:Run){
 if(p.run.id!==run.id||p.run.conversation_id!==run.conversation_id||p.run.revision<run.revision||p.understanding.input_revision!==p.input_revision)throw Error('任务展示与原Run/会话/输入版本不一致。');
 if(terminal(p.run.status)?p.phase!==p.run.status:['completed','failed','cancelled'].includes(p.phase))throw Error('展示终态与实际Run不一致。');
 const u=p.understanding,d=p.delivery;
 if(u.state==='available'&&(u.decision_record_ref?.kind!=='content'||u.model_output_ref?.kind!=='content'))throw Error('理解缺实际模型来源。');
 if(d&&(d.input_revision!==p.input_revision||d.run_revision!==p.run.revision||d.bundle_ref.kind!=='content'||d.artifact_ref.kind!=='artifact'||d.report_ref.kind!=='verification'||d.proposal_ref.kind!=='content'))throw Error('成果与当前任务展示版本不一致。');
 if(p.phase==='awaiting_acceptance'&&(!d||!d.requires_acceptance||d.outcome!=='succeeded'))throw Error('缺等待审阅的当前成果。');
}
export class HttpPresentationPort implements PresentationPort{
 constructor(private client:UawClient){}
 async read(run:Run,signal:AbortSignal){const identity=this.client.currentSession()?.identityKey;if(!identity)throw Error('当前浏览器身份不可用。');const p=await this.client.presentation(run.id,signal);signal.throwIfAborted();if(identity!==this.client.currentSession()?.identityKey)throw Error('任务展示读取期间身份已变化。');checkPresentation(p,run);return p;}
}
export type PresentationSource={identity:string;presentation:Presentation;conversation:ConversationView;receipts:ContinuationReceipt[];pending:PendingContinuation[]};
// Per-mounted Workspace memory only. Last values are display history, never permission or reusable reads.
export class PresentationSession{
 private generation=0;private key='';private last?:Presentation;
 constructor(private port:PresentationPort,private conversation:ConversationPort,private store:ContinuationStore){}
 invalidate(){this.generation++;}
 async read(identity:string,run:Run,signal:AbortSignal):Promise<PresentationSource>{
  const key=JSON.stringify([identity,run.conversation_id,run.id]);if(key!==this.key){this.key=key;this.last=undefined;}const generation=++this.generation;
  const guard=()=>{signal.throwIfAborted();if(generation!==this.generation||key!==this.key)throw new DOMException('已被当前读取取代','AbortError');};
  let p=await this.port.read(run,signal);guard();const c=await this.conversation.read(p.run,signal);guard();
  if(c.input_revision!==p.input_revision||canonical(c.run)!==canonical(p.run)){p=await this.port.read(c.run,signal);guard();}
  checkPresentation(p,run);if(c.input_revision!==p.input_revision||canonical(c.run)!==canonical(p.run))throw Error('原任务/补充/展示版本变化，需统一重新读取。');
  if(this.last&&(p.input_revision<this.last.input_revision||p.run.revision<this.last.run.revision||Date.parse(p.captured_at)<Date.parse(this.last.captured_at)))throw Error('较旧的展示响应已拒绝，保留上次核对值。');
  this.store.bind(identity);const scope={conversationId:run.conversation_id,runId:run.id},saved=this.store.pending(scope),ids=[...new Set([...c.continuation_request_ids,...saved.map(s=>s.requestId)])],receipts:ContinuationReceipt[]=[];
  if(ids.length>128)throw Error('原补充读取超过上限。');
  for(const id of ids){try{const r=await this.conversation.lookup(scope,id,signal);guard();if(r.patch.input_revision>p.input_revision||r.run.revision>p.run.revision)throw Error('补充回执已更新，需统一重新读取。');this.store.resolve(scope,r);receipts.push(r);}catch(e){if(e instanceof ApiFailure&&e.result.kind==='missing'&&saved.some(s=>s.requestId===id))continue;throw e;}}
  guard();this.last=structuredClone(p);return{identity,presentation:p,conversation:c,receipts,pending:this.store.pending(scope)};
 }
}
