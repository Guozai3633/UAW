import type {DisplayItem,Event,Payload,Run,Frame,Approval,Schema} from '../api/types';
export class SnapshotRequired extends Error {}
export class Projection {
 items=new Map<string,DisplayItem>();events=new Map<number,string>();run:Run|undefined;frame:Frame|undefined;
 approvals=new Map<string,Approval>();lastSeq=0;snapshotRevision=0;
 replaceItems(items:DisplayItem[],revision:number){if(revision<this.snapshotRevision)return;
  this.items=new Map();for(const item of items)this.item(item);this.snapshotRevision=revision;}
 item(item:DisplayItem){const previous=this.items.get(item.id);if(!previous||item.revision>previous.revision)this.items.set(item.id,structuredClone(item));}
 apply(event:Event,payload:Payload){
  const seen=this.events.get(event.seq);if(seen){if(seen!==event.event_id)throw new SnapshotRequired('相同seq出现不同事件');return;}
  if(event.seq<=this.lastSeq)return;
  if(event.item_ref){const item=this.items.get(event.item_ref.id);if(item&&item.conversation_id!==event.stream_id)throw new SnapshotRequired('事件与条目会话不一致');}
  if(this.lastSeq && event.seq!==this.lastSeq+1)throw new SnapshotRequired('事件缺序');
  if(event.type!==payload.action)throw new SnapshotRequired('事件正文类型不一致');
  switch(payload.action){
   case 'item.updated':if(payload.parameters.conversation_id!==event.stream_id)throw new SnapshotRequired('条目会话不一致');this.item(payload.parameters);break;
   case 'item.delta':{const patch=payload.parameters,old=this.items.get(patch.item_id);
    if(old && event.result_revision && event.result_revision<=old.revision)break;
    if(!old || old.revision!==patch.base_revision || event.base_revision!==patch.base_revision || !event.result_revision || event.result_revision<=old.revision)throw new SnapshotRequired('条目版本不一致');
    this.item({...old,revision:event.result_revision,updated_at:event.occurred_at,
     text:patch.replacement_text??(old.text+(patch.text_delta??'')),
     ...(patch.status?{status:patch.status}:{}),...(patch.resource_refs?{resource_refs:patch.resource_refs}:{})});break;}
   case 'run.updated':if(!this.run||payload.parameters.id!==this.run.id||payload.parameters.revision>this.run.revision)this.run=structuredClone(payload.parameters);break;
   case 'task.frame.committed':if(!this.frame||payload.parameters.task_id!==this.frame.task_id||payload.parameters.revision>this.frame.revision)this.frame=structuredClone(payload.parameters);break;
   case 'approval.required':this.approvals.set(payload.parameters.id,structuredClone(payload.parameters));break;
   // All other events are retained as structure; never guess success from text.
  }
  this.events.set(event.seq,event.event_id);this.lastSeq=event.seq;
  // Bounded in-memory de-dup; older seq cannot advance current state.
  if(this.events.size>2048)this.events.delete(this.events.keys().next().value!);
 }
 sorted(){return [...this.items.values()].sort((a,b)=>a.created_at.localeCompare(b.created_at));}
 clear(){this.items.clear();this.events.clear();this.approvals.clear();this.run=undefined;this.frame=undefined;this.lastSeq=0;this.snapshotRevision=0;}
}
export const terminal=(status:Schema['RunStatus'])=>['completed','failed','cancelled'].includes(status);
