import {readFileSync} from 'node:fs';
import {it,expect,vi} from 'vitest';
import {configure,render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {UawClient} from '../../src/lib/api/client';
import {HttpReviewPort} from '../../src/lib/api/a2-adapters';
import {Review} from '../../src/features/review/Review';
import {makeRun,now,ok} from '../fixtures';
import {canonical} from '../../src/lib/api/canonical';
const path=process.env.UAW_REVIEW_WIRE;
if(!path)throw Error('Actual delivery wire path required; this suite was not run');
// Read only the public payload in memory. Do not copy or print its body.
const view=JSON.parse(readFileSync(path,'utf8')).delivery.result.payload;
configure({getElementError:()=>new Error('Actual-wire DOM assertion failed (body redacted)')});
it('actual complete UTF-8 delivery passes default HTTP/Ref/hash checks without rewriting the record',async()=>{
 const transport=vi.fn(async()=>new Response(JSON.stringify(ok(view))));
 const port=new HttpReviewPort(new UawClient(()=>({identityKey:'readonly:actual-wire'}),transport));
 const result=await port.read(view.artifact_ref,view.run_id,new AbortController().signal);
 expect(canonical(result.delivery)===canonical(view)).toBe(true);expect(result.content===view.content).toBe(true);
 expect(result.artifact.media_type).toBe('text/markdown; charset=utf-8');
});
it('actual running/version5 fixed bundle permits receipt; component only requests a fresh Run read',async()=>{
 const transport=vi.fn(async(_url:RequestInfo|URL,options?:RequestInit)=>new Response(JSON.stringify(ok(options?.method==='POST'?{bundle_ref:view.bundle_ref,principal:{id:'readonly-user',kind:'user',auth_session_id:'readonly-session'},decision:'accept',created_at:now}:view))));
 const port=new HttpReviewPort(new UawClient(()=>({identityKey:'readonly:actual-wire'}),transport)),accepted=vi.fn();
 const run={...makeRun('running',5),id:view.run_id};
 try{
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false,gcTime:0}}})}><Review items={[]} run={run} port={port} identity="readonly:actual-wire" connected onAccepted={accepted}/></QueryClientProvider>);
  await waitFor(()=>expect(screen.queryByRole('button',{name:'接受整份成果'})?.hasAttribute('disabled')).toBe(false),{onTimeout:()=>new Error('Actual fixed delivery acceptance remained unavailable (body redacted)')});
  fireEvent.click(screen.getByRole('button',{name:'接受整份成果'}));
  await waitFor(()=>expect(accepted).toHaveBeenCalledOnce(),{onTimeout:()=>new Error('Actual fixed delivery receipt was not recognized (body redacted)')});
  const posts=transport.mock.calls.filter(call=>call[1]?.method==='POST');expect(posts.length).toBe(1);
  const sent=JSON.parse(String(posts[0][1]?.body));expect(canonical(sent.payload.bundle_ref)===canonical(view.bundle_ref)).toBe(true);expect(canonical(sent.payload.artifact_ref)===canonical(view.artifact_ref)).toBe(true);
  expect(sent.meta.expected_revision).toBeUndefined();expect(run.status).toBe('running');expect(run.revision).toBe(5);
  expect(screen.queryByRole('button',{name:'接受整份成果'})?.hasAttribute('disabled')).toBe(true);
 }finally{cleanup();}
});
