// Explicit A-owned CDP endpoint only; reuse original existing Page, never create a new context or exchange launch.
import {test,chromium} from '@playwright/test';
import {verifyOwnedInstalledPage} from './owned-page';
test('MS-U3b real owner-context: original session GET/reload without lifecycle or exchange writes',async()=>{
 let browser:Awaited<ReturnType<typeof chromium.connectOverCDP>>;
 try{browser=await chromium.connectOverCDP(process.env.UAW_U3B_OWNER_CDP_URL!);const expected=new URL(process.env.UAW_U3B_WEB_URL!);const pages=browser.contexts().flatMap(c=>c.pages()).filter(p=>{const u=new URL(p.url());return u.origin===expected.origin&&u.pathname===expected.pathname&&u.search===expected.search&&!u.hash.includes('uaw_launch');});
  if(pages.length!==1)throw Error();await verifyOwnedInstalledPage(pages[0],process.env.UAW_U3B_LOCAL_LAUNCH_ID!);
 }catch{throw Error('MS-U3b original owner context unavailable or readonly validation failed. No page, cookie, credential or source body is emitted.');}
 // A owns browser/context/page. Do not close it or log out; test worker exit disconnects its own CDP connection.
});
