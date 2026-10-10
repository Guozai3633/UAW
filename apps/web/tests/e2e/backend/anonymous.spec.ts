// Actual reachable A localhost API; no launch/cookie, no interception, no mutations.
import {test,expect} from '@playwright/test';
test('real TCP backend: anonymous browser receives actual auth denial and cannot execute',async({page})=>{
 const posts:string[]=[];page.on('request',request=>{if(['POST','DELETE'].includes(request.method()))posts.push(new URL(request.url()).pathname);});
 const reading=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/web/session'&&response.request().method()==='GET');
 await page.goto('/');const response=await reading;expect(response.status()).toBe(401);const wire=await response.json();expect(wire.kind).toBe('denied');
 await expect(page.getByRole('alert')).toHaveText(wire.failure.message);await expect(page.getByRole('button',{name:'发送原文'})).toBeDisabled();expect(posts).toHaveLength(0);
 await page.reload();await expect(page.getByRole('alert')).toHaveText(wire.failure.message);expect(posts).toHaveLength(0);await page.screenshot({path:'.test-results/u2-real-anonymous.png',fullPage:true});
});
