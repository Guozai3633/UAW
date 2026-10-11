import {ApiFailure,UawClient,requestMeta} from '../../lib/api/client';
import type {Schema} from '../../lib/api/types';
export type InstalledView=Schema['InstalledLaunchView'];
// IDs/CAS only. Never retain ready, grant, proof, token, path, keys or execution rights.
export type LaunchLookup={requestId:string;launchId?:string;revision?:number;stop?:{requestId:string;revision:number}};
export interface InstalledLaunchPort {
 lookup():LaunchLookup|undefined;
 start(signal:AbortSignal,recoverOriginal?:boolean):Promise<InstalledView>;
 get(id:string,signal:AbortSignal):Promise<InstalledView>;
 stop(old:InstalledView,signal:AbortSignal):Promise<InstalledView>;
 clear():void;
}
const key='uaw.web.local-launch.v1',validId=(v:unknown):v is string=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(v);
const revision=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0;
export const terminalLaunch=(v:InstalledView)=>['closed','failed','unavailable'].includes(v.state);
export class HttpInstalledLaunchPort implements InstalledLaunchPort {
 private identity:string|undefined;private value:LaunchLookup|undefined;private writing=false;private generation=0;
 constructor(private client:UawClient,private storage:Storage=localStorage){}
 private bind(){const session=this.client.currentSession();if(!session?.identityKey||session.principal?.kind!=='user')throw Error('当前浏览器用户不可用。');
  if(session.identityKey!==this.identity){let saved:unknown;try{saved=JSON.parse(this.storage.getItem(key)??'null');}catch{/* corrupt metadata */}
   const data=saved as {identity?:string;lookup?:LaunchLookup}|null,v=this.identity===undefined&&data?.identity===session.identityKey?data.lookup:undefined;
   this.value=v&&validId(v.requestId)&&(!v.launchId||validId(v.launchId))&&(v.revision===undefined||revision(v.revision))?{requestId:v.requestId,...(v.launchId?{launchId:v.launchId,revision:v.revision}:{}),...(v.launchId&&v.stop&&validId(v.stop.requestId)&&revision(v.stop.revision)?{stop:{requestId:v.stop.requestId,revision:v.stop.revision}}:{})}:undefined;
   this.identity=session.identityKey;this.generation++;this.writing=false;this.save();
  }return this.identity;
 }
 private save(){try{if(this.value)this.storage.setItem(key,JSON.stringify({identity:this.identity,lookup:this.value}));else this.storage.removeItem(key);}catch{throw Error('无法保存原本机请求ID，写入不可用。');}}
 private guard(identity:string,g:number,signal:AbortSignal){signal.throwIfAborted();if(identity!==this.client.currentSession()?.identityKey||g!==this.generation)throw Error('本机读取期间身份已变化。');}
 private check(v:InstalledView,id?:string,requestId?:string){if(id&&v.id!==id||requestId&&v.request_id!==requestId||v.workspace_ref.kind!=='workspace')throw Error('本机状态与原请求/工作区不匹配。');}
 lookup(){this.bind();return this.value?structuredClone(this.value):undefined;}
 clear(){this.value=undefined;this.identity=undefined;this.generation++;this.writing=false;try{this.storage.removeItem(key);}catch{/* local lookup is cleared */}}
 async get(id:string,signal:AbortSignal){const identity=this.bind(),g=this.generation;const lookup=this.value;
  if(lookup?.launchId&&lookup.launchId!==id)throw Error('只能读取原本机实例。');
  const view=await this.client.localGet(id,signal);this.guard(identity,g,signal);const latest=this.value??lookup;this.check(view,id,latest?.requestId);
  if(latest?.launchId&&latest.launchId!==id)throw Error('只能读取当前原实例。');
  if(latest?.revision!==undefined&&view.revision<latest.revision)throw Error('本机状态版本回退。');
  const stop=latest?.stop;this.value={requestId:view.request_id,launchId:view.id,revision:view.revision,...(stop&&!terminalLaunch(view)?{stop}:{})};this.save();return view;
 }
 async start(signal:AbortSignal,recoverOriginal=false){const identity=this.bind(),g=this.generation;if(this.writing)throw Error('原本机操作仍在进行。');this.writing=true;
  try{let original=this.value;
   if(recoverOriginal){if(!original||original.launchId)throw Error('已有实例先GET；没有原请求不能恢复。');}
   else if(original){if(!original.launchId)throw Error('启动结果未知；只能显式恢复原请求ID。');const current=await this.get(original.launchId,signal);this.guard(identity,g,signal);if(!terminalLaunch(current))throw Error('原本机实例仍在运行，请先停止。');original=undefined;}
   const meta=original?{request_id:original.requestId,schema_version:'0.1' as const}:requestMeta();
   this.value={requestId:meta.request_id};this.save();this.guard(identity,g,signal);
   try{const view=await this.client.localStart(meta,signal);this.guard(identity,g,signal);this.check(view,undefined,meta.request_id);this.value={requestId:view.request_id,launchId:view.id,revision:view.revision};this.save();return view;}
   catch(e){if(e instanceof ApiFailure&&e.result.kind!=='waiting'&&identity===this.client.currentSession()?.identityKey&&g===this.generation){this.value=undefined;this.save();}throw e;}
  }finally{if(g===this.generation)this.writing=false;}
 }
 async stop(old:InstalledView,signal:AbortSignal){const identity=this.bind(),g=this.generation;if(this.writing)throw Error('原本机操作仍在进行。');this.writing=true;
  try{const pending=this.value?.stop,current=await this.get(old.id,signal);this.guard(identity,g,signal);if(terminalLaunch(current))return current;
   if(pending)throw Error('停止结果未知；先GET原实例，不会重发。');
   if(current.revision!==old.revision||current.request_id!==old.request_id)throw Error('本机版本已变化，请重新读取。');
   const meta=requestMeta(current.revision);this.value={requestId:current.request_id,launchId:current.id,revision:current.revision,stop:{requestId:meta.request_id,revision:current.revision}};this.save();this.guard(identity,g,signal);
   try{const result=await this.client.localStop(current.id,meta,signal);this.guard(identity,g,signal);this.check(result,current.id,current.request_id);if(result.revision<current.revision)throw Error('停止回执版本回退。');this.value={requestId:result.request_id,launchId:result.id,revision:result.revision,...(!terminalLaunch(result)?{stop:{requestId:meta.request_id,revision:current.revision}}:{})};this.save();return result;}
   catch(e){if(e instanceof ApiFailure&&e.result.kind!=='waiting'&&identity===this.client.currentSession()?.identityKey&&g===this.generation){if(this.value)delete this.value.stop;this.save();}throw e;}
  }finally{if(g===this.generation)this.writing=false;}
 }
}
