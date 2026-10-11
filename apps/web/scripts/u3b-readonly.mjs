// MS-U3b real TCP read-only trial. Never uses private config, native or acceptance.
import {mkdir,writeFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
await mkdir('.test-results',{recursive:true});
const authenticated=process.argv.includes('--authenticated');
const pending=async(reason,missing=[])=>{await writeFile('.test-results/u3b-'+(authenticated?'authenticated':'anonymous')+'-pending.json',JSON.stringify({status:'pending',reason,missing},null,2));console.error('MS-U3b READONLY PENDING:',reason);process.exit(2);};
if(authenticated){
 const missing=['UAW_U3B_WEB_URL','UAW_U3B_OWNER_CDP_URL','UAW_U3B_LOCAL_LAUNCH_ID'].filter(k=>!process.env[k]);
 if(missing.length)await pending('A explicitly supplied original owner CDP context, exact existing page URL and local launch ID are required. New web launch cannot take over an old instance.',missing);
 let valid=false;try{const web=new URL(process.env.UAW_U3B_WEB_URL),cdp=new URL(process.env.UAW_U3B_OWNER_CDP_URL);const loopback=u=>['127.0.0.1','localhost','[::1]'].includes(u.hostname)&&!u.username&&!u.password;
 valid=web.protocol==='http:'&&loopback(web)&&!web.hash&&['http:','ws:'].includes(cdp.protocol)&&loopback(cdp)&&!cdp.search&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(process.env.UAW_U3B_LOCAL_LAUNCH_ID);}catch{}
 if(!valid)await pending('Declared original owner context/page/ID is invalid; credentials are not printed.');
}else{
 let available=false;try{const r=await fetch('http://127.0.0.1:8000/v1/web/session',{headers:{Referer:'http://127.0.0.1:5178/'},signal:AbortSignal.timeout(3000)});available=r.status===401&&(await r.json()).kind==='denied';}catch{}
 if(!available)await pending('A localhost API is unavailable or did not return the declared anonymous denial.');
}
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test','--config=u3b-readonly.config.ts','--project='+ (authenticated?'authenticated':'anonymous')],{stdio:'inherit',env:{...process.env,UAW_U3B_AUTH:authenticated?'1':'',PLAYWRIGHT_NO_COPY_PROMPT:'1',UAW_WEB_API_TARGET:'http://127.0.0.1:8000'}});process.exit(result.status??1);
