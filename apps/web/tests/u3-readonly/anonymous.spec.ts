// Real TCP, no fixtures or mutation. Screenshots disabled for this distinct trial.
import {test,expect} from '@playwright/test';
test('MS-U3 real anonymous: current auth denial and reload never dispatch',async({page})=>{
 const writes:string[]=[];page.on('request',r=>{if(r.method()!=='GET')writes.push(r.method());});
 const read=page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/web/session'&&r.request().method()==='GET');
 await page.goto('/');const response=await read;expect(response.status()).toBe(401);const result=await response.json();expect(result.kind).toBe('denied');
 await expect(page.getByRole('alert')).toHaveText(result.failure.message);await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();
 await page.reload();await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();expect(writes).toEqual([]);
});
