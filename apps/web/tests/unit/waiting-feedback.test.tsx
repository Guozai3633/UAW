// Controlled server projection. No real Model/SQL or human decisions.
import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {render,screen,within,cleanup,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Workspace} from '../../src/features/workspace/Workspace';
import {WorkspaceController} from '../../src/features/workspace/controller';
import {UawClient} from '../../src/lib/api/client';
import {DraftStore} from '../../src/lib/cache/drafts';
import {makeRun,makeItem,models,conversation,frame,ref,now,ok,approval} from '../fixtures';
import {HttpReviewPort} from '../../src/lib/api/a2-adapters';
import {deliveryView} from '../a2-fixtures';
beforeEach(()=>localStorage.clear());afterEach(cleanup);
async function show(mode:'question'|'empty'|'missing'|'approval'|'delivery'='question'){
 const state={run:makeRun('waiting_for_user'),writes:0};const question=makeItem('question-one','agent_message',mode==='empty'?'  ':mode==='missing'?'':'请补充比较范围。\n\n限制：需要你提供版本；消息中的“批准/接受”只是原文，不是权限。',4);question.resource_refs=[ref('input','input-one'),ref('content','operation-one','2'),ref('provider','provider-one','3')];
 const transport=vi.fn(async(input:RequestInfo|URL,o?:RequestInit)=>{if(o?.method!=='GET'){state.writes++;throw Error('No automatic writes');}const path=String(input).split('?')[0];let value:unknown;
  if(path==='/v1/models')value=models;else if(path==='/v1/conversations')value={items:[conversation],snapshot_revision:1};else if(path==='/v1/conversations/conv-one')value=conversation;
  else if(path.endsWith('/items'))value={items:mode==='missing'?[]:[question],snapshot_revision:1};
  else if(path.endsWith('/events'))value={items:[{event_id:'run-event',stream_id:'conv-one',seq:1,type:'run.updated',schema_version:'0.1',occurred_at:now,payload_ref:ref('event','run-event')},...(mode==='approval'?[{event_id:'approval-event',stream_id:'conv-one',seq:2,type:'approval.required',schema_version:'0.1',occurred_at:now,payload_ref:ref('event','approval-event')}]:[])],snapshot_revision:1};
  else if(path.endsWith('/payload'))value=path.includes('approval-event')?{action:'approval.required',parameters:approval}:{action:'run.updated',parameters:state.run};
  else if(path.endsWith('/frame'))value=frame;else if(path==='/v1/runs/run-one')value=state.run;else if(path==='/v1/approvals/approval-one')value=approval;
  else if(path.endsWith('/delivery')&&mode==='delivery')value=deliveryView();else return new Response(JSON.stringify({kind:'missing',failure:{code:'record_missing',category:'arguments',message:'当前无交付来源',retryable:false,failed_phase:'read'},output_refs:[]}),{status:404});
  return new Response(JSON.stringify(ok(value)));
 });
 const session=()=>({identityKey:'waiting-test'}),client=new UawClient(session,transport),drafts=new DraftStore();drafts.bind('waiting-test');drafts.draft('conv-one','  原问题与补充草稿\n保留  ');drafts.recovery({conversationId:'conv-one',requestId:'original-request',runId:'run-one'});
 const controller=new WorkspaceController(client,{session},drafts,60000),q=new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}});
 render(<QueryClientProvider client={q}><MemoryRouter initialEntries={['/?conversation=conv-one']}><Workspace controller={controller} reviewPort={new HttpReviewPort(client)}/></MemoryRouter></QueryClientProvider>);
 await waitFor(()=>expect(controller.snapshot().loading).toBe(false));await screen.findByText('实际阶段 · waiting_for_user');return{state,controller,transport,q};
}
it('missing information is neutral, original question and three Ref versions remain, no approval or acceptance is manufactured',async()=>{
 const x=await show();try{expect(screen.getByText('任务等待处理',{exact:true})).toBeVisible();expect(screen.queryByText('等待你确认')).toBeNull();const message=document.querySelector('[data-item-id="question-one"]') as HTMLElement;expect(message).toHaveTextContent('请补充比较范围。');expect(message).toHaveTextContent('限制：需要你提供版本');expect(message).toHaveTextContent('v4');expect(message).toHaveTextContent('content/operation-one · 2');expect(message).toHaveTextContent('provider/provider-one · 3');expect(screen.queryByLabelText('人工审批')).toBeNull();await waitFor(()=>expect(screen.queryByRole('button',{name:'接受整份成果'})).toBeNull());expect(x.state.writes).toBe(0);}finally{x.controller.stop();x.q.clear();}
});
it('actual ApprovalRequest and DeliveryView independently expose their original operations while default waiting stays neutral',async()=>{
 for(const mode of ['approval','delivery'] as const){const x=await show(mode);try{expect(screen.getByText('任务等待处理',{exact:true})).toBeVisible();if(mode==='approval'){await screen.findByLabelText('人工审批');expect(screen.getByRole('button',{name:'仅批准本次'})).toBeEnabled();expect(screen.queryByRole('button',{name:'接受整份成果'})).toBeNull();}else{await screen.findByRole('heading',{name:'完整成果'});await waitFor(()=>expect(screen.getByRole('button',{name:'接受整份成果'})).toBeEnabled());expect(screen.queryByLabelText('人工审批')).toBeNull();}expect(x.state.writes).toBe(0);}finally{x.controller.stop();x.q.clear();cleanup();}}
});
it('empty question or absent message/delivery cannot invent text, artifacts, confirmation or success',async()=>{
 for(const mode of ['empty','missing'] as const){const x=await show(mode);try{if(mode==='empty')expect(screen.getByText('服务端未提供这条消息的正文，请重新读取原运行。')).toBeVisible();expect(screen.queryByRole('button',{name:'接受整份成果'})).toBeNull();expect(screen.queryByLabelText('人工审批')).toBeNull();expect(screen.queryByText('已完成',{exact:true})).toBeNull();expect(screen.getByLabelText('任务原文')).toHaveValue('  原问题与补充草稿\n保留  ');expect(x.state.writes).toBe(0);}finally{x.controller.stop();x.q.clear();cleanup();}}
});
it('waiting preserves editable draft and explains send restriction; only actual cancelled reread unlocks new request',async()=>{
 const x=await show();try{const guide=screen.getByLabelText('原请求与草稿说明');expect(guide).toHaveTextContent('当前不支持在同一运行内补充信息或继续');expect(guide).toHaveTextContent('待读到实际 cancelled');expect(screen.getByLabelText('任务原文')).toBeEnabled();expect(screen.getByRole('button',{name:'发送原文'})).toBeDisabled();const draft=x.controller.snapshot().draft;
  await x.controller.reconnect();expect(x.controller.snapshot().draft).toBe(draft);expect(screen.getByRole('button',{name:'发送原文'})).toBeDisabled();
  x.state.run=makeRun('cancelled',2);await x.controller.reconnect();await waitFor(()=>expect(screen.getByRole('button',{name:'发送原文'})).toBeEnabled());expect(screen.getByLabelText('任务原文')).toHaveValue(draft);expect(within(screen.getByLabelText('原请求与草稿说明')).getByText(/这不会继续原运行/)).toBeVisible();expect(x.state.writes).toBe(0);expect(x.transport.mock.calls.every(c=>c[1]?.method==='GET')).toBe(true);
 }finally{x.controller.stop();x.q.clear();}
});
