// A supplied one-use launch only; no native, approval, cancellation or acceptance clicks.
import {test} from '@playwright/test';
test('MS-U3 real authenticated: explicit visible conversation, reload and original enrollment read only',async({page})=>{
 const forbidden:string[]=[],reads:string[]=[];let exchanges=0;
 page.on('request',r=>{const p=new URL(r.url()).pathname;if(r.method()==='GET')reads.push(p);else if(r.method()==='POST'&&p==='/v1/web/session')exchanges++;else forbidden.push(r.method());});
 // Block unexpected writes before network dispatch, never substitute a result.
 await page.route('**/v1/**',route=>{const r=route.request();if(r.method()==='GET'||r.method()==='POST'&&new URL(r.url()).pathname==='/v1/web/session')return route.continue();return route.abort('blockedbyclient');});
 try{
  const launch=new URL(process.env.UAW_U3_LAUNCH_URL!);launch.searchParams.set('conversation',process.env.UAW_U3_CONVERSATION_ID!);
  await page.goto(launch.href);await page.getByText('已连接 · 分页轮询',{exact:true}).waitFor();
  if(new URL(page.url()).searchParams.get('conversation')!==process.env.UAW_U3_CONVERSATION_ID||new URL(page.url()).hash.includes('uaw_launch'))throw Error();
  const before=exchanges;await page.reload();await page.getByText('已连接 · 分页轮询',{exact:true}).waitFor();
  if(exchanges!==before||new URL(page.url()).searchParams.get('conversation')!==process.env.UAW_U3_CONVERSATION_ID)throw Error();
  await page.getByRole('button',{name:'本机设备与目录状态'}).click();await page.getByLabel('原设备登记ID').fill(process.env.UAW_U3_ENROLLMENT_ID!);
  const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/runner/enrollments/'+process.env.UAW_U3_ENROLLMENT_ID&&r.request().method()==='GET');
  await page.getByRole('button',{name:'读取原设备登记'}).click();const actual=await response;const wire=await actual.json();
  if(wire.kind!=='ok')throw Error();const labels={pending:'等待本人在本机确认',active:'设备登记有效',revoked:'设备登记已撤销',expired:'设备登记已过期'};
  const label=labels[wire.payload?.state as keyof typeof labels];if(!label)throw Error();await page.getByText(label,{exact:true}).waitFor();
  if(forbidden.length||!reads.includes('/v1/conversations/'+process.env.UAW_U3_CONVERSATION_ID))throw Error();
 }catch{throw Error('MS-U3 real readonly trial failed; inspect the original service independently. No launch, credentials, response body, proof or DOM is emitted.');}
});
