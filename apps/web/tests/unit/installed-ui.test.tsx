import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {InstalledConnection} from '../../src/features/devices/InstalledConnection';
import {HttpInstalledLaunchPort} from '../../src/features/devices/installed';
import {UawClient} from '../../src/lib/api/client';
import {installed} from '../installed-fixtures';
import {ok} from '../fixtures';
const session=()=>({identityKey:'web-one',principal:{id:'user-one',kind:'user' as const,auth_session_id:'session-one'}});
beforeEach(()=>localStorage.clear());afterEach(cleanup);
it('only a user click starts; three system steps and bounded status reads never grant execution',async()=>{
 const transport=vi.fn(async(_i:RequestInfo|URL,o?:RequestInit)=>new Response(JSON.stringify(ok(installed('waiting_device',1,JSON.parse(String(o?.body)).meta.request_id))),{status:202}));const port=new HttpInstalledLaunchPort(new UawClient(session,transport));
 render(<InstalledConnection port={port} identity="web-one" connected pollLimit={1}/>);expect(transport).not.toHaveBeenCalled();expect(screen.getByText('选择你愿意开放的目录。')).toBeVisible();
 const start=screen.getByRole('button',{name:'连接本机只读目录'});fireEvent.click(start);fireEvent.click(start);await screen.findByText('等待本人确认账号');expect(transport).toHaveBeenCalledOnce();await screen.findByText(/自动读取已达本次上限/);expect(screen.getByText(/连接就绪也不表示文件工具已获执行许可/)).toBeVisible();
});
it('refresh only GETs original known launch; unavailable errors hide prior ready and preserve lookup',async()=>{
 localStorage.setItem('uaw.web.local-launch.v1',JSON.stringify({identity:'web-one',lookup:{requestId:'request-one',launchId:'launch-one',revision:1}}));let failed=false;
 const transport=vi.fn(async(_i:RequestInfo|URL,o?:RequestInit)=>{expect(o?.method).toBe('GET');if(failed)throw new TypeError('timeout');return new Response(JSON.stringify(ok(installed('ready',2))));});const port=new HttpInstalledLaunchPort(new UawClient(session,transport));
 render(<InstalledConnection port={port} identity="web-one" connected pollLimit={1}/>);await screen.findByText('本机当前连接就绪');failed=true;fireEvent.click(screen.getByRole('button',{name:'读取原本机连接'}));await screen.findByText(/连接中断/);expect(screen.queryByText('本机当前连接就绪')).toBeNull();expect(port.lookup()?.launchId).toBe('launch-one');expect(transport).toHaveBeenCalledTimes(2);
});
it('identity change/unmount aborts old reads, removes old status, and never automatically starts',async()=>{
 localStorage.setItem('uaw.web.local-launch.v1',JSON.stringify({identity:'web-one',lookup:{requestId:'request-one',launchId:'launch-one',revision:1}}));let release!:(r:Response)=>void;
 const transport=vi.fn(()=>new Promise<Response>(r=>{release=r;})),port=new HttpInstalledLaunchPort(new UawClient(session,transport));const v=render(<InstalledConnection port={port} identity="web-one" connected/>);
 v.rerender(<InstalledConnection port={port} identity="other" connected={false}/>);release(new Response(JSON.stringify(ok(installed('ready')))));await waitFor(()=>expect(screen.queryByText('本机当前连接就绪')).toBeNull());expect(screen.getByRole('button',{name:'连接本机只读目录'})).toBeDisabled();expect(transport).toHaveBeenCalledOnce();
});
