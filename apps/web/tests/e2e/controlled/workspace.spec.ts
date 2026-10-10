import {test,expect} from '@playwright/test';
import {controlledBackend} from './backend';
async function send(page:import('@playwright/test').Page,text='  整理材料\n保留原文  '){
 await page.goto('/?conversation=conv-one');await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();
 await page.getByRole('textbox',{name:'任务原文'}).fill(text);await page.getByRole('button',{name:'发送原文'}).click();
}
test('controlled: original→understanding→Markdown summary; reload/reconnect never resend',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>{errors.push(e.stack??e.message);console.error('PAGEERROR',e.stack??e.message);});const state=await controlledBackend(page);await send(page);await expect.poll(()=>({posts:state.turnPosts,errors})).toEqual({posts:1,errors:[]});
 await expect(page.locator('.original-text')).toHaveText('  整理材料\n保留原文  ');
 await expect(page.getByLabel('AI理解的任务')).toContainText('整理材料，保留来源并输出Markdown报告。');
 await expect(page.getByLabel('成果侧栏').getByRole('heading',{name:'材料报告'})).toBeVisible();
 await expect(page.getByRole('button',{name:'接受整份成果'})).toBeDisabled();
 await expect(page.getByText('实际阶段 · completed')).toBeVisible();await page.reload();
 await expect(page.locator('[data-item-id="user-one"]')).toHaveCount(1);await page.getByRole('button',{name:'重新读取并连接'}).click();
 await expect(page.locator('[data-item-id="artifact-item"]')).toHaveCount(1);expect(state.turnPosts).toBe(1);
 await expect(page.getByRole('button',{name:'发送原文'})).toBeInViewport();await expect(page.getByRole('button',{name:'退出并清理本地草稿'})).toBeInViewport();
 await page.screenshot({path:'.test-results/controlled-workspace.png',fullPage:true});
 const local=await page.evaluate(()=>localStorage.getItem('uaw.web.local.v1'));
 for(const forbidden of ['token','approval','budget','accepted'])expect(local).not.toContain(forbidden);
});
for(const decision of ['批准','拒绝'] as const)test(`controlled: fresh approval ${decision} binds exact hashes and version`,async({page})=>{
 const state=await controlledBackend(page,'approval');await send(page);await expect(page.getByLabel('人工审批')).toBeVisible();
 await page.getByRole('button',{name:decision==='批准'?'仅批准本次':'拒绝',exact:true}).click();
 await expect.poll(()=>state.decisionPosts).toBe(1);expect(state.decisionBody).toMatchObject({meta:{expected_revision:1},payload:{decision:{decision:decision==='批准'?'approve_once':'decline',expected_arguments_hash:'a'.repeat(64)}}});
 await page.reload();await expect(page.getByLabel('人工审批').getByText(decision==='批准'?'approved':'declined',{exact:true})).toBeVisible();expect(state.decisionPosts).toBe(1);
});
test('controlled: stale approval prevents POST',async({page})=>{const state=await controlledBackend(page,'approval');await send(page);await expect(page.getByLabel('人工审批')).toBeVisible();
 state.staleApproval=true;await page.getByRole('button',{name:'仅批准本次'}).click();await expect(page.getByRole('alert')).toContainText('审批已过期或版本变化');expect(state.decisionPosts).toBe(0);
});
test('controlled: actual terminal confirms cancel, no resend on refresh',async({page})=>{const state=await controlledBackend(page,'running');await send(page);
 await expect(page.getByText('实际阶段 · running')).toBeVisible();await page.getByRole('button',{name:'停止',exact:true}).click();await expect(page.getByText('实际阶段 · cancelled')).toBeVisible();
 await page.reload();await expect(page.getByText('实际阶段 · cancelled')).toBeVisible();expect(state.turnPosts).toBe(1);expect(state.controlPosts).toBe(1);
});
test('controlled: unknown send retained across refresh without matching text or resubmission',async({page})=>{const state=await controlledBackend(page,'unknown');await send(page);
 await expect(page.getByRole('alert')).toContainText('请求结果未知');await page.reload();await expect(page.getByRole('alert')).toContainText('待对账');
 await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();expect(state.turnPosts).toBe(1);
});
test('controlled: mobile layout, unavailable identity and denied API are readable',async({page})=>{
 await page.route('**/v1/web/session',route=>route.fulfill({status:503,json:{kind:'failed',failure:{code:'capability_unavailable',category:'dependency',message:'浏览器身份入口尚未接入',retryable:false,failed_phase:'authentication'},output_refs:[]}}));
 await page.setViewportSize({width:390,height:844});await page.goto('/');await expect(page.getByRole('alert')).toContainText('身份入口尚未接入');
 await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.screenshot({path:'.test-results/controlled-mobile.png',fullPage:true});
 await controlledBackend(page,'denied');await page.goto('/');await expect(page.getByRole('alert')).toContainText('浏览器入口未开放');
});

test('controlled: create uses actual model catalog and remains usable after opening',async({page})=>{
 const state=await controlledBackend(page);await page.goto('/');await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();
 await page.getByRole('button',{name:'新建会话',exact:true}).click();await expect(page.getByLabel('模型')).toContainText('受控测试模型（非LLM）');
 await page.getByRole('button',{name:'创建会话',exact:true}).click();await expect(page.getByLabel('会话侧栏').getByRole('button',{name:'研究材料整理'})).toBeVisible();
 await page.getByRole('textbox',{name:'任务原文'}).fill('创建后发送');await expect(page.getByRole('button',{name:'发送原文'})).toBeEnabled();await page.getByRole('button',{name:'发送原文'}).click();await expect.poll(()=>state.turnPosts).toBe(1);
});
test('controlled: disconnected reads reconcile original Run before reconnecting, never dispatch again',async({page})=>{
 const state=await controlledBackend(page,'running');await send(page);await expect(page.getByText('实际阶段 · running')).toBeVisible();
 state.disconnect=true;await page.getByRole('button',{name:'重新读取并连接'}).click();await expect(page.getByRole('alert')).toContainText('连接中断');await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();
 state.disconnect=false;await page.getByRole('button',{name:'重新读取并连接'}).click();await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();await page.reload();await expect(page.getByText('实际阶段 · running')).toBeVisible();expect(state.turnPosts).toBe(1);
});
