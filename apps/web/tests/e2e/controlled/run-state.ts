import {expect,type Page} from '@playwright/test';
// Technical values are retained for inspection; assertions explicitly open the user-facing details.
export async function expectRunState(page:Page,text:string){const details=page.locator('.run-state-details');await expect(details).toBeAttached();if(!await details.evaluate(node=>(node as HTMLDetailsElement).open))await details.getByText('任务状态详情',{exact:true}).click();await expect(details.getByText(text,{exact:true})).toBeVisible();}
