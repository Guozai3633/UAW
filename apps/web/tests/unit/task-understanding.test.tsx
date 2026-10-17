import {afterEach,it,expect} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {TaskUnderstanding} from '../../src/features/workspace/TaskUnderstanding';
import {frame,makeRun} from '../fixtures';
afterEach(cleanup);
it.each(['failed','cancelled','completed'] as const)('terminal %s without current understanding stops waiting and does not invent a summary',status=>{
 render(<TaskUnderstanding run={makeRun(status)} draft="" inputRevision={2}/>);expect(screen.getByLabelText('AI理解的任务')).toHaveTextContent('本次没有生成新的任务理解。');expect(screen.queryByText(/正在等待/)).toBeNull();expect(screen.queryByText(frame.summary!)).toBeNull();
});
it('old input understanding remains exactly readable with an old-version label; current understanding is never falsely old',()=>{
 const {rerender}=render(<TaskUnderstanding run={makeRun('failed')} frame={frame} draft="" inputRevision={2}/>);expect(screen.getByText('本次没有生成新的任务理解。')).toBeVisible();expect(screen.getByText('旧版本任务理解，仅供查阅。')).toBeVisible();expect(screen.getByText(frame.summary!)).toBeVisible();expect(screen.getByText(/输入版本 1/)).toBeVisible();rerender(<TaskUnderstanding run={makeRun('completed')} frame={{...frame,input_revision:2}} draft="" inputRevision={2}/>);expect(screen.queryByText('本次没有生成新的任务理解。')).toBeNull();expect(screen.queryByText(/旧版本/)).toBeNull();expect(screen.getByText(frame.summary!)).toBeVisible();
});
it('unverified/foreign understanding never becomes current, and user draft remains the composition baseline',()=>{
 const {rerender}=render(<TaskUnderstanding run={makeRun('failed')} frame={frame} draft=""/>);expect(screen.getByText('已保存的任务理解，尚未核对为当前输入版本。')).toBeVisible();rerender(<TaskUnderstanding run={makeRun('failed')} frame={{...frame,task_id:'foreign'}} draft="" inputRevision={2}/>);expect(screen.queryByText(frame.summary!)).toBeNull();rerender(<TaskUnderstanding run={makeRun('failed')} frame={frame} draft="  本人新草稿  " inputRevision={2}/>);expect(screen.getByText('发送后，将根据这段原文理解任务。')).toBeVisible();expect(screen.queryByText(frame.summary!)).toBeNull();
});
it('nonterminal without a summary retains actual waiting feedback',()=>{render(<TaskUnderstanding run={makeRun('running')} draft="" inputRevision={2}/>);expect(screen.getByText('正在等待实际任务理解…')).toBeVisible();expect(screen.queryByText('本次没有生成新的任务理解。')).toBeNull();});
