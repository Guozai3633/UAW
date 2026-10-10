import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {FileText,ShieldCheck,ExternalLink} from 'lucide-react';
import {Markdown} from '../../components/Markdown';
import type {DisplayItem,Ref,Run} from '../../lib/api/types';
import {ApiFailure,requestMeta} from '../../lib/api/client';
import {validate} from '../../lib/api/validation';
import {type ReviewPort,checkReview,sameReview} from './port';
export function Review({items,run,port,identity,connected,decisionAllowed=true,onAccepted}:{items:DisplayItem[];run?:Run;port?:ReviewPort;identity:string;connected:boolean;decisionAllowed?:boolean;onAccepted:()=>void}){
 const artifacts=items.filter(i=>i.type==='artifact');const [selected,setSelected]=useState('');
 const item=artifacts.find(i=>i.id===selected)??artifacts.at(-1);const ref=item?.resource_refs.find(r=>r.kind==='artifact');
 const actions=useRef(new Set<AbortController>());
 useEffect(()=>()=>{for(const a of actions.current)a.abort();actions.current.clear();},[identity,connected,ref?.id,ref?.version,ref?.content_hash,run?.id,run?.revision,run?.status,decisionAllowed]);
 const [busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[decisionPending,setDecisionPending]=useState(false);
 useEffect(()=>{setDecisionPending(false);setNotice('');},[identity,ref?.id,ref?.version,ref?.content_hash]);
 const query=useQuery({queryKey:['review',identity,run?.id,ref?.id,ref?.version,ref?.content_hash],enabled:!!port&&!!run&&connected,
  staleTime:0,gcTime:0,retry:false,refetchInterval:3000,queryFn:async({signal})=>{try{const v=await port!.read(ref,run!.id,signal);await checkReview(v,ref??v.delivery?.artifact_ref??{kind:'artifact',id:v.artifact.id,version:v.artifact.version});return v;}catch(e){if(e instanceof ApiFailure&&e.result.kind==='missing')return null;throw e;}}});
 async function accept(){if(!port||!run||!query.data||busy||decisionPending||query.data.decisionUncertain||query.data.delivery?.acceptance||query.data.delivery?.stale||!connected||!decisionAllowed||run.status!=='waiting_for_user')return;
  setBusy(true);setNotice('');const abort=new AbortController();actions.current.add(abort);let dispatched=false;try{
   const current=await port.read(ref,run.id,abort.signal);await checkReview(current,ref??current.delivery?.artifact_ref??{kind:'artifact',id:current.artifact.id,version:current.artifact.version});
   if(!await sameReview(query.data,current))throw new Error('成果或合同版本已变化，请刷新后重新审阅。');
   abort.signal.throwIfAborted();if(current.delivery?.stale||current.delivery?.acceptance||current.decisionUncertain)throw new Error('成果过时、已有决定或接受尚待对账');
   if(!current.requiresAcceptance)throw new Error('此合同不要求用户接受。');
   dispatched=true;const result=await port.accept(current,requestMeta(),abort.signal);abort.signal.throwIfAborted();
   if(result.kind!=='ok')throw new Error(result.failure?.message??'接受尚未确认');
   validate('CompletionAcceptance',result.payload);
   if(result.payload.decision!=='accept'||!samePin(result.payload.bundle_ref,current.bundleRef))throw new Error('接受回执版本不匹配');
   setDecisionPending(true);setNotice('接受已确认，正在读取运行状态。');onAccepted();
  }catch(e){if(dispatched)setDecisionPending(true);setNotice(e instanceof Error?e.message:'结果未知，请查询当前版本，不会自动重试。');if(dispatched){void query.refetch();onAccepted();}}
  finally{actions.current.delete(abort);setBusy(false);}
 }
 return <aside className="review-panel" aria-label="成果侧栏"><div className="panel-title"><span><FileText size={16}/>成果</span><span className="count">{artifacts.length}</span></div>
 {!item&&!query.data?<div className="review-empty"><div className="empty-icon"><FileText size={27}/></div><h3>每一份成果，都有出处</h3><p>{run?'当前 Run 尚无已登记成果，请读取当前成果。':'报告与文本将在这里出现。'}<br/>查看正文、来源与逐项核验。</p></div>:<>
 <div className="artifact-tabs">{artifacts.map(a=><button className={a.id===item?.id?'selected':''} key={a.id} onClick={()=>{setSelected(a.id);setNotice('');}}>{a.text.split('\n')[0].slice(0,36)||'文本成果'}</button>)}</div>
 <div className="review-body"><span className="eyebrow">{query.data?.artifact.media_type??'成果摘要'} · v{ref?.version??query.data?.artifact.version??item?.revision}</span><h3>{query.data?.artifact.title??'本次成果'}</h3>
 {query.data?.delivery&&<p className="muted">原要求：{query.data.delivery.contract.goal}</p>}
 <Markdown text={query.data?.content??item?.text??''}/>
 <div className="verification"><ShieldCheck size={16}/><strong>逐项核验</strong></div>
 {query.data?<><p>{query.data.report.outcome}</p>{query.data.report.verdicts.map(v=><section className="verdict" key={v.requirement_id}><strong>要求 {query.data?.delivery?.contract.requirements.find(r=>r.id===v.requirement_id)?.text??v.requirement_id} · {checkLabel(v.state)}</strong><p>{v.reason}</p>{v.limitations.map((line,i)=><p key={i}>{line}</p>)}<details><summary>核验依据与版本 · {v.evidence_refs.length}</summary>{v.evidence_refs.map((r,i)=><p key={i}>{r.kind}/{r.id}@{r.version}</p>)}</details></section>)}{query.data.report.checks.map(c=><section className="verdict" key={c.id}><strong>{c.kind} · {checkLabel(c.state)}</strong><p>{c.summary}</p><details><summary>核验依据与版本 · {c.evidence_refs.length}</summary>{c.evidence_refs.map((r,i)=><p key={i}>{r.kind}/{r.id}@{r.version}</p>)}</details></section>)}{query.data.report.limitations.map((v,i)=><p key={i}>{v}</p>)}</>:<p className="muted">尚无可用的完整正文与核验，当前仅展示服务端条目摘要。</p>}
 <details><summary>来源与版本 <ExternalLink size={12}/></summary><ul>{(query.data?.artifact.provenance_refs??item?.resource_refs??[]).map((r,i)=><li key={i}>{r.kind} / {r.id} / {r.version}</li>)}</ul></details>
 {query.error&&<p role="alert" className="error-text">{query.error.message}</p>}
 {query.data?.delivery?.stale&&<p role="alert">此成果相对当前任务已过时，仅供查阅。</p>}{query.data?.delivery?.acceptance&&<p role="status">实际合同决定：{query.data.delivery.acceptance.decision} · {query.data.delivery.acceptance.created_at}</p>}{query.data?.decisionUncertain&&<p role="status">接受结果未知；只查询实际 acceptance，无回执不重发。</p>}
 <button className="primary accept" disabled={!query.data?.requiresAcceptance||run?.status!=='waiting_for_user'||!connected||!decisionAllowed||busy||decisionPending||query.data?.decisionUncertain||!!query.data?.delivery?.acceptance||query.data?.delivery?.stale||query.isError} onClick={()=>void accept()}>{busy?'正在核对版本…':'接受整份成果'}</button>
 {!port&&<p className="muted">合同接受入口尚未接入。</p>}{notice&&<p role="status">{notice}</p>}
 </div></>}
 {port&&run&&<button className="review-refresh" disabled={!connected||busy} onClick={()=>void query.refetch()}>读取当前成果与接受回执</button>}{query.error&&(!item&&!query.data)&&<p role="alert" className="error-text">{query.error.message}</p>}
 </aside>;
}
const samePin=(a:Ref,b:Ref)=>a.kind===b.kind&&a.id===b.id&&a.version===b.version&&a.content_hash===b.content_hash;

const checkLabel=(state:string)=>({passed:'已通过',failed:'未通过',blocked:'受阻',not_run:'未运行'}[state]??state);
