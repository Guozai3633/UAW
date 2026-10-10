import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {FileText,ShieldCheck,ExternalLink} from 'lucide-react';
import {Markdown} from '../../components/Markdown';
import type {DisplayItem,Ref,Run} from '../../lib/api/types';
import {requestMeta} from '../../lib/api/client';
import {validate} from '../../lib/api/validation';
import {type ReviewPort,checkReview,sameReview} from './port';
export function Review({items,run,port,identity,connected,onAccepted}:{items:DisplayItem[];run?:Run;port?:ReviewPort;identity:string;connected:boolean;onAccepted:()=>void}){
 const artifacts=items.filter(i=>i.type==='artifact');const [selected,setSelected]=useState('');
 const item=artifacts.find(i=>i.id===selected)??artifacts.at(-1);const ref=item?.resource_refs.find(r=>r.kind==='artifact');
 const actions=useRef(new Set<AbortController>());
 useEffect(()=>()=>{for(const a of actions.current)a.abort();actions.current.clear();},[identity,connected,ref?.id,ref?.version,run?.id,run?.revision,run?.status]);
 const [busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[decisionPending,setDecisionPending]=useState(false);
 useEffect(()=>{setDecisionPending(false);setNotice('');},[identity,ref?.id,ref?.version]);
 const query=useQuery({queryKey:['review',identity,run?.id,ref?.id,ref?.version],enabled:!!port&&!!ref&&!!run&&connected,
  staleTime:0,gcTime:0,retry:false,queryFn:async({signal})=>{const v=await port!.read(ref!,run!.id,signal);await checkReview(v,ref!);return v;}});
 async function accept(){if(!port||!ref||!run||!query.data||busy||decisionPending||!connected)return;
  setBusy(true);setNotice('');const abort=new AbortController();actions.current.add(abort);let dispatched=false;try{
   const current=await port.read(ref,run.id,abort.signal);await checkReview(current,ref);
   if(!await sameReview(query.data,current))throw new Error('成果或合同版本已变化，请刷新后重新审阅。');
   abort.signal.throwIfAborted();if(!current.requiresAcceptance)throw new Error('此合同不要求用户接受。');
   dispatched=true;const result=await port.accept(current,requestMeta(),abort.signal);abort.signal.throwIfAborted();
   if(result.kind!=='ok')throw new Error(result.failure?.message??'接受尚未确认');
   validate('CompletionAcceptance',result.payload);
   if(result.payload.decision!=='accept'||!samePin(result.payload.bundle_ref,current.bundleRef))throw new Error('接受回执版本不匹配');
   setDecisionPending(true);setNotice('接受已确认，正在读取运行状态。');onAccepted();
  }catch(e){if(dispatched)setDecisionPending(true);setNotice(e instanceof Error?e.message:'结果未知，请查询当前版本，不会自动重试。');}
  finally{actions.current.delete(abort);setBusy(false);}
 }
 return <aside className="review-panel" aria-label="成果侧栏"><div className="panel-title"><span><FileText size={16}/>成果</span><span className="count">{artifacts.length}</span></div>
 {!item?<div className="review-empty"><div className="empty-icon"><FileText size={27}/></div><h3>每一份成果，都有出处</h3><p>报告与文本将在这里出现。<br/>查看正文、来源与逐项核验。</p></div>:<>
 <div className="artifact-tabs">{artifacts.map(a=><button className={a.id===item.id?'selected':''} key={a.id} onClick={()=>{setSelected(a.id);setNotice('');}}>{a.text.split('\n')[0].slice(0,36)||'文本成果'}</button>)}</div>
 <div className="review-body"><span className="eyebrow">{query.data?.artifact.media_type??'成果摘要'} · v{ref?.version??item.revision}</span><h3>{query.data?.artifact.title??'本次成果'}</h3>
 <Markdown text={query.data?.content??item.text}/>
 <div className="verification"><ShieldCheck size={16}/><strong>逐项核验</strong></div>
 {query.data?<><p>{query.data.report.outcome}</p>{query.data.report.verdicts.map(v=><section className="verdict" key={v.requirement_id}><strong>要求 {v.requirement_id} · {checkLabel(v.state)}</strong><p>{v.reason}</p>{v.limitations.map((line,i)=><p key={i}>{line}</p>)}<details><summary>核验依据与版本 · {v.evidence_refs.length}</summary>{v.evidence_refs.map((r,i)=><p key={i}>{r.kind}/{r.id}@{r.version}</p>)}</details></section>)}{query.data.report.checks.map(c=><section className="verdict" key={c.id}><strong>{c.kind} · {checkLabel(c.state)}</strong><p>{c.summary}</p></section>)}{query.data.report.limitations.map((v,i)=><p key={i}>{v}</p>)}</>:<p className="muted">成果正文与核验读取尚未接入，当前仅展示服务端条目摘要。</p>}
 <details><summary>来源与版本 <ExternalLink size={12}/></summary><ul>{(query.data?.artifact.provenance_refs??item.resource_refs).map((r,i)=><li key={i}>{r.kind} / {r.id} / {r.version}</li>)}</ul></details>
 {query.error&&<p role="alert" className="error-text">{query.error.message}</p>}
 <button className="primary accept" disabled={!query.data?.requiresAcceptance||run?.status!=='waiting_for_user'||!connected||busy||decisionPending} onClick={()=>void accept()}>{busy?'正在核对版本…':'接受整份成果'}</button>
 {!port&&<p className="muted">合同接受入口尚未接入。</p>}{notice&&<p role="status">{notice}</p>}
 </div></>}
 </aside>;
}
const samePin=(a:Ref,b:Ref)=>a.kind===b.kind&&a.id===b.id&&a.version===b.version&&a.content_hash===b.content_hash;

const checkLabel=(state:string)=>({passed:'已通过',failed:'未通过',blocked:'受阻',not_run:'未运行'}[state]??state);
