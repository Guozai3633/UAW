// Real browser/API only. No route interception, response fixture, injected identity or LLM substitute.
import {test,expect,type Cookie} from '@playwright/test';
let cookies:Cookie[]=[];
test.describe.configure({mode:'serial'});
test.beforeAll(async({browser})=>{const context=await browser.newContext();try{const page=await context.newPage();try{await page.goto(process.env.UAW_LIVE_LAUNCH_URL!);await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();}catch{throw new Error('实际本机会话交换未完成；启动链接未记录。');}cookies=await context.cookies();}finally{await context.close();}});
test.beforeEach(async({context})=>{await context.addCookies(cookies);});
test.afterAll(()=>{cookies=[];});
test('live: original to actual understanding/artifact and refresh without resubmission',async({page})=>{
 test.setTimeout(210000);
 const posts:string[]=[];page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/turns'))posts.push(r.postData()??'');});
 await page.goto('/');await expect(page.getByText('已连接 · 分页轮询')).toBeVisible();
 await page.getByRole('button',{name:'新建会话',exact:true}).click();await page.getByLabel('会话名称').fill('MS-U2 真实文本验收');await page.getByRole('button',{name:'创建会话',exact:true}).click();
 const original='把以下资料整理成一份简短Markdown报告，并逐项核验；不要改变资料。资料：项目甲完成3项，项目乙完成2项，总计5项。';
 const actualFrame=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/frame')&&r.status()===200,{timeout:180000});
 const actualDelivery=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/delivery')&&r.status()===200,{timeout:180000});
 await page.getByRole('textbox',{name:'任务原文'}).fill(original);await page.getByRole('button',{name:'发送原文'}).click();
 await expect(page.locator('.original-text')).toHaveText(original);const frame=(await (await actualFrame).json()).payload;expect(typeof frame.summary).toBe('string');expect(frame.summary.length).toBeGreaterThan(0);await expect(page.getByLabel('AI理解的任务')).toContainText(frame.summary);
 await expect(page.locator('[data-item-id]').filter({has:page.locator('.message-meta b',{hasText:'成果已登记'})})).toBeVisible({timeout:180000});
 const delivery=(await (await actualDelivery).json()).payload;expect(delivery.content.length).toBeGreaterThan(0);await expect(page.getByLabel('成果侧栏').getByRole('heading',{name:delivery.artifact.title,exact:true})).toBeVisible();
 await expect(page.getByLabel('成果侧栏').getByText('尚无可用的完整正文与核验',{exact:false})).toHaveCount(0);
 for(const verdict of delivery.report.verdicts)await expect(page.getByLabel('成果侧栏').getByText(verdict.reason,{exact:true})).toBeVisible();
 await page.reload();await expect(page.locator('.original-text')).toContainText(original);expect(posts).toHaveLength(1);
 await page.screenshot({path:'.test-results/live-artifact.png',fullPage:true});
});
test('live: actual pending approval and current decision',async({page})=>{
 await page.goto('/?conversation='+encodeURIComponent(process.env.UAW_LIVE_APPROVAL_CONVERSATION!));await expect(page.getByLabel('人工审批')).toBeVisible();
 await page.getByRole('button',{name:'仅批准本次'}).click();await expect(page.getByLabel('人工审批').getByText('approved',{exact:true})).toBeVisible({timeout:30000});await page.reload();
 await expect(page.getByLabel('人工审批').getByText('approved',{exact:true})).toBeVisible();
});
test('live: actual cancellation confirmed after refresh',async({page})=>{
 await page.goto('/?conversation='+encodeURIComponent(process.env.UAW_LIVE_CANCEL_CONVERSATION!));await expect(page.getByRole('button',{name:'停止',exact:true})).toBeEnabled();await page.getByRole('button',{name:'停止',exact:true}).click();
 await expect(page.getByText('实际阶段 · cancelled')).toBeVisible({timeout:60000});await page.reload();await expect(page.getByText('实际阶段 · cancelled')).toBeVisible();
});

test('live: actual decline and refresh do not decide again',async({page})=>{await page.goto('/?conversation='+encodeURIComponent(process.env.UAW_LIVE_DECLINE_CONVERSATION!));await expect(page.getByLabel('人工审批')).toBeVisible();await page.getByRole('button',{name:'拒绝',exact:true}).click();await expect(page.getByLabel('人工审批').getByText('declined',{exact:true})).toBeVisible();await page.reload();await expect(page.getByLabel('人工审批').getByText('declined',{exact:true})).toBeVisible();});
test('live: exact contract acceptance is confirmed by receipt then actual Run',async({page})=>{await page.goto('/?conversation='+encodeURIComponent(process.env.UAW_LIVE_ACCEPTANCE_CONVERSATION!));await expect(page.getByRole('button',{name:'接受整份成果'})).toBeEnabled();await page.getByRole('button',{name:'接受整份成果'}).click();await expect(page.getByText('实际合同决定：accept',{exact:false})).toBeVisible();await expect(page.getByText('实际阶段 · completed')).toBeVisible({timeout:60000});await page.reload();await expect(page.getByText('实际阶段 · completed')).toBeVisible();});
