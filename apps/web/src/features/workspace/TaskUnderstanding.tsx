import {Sparkles} from 'lucide-react';
import type {Frame,Run} from '../../lib/api/types';
import {terminal} from '../../lib/events/projection';
export function TaskUnderstanding({run,frame,draft,inputRevision}:{run?:Run;frame?:Frame;draft:string;inputRevision?:number}){
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
