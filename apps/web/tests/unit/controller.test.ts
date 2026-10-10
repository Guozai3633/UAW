import {beforeEach,it,expect,vi} from 'vitest';
import {WorkspaceController} from '../../src/features/workspace/controller';
import {UawClient} from '../../src/lib/api/client';
import {conversation,models,ok,makeRun,frame,now,ref,approval} from '../fixtures';
import type {Approval,Schema} from '../../src/lib/api/types';
function setup(){let run=makeRun();let hasRun=false;let pending=structuredClone(approval);const posts:RequestInit[]=[];
 const transport=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
  const path=String(input).split('?')[0];let data:unknown;
  if(options?.method==='POST'){posts.push(options);if(path.endsWith('/turns')){hasRun=true;data=run;}
   else if(path.endsWith('/control')){data={operation_id:'control-one',status:'accepted'};}
   else if(path.endsWith('/decisions')){const decision=JSON.parse(String(options.body)).payload.decision;pending={...pending,status:decision.decision==='decline'?'declined':'approved',revision:2};
    data={id:'grant-one',approval_ref:ref('approval',pending.id,'2'),actor:{id:'user-one',kind:'user',auth_session_id:'session-one'},decision,issued_at:now};}
   else data=conversation;
  }else if(path==='/v1/models')data=models;
  else if(path==='/v1/conversations/conv-one')data=conversation;
  else if(path.endsWith('/items'))data={items:[],snapshot_revision:hasRun?1:0};
  else if(path.endsWith('/events'))data={items:hasRun?[{event_id:'event-one',stream_id:'conv-one',seq:1,type:'run.updated',schema_version:'0.1',occurred_at:now,payload_ref:ref('event','event-one')}]:[],snapshot_revision:hasRun?1:0};
  else if(path.endsWith('/payload'))data={action:'run.updated',parameters:run};
  else if(path.endsWith('/frame'))data=frame;
  else if(path.includes('/approvals/'))data=pending;
  else data=run;
  return new Response(JSON.stringify(ok(data)),{status:200});
 });
 const c=new WorkspaceController(new UawClient(()=>({identityKey:'user-one'}),transport),{session:()=>({identityKey:'user-one'})},undefined,60000);
 return{c,transport,posts,setRun:(v:Schema['RunRecord'])=>{run=v;},setApproval:(a:Approval)=>{pending=a;}};
}
beforeEach(()=>localStorage.clear());
it('sends exact original once, refreshes known Run and does not treat cancellation acknowledgement as terminal',async()=>{
 const x=setup();await x.c.start('conv-one');x.c.edit('  保留原文\n  ');await x.c.send();
 expect(x.posts).toHaveLength(1);expect(JSON.parse(String(x.posts[0].body)).payload.text).toBe('  保留原文\n  ');
 expect(x.c.snapshot().run?.status).toBe('running');await x.c.cancel();expect(x.c.snapshot().stopping).toBe(true);expect(x.c.snapshot().run?.status).toBe('running');
 x.setRun(makeRun('cancelled',2));await x.c.reconnect();expect(x.c.snapshot().stopping).toBe(false);expect(x.c.snapshot().run?.status).toBe('cancelled');x.c.stop();
});
it('uncertain dispatch persists lookup only and refresh never resubmits',async()=>{
 const x=setup();await x.c.start('conv-one');x.transport.mockImplementationOnce(async()=>{throw new TypeError('lost');});x.c.edit('task');await x.c.send();
 expect(x.c.snapshot().recovery?.requestId).toBeTruthy();expect(x.c.snapshot().recovery?.runId).toBeUndefined();
 await x.c.reconnect();await x.c.send();expect(x.posts).toHaveLength(0);expect(x.c.snapshot().error).toContain('待对账');x.c.stop();
});
it('decision binds fresh hash/refs/revision, rejects changed approval',async()=>{
 const x=setup();await x.c.start('conv-one');await x.c.decide(approval,'approve_once');expect(x.posts).toHaveLength(1);
 const body=JSON.parse(String(x.posts[0].body));expect(body.meta.expected_revision).toBe(1);expect(body.payload.decision.expected_arguments_hash).toBe(approval.arguments_hash);
 x.setApproval({...approval,revision:2,arguments_hash:'b'.repeat(64)});await x.c.decide(approval,'decline');expect(x.posts).toHaveLength(1);x.c.stop();
});
