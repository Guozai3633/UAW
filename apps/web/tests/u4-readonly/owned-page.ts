import type {Page,Request} from '@playwright/test';
import {validate} from '../../src/lib/api/validation';
import {canonical} from '../../src/lib/api/canonical';
import {checkView,checkReceipt} from '../../src/features/conversation/port';
import type {Schema,Result} from '../../src/lib/api/types';
// Observe A's original existing Page only. No navigation, local persistence, writes, cookie export or body logging.
export async function verifyOwnedConversationPage(page:Page,runId:string){
 const url=new URL(page.url()),conversationId=url.searchParams.get('conversation'),id=/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
 if(!id.test(runId)||!conversationId||!id.test(conversationId)||url.hash)throw Error('Exact original conversation Page and Run required');
 let writes=0,reads=0;const onRequest=(r:Request)=>{if(new URL(r.url()).pathname.startsWith('/v1/')&&r.method()!=='GET')writes++;};page.on('request',onRequest);
 try{
  async function read<T>(path:string,schema:string,protocol=false):Promise<T>{reads++;const response=await page.evaluate(async({path,protocol})=>{const r=await fetch(path,{method:'GET',credentials:'same-origin',cache:'no-store',headers:{Accept:'application/json',...(protocol?{'X-UAW-Schema-Version':'0.2'}:{})},signal:AbortSignal.timeout(15000)});return{status:r.status,wire:await r.json()};},{path,protocol});validate(schema,response.wire);const result=response.wire as Result<T>;if(response.status!==200||result.kind!=='ok')throw Error();return result.payload;}
  const session=await read<Schema['WebSession']>('/v1/web/session','HttpWebSessionGetResult');if(session.principal.kind!=='user'||Date.parse(session.expires_at)<=Date.now())throw Error();
  const identity=canonical(session.principal),expiry=session.expires_at,conversation=await read<Schema['Conversation']>('/v1/conversations/'+encodeURIComponent(conversationId),'HttpConversationsGetResult');if(conversation.id!==conversationId||conversation.owner_id!==session.principal.id)throw Error();
  const run=await read<Schema['RunRecord']>('/v1/runs/'+encodeURIComponent(runId),'HttpRunsGetResult');if(run.id!==runId||run.conversation_id!==conversationId)throw Error();
  const path='/v1/runs/'+encodeURIComponent(runId)+'/conversation',view=await read<Schema['RunConversationView']>(path,'HttpRunsConversationGetResult',true);checkView(view,run);
  if(view.question){const q=await read<Schema['ClarificationView']>('/v1/runs/'+encodeURIComponent(runId)+'/clarifications/'+encodeURIComponent(view.question.question.item_id),'HttpRunsClarificationGetResult',true);if(canonical(q)!==canonical(view.question))throw Error();}
  const states={accepted:0,applied:0,superseded:0,cancelled:0};for(const requestId of view.continuation_request_ids){const r=await read<Schema['RunContinuationReceipt']>('/v1/runs/'+encodeURIComponent(runId)+'/continuations/'+encodeURIComponent(requestId),'HttpRunsContinuationGetResult',true);checkReceipt(r,{runId,conversationId},requestId);states[r.patch.state]++;}
  const final=await read<Schema['RunConversationView']>(path,'HttpRunsConversationGetResult',true),finalSession=await read<Schema['WebSession']>('/v1/web/session','HttpWebSessionGetResult');
  if(canonical(final)!==canonical(view)||canonical(finalSession.principal)!==identity||finalSession.expires_at!==expiry||page.url()!==url.href||writes)throw Error();
  return{status:'observed' as const,protocol:view.protocol,run_status:view.run.status,run_revision:view.run.revision,input_revision:view.input_revision,question_state:view.question?'open':'absent',patch_counts:states,reads,writes:0};
 }catch{throw Error('Original-Page readonly observation unavailable or changed; no credential, ID, source body or DOM is emitted.');}
 finally{page.off('request',onRequest);}
}
