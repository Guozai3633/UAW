import type {Run} from '../../lib/api/types';
import type {Recovery} from '../../lib/cache/drafts';
// Server state and original lookup only. Never interpret model prose as an action or authority.
export function RequestGuidance({run,recovery,activeId,stopping}:{run?:Run;recovery?:Recovery;activeId?:string;stopping:boolean}){
 const currentRecovery=!!recovery&&recovery.conversationId===activeId;
 const waiting=run?.status==='waiting_for_user';
 if(!waiting&&!currentRecovery&&run?.status!=='cancelled')return null;
 return <section className="notice request-guidance" role="status" aria-label="原请求与草稿说明">
 {currentRecovery&&<p>{recovery.runId?'原请求仍未结束或尚待核对，暂不能发送新请求。':'原发送结果尚待对账，未读到原请求 Run 回执前不会重发。'}你仍可编辑并保存草稿。</p>}
 {waiting&&<><p>任务等待处理。请阅读上方的原补充问题或限制；审批和成果接受仅依据实际来源提供操作。</p><p>当前不支持在同一运行内补充信息或继续。如需补充后重新提问，请自行点击“停止”，待读到实际 cancelled（已取消）终态，再将原问题与补充整理为新请求发送。草稿会保留。</p></>}
 {stopping&&<p>已请求停止，正在读取原运行状态；停止回执不代表已取消，请等待实际终态。</p>}
 {run?.status==='cancelled'&&!currentRecovery&&<p>原任务已取消。你可以整理原问题与补充后发送新请求；这不会继续原运行。</p>}
 </section>;
}
