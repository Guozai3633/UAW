import {writeFile,mkdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
const missing=['UAW_LIVE_WEB_URL','UAW_LIVE_LAUNCH_URL','UAW_LIVE_DECLINE_CONVERSATION','UAW_LIVE_ACCEPTANCE_CONVERSATION','UAW_LIVE_APPROVAL_CONVERSATION','UAW_LIVE_CANCEL_CONVERSATION'].filter(k=>!process.env[k]);
await mkdir('.test-results',{recursive:true});
if(missing.length){await writeFile('.test-results/live-pending.json',JSON.stringify({status:'pending',missing,
 reason:'A ms-i2j-a1 session protocol is consumed; an actual reachable configured backend, one-use launch URL, current trial fixtures and complete recovery/content/acceptance adapters are missing here. Controlled tests are not live acceptance.'},null,2));console.error('LIVE PENDING:',missing.join(', '));process.exit(2);}
const u=new URL(process.env.UAW_LIVE_WEB_URL);if(!['127.0.0.1','localhost','[::1]'].includes(u.hostname))throw Error('Live trial must use the declared localhost host');
const launch=new URL(process.env.UAW_LIVE_LAUNCH_URL);if(launch.origin!==u.origin||!new URLSearchParams(launch.hash.slice(1)).get('uaw_launch'))throw Error('A same-origin one-use launch fragment is required');
const result=spawnSync(process.execPath,['node_modules/@playwright/test/cli.js','test','--project=live'],{stdio:'inherit',env:{...process.env,UAW_LIVE_ONLY:'1'}});
process.exit(result.status??1);
