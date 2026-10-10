// Fixed HTTP fixtures only. No actual model, OS, native authorization or acceptance.
import {test,expect,type Page} from '@playwright/test';
import {conversation,models,makeRun,makeItem,frame,now,ref,ok,denied} from '../../fixtures';
import {deliveryView} from '../../a2-fixtures';
import {enrollment} from '../../enrollment-fixtures';
async function backend(page:Page){
 const state={writes:0,turns:0,decisions:0,session:'session-one',owner:'user-one',enrollment:enrollment(),lost:false,hidden:false};
 await page.route('**/v1/**',async route=>{const request=route.request(),url=new URL(request.url()),path=url.pathname;const write=request.method()!=='GET';if(write)state.writes++;
  const old={...conversation,id:'conv-old',title:'原待接受会话',owner_id:state.owner},fresh={...conversation,id:'conv-new',title:'最新学术草稿',owner_id:state.owner};
  const run={...makeRun('running'),conversation_id:old.id};let value:unknown;
  if(path==='/v1/web/session')value={principal:{id:state.owner,kind:'user',auth_session_id:state.session},expires_at:now,csrf_token:'c'.repeat(64)};
  else if(path==='/v1/models')value=models;
  else if(path==='/v1/conversations')value={items:state.hidden?[fresh]:[fresh,old],snapshot_revision:2};
  else if(path===`/v1/conversations/${old.id}`||path===`/v1/conversations/${fresh.id}`)value=path.endsWith(old.id)?old:fresh;
  else if(path.endsWith('/items')){const items=path.includes('/conv-old/')?[{...makeItem('original','user_message','原文不可改写'),conversation_id:old.id}]:[];value={items,snapshot_revision:1};}
  else if(path.endsWith('/events'))value={items:path.includes('/conv-old/')?[{event_id:'event-one',stream_id:old.id,seq:1,type:'run.updated',schema_version:'0.1',occurred_at:now,payload_ref:ref('event','event-one')}]:[],snapshot_revision:1};
  else if(path.endsWith('/payload'))value={action:'run.updated',parameters:run};
  else if(path==='/v1/runs/run-one'||path.includes('/turn-requests/'))value=run;
  else if(path.endsWith('/frame'))value=frame;
  else if(path.endsWith('/delivery'))value=deliveryView();
  else if(path.includes('/runner/enrollments/')){
   if(write){state.decisions++;if(state.lost)return route.abort('connectionfailed');state.enrollment=enrollment(path.endsWith('/revocation')?'revoked':'active',2);}
   value=state.enrollment;
  }else if(path.endsWith('/turns')){state.turns++;return route.abort('connectionfailed');}
  else return route.fulfill({status:403,json:denied('route_denied','无可见会话或设备来源')});
  return route.fulfill({json:ok(value)});
 });return state;
}
test('MS-U3: explicit older URL and drafts survive reload, list refresh and back navigation with zero writes',async({page})=>{
 const state=await backend(page);await page.goto('/?conversation=conv-old');await expect(page.locator('.chat-header')).toContainText('原待接受会话');
 await page.getByLabel('任务原文').fill('  旧会话草稿\n保留  ');await page.reload();await expect(page.getByLabel('任务原文')).toHaveValue('  旧会话草稿\n保留  ');
 await expect(page).toHaveURL(/conversation=conv-old/);await page.getByLabel('会话侧栏').getByRole('button',{name:'最新学术草稿'}).click();await page.getByLabel('任务原文').fill('新草稿');await page.reload();await expect(page).toHaveURL(/conversation=conv-new/);await expect(page.getByLabel('任务原文')).toHaveValue('新草稿');
 await page.evaluate(()=>{history.pushState(null,'','/?conversation=conv-old');window.dispatchEvent(new PopStateEvent('popstate'));});await expect(page.locator('.chat-header')).toContainText('原待接受会话');await expect(page.getByLabel('任务原文')).toHaveValue('  旧会话草稿\n保留  ');expect(state.writes).toBe(0);
});
test('MS-U3: hidden explicit URL never falls back to newest or retains old content',async({page})=>{
 const state=await backend(page);await page.goto('/?conversation=conv-hidden');await expect(page.getByRole('alert')).toContainText('可见列表');await expect(page.locator('.original-text')).toHaveCount(0);await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();await expect(page).toHaveURL(/conv-hidden/);expect(state.writes).toBe(0);
});
test('MS-U3: identity change on reload keeps URL but clears foreign drafts and reads current owner only',async({page})=>{
 const state=await backend(page);await page.goto('/?conversation=conv-new');await expect(page.locator('.chat-header')).toContainText('最新学术草稿');await page.getByLabel('任务原文').fill('foreign private draft');state.owner='user-two';state.session='session-two';await page.reload();await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();await expect(page.getByLabel('任务原文')).toHaveValue('');await expect(page).toHaveURL(/conv-new/);expect(state.writes).toBe(0);
});
test('MS-U3: original global recovery stays linked while another conversation retains its draft',async({page})=>{
 const state=await backend(page);
 await page.addInitScript(({now})=>{if(sessionStorage.getItem('u3-seed'))return;sessionStorage.setItem('u3-seed','yes');localStorage.setItem('uaw.web.local.v1',JSON.stringify({identity:`web:${location.origin}:user-one:session-one:${now}`,value:{version:1,activeConversationId:'conv-new',conversationIds:['conv-new','conv-old'],drafts:{'conv-new':'学术原文草稿'},recovery:{conversationId:'conv-old',requestId:'request-original',runId:'run-one'}}}));},{now});
 await page.goto('/?conversation=conv-new');await expect(page.getByLabel('任务原文')).toHaveValue('学术原文草稿');await page.reload();await expect(page.getByLabel('任务原文')).toHaveValue('学术原文草稿');await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();await page.getByRole('button',{name:'返回原请求会话'}).click();await expect(page).toHaveURL(/conv-old/);await expect(page.getByText('实际阶段 · running')).toBeVisible();await page.getByLabel('会话侧栏').getByRole('button',{name:'最新学术草稿'}).click();await expect(page.getByLabel('任务原文')).toHaveValue('学术原文草稿');expect(state.turns).toBe(0);expect(state.writes).toBe(0);
});
test('MS-U3: device pending/active/revoked are actual read states and absent candidate/root are unavailable',async({page})=>{
 const state=await backend(page);await page.goto('/?conversation=conv-new');await page.getByRole('button',{name:'本机设备与目录状态'}).click();
 await expect(page.getByText('可信本机候选来源尚未接入；首次登记不可用。')).toBeVisible();await expect(page.getByRole('button',{name:'请求设备登记'})).toBeDisabled();
 await page.getByLabel('原设备登记ID').fill('enrollment-one');await page.getByRole('button',{name:'读取原设备登记'}).click();await expect(page.getByText('等待本人在本机确认',{exact:true})).toBeVisible();
 state.enrollment=enrollment('active',2);await page.getByRole('button',{name:'读取原设备登记'}).click();await expect(page.getByText('设备登记有效',{exact:true})).toBeVisible();await expect(page.getByText(/不代表目录授权/)).toBeVisible();
 state.enrollment=enrollment('revoked',3);await page.getByRole('button',{name:'读取原设备登记'}).click();await expect(page.getByText('设备登记已撤销',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'读取本人确认结果'})).toBeDisabled();expect(state.writes).toBe(0);await page.screenshot({path:'.test-results/u3-controlled-device.png',fullPage:true});
});
test('MS-U3 controlled: unknown device confirmation survives reload and never retries POST without new original version',async({page})=>{
 const state=await backend(page);state.lost=true;await page.goto('/?conversation=conv-new');await page.getByRole('button',{name:'本机设备与目录状态'}).click();await page.getByLabel('原设备登记ID').fill('enrollment-one');await page.getByRole('button',{name:'读取原设备登记'}).click();await expect(page.getByRole('button',{name:'读取本人确认结果'})).toBeEnabled();await page.getByRole('button',{name:'读取本人确认结果'}).click();await expect(page.getByText(/请求结果未知/)).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'本机设备与目录状态'}).click();await expect(page.getByLabel('原设备登记ID')).toHaveValue('enrollment-one');await page.getByRole('button',{name:'读取原设备登记'}).click();await expect(page.getByRole('button',{name:'读取本人确认结果'})).toBeDisabled();expect(state.decisions).toBe(1);
 state.enrollment=enrollment('active',2);await page.getByRole('button',{name:'读取原设备登记'}).click();await expect(page.getByText('设备登记有效',{exact:true})).toBeVisible();expect(state.decisions).toBe(1);
});
test('MS-U3: server list removal clears active data on read and does not pick a newer conversation',async({page})=>{
 const state=await backend(page);await page.goto('/?conversation=conv-old');await expect(page.locator('.original-text')).toContainText('原文不可改写');state.hidden=true;await page.getByRole('button',{name:'重新读取并连接'}).click();await expect(page.getByRole('alert')).toContainText('可见列表');await expect(page.locator('.original-text')).toHaveCount(0);expect(state.writes).toBe(0);
});
