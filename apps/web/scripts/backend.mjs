import {mkdir,writeFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
await mkdir('.test-results',{recursive:true});let available=false;
try{const response=await fetch('http://127.0.0.1:8000/v1/web/session',{headers:{Referer:'http://127.0.0.1:5173/'},signal:AbortSignal.timeout(3000)});available=response.status===401;}catch{}
if(!available){await writeFile('.test-results/u2-backend-pending.json',JSON.stringify({status:'pending',reason:'A localhost API is unavailable or anonymous probe is not the declared 401'}));console.error('BACKEND PENDING: authenticated chain is not exercised');process.exit(2);}
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test','--project=backend'],{stdio:'inherit',env:{...process.env,UAW_READONLY_BACKEND:'1',UAW_WEB_API_TARGET:'http://127.0.0.1:8000'}});process.exit(result.status??1);
