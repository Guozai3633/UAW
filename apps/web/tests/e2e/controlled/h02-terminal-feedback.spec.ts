import {expectRunState} from './run-state';
import {presentationView} from '../../presentation-fixtures';
// Synthetic exact HTTP DTOs only; never the person's H02 report or authenticated Page.
import {test,expect,type Page} from '@playwright/test';
import type {Schema} from '../../../src/lib/api/types';
import {conversationView,continuationReceipt} from '../../conversation-fixtures';
import {deliveryView} from '../../a2-fixtures';
import {conversation,models,makeItem,makeRun,frame,now,ref,ok} from '../../fixtures';
async function backend(page:Page,status:Schema['RunStatus']='failed',patchState:Schema['RunInputPatch']['state']='accepted',oldFrame=false){
 const receipt=continuationReceipt('original-correction','correction',patchState),view={...conversationView(false),run:makeRun(status,6),input_revision:2,continuation_request_ids:['original-correction']};
 const delivery=deliveryView();delivery.stale=true;delivery.proposal.run_ref.version='4';const artifact=makeItem('artifact-original','artifact','成果已登记，正文在成果栏');artifact.resource_refs=[delivery.artifact_ref];const state={writes:[] as string[],gets:[] as string[],delivery,view};
 await page.route('**/v1/**',async route=>{const request=route.request(),path=new URL(request.url()).pathname;state.gets.push(path);if(request.method()!=='GET'){state.writes.push(path);return route.abort('blockedbyclient');}let value:unknown;
  if(path.endsWith('/presentation'))value=presentationView(view.run,2,['completed','failed','cancelled'].includes(view.run.status)?view.run.status as 'completed'|'failed'|'cancelled':'working');
  else if(path==='/v1/web/session')value={principal:{id:'user-one',kind:'user',auth_session_id:'feedback-controlled'},expires_at:now,csrf_token:'c'.repeat(64)};
  else if(path==='/v1/models')value=models;
  else if(path==='/v1/conversations')value={items:[conversation],snapshot_revision:1};
  else if(path==='/v1/conversations/conv-one')value=conversation;
  else if(path.endsWith('/items'))value={items:[makeItem('user-original','user_message','受控报告原文，不能自动拼接或重发。'),artifact],snapshot_revision:2};
  else if(path.endsWith('/events'))value={items:[{event_id:'run-final',stream_id:'conv-one',seq:1,type:'run.updated',schema_version:'0.1',occurred_at:now,payload_ref:ref('event','run-final')}],snapshot_revision:1};
  else if(path.endsWith('/payload'))value={action:'run.updated',parameters:view.run};
  else if(path==='/v1/runs/run-one')value=view.run;
  else if(path.endsWith('/conversation')){expect(request.headers()['x-uaw-schema-version']).toBe('0.2');value=view;}
  else if(path.endsWith('/continuations/original-correction')){expect(request.headers()['x-uaw-schema-version']).toBe('0.2');value=receipt;}
  else if(path.endsWith('/frame')&&oldFrame)value=frame;
  else if(path.endsWith('/delivery'))value=delivery;
  else return route.fulfill({status:404,json:{kind:'missing',failure:{code:'record_missing',category:'arguments',message:'当前没有新的任务理解或该来源',retryable:false,failed_phase:'read'},output_refs:[]}});
  return route.fulfill({json:ok(value)});
 });return state;
}
const panel=(page:Page)=>page.getByLabel('原任务对话');
for(const status of ['failed','cancelled','completed'] as const)test(`H02-I01 B controlled: accepted + ${status} shows unapplied terminal feedback, no waiting understanding or replay`,async({page})=>{
 const s=await backend(page,status);await page.goto('/?conversation=conv-one');await expectRunState(page,'实际阶段 · '+status);await expect(panel(page)).toContainText('已收到；本次未生效，任务已结束。');await expect(panel(page)).toContainText(status==='failed'?'原任务已失败':status==='cancelled'?'原任务已取消':'原任务已完成');await expect(panel(page).getByText('已收到，尚待生效',{exact:true})).toHaveCount(0);await expect(page.getByLabel('AI理解的任务')).toContainText('本次未单独提供理解摘要');await expect(page.getByLabel('AI理解的任务')).not.toContainText('正在等待');await page.getByLabel('任务原文').fill('  终态后本人草稿\n保留  ');await page.reload();await expect(panel(page)).toContainText('本次未生效');await expect(page.getByLabel('任务原文')).toHaveValue('  终态后本人草稿\n保留  ');expect(s.writes).toEqual([]);expect(s.gets.filter(p=>p.includes('/continuations/')).every(p=>p.endsWith('/original-correction'))).toBe(true);
});
test('H02-I01 B controlled: actually applied correction stays applied after failure; old execution frame is never presented as current model understanding',async({page})=>{
 const s=await backend(page,'failed','applied',true);await page.goto('/?conversation=conv-one');await expect(panel(page).getByText('已生效',{exact:true})).toBeVisible();await expect(panel(page)).not.toContainText('本次未生效');await expect(page.getByLabel('AI理解的任务')).toContainText('本次未单独提供理解摘要');await expect(page.getByLabel('AI理解的任务')).not.toContainText(frame.summary!);await expect(page.getByLabel('AI理解的任务')).toContainText('输入版本 2');await page.reload();await expect(panel(page).getByText('已生效',{exact:true})).toBeVisible();expect(s.writes).toEqual([]);
});
for(const width of [1050,390])test(`H02-I01 B controlled: ${width}px registered old artifact opens with full body/Refs/checks, stale acceptance forbidden and no POST`,async({page})=>{
 await page.setViewportSize({width,height:844});const s=await backend(page);await page.goto('/?conversation=conv-one');const entry=page.getByRole('button',{name:'查看成果 · 1',exact:true});await expect(entry).toBeInViewport();await entry.click();const dialog=page.getByRole('dialog',{name:'已登记成果'});await expect(dialog).toBeVisible();const review=dialog.getByLabel('成果侧栏');await expect(review.getByRole('heading',{name:'完整正文报告'})).toBeVisible();await expect(review).toContainText('这是完整成果，不是条目摘要。');await expect(review).toContainText('逐项核验理由');await expect(review).toContainText('成果对应任务修订 4 · 当前任务修订 6');await expect(review).toContainText('此成果为此前版本，仅供查阅');await expect(review.getByRole('button',{name:'接受整份成果'})).toBeDisabled();await review.getByText('来源与版本',{exact:true}).click();await expect(review).toContainText('input / input-one / 1');await expect(page.getByLabel('成果侧栏')).toHaveCount(1);expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);await page.screenshot({path:`.test-results/h02-i01-b-${width}-old-artifact.png`,fullPage:true});await dialog.getByRole('button',{name:'关闭成果'}).click();await expect(entry).toBeFocused();await page.reload();await expect(entry).toBeInViewport();expect(s.writes).toEqual([]);
});
test('H02-I01 B controlled: old proposal version stays read-only even without stale flag and current nonterminal Run',async({page})=>{
 await page.setViewportSize({width:1050,height:844});const s=await backend(page,'running');s.delivery.stale=false;await page.goto('/?conversation=conv-one');await page.getByRole('button',{name:'查看成果 · 1',exact:true}).click();const review=page.getByLabel('成果侧栏');await expect(review.getByRole('heading',{name:'完整正文报告'})).toBeVisible();await expect(review).toContainText('此成果为此前版本，仅供查阅');await expect(review.getByRole('button',{name:'接受整份成果'})).toBeDisabled();await page.keyboard.press('Escape');await expect(page.getByRole('dialog',{name:'已登记成果'})).toHaveCount(0);await page.getByRole('button',{name:'查看成果 · 1',exact:true}).click();await expect(review.getByRole('button',{name:'接受整份成果'})).toBeDisabled();expect(s.writes).toEqual([]);
});
