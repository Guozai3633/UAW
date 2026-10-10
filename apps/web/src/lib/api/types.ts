import type { components } from './generated/openapi';
export type Schema = components['schemas'];
export type Conversation = Schema['Conversation'];
export type Item = Schema['InteractionItem'];
export type DisplayItem = Omit<Item,'type'> & {type:string};
export type Event = Schema['EventEnvelope'];
export type Payload = Schema['EventPayload'];
export type Run = Schema['RunRecord'];
export type Frame = Schema['TaskFrame'];
export type Approval = Schema['ApprovalRequest'];
export type Ref = Schema['Ref'];
export type Failure = Schema['Failure'];
export type Result<T> = { kind:'ok'; payload:T; output_refs:Ref[]; revision?:number } |
 {kind:'waiting';wait_ref:Ref;output_refs:Ref[];failure?:Failure} |
 {kind:'missing'|'denied'|'conflict'|'stale'|'failed'|'cancelled';failure:Failure;output_refs:Ref[]};
