import {beforeEach,it,expect,vi} from 'vitest';
import {BrowserSessionHost} from '../../src/lib/api/browser-session';
import {ok,now,denied} from '../fixtures';
const session={principal:{id:'user-one',kind:'user',auth_session_id:'web-session-one'},expires_at:now,csrf_token:'c'.repeat(64)};
beforeEach(()=>{history.replaceState(null,'','/');localStorage.clear();});
it('exchanges exact published launch code once after removing fragment; CSRF stays in memory',async()=>{
 history.replaceState(null,'','/#uaw_launch=one-use-test-code');const transport=vi.fn(async(_url:RequestInfo|URL,options?:RequestInit)=>{expect(location.hash).toBe('');expect(options?.method).toBe('POST');return new Response(JSON.stringify(ok(session)));});
 const host=new BrowserSessionHost(transport);await host.initialize();expect(transport).toHaveBeenCalledOnce();expect(JSON.parse(String(transport.mock.calls[0][1]?.body)).payload).toEqual({launch_code:'one-use-test-code'});expect(host.session()?.csrfHeader?.value).toBe(session.csrf_token);expect(localStorage.length).toBe(0);host.dispose();
});
it('lost exchange queries current cookie session without replay; logout uses exact DELETE/CSRF/JSON',async()=>{
 history.replaceState(null,'','/#uaw_launch=one-use-test-code');const transport=vi.fn(async(_url:RequestInfo|URL,options?:RequestInit)=>{if(options?.method==='POST')throw new TypeError('lost');return new Response(JSON.stringify(ok(options?.method==='DELETE'?{operation_id:'logout-one',status:'completed'}:session)));});
 const host=new BrowserSessionHost(transport);await host.initialize();expect(transport.mock.calls.map(c=>c[1]?.method)).toEqual(['POST','GET']);await host.logout();expect(host.session()).toBeNull();const del=transport.mock.calls.at(-1)?.[1];expect(del?.method).toBe('DELETE');expect(del?.headers).toMatchObject({'X-UAW-CSRF':session.csrf_token});expect(JSON.parse(String(del?.body)).payload).toEqual({});host.dispose();
});
it('denied or revoked current session never becomes an anonymous identity',async()=>{const host=new BrowserSessionHost(vi.fn(async()=>new Response(JSON.stringify(denied('web_session_revoked','会话已撤销')),{status:403})));await host.initialize();expect(host.session()).toBeNull();expect(host.unavailableReason()).toBe('会话已撤销');host.dispose();});
