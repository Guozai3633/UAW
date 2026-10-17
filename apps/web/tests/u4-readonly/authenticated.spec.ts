import {test,chromium} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
import {verifyOwnedConversationPage} from './owned-page';
test('MS-U4 actual new service: original owner Page GET graph and original receipts only',async()=>{
 try{const browser=await chromium.connectOverCDP(process.env.UAW_U4_OWNER_CDP_URL!,{timeout:15000}),expected=new URL(process.env.UAW_U4_WEB_URL!);const pages=browser.contexts().flatMap(c=>c.pages()).filter(p=>p.url()===expected.href);if(pages.length!==1)throw Error();const observation=await verifyOwnedConversationPage(pages[0],process.env.UAW_U4_RUN_ID!);await writeFile('.test-results/ms-u4-live-observation.json',JSON.stringify(observation,null,2));}
 catch{throw Error('MS-U4 original owner Page or actual source unavailable/changed. No session, URL, credential or response body is emitted.');}
 // A owns Page/browser/context. Do not navigate, close, log out, exchange a launch or create another context.
});
