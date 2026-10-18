import {render,screen,cleanup} from '@testing-library/react';
import {expect,it} from 'vitest';
import {TaskUnderstanding} from '../../src/features/workspace/TaskUnderstanding';
import {makeRun,now} from '../fixtures';
it('stopping without a completed model decision does not promise a future understanding',()=>{
 const run=makeRun();
 render(<TaskUnderstanding run={run} draft="" synchronized sourceCurrent presentation={{protocol:'conversation-v1',run,input_revision:1,understanding:{state:'pending',input_revision:1},phase:'stopping',captured_at:now}}/>);
 expect(screen.getByLabelText('AI理解的任务')).toHaveTextContent('已请求停止，本次没有完整的任务理解。');
 expect(screen.getByLabelText('AI理解的任务')).not.toHaveTextContent('正在等待');
});

for(const replyState of ['receiving','interrupted'] as const)it(`reflects actual ${replyState} reply without inventing a completed understanding`,()=>{
 cleanup();const run=makeRun();
 render(<TaskUnderstanding run={run} draft="" synchronized sourceCurrent replyState={replyState} presentation={{protocol:'conversation-v1',run,input_revision:1,understanding:{state:'pending',input_revision:1},phase:'working',captured_at:now}}/>);
 const view=screen.getByLabelText('AI理解的任务');
 expect(view).toHaveTextContent(replyState==='receiving'?'正在生成回复':'本次回复已中断');
 expect(view).not.toHaveTextContent('正在等待实际模型理解');
});
