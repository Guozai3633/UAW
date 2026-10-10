import {it,expect,vi} from 'vitest';
import {HttpRecoveryPort,HttpReviewPort} from '../../src/lib/api/a2-adapters';
import {UawClient,TransportError,requestMeta} from '../../src/lib/api/client';
import {deliveryView} from '../a2-fixtures';
import {ok,makeRun,ref} from '../fixtures';
it('lookup uses exact original IDs; missing returns no Run, denial does not become missing',async()=>{
 const fetcher=vi.fn(async(_url:RequestInfo|URL)=>new Response(JSON.stringify(ok(makeRun()))));const port=new HttpRecoveryPort(new UawClient(()=>null,fetcher));
 expect((await port.find('conv-one','request-one',new AbortController().signal))?.id).toBe('run-one');expect(fetcher.mock.calls[0]?.[0]).toBe('/v1/conversations/conv-one/turn-requests/request-one');
 fetcher.mockResolvedValueOnce(new Response(JSON.stringify({kind:'missing',failure:{code:'record_missing',category:'arguments',message:'missing',retryable:false,failed_phase:'read'},output_refs:[]}),{status:404}));expect(await port.find('conv-one','request-one',new AbortController().signal)).toBeUndefined();
});
it('full delivery binds existing sources and dispatches exact immutable refs without expected_revision',async()=>{
 const view=deliveryView();const f=vi.fn(async(_url:RequestInfo|URL,options?:RequestInit)=>new Response(JSON.stringify(ok(options?.method==='POST'?deliveryView(true).acceptance:view))));const port=new HttpReviewPort(new UawClient(()=>null,f));const signal=new AbortController().signal;
 const result=await port.read(view.artifact_ref,view.run_id,signal);expect(result.content).toBe(view.content);expect(result.delivery?.report_ref).toEqual(view.report_ref);
 const meta=requestMeta();await port.accept(result,meta,signal);expect(f.mock.calls.at(-1)?.[0]).toBe('/v1/runs/run-one/delivery/acceptance');expect(JSON.parse(String(f.mock.calls.at(-1)?.[1]?.body))).toEqual({meta,payload:{bundle_ref:view.bundle_ref,artifact_ref:view.artifact_ref,decision:'accept'}});
});
it('ref/hash/source mismatch and stale current delivery cannot dispatch acceptance',async()=>{const v=deliveryView();const f=vi.fn(async()=>new Response(JSON.stringify(ok(v))));const port=new HttpReviewPort(new UawClient(()=>null,f));const signal=new AbortController().signal;
 await expect(port.read({...v.artifact_ref,content_hash:'f'.repeat(64)},v.run_id,signal)).rejects.toThrow('版本');
 const source=await port.read(undefined,v.run_id,signal);source.delivery!.stale=true;await expect(port.accept(source,requestMeta(),signal)).rejects.toThrow('过时');expect(f).toHaveBeenCalledTimes(2);
 v.proposal.report_ref=ref('verification','other-report');await expect(port.read(undefined,v.run_id,signal)).rejects.toThrow('关联');
});
it('malformed RunDeliveryView is rejected rather than guessed from successful HTTP',async()=>{const f=vi.fn(async()=>new Response(JSON.stringify(ok({content:'looks done'}))));await expect(new UawClient(()=>null,f).delivery('run-one')).rejects.toBeInstanceOf(TransportError);});
