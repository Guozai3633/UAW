import {validate} from './validation';
import type {Schema, Result} from './types';
export class TransportError extends Error { constructor(readonly uncertain:boolean) {super(uncertain?'请求结果未知，先查询原运行；不会自动重发。':'连接中断，请重新读取。');} }
export class ApiFailure extends Error { constructor(readonly result:Exclude<Result<never>,{kind:'ok'}>) {super(result.failure?.message ?? '等待服务端确认');} }
export type WebSession = {identityKey:string; csrfHeader?:{name:string;value:string}}; // supplied by A's authenticated host, memory only
export class UawClient {
 constructor(private session:()=>WebSession|null, private transport:typeof fetch=fetch) {}
 async call<T>(method:'GET'|'POST',path:string,schema:string,query:Record<string,string|number|undefined>={},payload?:unknown,meta?:Schema['RequestMeta'],signal?:AbortSignal):Promise<T> {
  const qs=new URLSearchParams();for(const[k,v]of Object.entries(query))if(v!==undefined)qs.set(k,String(v));
  const url=path+(qs.size?'?'+qs:''); const headers:Record<string,string>={Accept:'application/json'};
  if(method==='POST'){headers['Content-Type']='application/json';const csrf=this.session()?.csrfHeader;if(csrf)headers[csrf.name]=csrf.value;}
  let response:Response;
  try{response=await this.transport(url,{method,headers,credentials:'same-origin',cache:'no-store',signal,
    ...(method==='POST'?{body:JSON.stringify({meta,payload})}:{})});}
  catch(error){if(signal?.aborted)throw error;throw new TransportError(method==='POST');}
  let wire:unknown;try{wire=await response.json();}catch{throw new TransportError(method==='POST');}
  // Even HTTP202 may contain ok; only the validated kind decides.
  try{validate(schema,wire);}catch{throw new TransportError(method==='POST');}
  const result=wire as Result<T>;if(result.kind!=='ok')throw new ApiFailure(result);
  if(!response.ok)throw new TransportError(method==='POST');return result.payload;
 }
 models(signal?:AbortSignal){return this.call<Schema['ModelPage']>('GET','/v1/models','HttpModelsListResult',{},undefined,undefined,signal);}
 conversation(id:string,signal?:AbortSignal){return this.call<Schema['Conversation']>('GET',`/v1/conversations/${encodeURIComponent(id)}`,'HttpConversationsGetResult',{},undefined,undefined,signal);}
 create(payload:Schema['ConversationsCreateRequest'],meta:Schema['RequestMeta'],signal?:AbortSignal){validate('ConversationsCreateRequest',payload);return this.call<Schema['Conversation']>('POST','/v1/conversations','HttpConversationsCreateResult',{},payload,meta,signal);}
 items(id:string,cursor?:string,signal?:AbortSignal){return this.call<Schema['ItemPage']>('GET',`/v1/conversations/${encodeURIComponent(id)}/items`,'HttpConversationsItemsResult',{limit:100,cursor},undefined,undefined,signal);}
 events(id:string,cursor?:string,signal?:AbortSignal){return this.call<Schema['EventPage']>('GET',`/v1/conversations/${encodeURIComponent(id)}/events`,'HttpEventsReadResult',{limit:100,cursor},undefined,undefined,signal);}
 payload(id:string,signal?:AbortSignal){return this.call<Schema['EventPayload']>('GET',`/v1/events/${encodeURIComponent(id)}/payload`,'HttpEventsPayloadResult',{},undefined,undefined,signal);}
 submit(id:string,payload:Omit<Schema['TurnsSubmitRequest'],'conversation_id'>,meta:Schema['RequestMeta'],signal?:AbortSignal){validate('TurnsSubmitRequest',{...payload,conversation_id:id});return this.call<Schema['RunRecord']>('POST',`/v1/conversations/${encodeURIComponent(id)}/turns`,'HttpTurnsSubmitResult',{},payload,meta,signal);}
 run(id:string,signal?:AbortSignal){return this.call<Schema['RunRecord']>('GET',`/v1/runs/${encodeURIComponent(id)}`,'HttpRunsGetResult',{},undefined,undefined,signal);}
 frame(id:string,signal?:AbortSignal){return this.call<Schema['TaskFrame']>('GET',`/v1/tasks/${encodeURIComponent(id)}/frame`,'HttpTasksFrameResult',{},undefined,undefined,signal);}
 approval(id:string,signal?:AbortSignal){return this.call<Schema['ApprovalRequest']>('GET',`/v1/approvals/${encodeURIComponent(id)}`,'HttpApprovalsGetResult',{},undefined,undefined,signal);}
 decide(id:string,decision:Schema['ApprovalDecision'],meta:Schema['RequestMeta'],signal?:AbortSignal){validate('ApprovalsDecideRequest',{approval_id:id,decision});return this.call<Schema['ApprovalGrant']>('POST',`/v1/approvals/${encodeURIComponent(id)}/decisions`,'HttpApprovalsDecideResult',{}, {decision},meta,signal);}
 control(id:string,control:Schema['UserControl'],meta:Schema['RequestMeta'],signal?:AbortSignal){validate('RunsControlRequest',{run_id:id,control});return this.call<Schema['Acknowledgement']>('POST',`/v1/runs/${encodeURIComponent(id)}/control`,'HttpRunsControlResult',{}, {control},meta,signal);}
}
export const requestMeta=(expected_revision?:number):Schema['RequestMeta']=>({request_id:crypto.randomUUID(),schema_version:'0.1',...(expected_revision!==undefined?{expected_revision}:{})});
