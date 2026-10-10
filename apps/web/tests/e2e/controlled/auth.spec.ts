// Intercepted session protocol fixture, NOT real authentication acceptance.
import {test,expect} from '@playwright/test';
import {ok,models,now,denied} from '../../fixtures';
const session={principal:{id:'user-one',kind:'user',auth_session_id:'web-session-one'},expires_at:now,csrf_token:'c'.repeat(64)};
test('controlled: published session exchange removes fragment, logout clears local drafts and uses CSRF',async({page})=>{
 let exchanges=0,logout=0,loggedIn=false;await page.route('**/v1/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;
 if(path==='/v1/models')return route.fulfill({json:ok(models)});
 if(path==='/v1/web/session'&&req.method()==='POST'){exchanges++;expect(req.postDataJSON().payload).toEqual({launch_code:'controlled-one-use'});loggedIn=true;return route.fulfill({json:ok(session),headers:{'Set-Cookie':'controlled_session=test; Path=/; HttpOnly; SameSite=Strict'}});}
 if(path==='/v1/web/session'&&req.method()==='DELETE'){logout++;expect(req.headers()['x-uaw-csrf']).toBe(session.csrf_token);expect(req.postDataJSON().payload).toEqual({});loggedIn=false;return route.fulfill({json:ok({operation_id:'logout-one',status:'completed'}),headers:{'Set-Cookie':'controlled_session=; Path=/; HttpOnly; Max-Age=0'}});}
 return route.fulfill(loggedIn?{json:ok(session)}:{status:403,json:denied('authentication_required','请使用本机启动链接')});});
 await page.goto('/#uaw_launch=controlled-one-use');await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();expect(new URL(page.url()).hash).toBe('');expect(exchanges).toBe(1);
 const stored=await page.evaluate(()=>JSON.stringify(localStorage));expect(stored).not.toContain(session.csrf_token);expect(stored).not.toContain('controlled-one-use');
 await page.getByRole('button',{name:'退出并清理本地草稿'}).click();await expect.poll(()=>logout).toBe(1);await expect(page.getByRole('alert')).toContainText('会话已清理');expect(await page.evaluate(()=>localStorage.length)).toBe(0);await page.reload();await expect(page.getByRole('alert')).toContainText('本机启动链接');expect(exchanges).toBe(1);
});
test('controlled: lost exchange reconciles GET cookie session without consuming launch code twice',async({page})=>{
 let posts=0;await page.route('**/v1/**',async route=>{if(route.request().method()==='POST'){posts++;return route.abort('connectionfailed');}return route.fulfill({json:ok(new URL(route.request().url()).pathname==='/v1/models'?models:session)});});
 await page.goto('/#uaw_launch=controlled-lost');await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();expect(posts).toBe(1);expect(new URL(page.url()).hash).toBe('');
});
