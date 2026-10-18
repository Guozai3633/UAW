import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import type {Run} from '../../lib/api/types';
import type {ConversationPort} from '../conversation/port';
import type {ContinuationStore} from '../conversation/store';
import {PresentationSession,type PresentationPort,type PresentationSource} from './port';
export type CoordinatedPresentation={source?:PresentationSource;updating:boolean;current:boolean;error:string;refresh:()=>void;reconcile:()=>void};
export function usePresentation(port:PresentationPort|undefined,conversation:ConversationPort|undefined,store:ContinuationStore,identity:string,run:Run|undefined,connected:boolean):CoordinatedPresentation{
 const session=useMemo(()=>port&&conversation?new PresentationSession(port,conversation,store):undefined,[port,conversation,store]);
 const key=JSON.stringify([identity,run?.conversation_id,run?.id]);const [state,setState]=useState<{key:string;source?:PresentationSource;updating:boolean;current:boolean;error:string}>({key,updating:false,current:false,error:''});
 const abort=useRef<AbortController|undefined>(undefined),timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined),reads=useRef(0),active=useRef(false),inflight=useRef(false);
 const refresh=useCallback(async()=>{if(!active.current||!session||!run||!connected)return;abort.current?.abort();clearTimeout(timer.current);const current=new AbortController();abort.current=current;inflight.current=true;
  setState(old=>({...old,key,source:old.key===key?old.source:undefined,updating:true,current:old.key===key&&old.current,error:''}));
  try{const source=await session.read(identity,run,current.signal);if(!current.signal.aborted&&active.current)setState({key,source,updating:false,current:source.presentation.phase!=='unavailable',error:source.presentation.phase==='unavailable'?'当前任务来源不可核对。':''});}
  catch(e){if(!current.signal.aborted&&active.current)setState(old=>({...old,updating:false,current:false,error:e instanceof Error?e.message:'任务展示来源不可用。'}));}
  finally{if(abort.current===current)inflight.current=false;if(abort.current===current&&active.current&&!current.signal.aborted){reads.current++;if(reads.current<120)timer.current=setTimeout(()=>void refresh(),3000);else setState(old=>({...old,error:'本次展示自动读取已达上限，请手动读取。'}));}}
 },[session,identity,run?.id,run?.conversation_id,run?.revision,run?.status,connected,key]);
 useEffect(()=>{active.current=true;reads.current=0;if(connected&&run)void refresh();return()=>{active.current=false;abort.current?.abort();session?.invalidate();inflight.current=false;clearTimeout(timer.current);};},[refresh]);
 const same=state.key===key;return{source:same?state.source:undefined,updating:same&&state.updating,current:!!(same&&state.current&&connected&&run&&state.source&&state.source.presentation.run.revision>=run.revision),error:same?state.error:'',refresh:()=>{reads.current=0;void refresh();},reconcile:()=>{if(reads.current<120&&!inflight.current)void refresh();}};
}
