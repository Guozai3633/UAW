// Intercepted protocol fixtures only. No actual human labels, acceptance or LLM.
import {test,expect,type Page} from '@playwright/test';
import {controlledBackend} from './backend';
import {ok} from '../../fixtures';
import raw from '../../fixtures/quality.json' with {type:'json'};
import type {QualityView,Feedback} from '../../../src/features/quality/port';

async function setup(page:Page){
 const original=await controlledBackend(page);original.submitted=true;
 let view=structuredClone(raw) as QualityView;const writes:string[]=[];let lose=false;const feedback:Feedback[]=[];
 await page.route('**/v1/quality/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  if(path==='/v1/quality/reviews')return route.fulfill({json:ok({items:[{id:view.id,revision:view.revision,title:view.title,status:view.status,updated_at:view.updated_at,origin:view.origin}],next_cursor:null})});
  if(request.method()==='GET')return route.fulfill({json:ok(view)});
  const body=request.postDataJSON();writes.push(path);
  expect(body.meta.expected_revision).toBe(view.revision);expect(body.payload.packet_sha256).toBe(view.packet_sha256);
  view={...view,revision:view.revision+1,judgments:body.payload.judgments};
  if(lose){lose=false;return route.abort('connectionfailed');}
  return route.fulfill({json:ok(view)});
 });
 await page.route('**/v1/runs/run-one/feedback',async route=>{
  const request=route.request();if(request.method()==='GET')return route.fulfill({json:ok({items:feedback})});
  const body=request.postDataJSON();writes.push('/v1/runs/run-one/feedback');
  const next={...body.payload,id:body.payload.feedback_id,run_id:'run-one',revision:1,created_at:raw.created_at,updated_at:raw.updated_at};delete next.feedback_id;
  feedback.push(next);return route.fulfill({json:ok(next)});
 });
 await page.goto('/?conversation=conv-one');
 if((page.viewportSize()?.width??1280)<700)await page.getByRole('button',{name:'显示会话'}).click();
 await expect(page.getByRole('button',{name:'质量审阅与反馈',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'质量审阅与反馈',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'质量审阅与反馈'});
 await dialog.getByRole('button',{name:/受控质量样本/}).click();
 await expect(dialog.getByRole('heading',{name:'实际完整回答'})).toBeVisible();
 return {dialog,writes,loseNext:()=>{lose=true;},original};
}

test('quality controlled: original sources, blank judgments, saved draft and browser reload',async({page})=>{
 const {dialog,writes}=await setup(page);
 await expect(dialog.getByText('合计5。')).toBeVisible();
 await dialog.getByText('given-table · provided_material',{exact:true}).click();
 await expect(dialog.getByText('第一项2；第二项3。')).toBeVisible();
 for(const field of await dialog.getByRole('combobox').all())await expect(field).toHaveValue('');
 await expect(dialog.getByRole('checkbox')).not.toBeChecked();
 await expect(dialog.getByRole('button',{name:'提交我的审阅'})).toBeDisabled();
 await dialog.getByLabel('审阅意见').fill('受控测试草稿；需要继续查阅依据。');
 await dialog.getByRole('button',{name:'保存审阅草稿'}).click();
 await expect(dialog.getByText('草稿已保存，可以关闭后重新打开。')).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'质量审阅与反馈',exact:true}).click();
 await page.getByRole('button',{name:/受控质量样本/}).click();
 await expect(page.getByLabel('审阅意见')).toHaveValue('受控测试草稿；需要继续查阅依据。');
 await expect(page.getByText('审阅 v2 · 草稿',{exact:true})).toBeVisible();
 expect(writes).toEqual(['/v1/quality/reviews/controlled-web-review/draft']);
 await page.screenshot({path:'.test-results/quality-controlled-draft.png',fullPage:true});
});

test('quality controlled: lost reply requires reread and does not resend',async({page})=>{
 const {dialog,writes,loseNext}=await setup(page);loseNext();
 await dialog.getByLabel('审阅意见').fill('受控结果已保存，回复故意丢失。');
 await dialog.getByRole('button',{name:'保存审阅草稿'}).click();
 await expect(dialog.getByText('保存结果尚未确认，先重新读取；不会自动重发。')).toBeVisible();
 await expect(dialog.getByRole('button',{name:'保存审阅草稿'})).toBeDisabled();
 await dialog.getByRole('button',{name:'重新读取此审阅'}).click();
 await expect(dialog.getByText('审阅 v2 · 草稿',{exact:true})).toBeVisible();
 await expect(dialog.getByLabel('审阅意见')).toHaveValue('受控结果已保存，回复故意丢失。');
 expect(writes).toHaveLength(1);
});

for(const width of [1280,390])test(`quality controlled: Run feedback saved and reopened at ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900});
 const {dialog,writes,original}=await setup(page);
 await dialog.getByRole('button',{name:'当前任务反馈',exact:true}).click();
 await expect(dialog.getByText('已读取原任务反馈。')).toBeVisible();
 await dialog.getByLabel('具体问题').fill('受控反馈：等待文案不够清楚。');
 await dialog.getByRole('button',{name:'保存任务反馈'}).click();
 await expect(dialog.getByText('反馈已保存；原任务和成果接受状态保持。')).toBeVisible();
 await dialog.getByRole('button',{name:'关闭',exact:true}).click();
 await page.getByRole('button',{name:'质量审阅与反馈',exact:true}).click();
 await dialog.getByRole('button',{name:'当前任务反馈',exact:true}).click();
 await dialog.getByRole('button',{name:/其他 · v1/}).click();
 await expect(dialog.getByLabel('具体问题')).toHaveValue('受控反馈：等待文案不够清楚。');
 expect(writes).toEqual(['/v1/runs/run-one/feedback']);expect(original.turnPosts).toBe(0);expect(original.decisionPosts).toBe(0);expect(original.controlPosts).toBe(0);
});
