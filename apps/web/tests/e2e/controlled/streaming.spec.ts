import {test,expect} from '@playwright/test';
import {controlledBackend} from './backend';
import {frame,makeItem,now,ok,ref} from '../../fixtures';

test('controlled stream: partial text survives reload; final replaces one Item, no replay POST',async({page})=>{
 const state=await controlledBackend(page,'running');let stage=0;
 const message=()=>({...makeItem('stream-reply','agent_message',stage===1?'实际到达的前半句':'实际到达的前半句，和完整后半句。'),revision:stage,status:stage===1?'in_progress':'completed'});
 const events=()=>[
  {action:'run.updated',parameters:state.run},
  {action:'task.frame.committed',parameters:frame},
  ...(stage?[{action:'item.updated',parameters:message()}]:[]),
 ];
 await page.route('**/v1/conversations/conv-one/items?*',async route=>route.fulfill({json:ok({items:state.submitted?[makeItem('user-one','user_message',state.original),...(stage?[message()]:[])]:[],snapshot_revision:stage?3:0})}));
 await page.route('**/v1/conversations/conv-one/events?*',async route=>{
  const after=Number(new URL(route.request().url()).searchParams.get('after_seq')??0);
  const payloads=state.submitted?events():[];
  // Stage 2 is a new event, preserving the exact original event 3 snapshot.
  if(stage===2)payloads.splice(2,0,{action:'item.updated',parameters:{...message(),revision:1,status:'in_progress',text:'实际到达的前半句'}});
  await route.fulfill({json:ok({items:payloads.map((p,n)=>({event_id:'stream-event-'+(n+1),seq:n+1,stream_id:'conv-one',type:p.action,schema_version:'0.1',occurred_at:now,payload_ref:ref('event','stream-event-'+(n+1))})).filter(e=>e.seq>after),snapshot_revision:payloads.length})});
 });
 await page.route('**/v1/events/stream-event-*/payload',async route=>{
  const seq=Number(route.request().url().split('stream-event-')[1].split('/')[0]);
  const parameters=seq<=2?events()[seq-1]:{action:'item.updated',parameters:seq===3?{...message(),revision:1,status:'in_progress',text:'实际到达的前半句'}:message()};
  await route.fulfill({json:ok(parameters)});
 });
 await page.goto('/?conversation=conv-one');await page.getByRole('textbox',{name:'任务原文'}).fill('普通测试');await page.getByRole('button',{name:'发送原文'}).click();
 await expect.poll(()=>state.turnPosts).toBe(1);stage=1;
 const reply=page.locator('[data-item-id="stream-reply"]');
 await expect(reply).toContainText('实际到达的前半句');await expect(reply).toContainText('正在接收正文，尚未完成');
 await page.reload();await expect(reply).toHaveCount(1);await expect(reply).toContainText('实际到达的前半句');expect(state.turnPosts).toBe(1);
 stage=2;await expect(reply).toContainText('和完整后半句');await expect(reply).not.toContainText('正在接收正文');
 await page.getByRole('button',{name:'重新读取并连接'}).click();await expect(reply).toHaveCount(1);expect(state.turnPosts).toBe(1);
 await page.screenshot({path:'.test-results/a18-stream-recovered.png'});
});
