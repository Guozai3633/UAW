import {UawClient} from '../../lib/api/client';
import {canonical} from '../../lib/api/canonical';
import {terminal} from '../../lib/events/projection';
import type {Run,Schema} from '../../lib/api/types';
export type ConversationView=Schema['RunConversationView'];
export type ContinuationReceipt=Schema['RunContinuationReceipt'];
export type ControlKind='clarification_answer'|'correction';
export type ControlScope={conversationId:string;runId:string};
export interface ConversationPort {
 read(run:Run,signal:AbortSignal):Promise<ConversationView>;
 question(scope:ControlScope,itemId:string,signal:AbortSignal):Promise<Schema['ClarificationView']>;
 lookup(scope:ControlScope,requestId:string,signal:AbortSignal):Promise<ContinuationReceipt>;
 submit(view:ConversationView,kind:ControlKind,text:string,meta:Schema['ConversationRequestMeta'],signal:AbortSignal):Promise<ContinuationReceipt>;
}
export function checkView(v:ConversationView,run:Run){
 if(v.run.id!==run.id||v.run.conversation_id!==run.conversation_id||v.run.revision<run.revision)throw Error('原Run/会话或当前版本不匹配。');
 const q=v.question;if(q&&(q.run_revision!==v.run.revision||q.run_status!==v.run.status||q.input_revision!==v.input_revision||q.question.run_id!==v.run.id||q.question.conversation_id!==v.run.conversation_id||q.question.input_revision!==v.input_revision||q.question.state!=='open'||v.run.status!=='waiting_for_user'))throw Error('问题与当前原Run/输入版本不匹配。');
}
export function checkReceipt(v:ContinuationReceipt,scope:ControlScope,requestId:string){
 if(v.run.id!==scope.runId||v.run.conversation_id!==scope.conversationId||v.patch.run_id!==scope.runId||v.patch.conversation_id!==scope.conversationId||v.patch.request_id!==requestId||v.patch.input_revision!==v.patch.base_input_revision+1)throw Error('补充回执与原会话/Run/请求或输入版本不匹配。');
}
const pin=(v:ConversationView)=>canonical({run:v.run,input_revision:v.input_revision,...(v.question?{question:v.question}:{})});
export class HttpConversationPort implements ConversationPort {
 private writing:symbol|undefined;
 constructor(private client:UawClient){}
 private identity(){const s=this.client.currentSession();if(!s?.identityKey||s.principal?.kind!=='user')throw Error('当前浏览器用户不可用。');return s.identityKey;}
 private guard(identity:string,signal:AbortSignal){signal.throwIfAborted();if(identity!==this.client.currentSession()?.identityKey)throw Error('对话读取期间身份已变化。');}
 async read(run:Run,signal:AbortSignal){const identity=this.identity();const v=await this.client.runConversation(run.id,signal);this.guard(identity,signal);checkView(v,run);return v;}
 async question(scope:ControlScope,itemId:string,signal:AbortSignal){const identity=this.identity();const v=await this.client.clarification(scope.runId,itemId,signal);this.guard(identity,signal);if(v.question.run_id!==scope.runId||v.question.conversation_id!==scope.conversationId||v.question.item_id!==itemId)throw Error('指定问题不属于原Run/会话。');return v;}
 async lookup(scope:ControlScope,requestId:string,signal:AbortSignal){const identity=this.identity();const v=await this.client.continuation(scope.runId,requestId,signal);this.guard(identity,signal);checkReceipt(v,scope,requestId);return v;}
 async submit(old:ConversationView,kind:ControlKind,text:string,meta:Schema['ConversationRequestMeta'],signal:AbortSignal){
  if(this.writing)throw Error('原补充请求仍在提交。');const identity=this.identity(),token=Symbol('continuation');this.writing=token;
  try{const fixed=structuredClone(old),fixedMeta=structuredClone(meta),exactText=text;const current=await this.read(fixed.run,signal);this.guard(identity,signal);
   if(terminal(current.run.status)||pin(fixed)!==pin(current)||fixedMeta.expected_revision!==fixed.run.revision)throw Error('原Run/输入/问题版本已变化；草稿保留，请重新读取。');
   const scope={runId:current.run.id,conversationId:current.run.conversation_id};let receipt:ContinuationReceipt;
   if(kind==='clarification_answer'){const q=current.question;if(!q)throw Error('没有当前开放问题，不能回答。');const fresh=await this.question(scope,q.question.item_id,signal);this.guard(identity,signal);if(canonical(fresh)!==canonical(q))throw Error('原问题已变化；草稿保留，请重新读取。');
    receipt=await this.client.answer(scope.runId,q.question.item_id,{expected_input_revision:current.input_revision,expected_question_revision:q.question.revision,text:exactText,attachment_refs:[]},fixedMeta,signal);
   }else receipt=await this.client.correct(scope.runId,{expected_input_revision:current.input_revision,text:exactText,attachment_refs:[]},fixedMeta,signal);
   this.guard(identity,signal);checkReceipt(receipt,scope,fixedMeta.request_id);const patch=receipt.patch;
   if(patch.kind!==kind||patch.base_input_revision!==current.input_revision||kind==='clarification_answer'&&(patch.question_item_id!==current.question!.question.item_id||patch.question_revision!==current.question!.question.revision))throw Error('补充回执未绑定原提交版本。');
   return receipt;
  }finally{if(this.writing===token)this.writing=undefined;}
 }
}
