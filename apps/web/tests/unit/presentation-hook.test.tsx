import {afterEach,it,expect,vi} from 'vitest';
import {renderHook,act} from '@testing-library/react';
import {usePresentation} from '../../src/features/presentation/usePresentation';
import {ContinuationStore} from '../../src/features/conversation/store';
import {presentationView} from '../presentation-fixtures';
import {conversationView} from '../conversation-fixtures';
afterEach(()=>{vi.useRealTimers();localStorage.clear();});
it('automatic reconciliation shares the120-read bound; only explicit manual refresh opens a new read window',async()=>{
 vi.useFakeTimers();const p=presentationView(),port={read:vi.fn(async()=>structuredClone(p))},conversation={read:vi.fn(async()=>({...conversationView(false),run:p.run})),lookup:vi.fn(),question:vi.fn(),submit:vi.fn()},store=new ContinuationStore();const h=renderHook(()=>usePresentation(port,conversation,store,'owner',p.run,true));await act(async()=>{await vi.advanceTimersByTimeAsync(360001);});expect(port.read).toHaveBeenCalledTimes(120);await act(async()=>{for(let n=0;n<5;n++)h.result.current.reconcile();await Promise.resolve();});expect(port.read).toHaveBeenCalledTimes(120);await act(async()=>{h.result.current.refresh();await Promise.resolve();});expect(port.read).toHaveBeenCalledTimes(121);expect(h.result.current.source?.presentation.run).toEqual(p.run);h.unmount();
});
it('automatic reconciliation does not replace an in-flight read or publish after unmount',async()=>{
 const p=presentationView();let release!:(v:typeof p)=>void;const port={read:vi.fn(()=>new Promise<typeof p>(r=>{release=r;}))},conversation={read:vi.fn(async()=>({...conversationView(false),run:p.run})),lookup:vi.fn(),question:vi.fn(),submit:vi.fn()},store=new ContinuationStore(),h=renderHook(()=>usePresentation(port,conversation,store,'owner',p.run,true));act(()=>{h.result.current.reconcile();h.result.current.reconcile();});expect(port.read).toHaveBeenCalledOnce();h.unmount();await act(async()=>{release(p);await Promise.resolve();});expect(conversation.read).not.toHaveBeenCalled();
});
