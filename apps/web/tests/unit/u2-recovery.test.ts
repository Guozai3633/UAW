import {beforeEach,it,expect,vi} from 'vitest';
import {UawClient,requestMeta} from '../../src/lib/api/client';
import {HttpRecoveryPort,HttpReviewPort} from '../../src/lib/api/a2-adapters';
import {WorkspaceController} from '../../src/features/workspace/controller';
import {deliveryView} from '../a2-fixtures';
import {ok,conversation,models,makeRun,frame} from '../fixtures';
beforeEach(()=>localStorage.clear());
it('lost acceptance survives new port and only real acceptance clears lookup; absent receipt never permits a new ID',async()=>{
 let receipt=false;const view=deliveryView();const calls:RequestInit[]=[];const f=vi.fn(async(_url:RequestInfo|URL,options?:RequestInit)=>{calls.push(options!);if(options?.method==='POST')throw new TypeError('response lost');return new Response(JSON.stringify(ok(receipt?deliveryView(true):view)));});
 const client=new UawClient(()=>({identityKey:'user-one'}),f),signal=new AbortController().signal;let port=new HttpReviewPort(client);const before=await port.read(undefined,'run-one',signal);await expect(port.accept(before,requestMeta(),signal)).rejects.toThrow('未知');
 port=new HttpReviewPort(client);const pending=await port.read(undefined,'run-one',signal);expect(pending.decisionUncertain).toBe(true);await expect(port.accept(pending,requestMeta(),signal)).rejects.toThrow('不会换');expect(calls.filter(c=>c.method==='POST')).toHaveLength(1);
 const stored=localStorage.getItem('uaw.web.acceptance-lookups.v1')!;for(const secret of ['accepted','principal','csrf','permission','content_hash','正文'])expect(stored).not.toContain(secret);
 receipt=true;const actual=await port.read(undefined,'run-one',signal);expect(actual.delivery?.acceptance?.decision).toBe('accept');expect(actual.decisionUncertain).toBe(false);await expect(port.accept(actual,requestMeta(),signal)).rejects.toThrow('已有决定');
});
it('identity change during a delivery wait cannot authorize a decision',async()=>{
 let identity='first';let release!:(r:Response)=>void;const f=vi.fn(()=>new Promise<Response>(resolve=>{release=resolve;}));const port=new HttpReviewPort(new UawClient(()=>({identityKey:identity}),f));
 const reading=port.read(undefined,'run-one',new AbortController().signal);identity='second';release(new Response(JSON.stringify(ok(deliveryView()))));await expect(reading).rejects.toThrow('身份已变化');expect(f).toHaveBeenCalledOnce();
});
it('lost submit reconciles original request before history; refreshed controller sends nothing',async()=>{
 const urls:string[]=[];let posts=0;const fetcher=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{const path=String(input).split('?')[0];urls.push(path);let payload:unknown;
 if(options?.method==='POST'){posts++;throw new TypeError('lost');}if(path==='/v1/models')payload=models;else if(path==='/v1/conversations')payload={items:[conversation],snapshot_revision:1};else if(path.includes('/turn-requests/'))payload=makeRun();else if(path.endsWith('/items')||path.endsWith('/events'))payload={items:[],snapshot_revision:1};else if(path.endsWith('/frame'))payload=frame;else if(path.includes('/runs/'))payload=makeRun();else payload=conversation;return new Response(JSON.stringify(ok(payload)));});
 const client=new UawClient(()=>({identityKey:'user-one'}),fetcher);const host={session:()=>({identityKey:'user-one'}),recovery:new HttpRecoveryPort(client)};let controller=new WorkspaceController(client,host,undefined,60000);
 await controller.start();controller.edit('  原文保留  ');await controller.send();const id=controller.snapshot().recovery!.requestId;controller.stop();urls.length=0;
 controller=new WorkspaceController(client,host,undefined,60000);await controller.start();expect(controller.snapshot().run?.id).toBe('run-one');expect(urls.some(url=>url.endsWith(id))).toBe(true);expect(urls.findIndex(url=>url.includes('/turn-requests/'))).toBeLessThan(urls.findIndex(url=>url.endsWith('/items')));expect(posts).toBe(1);controller.stop();
});
it('server list follows fixed cursor and deduplicates revisions; expired cursor restarts from first page',async()=>{
 let expired=true;const queries:string[]=[];const fetcher=vi.fn(async(input:RequestInfo|URL)=>{const url=String(input);if(url.startsWith('/v1/conversations?')){queries.push(url);if(url.includes('cursor=next')){if(expired){expired=false;return new Response(JSON.stringify({kind:'stale',failure:{code:'cursor_invalid',category:'conflict',message:'expired',retryable:false,failed_phase:'read'},output_refs:[]}));}return new Response(JSON.stringify(ok({items:[{...conversation,revision:2,title:'new'}, {...conversation,id:'conv-two'}],snapshot_revision:2})));}return new Response(JSON.stringify(ok({items:[conversation],snapshot_revision:2,next_cursor:'next'})));}
 return new Response(JSON.stringify(ok(url==='/v1/models'?models:url.includes('/items')||url.includes('/events')?{items:[],snapshot_revision:1}:conversation)));});
 const controller=new WorkspaceController(new UawClient(()=>({identityKey:'user-one'}),fetcher),{session:()=>({identityKey:'user-one'})},undefined,60000);await controller.start();expect(queries).toHaveLength(4);expect(controller.snapshot().conversations).toHaveLength(2);expect(controller.snapshot().conversations.some(c=>c.id==='conv-two')).toBe(true);controller.stop();
});
