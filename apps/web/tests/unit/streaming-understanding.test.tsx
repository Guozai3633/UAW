import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import {TaskUnderstanding} from '../../src/features/workspace/TaskUnderstanding';
import {makeRun,now} from '../fixtures';
it('stopping without a completed model decision does not promise a future understanding',()=>{
 const run=makeRun();
 render(<TaskUnderstanding run={run} draft="" synchronized sourceCurrent presentation={{protocol:'conversation-v1',run,input_revision:1,understanding:{state:'pending',input_revision:1},phase:'stopping',captured_at:now}}/>);
 expect(screen.getByLabelText('AI理解的任务')).toHaveTextContent('已请求停止，本次没有完整的任务理解。');
 expect(screen.getByLabelText('AI理解的任务')).not.toHaveTextContent('正在等待');
});
