// Controlled public HTTP only; no real native, OS keys, directory authorization or file execution.
import {test,expect,type Page} from '@playwright/test';
import {conversation,models,now,ok,denied} from '../../fixtures';
import {installed} from '../../installed-fixtures';
import {verifyOwnedInstalledPage} from '../../u3b-readonly/owned-page';
async function backend(page:Page){
 const state={starts:[] as string[],stops:0,gets:0,logout:0,identity:'session-one',loggedIn:true,lostStart:false,lostStop:false,unavailable:false,postReadsLost:false,view:installed()};
 await page.route('**/v1/**',async route=>{const r=route.request(),path=new URL(r.url()).pathname;
  if(path==='/v1/web/session'){if(r.method()==='DELETE'){state.logout++;state.loggedIn=false;return route.fulfill({json:ok({operation_id:'logout-one',status:'completed'})});}return route.fulfill(state.loggedIn?{json:ok({principal:{id:'user-one',kind:'user',auth_session_id:state.identity},expires_at:now,csrf_token:'c'.repeat(64)})}:{status:401,json:denied()});}
  if(path==='/v1/models')return route.fulfill({json:ok(models)});
  if(path==='/v1/conversations')return route.fulfill({json:ok({items:[conversation],snapshot_revision:1})});
  if(path==='/v1/conversations/conv-one')return route.fulfill({json:ok(conversation)});
  if(path.endsWith('/items')||path.endsWith('/events'))return route.fulfill({json:ok({items:[],snapshot_revision:1})});
  if(path==='/v1/runner/local'){
   const body=r.postDataJSON();expect(body.payload).toEqual({});state.starts.push(body.meta.request_id);
   if(state.unavailable)return route.fulfill({status:503,json:{...denied('dependency_unavailable','本机安装来源未配置'),kind:'failed'}});
   state.view=installed('starting',1,body.meta.request_id);if(state.lostStart){state.lostStart=false;return route.abort('connectionfailed');}return route.fulfill({status:202,json:ok(state.view)});
  }
  if(path==='/v1/runner/local/launch-one/stop'){const body=r.postDataJSON();expect(body.payload).toEqual({});expect(body.meta.expected_revision).toBe(state.view.revision);state.stops++;state.view=installed('closed',state.view.revision+1,state.view.request_id);if(state.lostStop){state.postReadsLost=true;return route.abort('connectionfailed');}return route.fulfill({json:ok(state.view)});}
  if(path==='/v1/runner/local/launch-one'){state.gets++;if(state.postReadsLost)return route.abort('connectionfailed');return route.fulfill({json:ok(state.view)});}
  return route.fulfill({status:403,json:denied('unknown_route','无此公开来源')});
 });return state;
}
async function open(page:Page){await page.getByRole('button',{name:'本机设备与目录状态'}).click();await expect(page.getByText('选择你愿意开放的目录。')).toBeVisible();}
test('MS-U3b controlled: click starts once, system steps and current lifecycle never imply file rights, stop is original CAS',async({page})=>{
 const s=await backend(page);await page.goto('/?conversation=conv-one');await open(page);expect(s.starts).toHaveLength(0);await page.getByRole('button',{name:'连接本机只读目录',exact:true}).dblclick();await expect(page.getByText('本机连接已登记',{exact:true})).toBeVisible();expect(s.starts).toHaveLength(1);
 for(const state of ['waiting_device','connecting','selecting_directory','ready'] as const){s.view=installed(state,s.view.revision+1,s.view.request_id);await page.getByRole('button',{name:'读取原本机连接',exact:true}).click();await expect(page.getByText(`实际状态：${state}`,{exact:false})).toBeVisible();}
 await expect(page.getByText('每次文件工具、任务、审批与预算仍需独立复查。')).toBeVisible();await page.screenshot({path:'.test-results/u3b-controlled-ready.png',fullPage:true});await page.getByRole('button',{name:'停止本机连接',exact:true}).click();await expect(page.getByText('本机连接已关闭',{exact:true})).toBeVisible();expect(s.stops).toBe(1);
});
test('MS-U3b controlled: known-ID refresh and conversation switch only GET original launch, draft is preserved',async({page})=>{
 const s=await backend(page);await page.goto('/?conversation=conv-one');await expect(page.locator('.chat-header')).toContainText(conversation.title);await page.getByLabel('任务原文').fill('  固定用户原文\n保留  ');await open(page);await page.getByRole('button',{name:'连接本机只读目录',exact:true}).click();await expect(page.getByText('本机连接已登记',{exact:true})).toBeVisible();s.view=installed('ready',2,s.view.request_id);
 await page.reload();await open(page);await expect(page.getByText('本机当前连接就绪',{exact:true})).toBeVisible();expect(s.starts).toHaveLength(1);await page.getByRole('button',{name:'返回工作区'}).click();await expect(page.getByLabel('任务原文')).toHaveValue('  固定用户原文\n保留  ');
 const saved=await page.evaluate(()=>localStorage.getItem('uaw.web.local-launch.v1'));expect(saved).not.toContain('ready');expect(saved).not.toContain('device_ref');expect(saved).not.toContain('proof');expect(s.gets).toBeGreaterThan(0);
});
test('MS-U3b controlled: lost start has no ID; reload never POSTs and explicit recovery replays same request ID',async({page})=>{
 const s=await backend(page);s.lostStart=true;await page.goto('/');await open(page);await page.getByRole('button',{name:'连接本机只读目录',exact:true}).click();await expect(page.getByRole('button',{name:'恢复原连接请求'})).toBeVisible();const original=s.starts[0];await page.reload();await open(page);await expect(page.getByRole('button',{name:'恢复原连接请求'})).toBeVisible();expect(s.starts).toEqual([original]);expect(s.gets).toBe(0);
 await page.getByRole('button',{name:'恢复原连接请求'}).click();await expect(page.getByText('本机连接已登记',{exact:true})).toBeVisible();expect(s.starts).toEqual([original,original]);await page.reload();await open(page);await expect(page.getByText('本机连接已登记',{exact:true})).toBeVisible();expect(s.starts).toEqual([original,original]);
});
test('MS-U3b controlled: stop unknown first GETs on reload, terminal original response clears it without another stop',async({page})=>{
 const s=await backend(page);await page.goto('/');await open(page);await page.getByRole('button',{name:'连接本机只读目录',exact:true}).click();await expect(page.getByText('本机连接已登记',{exact:true})).toBeVisible();s.lostStop=true;await page.getByRole('button',{name:'停止本机连接',exact:true}).click();await expect(page.getByText('原停止结果待对账；只读取原连接，不会重发停止。')).toBeVisible();expect(s.stops).toBe(1);
 s.postReadsLost=false;await page.reload();await open(page);await expect(page.getByText('本机连接已关闭',{exact:true})).toBeVisible();expect(s.stops).toBe(1);expect(s.starts).toHaveLength(1);
});
test('MS-U3b controlled: same account new session cannot inherit, logout clears lookup without frontend stop',async({page})=>{
 const s=await backend(page);await page.goto('/');await open(page);await page.getByRole('button',{name:'连接本机只读目录',exact:true}).click();await expect(page.getByText('本机连接已登记',{exact:true})).toBeVisible();const reads=s.gets;s.identity='session-two';await page.reload();await open(page);await expect(page.getByRole('button',{name:'连接本机只读目录',exact:true})).toBeEnabled();expect(s.gets).toBe(reads);await expect(page.getByText('原连接：launch-one')).toHaveCount(0);expect(s.starts).toHaveLength(1);
 await page.getByRole('button',{name:'返回工作区'}).click();await page.getByRole('button',{name:'退出并清理本地草稿'}).click();await expect.poll(()=>s.logout).toBe(1);expect(await page.evaluate(()=>localStorage.getItem('uaw.web.local-launch.v1'))).toBeNull();expect(s.stops).toBe(0);
});
test('MS-U3b controlled: actual 503 is unavailable, refresh does not retry or show ready',async({page})=>{
 const s=await backend(page);s.unavailable=true;await page.goto('/');await open(page);await page.getByRole('button',{name:'连接本机只读目录',exact:true}).click();await expect(page.getByText('本机安装来源未配置',{exact:true})).toBeVisible();await page.reload();await open(page);expect(s.starts).toHaveLength(1);await expect(page.getByText('本机当前连接就绪',{exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'连接本机只读目录',exact:true})).toBeEnabled();
});

test('MS-U3b controlled: reusable same owner Page verifier performs GET/reload with no launch exchange or lifecycle write',async({page})=>{
 const s=await backend(page);await page.goto('/?conversation=conv-one');await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();s.view=installed('ready',3);await verifyOwnedInstalledPage(page,'launch-one');expect(s.starts).toEqual([]);expect(s.stops).toBe(0);expect(s.gets).toBeGreaterThanOrEqual(3);
});
