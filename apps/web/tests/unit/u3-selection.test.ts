import {beforeEach,it,expect,vi} from 'vitest';
import {WorkspaceController} from '../../src/features/workspace/controller';
import {DraftStore} from '../../src/lib/cache/drafts';
import {UawClient} from '../../src/lib/api/client';
import {conversation,models,makeRun,frame,ok,denied} from '../fixtures';
beforeEach(()=>localStorage.clear());
function setup(){let identity='user-one',hidden=false;const conversations=[{...conversation,id:'conv-new',title:'最新会话'},conversation];
 const session=()=>({identityKey:identity,principal:{id:identity,kind:'user' as const,auth_session_id:'session-one'}});
 const transport=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{if(init?.method!=='GET')throw Error('Refresh must be read-only');const path=String(input).split('?')[0];
  if(hidden&&path==='/v1/conversations/conv-one')return new Response(JSON.stringify(denied()),{status:403});
  const payload=path==='/v1/models'?models:path==='/v1/conversations'?{items:conversations.map(c=>({...c,owner_id:identity})),snapshot_revision:1}:path.endsWith('/items')||path.endsWith('/events')?{items:[],snapshot_revision:1}:path.endsWith('/frame')?frame:path.includes('/runs/')?makeRun():{...conversations.find(c=>path.endsWith('/'+c.id))!,owner_id:identity};
  return new Response(JSON.stringify(ok(payload)));
 });
 const drafts=new DraftStore();drafts.bind(identity);const controller=new WorkspaceController(new UawClient(session,transport),{session},drafts,60000);
 return {controller,drafts,transport,identity:(v:string)=>{identity=v;},hide:()=>{hidden=true;}};
}
it('explicit URL overrides newest and old recovery, refresh restores selected draft without POST',async()=>{
 const x=setup();x.drafts.select('conv-new');x.drafts.recovery({conversationId:'conv-one',requestId:'request-original',runId:'run-one'});x.drafts.draft('conv-new','  当前原文\n  ');
 try{await x.controller.start('conv-new');expect(x.controller.snapshot().active?.id).toBe('conv-new');expect(x.controller.snapshot().draft).toBe('  当前原文\n  ');expect(x.controller.snapshot().recovery?.conversationId).toBe('conv-one');
 await x.controller.start();expect(x.controller.snapshot().active?.id).toBe('conv-new');expect(x.transport.mock.calls.every(c=>c[1]?.method==='GET')).toBe(true);}finally{x.controller.stop();}
});
it('same identity selected conversation outranks newest, invisible URL never falls back',async()=>{
 const x=setup();x.drafts.select('conv-one');try{await x.controller.start();expect(x.controller.snapshot().active?.id).toBe('conv-one');await x.controller.start('conv-hidden');expect(x.controller.snapshot().active).toBeUndefined();expect(x.controller.snapshot().items).toEqual([]);expect(x.controller.snapshot().connected).toBe(false);expect(x.controller.snapshot().error).toContain('可见列表');}finally{x.controller.stop();}
});
it('current ownership, identity switch and revoked reads cannot retain another identity draft or details',async()=>{
 const x=setup();x.drafts.draft('conv-one','private');try{await x.controller.start('conv-one');x.identity('user-two');await x.controller.start('conv-one');expect(x.controller.snapshot().draft).toBe('');expect(x.controller.snapshot().active?.owner_id).toBe('user-two');x.hide();await x.controller.reconnect();expect(x.controller.snapshot().active).toBeUndefined();expect(x.controller.snapshot().run).toBeUndefined();expect(x.controller.snapshot().items).toEqual([]);}finally{x.controller.stop();}
});
