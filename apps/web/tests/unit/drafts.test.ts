import {describe,it,expect,beforeEach} from 'vitest';
import {DraftStore} from '../../src/lib/cache/drafts';
describe('identity-bound drafts and lookup IDs',()=>{
 beforeEach(()=>localStorage.clear());
 it('restores same identity IDs and draft, no authoritative state',()=>{const s=new DraftStore();s.bind('issuer:user-a:epoch-1');s.remember('conv-one');s.draft('conv-one','  原文  ');s.recovery({requestId:'request-one',conversationId:'conv-one',runId:'run-one'});
  const fresh=new DraftStore();fresh.bind('issuer:user-a:epoch-1');expect(fresh.read().drafts['conv-one']).toBe('  原文  ');expect(fresh.read().recovery?.runId).toBe('run-one');
  const value=localStorage.getItem('uaw.web.local.v1')!;for(const forbidden of ['csrf','token','approval','status','budget','acceptance'])expect(value).not.toContain(forbidden);});
 it('clears on logout/identity or epoch change, never merges foreign data',()=>{const s=new DraftStore();s.bind('user-a');s.draft('conv-one','private');s.bind('user-b');expect(s.read().drafts).toEqual({});
  s.clear();expect(localStorage.length).toBe(0);});
 it('ignores malformed persisted metadata and returns copies',()=>{localStorage.setItem('uaw.web.local.v1','{corrupt');const s=new DraftStore();s.bind('user');s.remember('conv-one');
  const copy=s.read();copy.conversationIds.push('foreign');expect(s.read().conversationIds).toEqual(['conv-one']);});
});
