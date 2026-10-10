import {beforeEach,afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {Devices} from '../../src/features/devices/Devices';
import {HttpEnrollmentPort} from '../../src/features/devices/port';
import {UawClient,requestMeta} from '../../src/lib/api/client';
import {enrollment} from '../enrollment-fixtures';
import {ok} from '../fixtures';
beforeEach(()=>localStorage.clear());afterEach(cleanup);
const session=()=>({identityKey:'user-one',principal:{id:'user-one',kind:'user' as const,auth_session_id:'session-one'}});
it('all four published HTTP methods bind payload, path and exact CAS without browser proof',async()=>{
 const f=vi.fn(async()=>new Response(JSON.stringify(ok(enrollment())))),client=new UawClient(session,f);
 await client.beginEnrollment('candidate-one',requestMeta());await client.enrollment('enrollment-one');await client.confirmEnrollment('enrollment-one',requestMeta(1));await client.revokeEnrollment('enrollment-one',requestMeta(1));
 expect(f.mock.calls).toHaveLength(4);const calls=f.mock.calls as unknown as [string,RequestInit][];
 expect(calls[0][0]).toBe('/v1/runner/enrollments');expect(JSON.parse(String(calls[0][1].body)).payload).toEqual({candidate_id:'candidate-one'});
 for(const i of [2,3]){expect(JSON.parse(String(calls[i][1].body))).toMatchObject({meta:{expected_revision:1},payload:{}});}
 expect(calls[2][0]).toContain('/enrollment-one/confirmation');expect(calls[3][0]).toContain('/enrollment-one/revocation');
});
it('absent trusted candidate leaves begin unavailable; known ID still reads pending without showing secret evidence',async()=>{
 const f=vi.fn(async()=>new Response(JSON.stringify(ok(enrollment())))),port=new HttpEnrollmentPort(new UawClient(session,f));
 render(<Devices port={port} identity="user-one" connected/>);await screen.findByText('可信本机候选来源尚未接入；首次登记不可用。');
 expect(screen.getByRole('button',{name:'请求设备登记'})).toBeDisabled();fireEvent.change(screen.getByLabelText('原设备登记ID'),{target:{value:'enrollment-one'}});fireEvent.click(screen.getByRole('button',{name:'读取原设备登记'}));
 await screen.findByText('等待本人在本机确认');expect(document.body.textContent).not.toContain('n'.repeat(32));expect(screen.getByText(/设备登记有效不代表目录授权/)).toBeVisible();
});
it('active, revoked and expired show actual states, never directory authorization',async()=>{
 for(const [state,text] of [['active','设备登记有效'],['revoked','设备登记已撤销'],['expired','设备登记已过期']] as const){const port=new HttpEnrollmentPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(enrollment(state)))))));const v=render(<Devices port={port} identity="user-one" connected/>);fireEvent.change(screen.getByLabelText('原设备登记ID'),{target:{value:'enrollment-one'}});fireEvent.click(screen.getByRole('button',{name:'读取原设备登记'}));await screen.findByText(text);expect(screen.getByRole('button',{name:'读取本人确认结果'})).toBeDisabled();v.unmount();}
});
it('unknown confirmation retains original lookup across reload and queries same ID before another write',async()=>{
 let value=enrollment(),posts=0;const f=vi.fn(async(_input:RequestInfo|URL,options?:RequestInit)=>{if(options?.method==='POST'){posts++;throw new TypeError('lost');}return new Response(JSON.stringify(ok(value)));});
 let port=new HttpEnrollmentPort(new UawClient(session,f));await expect(port.decide(value,'confirmation',new AbortController().signal)).rejects.toThrow('未知');
 port=new HttpEnrollmentPort(new UawClient(session,f));expect(port.uncertain()).toBe(true);await port.read(value.id,new AbortController().signal);await expect(port.decide(value,'confirmation',new AbortController().signal)).rejects.toThrow('不会重发');expect(posts).toBe(1);
 const saved=localStorage.getItem('uaw.web.enrollment-lookup.v1')!;for(const forbidden of ['nonce','proof','public_key','csrf','active','approved'])expect(saved).not.toContain(forbidden);
 value=enrollment('active',2);await port.read(value.id,new AbortController().signal);expect(port.uncertain()).toBe(false);
});
it('changed challenge/revision, expired deadline, mismatched owner or identity wait cannot dispatch',async()=>{
 const signal=new AbortController().signal,old=enrollment();const f=vi.fn(async()=>new Response(JSON.stringify(ok(enrollment('pending',2))))),port=new HttpEnrollmentPort(new UawClient(session,f));await expect(port.decide(old,'confirmation',signal)).rejects.toThrow('版本');expect(f).toHaveBeenCalledOnce();
 const expired=enrollment();expired.proof_document.expires_at='2000-01-01T00:00:00Z';const exp=new HttpEnrollmentPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(expired))))));await expect(exp.decide(expired,'confirmation',signal)).rejects.toThrow('状态');
 const foreign=enrollment();foreign.proof_document.owner.auth_session_id='foreign';const other=new HttpEnrollmentPort(new UawClient(session,vi.fn(async()=>new Response(JSON.stringify(ok(foreign))))));await expect(other.read(old.id,signal)).rejects.toThrow('身份');
});
it('UI identity change cancels old read so its response cannot show another login record',async()=>{
 let release!:(v:Response)=>void;const transport=vi.fn(()=>new Promise<Response>(r=>{release=r;})),port=new HttpEnrollmentPort(new UawClient(session,transport));const v=render(<Devices port={port} identity="user-one" connected/>);
 fireEvent.change(screen.getByLabelText('原设备登记ID'),{target:{value:'enrollment-one'}});fireEvent.click(screen.getByRole('button',{name:'读取原设备登记'}));
 v.rerender(<Devices port={port} identity="other" connected={false}/>);release(new Response(JSON.stringify(ok(enrollment('active')))));await waitFor(()=>expect(screen.queryByText('设备登记有效')).toBeNull());
});

it('lost begin retains original candidate/request lookup across reload, never silently dispatches a new ID',async()=>{
 let posts=0;const fetcher=vi.fn(async(_input:RequestInfo|URL,options?:RequestInit)=>{if(options?.method==='POST'){posts++;throw new TypeError('lost');}return new Response(JSON.stringify(ok(enrollment())));});
 const source={current:async()=>({candidateId:'candidate-one'})},signal=new AbortController().signal;
 let port=new HttpEnrollmentPort(new UawClient(session,fetcher),source);await expect(port.begin(signal)).rejects.toThrow('未知');
 const lookup=localStorage.getItem('uaw.web.enrollment-lookup.v1');port=new HttpEnrollmentPort(new UawClient(session,fetcher),source);await expect(port.begin(signal)).rejects.toThrow('不会换请求ID');expect(posts).toBe(1);expect(localStorage.getItem('uaw.web.enrollment-lookup.v1')).toBe(lookup);
 await port.read('enrollment-one',signal);expect(port.uncertain()).toBe(false);expect(posts).toBe(1);
});
it('blocked lookup persistence refuses dispatch, and late identity or cancellation never returns a record',async()=>{
 const signal=new AbortController().signal,fetcher=vi.fn(async()=>new Response(JSON.stringify(ok(enrollment()))));
 const storage={getItem:()=>null,removeItem:()=>{},setItem:()=>{throw Error('blocked');}} as unknown as Storage;
 const port=new HttpEnrollmentPort(new UawClient(session,fetcher),{current:async()=>({candidateId:'candidate-one'})},storage);
 await expect(port.begin(signal)).rejects.toThrow('无法保存');expect(fetcher).not.toHaveBeenCalled();
 let identity=session(),release!:(r:Response)=>void;const later=new HttpEnrollmentPort(new UawClient(()=>identity,vi.fn(()=>new Promise<Response>(r=>{release=r;}))));
 const reading=later.read('enrollment-one',signal);identity={...session(),identityKey:'other'};release(new Response(JSON.stringify(ok(enrollment()))));await expect(reading).rejects.toThrow('身份');
 const cancelled=new AbortController();cancelled.abort();await expect(new HttpEnrollmentPort(new UawClient(session,fetcher)).read('enrollment-one',cancelled.signal)).rejects.toThrow();
});
