// Frozen public DTO fixtures, controlled only: no actual LLM, clock or production recovery.
import type {Schema} from '../src/lib/api/types';
import {makeRun,now,ref} from './fixtures';
export function conversationView(question=true):Schema['RunConversationView']{
 const run=makeRun(question?'waiting_for_user':'running',4);
 return {protocol:'conversation-v1',run,input_revision:1,continuation_request_ids:[],...(question?{question:{run_revision:4,run_status:'waiting_for_user',input_revision:1,question:{protocol:'conversation-v1',run_id:run.id,conversation_id:run.conversation_id,item_id:'question-one',revision:2,input_revision:1,prompt:{text:'请提供要分析的材料范围。',reason:'缺少原材料，当前无法作出有依据的分析。',options:['仅分析第一段','分析全部材料']},decision_record_ref:ref('content','decision-one','3'),state:'open',created_at:now}}}:{})};
}
export function continuationReceipt(requestId='request-one',kind:Schema['RunInputPatch']['kind']='clarification_answer',state:Schema['RunInputPatch']['state']='accepted'):Schema['RunContinuationReceipt']{
 return {protocol:'conversation-v1',run:makeRun('queued',5),patch:{protocol:'conversation-v1',run_id:'run-one',conversation_id:'conv-one',request_id:requestId,input_ref:ref('input','input-answer'),kind,base_input_revision:1,input_revision:2,state,created_at:now,...(kind==='clarification_answer'?{question_item_id:'question-one',question_revision:2}:{}),...(state==='applied'?{applied_at:now}:{})},event_seq:8};
}
