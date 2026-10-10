// MS-U3 real TCP read-only trial. Never uses private config, native or acceptance.
import {mkdir,writeFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
await mkdir('.test-results',{recursive:true});
const authenticated=process.argv.includes('--authenticated');
const pending=async(reason,missing=[])=>{await writeFile('.test-results/u3-'+(authenticated?'authenticated':'anonymous')+'-pending.json',JSON.stringify({status:'pending',reason,missing},null,2));console.error('MS-U3 READONLY PENDING:',reason);process.exit(2);};
if(authenticated){
 const missing=['UAW_U3_WEB_URL','UAW_U3_LAUNCH_URL','UAW_U3_CONVERSATION_ID','UAW_U3_ENROLLMENT_ID'].filter(k=>!process.env[k]);
 if(missing.length)await pending('A short-lived launch and actual visible conversation/enrollment IDs are required; no native or result decision will be clicked.',missing);
 let valid=false;try{const web=new URL(process.env.UAW_U3_WEB_URL),launch=new URL(process.env.UAW_U3_LAUNCH_URL);valid=web.protocol==='http:'&&['127.0.0.1','localhost','[::1]'].includes(web.hostname)&&launch.origin===web.origin&&!!new URLSearchParams(launch.hash.slice(1)).get('uaw_launch')&&!web.username&&!web.password&&['UAW_U3_CONVERSATION_ID','UAW_U3_ENROLLMENT_ID'].every(k=>/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(process.env[k]));}catch{}
 if(!valid)await pending('Declared loopback launch or actual lookup IDs are invalid. Credentials are not printed.');
}else{
 let available=false;try{const r=await fetch('http://127.0.0.1:8000/v1/web/session',{headers:{Referer:'http://127.0.0.1:5178/'},signal:AbortSignal.timeout(3000)});available=r.status===401&&(await r.json()).kind==='denied';}catch{}
 if(!available)await pending('A localhost API is unavailable or did not return the declared anonymous denial.');
}
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test','--config=u3-readonly.config.ts','--project='+ (authenticated?'authenticated':'anonymous')],{stdio:'inherit',env:{...process.env,UAW_U3_AUTH:authenticated?'1':'',UAW_WEB_API_TARGET:'http://127.0.0.1:8000'}});process.exit(result.status??1);
