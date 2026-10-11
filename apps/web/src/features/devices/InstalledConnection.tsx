import {useEffect,useRef,useState} from 'react';
import {terminalLaunch,type InstalledLaunchPort,type InstalledView,type LaunchLookup} from './installed';
const labels={starting:'本机连接已登记',waiting_device:'等待本人确认账号',connecting:'正在连接本机',selecting_directory:'等待本人选择并确认只读目录',ready:'本机当前连接就绪',closed:'本机连接已关闭',failed:'本机连接失败',unavailable:'本机连接当前不可用'};
export function InstalledConnection({port,identity,connected,pollMs=2000,pollLimit=120}:{port?:InstalledLaunchPort;identity:string;connected:boolean;pollMs?:number;pollLimit?:number}){
 const [view,setView]=useState<InstalledView>(),[lookup,setLookup]=useState<LaunchLookup>(),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 const current=useRef<AbortController|undefined>(undefined),timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined),locked=useRef(false),rounds=useRef(0),alive=useRef(false);
 const cancel=()=>{current.current?.abort();clearTimeout(timer.current);};
 function schedule(v:InstalledView){clearTimeout(timer.current);if(!alive.current||terminalLaunch(v))return;
  if(rounds.current>=pollLimit){setMessage('自动读取已达本次上限，请手动读取原连接；期限不会延长。');return;}
  timer.current=setTimeout(()=>void perform('read',v.id),pollMs);
 }
 async function perform(action:'read'|'start'|'recover'|'stop',id?:string){if(!port||!connected||!alive.current||locked.current)return;
  locked.current=true;setBusy(true);setMessage('');cancel();const abort=new AbortController();current.current=abort;
  try{const saved=port.lookup();const original=id??saved?.launchId;
   const v=action==='start'?await port.start(abort.signal):action==='recover'?await port.start(abort.signal,true):action==='stop'&&view?await port.stop(view,abort.signal):original?await port.get(original,abort.signal):undefined;
   if(abort.signal.aborted||!alive.current)return;
   setLookup(port.lookup());if(v){setView(v);rounds.current++;schedule(v);}else setMessage('原启动回复未知且没有实例ID；只能由你显式恢复原请求，刷新不会重发。');
  }catch(e){if(!abort.signal.aborted&&alive.current){setView(undefined);setMessage(e instanceof Error?e.message:'本机来源不可用');try{setLookup(port.lookup());}catch{setLookup(undefined);}}}
  finally{if(current.current===abort){locked.current=false;if(alive.current)setBusy(false);}}
 }
 useEffect(()=>{alive.current=true;cancel();locked.current=false;rounds.current=0;setBusy(false);setView(undefined);setLookup(undefined);setMessage('');
  if(connected&&port){try{const saved=port.lookup();setLookup(saved);if(saved?.launchId)void perform('read',saved.launchId);else if(saved)setMessage('原启动回复未知且没有实例ID；只能由你显式恢复原请求，刷新不会重发。');}catch(e){setMessage(e instanceof Error?e.message:'本机来源不可用');}}
  const hide=()=>{alive.current=false;cancel();};window.addEventListener('pagehide',hide);
  return()=>{alive.current=false;cancel();window.removeEventListener('pagehide',hide);};
 },[port,identity,connected]);
 const noId=!!lookup&&!lookup.launchId;
 return <section className="installed-panel" aria-label="连接本机只读目录"><h2>连接本机只读目录</h2><p>点击后，请在系统窗口完成三步：</p><ol><li>确认当前账号和本机设备。</li><li>选择你愿意开放的目录。</li><li>确认本次只读范围。</li></ol>
 <p>网页不会代替你点确认。启动已登记不表示授权；连接就绪也不表示文件工具已获执行许可。</p>
 {!port&&<p role="status">本机生命周期来源未接入，当前不可用。</p>}
 {view&&<><strong>{labels[view.state]}</strong><p>实际状态：{view.state} · 原版本 {view.revision}</p><p>原连接：{view.id}</p>{view.expires_at&&<p>原期限：{view.expires_at}</p>}{view.failure_code&&<p>原失败码：{view.failure_code}</p>}{view.state==='ready'&&<p>每次文件工具、任务、审批与预算仍需独立复查。</p>}</>}
 {message&&<p role="status">{message}</p>}{lookup?.stop&&<p role="status">原停止结果待对账；只读取原连接，不会重发停止。</p>}
 <div className="dialog-actions"><button disabled={!connected||!port||busy||noId||!!lookup?.launchId&&(!view||!terminalLaunch(view))} onClick={()=>void perform('start')}>连接本机只读目录</button>
 {noId&&<button disabled={!connected||!port||busy} onClick={()=>void perform('recover')}>恢复原连接请求</button>}
 {lookup?.launchId&&<button disabled={!connected||!port||busy} onClick={()=>{rounds.current=0;void perform('read');}}>读取原本机连接</button>}
 <button disabled={!connected||!port||busy||!view||terminalLaunch(view)||!!lookup?.stop} onClick={()=>void perform('stop')}>停止本机连接</button></div></section>;
}
