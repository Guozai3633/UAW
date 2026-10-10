// Controlled complete A2 DTO replay with A's observed actual media_type.
// This transport is not a new authenticated backend/model run.
import {beforeEach,it,expect,vi} from 'vitest';
import {checkReview,type ReviewSnapshot} from '../../src/features/review/port';
import {HttpReviewPort} from '../../src/lib/api/a2-adapters';
import {recordHash} from '../../src/lib/api/canonical';
import {UawClient} from '../../src/lib/api/client';
import {deliveryView} from '../a2-fixtures';
import {ok,ref} from '../fixtures';
beforeEach(()=>localStorage.clear());
const snap=(v:ReturnType<typeof deliveryView>):ReviewSnapshot=>({artifact:v.artifact,content:v.content,report:v.report,bundleRef:v.bundle_ref,contractRef:v.contract_ref,requiresAcceptance:v.requires_acceptance,delivery:v});
it('both text types permit only an optional UTF-8 charset, preserving complete body and pins',async()=>{
 for(const media of ['text/markdown','text/plain','text/markdown; charset=utf-8','text/plain;charset=utf-8','TEXT/MARKDOWN; CHARSET=UTF-8',' text/plain ; charset = "UTF-8" 	']){
  const v=deliveryView();v.artifact.media_type=media;await checkReview(snap(v),v.artifact_ref);
  expect(v.artifact.media_type).toBe(media);
 }
});
it('rejects unsupported types, charsets, extra/duplicate parameters and malformed values',async()=>{
 for(const media of ['text/html','application/json','image/png','text/markdownx','text/markdown; charset=ascii','text/plain; charset=iso-8859-1','text/markdown; charset=utf8','text/plain; charset=utf-16','text/plain; charset="utf-8','text/plain; charset=','text/plain; charset=utf-8; charset=utf-8','text/plain; charset=utf-8; format=flowed','text/markdown; boundary=x','text/plain;','text/plain; charset=utf-8junk','text/plain; charset=utf-8\n','text/plain\r\n; charset=utf-8','text/plain\u00a0; charset=utf-8']){
  const v=deliveryView();v.artifact.media_type=media;await expect(checkReview(snap(v),v.artifact_ref),media).rejects.toThrow('版本');
 }
});
it('actual observed media_type works through full RunDeliveryView HTTP adapter without weakening source or contract checks',async()=>{
 const v=deliveryView();v.artifact.media_type='text/markdown; charset=utf-8';
 v.artifact_ref.content_hash=await recordHash(v.artifact);
 const rebind=async()=>{v.artifact_ref.content_hash=await recordHash(v.artifact);v.report.target_refs=[{...v.artifact_ref}];v.proposal.artifact_refs=[{...v.artifact_ref}];};await rebind();
 const f=vi.fn(async(_url:RequestInfo|URL)=>new Response(JSON.stringify(ok(v))));const port=new HttpReviewPort(new UawClient(()=>({identityKey:'user-one'}),f));const signal=new AbortController().signal;
 const result=await port.read(v.artifact_ref,v.run_id,signal);
 expect(result.content).toBe(v.content);expect(result.delivery).toEqual(v);expect(result.artifact.media_type).toBe('text/markdown; charset=utf-8');
 v.content+='changed';await expect(port.read(undefined,v.run_id,signal)).rejects.toThrow('摘要或长度');
 v.content=result.content;v.artifact.size_bytes++;await rebind();
 await expect(port.read(undefined,v.run_id,signal)).rejects.toThrow('摘要或长度');
 v.artifact.size_bytes--;v.artifact.content_hash='f'.repeat(64);await rebind();
 await expect(port.read(undefined,v.run_id,signal)).rejects.toThrow('摘要或长度');
 v.artifact=structuredClone(result.artifact);await rebind();
 v.proposal.contract_ref=ref('content','other-contract');await expect(port.read(undefined,v.run_id,signal)).rejects.toThrow('关联');
 v.proposal.contract_ref={...v.contract_ref};await expect(port.read({...v.artifact_ref,version:'2'},v.run_id,signal)).rejects.toThrow('版本');
 v.artifact.title='changed metadata';await expect(port.read(undefined,v.run_id,signal)).rejects.toThrow('来源摘要');
 expect(f.mock.calls.every(call=>call[0]===`/v1/runs/${v.run_id}/delivery`)).toBe(true);
});
