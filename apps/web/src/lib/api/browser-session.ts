import {UawClient,requestMeta,type WebSession} from './client';
import type {Schema} from './types';
import type {WorkspaceHost} from '../../features/workspace/controller';
// Exact published ms-i2j-a1 protocol. Launch and CLI Bearer remain outside Web.
export class BrowserSessionHost implements WorkspaceHost {
 private current:Schema['WebSession']|undefined;private listeners=new Set<()=>void>();
 private error='正在读取当前浏览器会话…';private timer:ReturnType<typeof setTimeout>|undefined;
 private abort=new AbortController();private generation=0;
 constructor(private transport:typeof fetch=(input,init)=>fetch(input,init)){}
 session=():WebSession|null=>{const v=this.current;if(!v||Date.parse(v.expires_at)<=Date.now())return null;
  return{identityKey:`web:${location.origin}:${v.principal.id}:${v.principal.auth_session_id}:${v.expires_at}`,csrfHeader:{name:'X-UAW-CSRF',value:v.csrf_token}};};
 unavailableReason=()=>this.error;
 subscribe=(f:()=>void)=>{this.listeners.add(f);return()=>{this.listeners.delete(f);};};
 private publish(value:Schema['WebSession']|undefined,error=''){
  const previous=this.session()?.identityKey;const oldError=this.error;
  if(value&&(value.principal.kind!=='user'||Date.parse(value.expires_at)<=Date.now())){value=undefined;error='浏览器用户会话已过期或不可用。';}
  this.current=value;this.error=error;
  if(previous!==this.session()?.identityKey||oldError!==error)for(const listener of this.listeners)listener();
 }
 private schedule(g:number){clearTimeout(this.timer);if(g!==this.generation)return;
  this.timer=setTimeout(()=>void this.refresh(g),Math.min(10000,Math.max(100,Date.parse(this.current?.expires_at??'')-Date.now()||10000)));}
 private async refresh(g:number){try{const v=await new UawClient(this.session,this.transport).webSession(this.abort.signal);if(g===this.generation)this.publish(v);}
  catch(e){if(g===this.generation)this.publish(undefined,e instanceof Error?e.message:'会话读取不可用。');}finally{this.schedule(g);}}
 async initialize(){const g=++this.generation;this.abort.abort();this.abort=new AbortController();clearTimeout(this.timer);
  const fragment=new URLSearchParams(location.hash.slice(1));const code=fragment.get('uaw_launch');
  // Remove transient credential before dispatch, rendering, or async waiting.
  if(code!==null){fragment.delete('uaw_launch');history.replaceState(null,'',location.pathname+location.search+(fragment.size?'#'+fragment:''));}
  if(code!==null){try{const v=await new UawClient(this.session,this.transport).exchange(code,requestMeta(),this.abort.signal);if(g===this.generation){this.publish(v);this.schedule(g);}return;}
   catch{/* Lost exchange is reconciled by GET; never replay the one-use code. */}}
  await this.refresh(g);
 }
 logout=async()=>{const session=this.session();++this.generation;clearTimeout(this.timer);this.abort.abort();this.abort=new AbortController();this.publish(undefined,'会话已清理，请使用新的本机启动链接。');
  if(!session)return;
  try{await new UawClient(()=>session,this.transport).logout(requestMeta(),this.abort.signal);}
  catch(e){this.publish(undefined,'退出结果未确认；本地已清理。'+(e instanceof Error?e.message:''));}
 };
 dispose(){++this.generation;this.abort.abort();clearTimeout(this.timer);this.publish(undefined,'浏览器会话已关闭。');}
}
