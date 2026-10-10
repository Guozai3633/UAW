import {validate} from './validation';
import type {Schema, Result,DisplayItem} from './types';
export class TransportError extends Error { constructor(readonly uncertain:boolean) {super(uncertain?'请求结果未知，先查询原运行；不会自动重发。':'连接中断，请重新读取。');} }
export class ApiFailure extends Error { constructor(readonly result:Exclude<Result<never>,{kind:'ok'}>) {super(result.failure?.message ?? '等待服务端确认');} }
export type WebSession = {identityKey:string; principal?:Schema['Principal'];csrfHeader?:{name:string;value:string}}; // supplied by A's authenticated host, memory only
export class UawClient {
 constructor(private session:()=>WebSession|null, private transport:typeof fetch=(input,init)=>fetch(input,init)) {}
 currentSession(){return this.session();}
 async call<T>(method:'GET'|'POST'|'DELETE',path:string,schema:string,query:Record<string,string|number|undefined>={},payload?:unknown,meta?:Schema['RequestMeta'],signal?:AbortSignal):Promise<T> {
  const qs=new URLSearchParams();for(const[k,v]of Object.entries(query))if(v!==undefined)qs.set(k,String(v));
  const url=path+(qs.size?'?'+qs:''); const headers:Record<string,string>={Accept:'application/json'};
  if(method!=='GET'){headers['Content-Type']='application/json';const csrf=this.session()?.csrfHeader;if(csrf){if(['authorization','cookie','origin','content-type','accept'].includes(csrf.name.toLowerCase()))throw new Error('身份host不能替代HTTP认证协议');headers[csrf.name]=csrf.value;}}
  let response:Response;
  try{response=await this.transport(url,{method,headers,credentials:'same-origin',cache:'no-store',signal:signal?AbortSignal.any([signal,AbortSignal.timeout(15000)]):AbortSignal.timeout(15000),
    ...(method!=='GET'?{body:JSON.stringify({meta,payload})}:{})});}
  catch(error){if(signal?.aborted)throw error;throw new TransportError(method!=='GET');}
  let wire:unknown;try{wire=await response.json();}catch{throw new TransportError(method!=='GET');}
  // Even HTTP202 may contain ok; only the validated kind decides.
  try{validate(schema,wire);}catch{throw new TransportError(method!=='GET');}
  const result=wire as Result<T>;if(result.kind!=='ok')throw new ApiFailure(result);
  if(!response.ok)throw new TransportError(method!=='GET');return result.payload;
 }
 webSession(signal?:AbortSignal){return this.call<Schema['WebSession']>('GET','/v1/web/session','HttpWebSessionGetResult',{},undefined,undefined,signal);}
 exchange(launch_code:string,meta:Schema['RequestMeta'],signal?:AbortSignal){const payload={launch_code};validate('WebSessionExchangeRequest',payload);return this.call<Schema['WebSession']>('POST','/v1/web/session','HttpWebSessionExchangeResult',{},payload,meta,signal);}
 logout(meta:Schema['RequestMeta'],signal?:AbortSignal){return this.call<Schema['Acknowledgement']>('DELETE','/v1/web/session','HttpWebSessionLogoutResult',{}, {},meta,signal);}
 conversations(cursor?:string,signal?:AbortSignal){return this.call<Schema['ConversationPage']>('GET','/v1/conversations','HttpConversationsListResult',{limit:100,cursor},undefined,undefined,signal);}
 lookup(conversationId:string,requestId:string,signal?:AbortSignal){return this.call<Schema['RunRecord']>('GET',`/v1/conversations/${encodeURIComponent(conversationId)}/turn-requests/${encodeURIComponent(requestId)}`,'HttpTurnsLookupResult',{},undefined,undefined,signal);}
 delivery(runId:string,signal?:AbortSignal){return this.call<Schema['RunDeliveryView']>('GET',`/v1/runs/${encodeURIComponent(runId)}/delivery`,'HttpRunsDeliveryResult',{},undefined,undefined,signal);}
 artifact(id:string,version?:string,signal?:AbortSignal){return this.call<Schema['ArtifactRecord']>('GET',`/v1/artifacts/${encodeURIComponent(id)}`,'HttpArtifactsGetResult',{version},undefined,undefined,signal);}
 content(id:string,version:string,content_hash:string,signal?:AbortSignal){return this.call<Schema['ArtifactContentView']>('GET',`/v1/artifacts/${encodeURIComponent(id)}/content`,'HttpArtifactsContentResult',{version,content_hash},undefined,undefined,signal);}
 acceptDelivery(runId:string,payload:Omit<Schema['RunsDeliveryAcceptRequest'],'run_id'>,meta:Schema['RequestMeta'],signal?:AbortSignal){validate('RunsDeliveryAcceptRequest',{...payload,run_id:runId});return this.call<Schema['CompletionAcceptance']>('POST',`/v1/runs/${encodeURIComponent(runId)}/delivery/acceptance`,'HttpRunsDeliveryAcceptResult',{},payload,meta,signal);}
 models(signal?:AbortSignal){return this.call<Schema['ModelPage']>('GET','/v1/models','HttpModelsListResult',{},undefined,undefined,signal);}
 conversation(id:string,signal?:AbortSignal){return this.call<Schema['Conversation']>('GET',`/v1/conversations/${encodeURIComponent(id)}`,'HttpConversationsGetResult',{},undefined,undefined,signal);}
 create(payload:Schema['ConversationsCreateRequest'],meta:Schema['RequestMeta'],signal?:AbortSignal){validate('ConversationsCreateRequest',payload);return this.call<Schema['Conversation']>('POST','/v1/conversations','HttpConversationsCreateResult',{},payload,meta,signal);}
 items(id:string,cursor?:string,signal?:AbortSignal){return this.call<Omit<Schema['ItemPage'],'items'>&{items:DisplayItem[]}>('GET',`/v1/conversations/${encodeURIComponent(id)}/items`,'HttpConversationsItemsResult',{limit:100,cursor},undefined,undefined,signal);}
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
