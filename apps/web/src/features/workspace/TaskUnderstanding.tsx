import type {Presentation} from '../presentation/port';
import {Sparkles} from 'lucide-react';
import type {Frame,Run} from '../../lib/api/types';
import {terminal} from '../../lib/events/projection';
export function TaskUnderstanding({run,frame,draft,inputRevision,presentation,synchronized=false,sourceCurrent=false,updating=false}:{run?:Run;frame?:Frame;draft:string;inputRevision?:number;presentation?:Presentation;synchronized?:boolean;sourceCurrent?:boolean;updating?:boolean}){
 if(!run&&!draft)return <div className="understanding" aria-label="AI理解的任务"><div><Sparkles size={14}/><b>AI理解的任务</b></div><p>写下你的任务，从一段原文开始。</p><small>理解是提示，你的原文是执行基准。</small></div>;
 if(synchronized){const u=presentation?.understanding;return <div className="understanding" aria-label="AI理解的任务"><div><Sparkles size={14}/><b>AI理解的任务</b>{u&&<span>输入版本 {u.input_revision}</span>}</div>
 {draft?<p>发送后，将根据这段原文理解任务。</p>:<>{!sourceCurrent&&<p>理解来源暂不可核对。{u?.state==='available'?'以下为上次已核对的理解。':''}</p>}{updating&&<small>后台更新中</small>}
 {u?.state==='available'?<><p>{u.value!.summary}</p>{u.value!.assumptions.length>0&&<ul>{u.value!.assumptions.map((a,n)=><li key={n}>{a}</li>)}</ul>}<details><summary>理解来源与版本</summary>{[u.decision_record_ref!,u.model_output_ref!].map((r,n)=><p key={n}>{r.kind}/{r.id}@{r.version}</p>)}</details></>:sourceCurrent&&u?.state==='not_provided'?<p>按你的原文执行，本次未单独提供理解摘要。</p>:sourceCurrent&&u?.state==='pending'?<p>{run&&terminal(run.status)?'本次没有生成新的任务理解。':'正在等待实际模型理解…'}</p>:null}</>}
 <small>理解是提示，你的原文是执行基准。</small></div>;}
 const saved=frame?.task_id===run?.task_id?frame:undefined,hasSummary=!!saved?.summary?.trim();
 const current=hasSummary&&inputRevision!==undefined&&saved?.input_revision===inputRevision;
 const old=hasSummary&&inputRevision!==undefined&&saved?.input_revision!==undefined&&saved.input_revision<inputRevision;
 const ended=!!run&&terminal(run.status);
 return <div className="understanding" aria-label="AI理解的任务"><div><Sparkles size={14}/><b>AI理解的任务</b>{saved&&!draft&&<span>v{saved.revision}{saved.input_revision!==undefined&&` · 输入版本 ${saved.input_revision}`}</span>}</div>
 {draft?<p>发送后，将根据这段原文理解任务。</p>:<>
 {ended&&!current&&<p>本次没有生成新的任务理解。</p>}
 {hasSummary?<>{!current&&<small>{old?'旧版本任务理解，仅供查阅。':'已保存的任务理解，尚未核对为当前输入版本。'}</small>}<p>{saved!.summary}</p></>:!ended&&<p>{run?'正在等待实际任务理解…':'写下你的任务，从一段原文开始。'}</p>}
 </>}<small>理解是提示，你的原文是执行基准。</small></div>;
}
