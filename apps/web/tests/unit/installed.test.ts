import {beforeEach,it,expect,vi} from 'vitest';
import {HttpInstalledLaunchPort} from '../../src/features/devices/installed';
import {UawClient,requestMeta} from '../../src/lib/api/client';
import {installed} from '../installed-fixtures';
import {ok,denied} from '../fixtures';
beforeEach(()=>localStorage.clear());
const session=()=>({identityKey:'web-one',principal:{id:'user-one',kind:'user' as const,auth_session_id:'session-one'}});
it('fixed local start/get/stop HTTP validates exact empty payload/CAS and full ready DTO',async()=>{
 const calls:[string,RequestInit|undefined][]=[];const client=new UawClient(session,vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{calls.push([String(input),init]);return new Response(JSON.stringify(ok(installed('ready'))),{status:init?.method==='POST'?202:200});}));
 await client.localStart(requestMeta());await client.localGet('launch-one');await client.localStop('launch-one',requestMeta(1));expect(calls.map(c=>c[0])).toEqual(['/v1/runner/local','/v1/runner/local/launch-one','/v1/runner/local/launch-one/stop']);
 expect(JSON.parse(String(calls[0][1]?.body)).payload).toEqual({});expect(JSON.parse(String(calls[2][1]?.body))).toMatchObject({meta:{expected_revision:1},payload:{}});
 const bad={...installed('ready'),path:'private'};await expect(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(bad))))).localGet('launch-one')).rejects.toThrow();
 const incomplete=installed('ready');delete incomplete.device_ref;await expect(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(incomplete))))).localGet('launch-one')).rejects.toThrow();
});
it('double click has one write; no status/proof/rights persists and restored GET uses original identity/request',async()=>{
 let release!:(r:Response)=>void,requestId='';const fetcher=vi.fn(async(_input:RequestInfo|URL,options?:RequestInit)=>{requestId=JSON.parse(String(options?.body)).meta.request_id;return new Promise<Response>(r=>{release=r;});});
 const port=new HttpInstalledLaunchPort(new UawClient(session,fetcher)),signal=new AbortController().signal;const first=port.start(signal);await expect(port.start(signal)).rejects.toThrow('进行');release(new Response(JSON.stringify(ok(installed('starting',1,requestId))),{status:202}));await first;expect(fetcher).toHaveBeenCalledOnce();
 const saved=localStorage.getItem('uaw.web.local-launch.v1')!;for(const forbidden of ['ready','workspace_ref','nonce','proof','key','path','permission'])expect(saved).not.toContain(forbidden);
 const read=vi.fn(async()=>new Response(JSON.stringify(ok(installed('ready',2,requestId))))),reloaded=new HttpInstalledLaunchPort(new UawClient(session,read));expect(reloaded.lookup()?.launchId).toBe('launch-one');await reloaded.get('launch-one',signal);expect(read.mock.calls).toHaveLength(1);
});
it('lost start without ID blocks automatic new IDs; explicit recovery sends same request ID only',async()=>{
 const requestIds:string[]=[];const fetcher=vi.fn(async(_i:RequestInfo|URL,o?:RequestInit)=>{const id=JSON.parse(String(o?.body)).meta.request_id;requestIds.push(id);if(requestIds.length===1)throw new TypeError('lost');return new Response(JSON.stringify(ok(installed('waiting_device',2,id))));}),signal=new AbortController().signal;
 let port=new HttpInstalledLaunchPort(new UawClient(session,fetcher));await expect(port.start(signal)).rejects.toThrow('未知');port=new HttpInstalledLaunchPort(new UawClient(session,fetcher));expect(port.lookup()?.launchId).toBeUndefined();await expect(port.start(signal)).rejects.toThrow('原请求ID');expect(requestIds).toHaveLength(1);await port.start(signal,true);expect(requestIds).toEqual([requestIds[0],requestIds[0]]);
});
it('known launch first GET, lost stop cannot retry; terminal actual read alone reconciles stop',async()=>{
 let view=installed('starting'),posts=0;const transport=vi.fn(async(_i:RequestInfo|URL,o?:RequestInit)=>{if(o?.method==='POST'){posts++;throw new TypeError('lost');}return new Response(JSON.stringify(ok(view)));}),signal=new AbortController().signal;
 let port=new HttpInstalledLaunchPort(new UawClient(session,transport));await port.get(view.id,signal);await expect(port.stop(view,signal)).rejects.toThrow('未知');port=new HttpInstalledLaunchPort(new UawClient(session,transport));await expect(port.stop(view,signal)).rejects.toThrow('先GET');expect(posts).toBe(1);view=installed('closed',2);await port.get(view.id,signal);expect(port.lookup()?.stop).toBeUndefined();expect(posts).toBe(1);
});
it('cross Web session cannot inherit, late identity/abort/clear rejects, current denied never returns prior ready',async()=>{
 const signal=new AbortController().signal,base=installed('ready');const original=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(base))))));await original.get(base.id,signal);
 const fresh=new HttpInstalledLaunchPort(new UawClient(()=>({...session(),identityKey:'web-two',principal:{...session().principal,auth_session_id:'session-two'}})));expect(fresh.lookup()).toBeUndefined();
 let value=session(),release!:(r:Response)=>void;const port=new HttpInstalledLaunchPort(new UawClient(()=>value,vi.fn(()=>new Promise<Response>(r=>{release=r;}))));const reading=port.get('launch-one',signal);value={...session(),identityKey:'changed'};release(new Response(JSON.stringify(ok(base))));await expect(reading).rejects.toThrow('身份');
 const no=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(denied()),{status:403}))));await expect(no.get('launch-one',signal)).rejects.toThrow();const abort=new AbortController();const clearPort=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async()=>{abort.abort();return new Response(JSON.stringify(ok(base)));})));await expect(clearPort.get('launch-one',abort.signal)).rejects.toThrow();original.clear();expect(localStorage.getItem('uaw.web.local-launch.v1')).toBeNull();
});
it('stale revisions, mismatched IDs/request and unavailable writes do not bypass original boundary',async()=>{
 const signal=new AbortController().signal;localStorage.setItem('uaw.web.local-launch.v1',JSON.stringify({identity:'web-one',lookup:{requestId:'request-one',launchId:'launch-one',revision:3}}));
 for(const view of [installed('ready',2),{...installed('ready',3),id:'foreign'},{...installed('ready',3),request_id:'foreign'}]){const port=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(view))))));await expect(port.get('launch-one',signal)).rejects.toThrow();}
 localStorage.clear();let posts=0;const transport=vi.fn(async(_i:RequestInfo|URL,o?:RequestInit)=>{if(o?.method==='POST')posts++;return new Response(JSON.stringify(ok(installed('connecting',2))));});const port=new HttpInstalledLaunchPort(new UawClient(session,transport));await port.get('launch-one',signal);await expect(port.stop(installed('starting'),signal)).rejects.toThrow('版本');expect(posts).toBe(0);
 const storage={getItem:()=>null,removeItem:()=>{},setItem:()=>{throw Error('no storage');}} as unknown as Storage;await expect(new HttpInstalledLaunchPort(new UawClient(session,transport),storage).start(signal)).rejects.toThrow('保存');expect(posts).toBe(0);
});

it('concurrent old GET cannot roll the latest in-operation lookup revision backward',async()=>{
 const pending:((r:Response)=>void)[]=[];const port=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(()=>new Promise<Response>(r=>pending.push(r))))),signal=new AbortController().signal;
 const old=port.get('launch-one',signal),fresh=port.get('launch-one',signal);pending[1](new Response(JSON.stringify(ok(installed('ready',3)))));await fresh;pending[0](new Response(JSON.stringify(ok(installed('starting',1)))));await expect(old).rejects.toThrow('回退');expect(port.lookup()?.revision).toBe(3);
});

it('logout clear wins a late start, abort preserves unknown original ID, and explicit 503 stays unavailable',async()=>{
 const signal=new AbortController().signal;let release!:(r:Response)=>void,id='';const port=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async(_i:RequestInfo|URL,o?:RequestInit)=>{id=JSON.parse(String(o?.body)).meta.request_id;return new Promise<Response>(r=>{release=r;});})));
 const start=port.start(signal);port.clear();release(new Response(JSON.stringify(ok(installed('ready',2,id)))));await expect(start).rejects.toThrow('身份');expect(localStorage.getItem('uaw.web.local-launch.v1')).toBeNull();
 const abort=new AbortController(),cancelled=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async()=>{abort.abort();return new Response(JSON.stringify(ok(installed())));})));await expect(cancelled.start(abort.signal)).rejects.toThrow();expect(cancelled.lookup()?.requestId).toBeDefined();cancelled.clear();
 const unavailable=new HttpInstalledLaunchPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify({...denied('dependency_unavailable','本机来源未配置'),kind:'failed'}),{status:503}))));await expect(unavailable.start(signal)).rejects.toThrow('未配置');expect(unavailable.lookup()).toBeUndefined();
});

it('controlled RPC timeout uses the fixed 15s transport bound and retains original unknown start metadata',async()=>{
 const deadline=new AbortController();const timeout=vi.spyOn(AbortSignal,'timeout').mockImplementationOnce(ms=>{expect(ms).toBe(15000);return deadline.signal;});
 const fetcher=vi.fn((_i:RequestInfo|URL,o?:RequestInit)=>new Promise<Response>((_resolve,reject)=>{o?.signal?.addEventListener('abort',()=>reject(o.signal?.reason),{once:true});}));
 try{const port=new HttpInstalledLaunchPort(new UawClient(session,fetcher));const pending=expect(port.start(new AbortController().signal)).rejects.toThrow('未知');deadline.abort(new DOMException('controlled timeout','TimeoutError'));await pending;expect(port.lookup()?.requestId).toBeDefined();expect(port.lookup()?.launchId).toBeUndefined();await expect(port.start(new AbortController().signal)).rejects.toThrow('原请求ID');expect(fetcher).toHaveBeenCalledOnce();}finally{timeout.mockRestore();}
});
