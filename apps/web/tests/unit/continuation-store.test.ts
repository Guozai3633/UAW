import {beforeEach,it,expect} from 'vitest';
import {ContinuationStore,type PendingContinuation} from '../../src/features/conversation/store';
import {continuationReceipt} from '../conversation-fixtures';
beforeEach(()=>localStorage.clear());const scope={conversationId:'conv-one',runId:'run-one'},pending:PendingContinuation={requestId:'request-one',kind:'correction',runRevision:4,inputRevision:1};
it('drafts and lookup IDs bind full identity/conversation/Run; clear removes them without cached authority',()=>{
 let s=new ContinuationStore();s.bind('user-one:session-one');s.draft(scope,'correction','  原文\n  ');s.mark(scope,pending);s=new ContinuationStore();s.bind('user-one:session-one');expect(s.draft(scope,'correction')).toBe('  原文\n  ');expect(s.pending(scope)).toEqual([pending]);expect(s.pending({...scope,runId:'run-two'})).toEqual([]);expect(s.draft({...scope,conversationId:'conv-two'},'correction')).toBe('');s.bind('user-one:session-two');expect(s.draft(scope,'correction')).toBe('');expect(s.pending(scope)).toEqual([]);s.clear();expect(localStorage.length).toBe(0);
});
it('per-request keys preserve two tab CAS contenders and resolve only the exact original receipt',()=>{
 const a=new ContinuationStore(),b=new ContinuationStore();a.bind('one');b.bind('one');a.mark(scope,pending);b.mark(scope,{...pending,requestId:'request-two'});expect(a.pending(scope).map(p=>p.requestId).sort()).toEqual(['request-one','request-two']);a.resolve(scope,continuationReceipt('request-one','correction'));expect(b.pending(scope).map(p=>p.requestId)).toEqual(['request-two']);const bad=continuationReceipt('request-two','clarification_answer');expect(()=>b.resolve(scope,bad)).toThrow('原补充版本');expect(b.pending(scope)).toHaveLength(1);
 for(const forbidden of ['accepted','applied','csrf','proof','permission','model_choice','clock_ref'])expect(JSON.stringify(localStorage)).not.toContain(forbidden);
});
it('pending persistence failure blocks dispatch and malformed original metadata does not become an empty successful recovery',()=>{
 const blocked={getItem:()=>null,setItem:()=>{throw Error('blocked');},removeItem:()=>{},clear:()=>{},length:0,key:()=>null} satisfies Storage;const s=new ContinuationStore(blocked);s.bind('one');expect(()=>s.mark(scope,pending)).toThrow('没有发送');const actual=new ContinuationStore();actual.bind('one');localStorage.setItem('uaw.web.continuation.pending.v1.request-one',JSON.stringify({identity:'one',scope,pending:{...pending,inputRevision:0}}));expect(()=>actual.pending(scope)).toThrow('损坏');
});

it('corrupt scope, unexpected answer metadata and colliding request IDs block a new submission without deleting the original',()=>{
 const s=new ContinuationStore();s.bind('one');s.mark(scope,pending);expect(()=>s.mark({...scope,runId:'run-two'},pending)).toThrow('没有发送');expect(s.pending(scope)).toEqual([pending]);expect(()=>s.mark(scope,{...pending,requestId:'bad-one',questionId:'not-for-correction'})).toThrow('没有发送');localStorage.setItem('uaw.web.continuation.pending.v1.bad',JSON.stringify({identity:'one',scope:{conversationId:'conv-one'},pending}));expect(()=>s.pending(scope)).toThrow('损坏');expect(localStorage.getItem('uaw.web.continuation.pending.v1.request-one')).not.toBeNull();
});
