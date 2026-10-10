// Dispatch lookup IDs only. No receipt, approval, permission or accepted status.
export type DecisionLookup={runId:string;requestId:string;bundleId:string;artifactId:string};
const key='uaw.web.acceptance-lookups.v1';
const id=(v:unknown):v is string=>typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(v);
export class AcceptanceLookups {
 private identity:string|undefined;private entries:DecisionLookup[]=[];
 constructor(private storage:Storage=localStorage){}
 bind(identity:string){if(identity===this.identity)return;this.entries=[];
  try{const raw=this.storage.getItem(key);const saved=raw?JSON.parse(raw):null;
   if(!this.identity&&saved?.identity===identity&&Array.isArray(saved.entries))this.entries=saved.entries.filter((v:DecisionLookup)=>v&&id(v.runId)&&id(v.requestId)&&id(v.bundleId)&&id(v.artifactId)).slice(0,32);
   this.identity=identity;this.write();
  }catch{this.identity=identity;throw new Error('无法安全保存接受查找ID，合同决定暂不可用。');}
 }
 find(runId:string){return this.entries.find(v=>v.runId===runId);}
 mark(value:DecisionLookup){if(this.find(value.runId))throw new Error('接受结果尚未对账，不会换request_id重发。');if(this.entries.length>=32)throw new Error('接受待对账查找已达上限。');this.entries.push({...value});this.write();}
 clear(runId:string){this.entries=this.entries.filter(v=>v.runId!==runId);this.write();}
 private write(){this.storage.setItem(key,JSON.stringify({version:1,identity:this.identity,entries:this.entries}));}
}

export function clearAcceptanceLookups(){try{localStorage.removeItem(key);}catch{/* current view remains blocked on uncertain result */}}
