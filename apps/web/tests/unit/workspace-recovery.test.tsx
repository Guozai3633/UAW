import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,waitFor,act,cleanup} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Workspace} from '../../src/features/workspace/Workspace';
import {WorkspaceController} from '../../src/features/workspace/controller';
import {DraftStore} from '../../src/lib/cache/drafts';
import {UawClient} from '../../src/lib/api/client';
import {conversation,models,makeRun,frame,ok} from '../fixtures';
afterEach(()=>{cleanup();localStorage.clear();});
it('another conversation explains its blocked draft and returns to the original Run without deleting IDs or dispatching',async()=>{
 const identity='user-one';localStorage.clear();const store=new DraftStore();store.bind(identity);
 const recovery={requestId:'request-original',conversationId:'conv-one',runId:'run-one'};store.recovery(recovery);store.draft('conv-two','  学术草稿原文\n保留  ');
 const second={...conversation,id:'conv-two',title:'学术草稿会话'};
 const transport=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
  if(options?.method && options.method!=='GET')throw Error('Navigation must not dispatch');
  const path=String(input).split('?')[0];let data:unknown;
  if(path==='/v1/models')data=models;else if(path==='/v1/conversations')data={items:[conversation,second],snapshot_revision:1};
  else if(path.endsWith('/items')||path.endsWith('/events'))data={items:[],snapshot_revision:1};
  else if(path.endsWith('/frame'))data=frame;else if(path==='/v1/runs/run-one')data=makeRun('running');else data=path.endsWith('/conv-two')?second:conversation;
  return new Response(JSON.stringify(ok(data)));
 });
 const controller=new WorkspaceController(new UawClient(()=>({identityKey:identity}),transport),{session:()=>({identityKey:identity})},store,60000);
 const view=render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><Workspace controller={controller}/></MemoryRouter></QueryClientProvider>);
 try{
  await waitFor(()=>expect(controller.snapshot().active?.id).toBe('conv-one'));
  await act(()=>controller.open('conv-two'));await screen.findByRole('button',{name:'返回原请求会话'});
  expect(screen.getByRole('button',{name:'发送原文'})).toBeDisabled();expect(screen.getByRole('textbox',{name:'任务原文'})).toHaveValue('  学术草稿原文\n保留  ');
  expect(controller.snapshot().connected).toBe(true);expect(store.read().recovery).toEqual(recovery);
  fireEvent.click(screen.getByRole('button',{name:'返回原请求会话'}));await waitFor(()=>expect(controller.snapshot().active?.id).toBe('conv-one'));
  await waitFor(()=>expect(controller.snapshot().run?.id).toBe('run-one'));expect(store.read().recovery).toEqual(recovery);
  await act(()=>controller.open('conv-two'));expect(screen.getByRole('textbox',{name:'任务原文'})).toHaveValue('  学术草稿原文\n保留  ');
  expect(transport.mock.calls.every(call=>call[1]?.method==='GET')).toBe(true);expect(store.read().recovery?.requestId).toBe('request-original');
 }finally{view.unmount();controller.stop();}
});
