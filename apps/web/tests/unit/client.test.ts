import {makeItem,ok} from '../fixtures';
import {describe,it,expect,vi} from 'vitest';
import {UawClient,TransportError,ApiFailure,requestMeta} from '../../src/lib/api/client';
describe('actual wire client',()=>{
 it('preserves original text and path fields outside JSON; HTTP202 waiting remains waiting',async()=>{
  const original='  用户原文\n不要改写  ';
  const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify({kind:'waiting',wait_ref:{kind:'run',id:'run-one',version:'1'},output_refs:[]}),{status:202}));
  const client=new UawClient(()=>({identityKey:'user-a'}),fetcher);
  const meta=requestMeta(1);
  await expect(client.submit('conv-one',{text:original,attachment_refs:[]},meta)).rejects.toBeInstanceOf(ApiFailure);
  const [url,options]=fetcher.mock.calls[0];
  expect(url).toBe('/v1/conversations/conv-one/turns');
  expect(JSON.parse(options.body)).toEqual({meta,payload:{text:original,attachment_refs:[]}});
  expect(options.credentials).toBe('same-origin');expect(options.cache).toBe('no-store');
  expect(options.headers.Authorization).toBeUndefined();
 });
 it('never retries an uncertain send',async()=>{const f=vi.fn().mockRejectedValue(new TypeError('network'));
  await expect(new UawClient(()=>null,f).submit('conv-one',{text:'hello',attachment_refs:[]},requestMeta(1))).rejects.toBeInstanceOf(TransportError);
  expect(f).toHaveBeenCalledTimes(1);});
 it('refuses malformed successful payload',async()=>{const f=vi.fn().mockResolvedValue(new Response(JSON.stringify({kind:'ok',payload:{status:'completed'},output_refs:[]})));
  await expect(new UawClient(()=>null,f).run('run-one')).rejects.toBeInstanceOf(TransportError);});
 it('propagates permission denial',async()=>{const f=vi.fn().mockResolvedValue(new Response(JSON.stringify({kind:'denied',failure:{code:'origin_denied',category:'authorization',message:'浏览器入口未开放',retryable:false,failed_phase:'authentication'},output_refs:[]}),{status:403}));
  await expect(new UawClient(()=>null,f).models()).rejects.toThrow('浏览器入口未开放');});
});

it('future Item types stay readable but revisions remain strictly validated',async()=>{
 const item={...makeItem('future-one','agent_message','read only'),type:'future_display'};
 const f=vi.fn().mockImplementation(async()=>new Response(JSON.stringify(ok({items:[item],snapshot_revision:1}))));
 const client=new UawClient(()=>null,f);expect((await client.items('conv-one')).items[0].type).toBe('future_display');
 item.revision=-1;await expect(client.items('conv-one')).rejects.toBeInstanceOf(TransportError);
});
it('host cannot inject administrator authorization instead of the published CSRF protocol',async()=>{
 const f=vi.fn();const client=new UawClient(()=>({identityKey:'user',csrfHeader:{name:'Authorization',value:'forbidden'}}),f);
 await expect(client.submit('conv-one',{text:'task',attachment_refs:[]},requestMeta(1))).rejects.toThrow('HTTP认证协议');expect(f).not.toHaveBeenCalled();
});
