import type {Page} from '@playwright/test';
import {validate} from '../../src/lib/api/validation';
import {canonical} from '../../src/lib/api/canonical';
// A can call this with its original authenticated Page; no new browser/session or credential exchange.
export async function verifyOwnedInstalledPage(page:Page,launchId:string){
 if(!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(launchId)||new URL(page.url()).hash.includes('uaw_launch'))throw Error('Original owner page/ID required');
 let writes=0;const onRequest=(r:import('@playwright/test').Request)=>{if(new URL(r.url()).pathname.startsWith('/v1/')&&r.method()!=='GET')writes++;};
 const guard=async(route:import('@playwright/test').Route)=>{if(route.request().method()==='GET')await route.fallback();else await route.abort('blockedbyclient');};
 page.on('request',onRequest);await page.route('**/v1/**',guard);
 try{
  const read=async()=>page.evaluate(async id=>({session:await(await fetch('/v1/web/session',{credentials:'same-origin',cache:'no-store'})).json(),launch:await(await fetch('/v1/runner/local/'+encodeURIComponent(id),{credentials:'same-origin',cache:'no-store'})).json()}),launchId);
  const original=await read();validate('HttpWebSessionGetResult',original.session);validate('HttpRunnerLocalGetResult',original.launch);
  if(original.session.kind!=='ok'||original.session.payload.principal.kind!=='user'||original.launch.kind!=='ok'||original.launch.payload.id!==launchId)throw Error();
  const identity=canonical(original.session.payload.principal),expiry=original.session.payload.expires_at,wire=original.launch.payload;
  // Persist only verified original lookup metadata in this same owner context. Never export cookies/session state.
  await page.evaluate(({wire,identityKey})=>localStorage.setItem('uaw.web.local-launch.v1',JSON.stringify({identity:identityKey,lookup:{requestId:wire.request_id,launchId:wire.id,revision:wire.revision}})),{wire:{request_id:wire.request_id,id:wire.id,revision:wire.revision},identityKey:`web:${new URL(page.url()).origin}:${original.session.payload.principal.id}:${original.session.payload.principal.auth_session_id}:${expiry}`});
  await page.reload();await page.getByText('已连接 · 分页轮询',{exact:true}).waitFor();const refreshed=await read();validate('HttpWebSessionGetResult',refreshed.session);validate('HttpRunnerLocalGetResult',refreshed.launch);
  if(refreshed.session.kind!=='ok'||canonical(refreshed.session.payload.principal)!==identity||refreshed.session.payload.expires_at!==expiry||refreshed.launch.kind!=='ok'||refreshed.launch.payload.id!==wire.id||refreshed.launch.payload.request_id!==wire.request_id||refreshed.launch.payload.revision<wire.revision)throw Error();
  const response=page.waitForResponse(r=>r.request().method()==='GET'&&new URL(r.url()).pathname==='/v1/runner/local/'+launchId);
  await page.getByRole('button',{name:'本机设备与目录状态'}).click();const actual=await(await response).json();validate('HttpRunnerLocalGetResult',actual);
  if(actual.kind!=='ok'||actual.payload.id!==wire.id||actual.payload.request_id!==wire.request_id||actual.payload.revision<refreshed.launch.payload.revision)throw Error();
  await page.getByText('实际状态：'+actual.payload.state,{exact:false}).waitFor();const finalSession=await page.evaluate(async()=>await(await fetch('/v1/web/session',{credentials:'same-origin',cache:'no-store'})).json());validate('HttpWebSessionGetResult',finalSession);
  if(finalSession.kind!=='ok'||canonical(finalSession.payload.principal)!==identity||finalSession.payload.expires_at!==expiry||writes)throw Error();
 }catch{throw Error('Owned-page readonly validation failed; no credentials, proof, response body or DOM are emitted.');}
 finally{page.off('request',onRequest);await page.unroute('**/v1/**',guard);}
}
