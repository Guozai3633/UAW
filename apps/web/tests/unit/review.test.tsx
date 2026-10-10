import {afterEach,it,expect,vi} from 'vitest';
import {cleanup,render,screen,fireEvent,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {createHash} from 'node:crypto';
import {Review} from '../../src/features/review/Review';
import {checkReview,type ReviewSnapshot,type ReviewPort} from '../../src/features/review/port';
import {makeItem,makeRun,ref,now} from '../fixtures';
const pin=ref('artifact','artifact-one');
const content='# 正文报告\n\n实际内容与来源。';
function snapshot():ReviewSnapshot{return{artifact:{id:pin.id,version:'1',title:'报告',format_kind:'markdown',media_type:'text/markdown',content_ref:ref('content','body-one'),size_bytes:Buffer.byteLength(content),content_hash:createHash('sha256').update(content).digest('hex'),provenance_refs:[ref('input','input-one')],verification_refs:[ref('verification','report-one')],created_at:now},content,
 report:{id:'report-one',contract_ref:ref('content','contract-one'),target_refs:[pin],checks:[],verdicts:[],outcome:'succeeded',limitations:['受控组件测试不证明LLM质量'],created_at:now},bundleRef:ref('content','bundle-one'),contractRef:ref('content','contract-one'),requiresAcceptance:true};}
function show(port?:ReviewPort){const item=makeItem('artifact-item','artifact','摘要');item.resource_refs=[pin];const accepted=vi.fn();render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}})}><Review items={[item]} run={makeRun('waiting_for_user')} port={port} identity="user-one" connected onAccepted={accepted}/></QueryClientProvider>);return accepted;}
afterEach(cleanup);
it('missing production review port leaves content and acceptance explicitly unavailable',()=>{show();expect(screen.getByRole('button',{name:'接受整份成果'})).toBeDisabled();expect(screen.getByText('合同接受入口尚未接入。')).toBeInTheDocument();});
it('rejects altered content and stale artifact versions',async()=>{const v=snapshot();await checkReview(v,pin);await expect(checkReview({...v,content:content+'篡改'},pin)).rejects.toThrow('摘要或长度');await expect(checkReview(v,{...pin,version:'2'})).rejects.toThrow('版本');});
it('accepts exact current bundle receipt then queries Run; does not mark it completed',async()=>{
 const v=snapshot();const read=vi.fn(async()=>structuredClone(v));const accept=vi.fn(async(value:ReviewSnapshot)=>({kind:'ok' as const,payload:{bundle_ref:value.bundleRef,principal:{id:'user-one',kind:'user' as const,auth_session_id:'session-one'},decision:'accept' as const,created_at:now},output_refs:[]}));const accepted=show({read,accept});
 await screen.findByRole('heading',{name:'正文报告'});await waitFor(()=>expect(screen.getByRole('button',{name:'接受整份成果'})).toBeEnabled());fireEvent.click(screen.getByRole('button',{name:'接受整份成果'}));await waitFor(()=>expect(accepted).toHaveBeenCalledOnce());expect(read).toHaveBeenCalledTimes(2);expect(accept.mock.calls[0]?.[0]).toEqual(v);expect(screen.getByRole('status')).toHaveTextContent('正在读取运行状态');
});
it('changed verification before acceptance blocks dispatch',async()=>{let reads=0;const accept=vi.fn();show({read:async()=>{const v=snapshot();if(++reads>1)v.report.limitations=['new restriction'];return v;},accept});await screen.findByRole('heading',{name:'正文报告'});fireEvent.click(screen.getByRole('button',{name:'接受整份成果'}));await screen.findByText('成果或合同版本已变化，请刷新后重新审阅。');expect(accept).not.toHaveBeenCalled();});

it('unknown dispatched acceptance blocks repeated decisions in the current view',async()=>{const accept=vi.fn(async()=>{throw new Error('接受结果未知，先查询原请求');});show({read:async()=>snapshot(),accept});await screen.findByRole('heading',{name:'正文报告'});fireEvent.click(screen.getByRole('button',{name:'接受整份成果'}));await screen.findByText('接受结果未知，先查询原请求');expect(screen.getByRole('button',{name:'接受整份成果'})).toBeDisabled();expect(accept).toHaveBeenCalledOnce();});

it('honors optional fixed Ref hash and shows failed requirements with their actual reason and limits',async()=>{const v=snapshot();await expect(checkReview(v,{...pin,content_hash:'f'.repeat(64)})).rejects.toThrow('版本');v.report.outcome='failed';v.report.verdicts=[{requirement_id:'requirement-one',state:'failed',evidence_refs:[],reason:'资料缺少核验依据',limitations:['仍须人工复核']}];show({read:async()=>v,accept:vi.fn()});await screen.findByText('要求 requirement-one · 未通过');expect(screen.getByText('资料缺少核验依据')).toBeInTheDocument();expect(screen.getByText('仍须人工复核')).toBeInTheDocument();});
