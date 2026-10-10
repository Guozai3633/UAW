// Controlled public DTO; not actual OS, keys, native confirmation or permission.
import type {Schema} from '../src/lib/api/types';
import {now,ref} from './fixtures';
export function enrollment(state:Schema['RunnerEnrollmentRecord']['state']='pending',revision=1):Schema['RunnerEnrollmentRecord']{
 const peer=(role:'control'|'device')=>({role,identity:{pid:role==='control'?10:20,created:'12345',user_sid:'sid-test',logon_sid:'logon-test'},actor:{id:role+'-actor',kind:'runner' as const,auth_session_id:'session-peer'},key_id:role+'-key',key_ref:ref('content',role+'-key'),public_key:'A'.repeat(43)+'='});
 return{id:'enrollment-one',revision,state,created_at:now,proof_document:{protocol:'uaw-enrollment-v1',enrollment_id:'enrollment-one',candidate_ref:ref('content','candidate-one'),owner:{id:'user-one',kind:'user',auth_session_id:'session-one'},device_id:'device-one',control:peer('control'),device:peer('device'),nonce:'n'.repeat(32),expires_at:now}};
}
