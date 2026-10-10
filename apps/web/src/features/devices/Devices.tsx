import {useEffect,useRef,useState} from 'react';
import type {Schema} from '../../lib/api/types';
import type {EnrollmentPort} from './port';
const labels={pending:'等待本人在本机确认',active:'设备登记有效',revoked:'设备登记已撤销',expired:'设备登记已过期'};
export function Devices({port,identity,connected}:{port?:EnrollmentPort;identity:string;connected:boolean}){
 const [id,setId]=useState(''),[record,setRecord]=useState<Schema['RunnerEnrollmentRecord']>(),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[located,setLocated]=useState(false);
 const current=useRef<AbortController|undefined>(undefined);
 useEffect(()=>{setRecord(undefined);setId('');setMessage('');setLocated(false);setBusy(false);current.current?.abort();if(!connected||!port)return;
  const abort=new AbortController();current.current=abort;void port.locate(abort.signal).then(v=>{if(!abort.signal.aborted){setLocated(!!v.candidateId);if(v.enrollmentId)setId(v.enrollmentId);}}).catch(e=>{if(!abort.signal.aborted)setMessage(e.message);});
  return()=>{abort.abort();current.current?.abort();};},[identity,connected,port]);
 async function perform(action:'read'|'begin'|'confirmation'|'revocation'){
  if(!port||!connected||busy)return;setBusy(true);setMessage('');current.current?.abort();const abort=new AbortController();current.current=abort;
  try{const v=action==='read'?await port.read(id,abort.signal):action==='begin'?await port.begin(abort.signal):record?await port.decide(record,action,abort.signal):undefined;
   if(!abort.signal.aborted&&v){setRecord(v);setId(v.id);if(port.uncertain())setMessage('原请求结果未知；只查询同一登记，不换请求ID重发。');}
  }catch(e){if(!abort.signal.aborted){setRecord(undefined);setMessage(e instanceof Error?e.message:'登记不可用');}}finally{if(current.current===abort)setBusy(false);}
 }
 return <section className="device-panel" aria-label="本机设备状态"><h2>本机设备</h2><p>登记与目录权限分别核对。网页不会代替你确认本机窗口。</p>
 {!port&&<p role="status">设备状态来源尚未接入，当前不可用。</p>}
 <label>原设备登记ID<input aria-label="原设备登记ID" value={id} onChange={e=>{setId(e.target.value);setRecord(undefined);}} maxLength={128}/></label>
 <div className="dialog-actions"><button disabled={!port||!connected||!id.trim()||busy} onClick={()=>void perform('read')}>读取原设备登记</button><button disabled={!port||!connected||!located||busy} onClick={()=>void perform('begin')}>请求设备登记</button></div>
 {message&&<p role="status">{message}</p>}
 {record&&<><strong>{labels[record.state]}</strong><p>原登记：{record.id} · 版本 {record.revision}</p><p>原期限：{record.proof_document.expires_at}</p><p>设备登记有效不代表目录授权；目录来源尚无可用HTTP，状态不可用。</p><div className="dialog-actions"><button disabled={!connected||busy||record.state!=='pending'||!!port?.uncertain()} onClick={()=>void perform('confirmation')}>读取本人确认结果</button><button disabled={!connected||busy||!['pending','active'].includes(record.state)||!!port?.uncertain()} onClick={()=>void perform('revocation')}>撤销此登记</button></div></>}
 <p>文件读取仍以当前获准来源和实际运行回执为准。</p></section>;
}
