import type {Schema,Run} from '../src/lib/api/types';
import {makeRun,now,ref} from './fixtures';
import {deliveryView} from './a2-fixtures';
export function presentationView(run:Run=makeRun('running',5),input=1,phase:Schema['RunPresentationView']['phase']='working',available=false):Schema['RunPresentationView']{
 return{protocol:'conversation-v1',run:structuredClone(run),input_revision:input,phase,understanding:available?{state:'available',input_revision:input,value:{summary:'受控模型理解摘要，来自原模型记录。',assumptions:['受控假设，不授予权限。']},decision_record_ref:ref('content','decision-presentation','2'),model_output_ref:ref('content','output-presentation','3')}:{state:'not_provided',input_revision:input},captured_at:now};
}
export function withDelivery(p:Schema['RunPresentationView'],d=deliveryView()):Schema['RunPresentationView']{
 return {...p,delivery:{bundle_ref:d.bundle_ref,artifact_ref:d.artifact_ref,report_ref:d.report_ref,proposal_ref:d.proposal_ref,run_revision:p.run.revision,input_revision:p.input_revision,outcome:d.report.outcome,requires_acceptance:d.requires_acceptance}};
}
