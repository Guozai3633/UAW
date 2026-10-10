// Exact A2 DTO fixture; controlled protocol input, never a production provider.
import {createHash} from 'node:crypto';
import type {Schema} from '../src/lib/api/types';
import {now,ref} from './fixtures';
export function deliveryView(acceptance=false):Schema['RunDeliveryView']{
 const content='# 完整正文报告\n\n这是完整成果，不是条目摘要。';
 const artifact={id:'artifact-one',version:'1',title:'完整成果',format_kind:'markdown',media_type:'text/markdown',content_ref:ref('content','body-one'),size_bytes:Buffer.byteLength(content),content_hash:createHash('sha256').update(content).digest('hex'),provenance_refs:[ref('input','input-one')],verification_refs:[ref('verification','report-one')],created_at:now};
 const artifact_ref=ref('artifact',artifact.id),bundle_ref=ref('content','bundle-one'),contract_ref=ref('content','contract-one'),report_ref=ref('verification','report-one');
 return{run_id:'run-one',bundle_ref,artifact_ref,artifact,content,contract_ref,contract:{goal:'原文为基准',requirements:[{id:'requirement-one',text:'完整成果可核验',mandatory:true,source_refs:[ref('input','input-one')]}],outputs:[],version:'1',acceptance_required:true},report_ref,
 report:{id:'report-one',contract_ref,target_refs:[artifact_ref],checks:[],verdicts:[{requirement_id:'requirement-one',state:'passed',evidence_refs:[ref('input','input-one')],reason:'逐项核验理由',limitations:['受控测试不证明实际模型质量']}],outcome:'succeeded',limitations:[],created_at:now},
 proposal_ref:ref('content','proposal-one'),proposal:{run_ref:ref('run','run-one'),contract_ref,outcome:'succeeded',artifact_refs:[artifact_ref],report_ref,unresolved_effect_refs:[],created_at:now},requires_acceptance:true,stale:false,
 ...(acceptance?{acceptance:{bundle_ref,principal:{id:'user-one',kind:'user',auth_session_id:'session-one'},decision:'accept',created_at:now}}:{})};
}
