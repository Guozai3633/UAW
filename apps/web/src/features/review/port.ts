import {canonical} from '../../lib/api/canonical';
import type {Schema,Ref,Result} from '../../lib/api/types';
import {validate} from '../../lib/api/validation';
// Optional internal adapter proposed to A. No invented HTTP endpoint.
export type ReviewSnapshot={artifact:Schema['ArtifactRecord'];content:string;report:Schema['VerificationReport'];
 bundleRef:Ref;contractRef:Ref;requiresAcceptance:boolean;delivery?:Schema['RunDeliveryView'];decisionUncertain?:boolean};
export interface ReviewPort {
 read(artifactRef:Ref|undefined,runId:string,signal:AbortSignal):Promise<ReviewSnapshot>;
 accept(snapshot:ReviewSnapshot,meta:Schema['RequestMeta'],signal:AbortSignal):Promise<Result<Schema['CompletionAcceptance']>>;
}
export async function checkReview(value:ReviewSnapshot,requested:Ref){
 validate('ArtifactRecord',value.artifact);validate('VerificationReport',value.report);
 validate('Ref',value.bundleRef);validate('Ref',value.contractRef);
 if(value.artifact.id!==requested.id || value.artifact.version!==requested.version ||
 !matchesPin(value.report.contract_ref,value.contractRef) ||
 !value.report.target_refs.some(r=>matchesPin(r,requested)) ||
 !isUtf8Text(value.artifact.media_type) || value.content.length>131072 || typeof value.requiresAcceptance!=='boolean')throw new Error('成果与合同版本不匹配');
 const bytes=new TextEncoder().encode(value.content);const digest=await crypto.subtle.digest('SHA-256',bytes);
 const hash=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');
 if(bytes.length!==value.artifact.size_bytes||hash!==value.artifact.content_hash)throw new Error('成果正文摘要或长度不匹配');
}
export async function sameReview(a:ReviewSnapshot,b:ReviewSnapshot){
 const {decisionUncertain:ignoredA,...left}=a;const {decisionUncertain:ignoredB,...right}=b;void ignoredA;void ignoredB;return canonical(left)===canonical(right);
}

export const matchesPin=(actual:Ref,requested:Ref)=>actual.kind===requested.kind&&actual.id===requested.id&&actual.version===requested.version&&(!requested.content_hash||actual.content_hash===requested.content_hash)&&(!requested.location||canonical(actual.location)===canonical(requested.location))&&(!requested.access_scope||canonical(actual.access_scope)===canonical(requested.access_scope));

// Only these UTF-8 text representations are implemented. Keep the original
// media_type on the ArtifactRecord; byte/hash and all Ref checks remain exact.
function isUtf8Text(mediaType:string):boolean{
 return !/[\r\n]/.test(mediaType) && /^[ \t]*text\/(?:plain|markdown)[ \t]*(?:;[ \t]*charset[ \t]*=[ \t]*(?:utf-8|"utf-8")[ \t]*)?$/i.test(mediaType);
}
