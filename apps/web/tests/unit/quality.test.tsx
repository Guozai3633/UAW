import React from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QualityPanel} from '../../src/features/quality/QualityPanel';
import type {QualityPort,QualityView} from '../../src/features/quality/port';
import {TransportError,UawClient} from '../../src/lib/api/client';
import {HttpQualityPort} from '../../src/features/quality/port';
import {TaskUnderstanding} from '../../src/features/workspace/TaskUnderstanding';
import {validate} from '../../src/lib/api/validation';
import raw from '../fixtures/quality.json';

afterEach(cleanup);
function fixture(){
 let current=structuredClone(raw) as QualityView;
 const port:QualityPort={
  list:vi.fn(async()=>({items:[{id:current.id,revision:current.revision,title:current.title,status:current.status,updated_at:current.updated_at,origin:current.origin}],next_cursor:null})),
  get:vi.fn(async()=>structuredClone(current)),
  save:vi.fn(async(_view,judgments,submit)=>{current={...current,revision:current.revision+1,judgments:structuredClone(judgments),status:submit?'submitted':'draft'};return current;}),
  export:vi.fn(),feedback:vi.fn(async()=>({items:[]})),saveFeedback:vi.fn(),
 };
 return {port,current:()=>current};
}
async function open(port:QualityPort){render(<QualityPanel port={port} onClose={()=>{}}/>);fireEvent.click(await screen.findByRole('button',{name:/受控质量样本/}));await screen.findByRole('heading',{name:'实际完整回答'});}

it('opens the original material and answer with no ratings or human declaration selected',async()=>{
 const {port}=fixture();await open(port);
 expect(screen.getByText('核对给定数量：2+3。')).toBeInTheDocument();expect(screen.getByText('合计5。')).toBeInTheDocument();
 expect(screen.getByText('第一项2；第二项3。')).toBeInTheDocument();
 for(const select of screen.getAllByRole('combobox'))expect(select).toHaveValue('');
 expect(screen.getByRole('checkbox')).not.toBeChecked();expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeDisabled();expect(port.save).not.toHaveBeenCalled();
 expect(screen.getByText('原模型核验（不是人工事实判断）')).toBeInTheDocument();
});

it('saves unknown judgments as a draft and reopens the persisted revision',async()=>{
 const {port}=fixture();await open(port);
 fireEvent.change(screen.getByLabelText('审阅意见'),{target:{value:'还需要查阅原始依据。'}});
 fireEvent.click(screen.getByRole('button',{name:'保存审阅草稿'}));
 await screen.findByText('草稿已保存，可以关闭后重新打开。');
 expect(port.save).toHaveBeenCalledOnce();const args=vi.mocked(port.save).mock.calls[0];
 expect(args[1][0].critical_error).toBeNull();expect(args[2]).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:'重新读取此审阅'}));
 await screen.findByText('审阅 v2 · 草稿');expect(screen.getByLabelText('审阅意见')).toHaveValue('还需要查阅原始依据。');
});

it('keeps uncertain writes disabled until an explicit re-read and never retries automatically',async()=>{
 const {port}=fixture();port.save=vi.fn(async()=>{throw new TransportError(true);});await open(port);
 fireEvent.click(screen.getByRole('button',{name:'保存审阅草稿'}));
 await screen.findByText('保存结果尚未确认，先重新读取；不会自动重发。');
 expect(screen.getByRole('button',{name:'保存审阅草稿'})).toBeDisabled();expect(port.save).toHaveBeenCalledOnce();
 fireEvent.click(screen.getByRole('button',{name:'重新读取此审阅'}));
 await waitFor(()=>expect(screen.getByRole('button',{name:'保存审阅草稿'})).toBeEnabled());
 expect(port.save).toHaveBeenCalledOnce();
});

it('requires the explicit declaration plus completed mandatory judgments for submission',async()=>{
 const {port}=fixture();await open(port);
 fireEvent.change(screen.getByLabelText('题目与参考标准'),{target:{value:'needs_revision'}});
 fireEvent.change(screen.getByLabelText('是否有关键错误'),{target:{value:'true'}});
 fireEvent.change(screen.getByLabelText('是否已亲自核对参考依据'),{target:{value:'true'}});
 fireEvent.change(screen.getByLabelText('审阅意见'),{target:{value:'这是受控交互测试，不是真人评价。'}});
 expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeDisabled();
 fireEvent.click(screen.getByRole('checkbox'));
 expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeEnabled();
 fireEvent.click(screen.getByRole('button',{name:'提交我的审阅'}));
 await screen.findByText('审阅已提交并冻结。它不会接受成果或结束原任务。');
 expect(vi.mocked(port.save).mock.calls[0][2]).toBe(true);expect(screen.queryByRole('button',{name:'提交我的审阅'})).not.toBeInTheDocument();
});

it('does not submit an acceptable judgment while evidence is unknown or a critical error remains',async()=>{
 const {port}=fixture();await open(port);
 fireEvent.change(screen.getByLabelText('题目与参考标准'),{target:{value:'verified'}});
 fireEvent.change(screen.getByLabelText('是否有关键错误'),{target:{value:'false'}});
 fireEvent.change(screen.getByLabelText('是否已亲自核对参考依据'),{target:{value:'true'}});
 fireEvent.change(screen.getByLabelText('回答质量是否可接受'),{target:{value:'true'}});
 fireEvent.change(screen.getByLabelText('审阅意见'),{target:{value:'Controlled consistency test; not a human rating.'}});
 fireEvent.click(screen.getByRole('checkbox'));
 expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeDisabled();
 fireEvent.change(screen.getByLabelText('是否虚构引用或依据'),{target:{value:'true'}});
 expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeDisabled();
 fireEvent.change(screen.getByLabelText('是否虚构引用或依据'),{target:{value:'false'}});
 expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeEnabled();
 fireEvent.change(screen.getByLabelText('是否有关键错误'),{target:{value:'true'}});
 expect(screen.getByRole('button',{name:'提交我的审阅'})).toBeDisabled();
 expect(port.save).not.toHaveBeenCalled();
});

it('clears the old identity by unmounting and ignores a late old response',async()=>{
 const old=fixture(),next=fixture();let finish!:(view:QualityView)=>void;
 old.port.get=vi.fn(()=>new Promise<QualityView>(resolve=>{finish=resolve;}));
 const first=render(<QualityPanel port={old.port} onClose={()=>{}}/>);
 fireEvent.click(await screen.findByRole('button',{name:/受控质量样本/}));first.unmount();
 render(<React.StrictMode><QualityPanel port={next.port} onClose={()=>{}}/></React.StrictMode>);
 finish(old.current());await screen.findByRole('button',{name:/受控质量样本/});
 expect(screen.queryByRole('heading',{name:'实际完整回答'})).not.toBeInTheDocument();expect(next.port.save).not.toHaveBeenCalled();
});

it('sends the exact source and CAS without a self-reported reviewer',async()=>{
 const row=structuredClone(raw) as QualityView;validate('QualityReviewView',row);
 const requests:{url:string;body:any}[]=[];
 const transport=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
  requests.push({url:String(input),body:JSON.parse(String(init?.body))});
  return new Response(JSON.stringify({kind:'ok',payload:{...row,revision:2},output_refs:[]}),{headers:{'Content-Type':'application/json'}});
 });
 const client=new UawClient(()=>({identityKey:'controlled-session',csrfHeader:{name:'X-UAW-CSRF',value:'c'.repeat(64)}}),transport);
 await new HttpQualityPort(client).save(row,row.judgments,false);
 expect(requests[0].url).toBe(`/v1/quality/reviews/${row.id}/draft`);
 expect(requests[0].body.meta.expected_revision).toBe(1);expect(requests[0].body.payload.packet_sha256).toBe(row.packet_sha256);
 expect(requests[0].body.payload.human_attested).toBeUndefined();expect(requests[0].body.payload.reviewer_id).toBeUndefined();
});

it('saves feedback against the selected Run and reopens the persisted notes',async()=>{
 const {port}=fixture();const pin={run_id:'controlled-run',run_revision:5,input_revision:2};
 let saved:any;
 port.feedback=vi.fn(async()=>({items:saved?[saved]:[]}));
 port.saveFeedback=vi.fn(async(_pin,category,notes)=>{saved={...pin,id:'controlled-feedback',revision:1,category,notes,created_at:raw.created_at,updated_at:raw.updated_at};return saved;});
 const first=render(<QualityPanel port={port} pin={pin} onClose={()=>{}}/>);
 fireEvent.click(screen.getByRole('button',{name:'当前任务反馈'}));await screen.findByText('已读取原任务反馈。');
 fireEvent.change(screen.getByLabelText('具体问题'),{target:{value:'纠正后的状态需要更容易看懂。'}});
 fireEvent.change(screen.getByLabelText('反馈类别'),{target:{value:'presentation'}});
 fireEvent.click(screen.getByRole('button',{name:'保存任务反馈'}));await screen.findByText('反馈已保存；原任务和成果接受状态保持。');
 expect(vi.mocked(port.saveFeedback).mock.calls[0].slice(0,4)).toEqual([pin,'presentation','纠正后的状态需要更容易看懂。',undefined]);
 first.unmount();render(<QualityPanel port={port} pin={{...pin,run_revision:6}} onClose={()=>{}}/>);
 fireEvent.click(screen.getByRole('button',{name:'当前任务反馈'}));
 fireEvent.click(await screen.findByRole('button',{name:/页面与状态 · v1/}));
 expect(screen.getByLabelText('具体问题')).toHaveValue('纠正后的状态需要更容易看懂。');
});

it('shows the idle task prompt without an unavailable-source warning in a new conversation',()=>{
 render(<TaskUnderstanding draft="" synchronized/>);
 expect(screen.getByText('写下你的任务，从一段原文开始。')).toBeInTheDocument();
 expect(screen.queryByText(/理解来源暂不可核对/)).not.toBeInTheDocument();
});
