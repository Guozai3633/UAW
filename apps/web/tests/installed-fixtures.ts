// Controlled public lifecycle DTO only: no native/OS proof, file reads or real grants.
import type {Schema} from '../src/lib/api/types';
import {now,ref} from './fixtures';
export function installed(state:Schema['InstalledLaunchView']['state']='starting',revision=1,request_id='request-one'):Schema['InstalledLaunchView']{
 return {id:'launch-one',request_id,revision,state,workspace_ref:ref('workspace','workspace-one'),created_at:now,updated_at:now,
 ...(state==='ready'?{enrollment_id:'enrollment-one',device_ref:ref('device','device-one'),expires_at:'2099-01-01T00:00:00Z'}:{})};
}
