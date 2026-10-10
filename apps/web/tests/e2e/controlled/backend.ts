// Explicit intercepted backend fixture. No SQL, LLM, Runner, product auth or acceptance.
import type {Page,Route} from '@playwright/test';
import {conversation,models,makeRun,makeItem,frame,approval,now,ref,ok,denied} from '../../fixtures';
import type {Event,Payload} from '../../../src/lib/api/types';
export async function controlledBackend(page:Page,scenario:'artifact'|'approval'|'running'|'unknown'|'denied'='artifact'){
 const state={turnPosts:0,controlPosts:0,decisionPosts:0,submitted:false,original:'',approval:structuredClone(approval),
  run:makeRun(scenario==='artifact'?'completed':scenario==='approval'?'waiting_for_user':'running'),cancelled:false,disconnect:false,staleApproval:false,
  decisionBody:undefined as unknown};
 await page.addInitScript(()=>{window.uawWebHost={session:()=>({identityKey:'controlled:test-user:workspace-one:epoch-1'})};});
 const payloads=new Map<string,Payload>();
 function event(seq:number,payload:Payload):Event{const id='event-'+seq;payloads.set(id,payload);return{event_id:id,stream_id:conversation.id,seq,type:payload.action,schema_version:'0.1',occurred_at:now,payload_ref:ref('event',id)};}
 await page.route('**/v1/**',async(route:Route)=>{
  const req=route.request();const path=new URL(req.url()).pathname;
  if(state.disconnect)return route.abort('connectionfailed');
  if(scenario==='denied')return route.fulfill({status:403,json:denied()});
  let data:unknown;const body=req.method()==='POST'?req.postDataJSON():undefined;
  if(path==='/v1/models')data=models;
  else if(path==='/v1/conversations')data=req.method()==='POST'?conversation:{items:[conversation],snapshot_revision:1};
  else if(path==='/v1/conversations/conv-one')data=conversation;
  else if(path.endsWith('/turns')){state.turnPosts++;state.original=body.payload.text;state.submitted=true;
   if(scenario==='unknown')return route.abort('connectionfailed');data=state.run;
  }else if(path.endsWith('/items')){
   const items=state.submitted?[makeItem('user-one','user_message',state.original),makeItem('understanding-one','understanding',frame.summary!)]:[];
   if(state.submitted&&scenario==='artifact'){const artifact=makeItem('artifact-item','artifact','# 材料报告\n\n|要点|来源|\n|---|---|\n|保留原文|用户材料|');artifact.resource_refs=[ref('artifact','artifact-one')];items.push(artifact);}
   if(state.submitted&&scenario==='approval'){const i=makeItem('approval-item','approval',approval.summary);i.resource_refs=[ref('approval',approval.id)];items.push(i);}
   data={items,snapshot_revision:state.submitted?3:0};
  }else if(path.endsWith('/events')){const events=state.submitted?[event(1,{action:'run.updated',parameters:state.run}),event(2,{action:'task.frame.committed',parameters:frame})]:[];
   if(state.submitted&&scenario==='approval')events.push(event(3,{action:'approval.required',parameters:state.approval}));
   data={items:events,snapshot_revision:events.length};
  }else if(path.endsWith('/payload'))data=payloads.get(path.split('/').at(-2)!);
  else if(path.endsWith('/frame'))data=frame;
  else if(path.endsWith('/control')){state.controlPosts++;state.cancelled=true;data={operation_id:'control-one',status:'accepted'};}
  else if(path==='/v1/runs/run-one'){if(state.cancelled)state.run=makeRun('cancelled',2);data=state.run;}
  else if(path.endsWith('/decisions')){state.decisionPosts++;state.decisionBody=body;
   state.approval={...state.approval,revision:2,status:body.payload.decision.decision==='decline'?'declined':'approved'};
   data={id:'grant-one',approval_ref:ref('approval',approval.id,'2'),actor:{id:'user-one',kind:'user',auth_session_id:'session-one'},decision:body.payload.decision,issued_at:now};
  }else if(path==='/v1/approvals/approval-one'){data=state.staleApproval?{...state.approval,revision:2,arguments_hash:'b'.repeat(64)}:state.approval;}
  else return route.fulfill({status:503,json:{kind:'failed',failure:{code:'capability_unavailable',category:'dependency',message:'受控fixture未声明该接口',retryable:false,failed_phase:'admission'},output_refs:[]}});
  return route.fulfill({status:200,json:ok(data)});
 });
 return state;
}
