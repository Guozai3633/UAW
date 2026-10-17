// Explicit A-supplied exact new service and original owner browser only. No default localhost/launch discovery.
import {mkdir,writeFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
await mkdir('.test-results',{recursive:true});
async function pending(reason,missing=[]){await writeFile('.test-results/ms-u4-live-pending.json',JSON.stringify({status:'pending',reason,missing},null,2));console.error('MS-U4 READONLY PENDING:',reason);process.exit(2);}
const missing=['UAW_U4_WEB_URL','UAW_U4_OWNER_CDP_URL','UAW_U4_RUN_ID'].filter(k=>!process.env[k]);
if(missing.length)await pending('A must supply the exact new version URL, original owner CDP Page and actual Run ID. No connection attempted.',missing);
let valid=false;try{const web=new URL(process.env.UAW_U4_WEB_URL),cdp=new URL(process.env.UAW_U4_OWNER_CDP_URL),local=u=>['127.0.0.1','localhost','[::1]'].includes(u.hostname)&&!u.username&&!u.password;valid=web.protocol==='http:'&&local(web)&&!web.hash&&web.searchParams.size===1&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(web.searchParams.get('conversation')??'')&&['http:','ws:'].includes(cdp.protocol)&&local(cdp)&&!cdp.search&&!cdp.hash&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(process.env.UAW_U4_RUN_ID);}catch{}
if(!valid)await pending('Declared original owner Page/Run is invalid. Credentials are not printed; no connection attempted.');
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test','--config=u4-readonly.config.ts','--project=owner-page'],{stdio:'inherit',env:{...process.env,PLAYWRIGHT_NO_COPY_PROMPT:'1'}});process.exit(result.status??1);
