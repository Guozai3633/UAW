import type {Schema,Ref,Result} from '../../lib/api/types';
import {validate} from '../../lib/api/validation';
// Optional internal adapter proposed to A. No invented HTTP endpoint.
export type ReviewSnapshot={artifact:Schema['ArtifactRecord'];content:string;report:Schema['VerificationReport'];
 bundleRef:Ref;contractRef:Ref;requiresAcceptance:boolean};
export interface ReviewPort {
 read(artifactRef:Ref,runId:string,signal:AbortSignal):Promise<ReviewSnapshot>;
 accept(snapshot:ReviewSnapshot,meta:Schema['RequestMeta'],signal:AbortSignal):Promise<Result<Schema['CompletionAcceptance']>>;
}
export function checkReview(value:ReviewSnapshot,requested:Ref){
 validate('ArtifactRecord',value.artifact);validate('VerificationReport',value.report);
 validate('Ref',value.bundleRef);validate('Ref',value.contractRef);
 if(value.artifact.id!==requested.id || value.artifact.version!==requested.version ||
 value.report.contract_ref.id!==value.contractRef.id || value.report.contract_ref.version!==value.contractRef.version ||
 !value.report.target_refs.some(r=>r.kind==='artifact'&&r.id===requested.id&&r.version===requested.version) ||
 !['text/plain','text/markdown'].includes(value.artifact.media_type) || value.content.length>131072 || typeof value.requiresAcceptance!=='boolean')throw new Error('成果与合同版本不匹配');
}
export async function sameReview(a:ReviewSnapshot,b:ReviewSnapshot){
 return JSON.stringify(a)===JSON.stringify(b);
}
