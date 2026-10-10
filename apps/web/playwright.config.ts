import {defineConfig,devices} from '@playwright/test';
import path from 'node:path';
process.env.PLAYWRIGHT_BROWSERS_PATH??=path.resolve('.playwright');
export default defineConfig({testDir:'./tests/e2e',fullyParallel:false,workers:1,retries:0,
 outputDir:'.test-results/playwright',reporter:[['list'],['junit',{outputFile:process.env.UAW_READONLY_BACKEND?'.test-results/u2-backend-browser.xml':'.test-results/playwright.xml'}]],
 use:{...devices['Desktop Chrome'],screenshot:'only-on-failure',trace:'retain-on-failure'},
 projects:[{name:'backend',testMatch:'backend/**/*.spec.ts',use:{baseURL:'http://127.0.0.1:5173',trace:'off'}},{name:'chromium',testMatch:'controlled/**/*.spec.ts',use:{baseURL:'http://127.0.0.1:5177'}},
  {name:'live',testMatch:'live/**/*.spec.ts',use:{baseURL:process.env.UAW_LIVE_WEB_URL,trace:'off'}}],
 webServer:process.env.UAW_LIVE_ONLY?undefined:{command:process.env.UAW_READONLY_BACKEND?'pnpm preview --port 5173':'pnpm preview --port 5177',url:process.env.UAW_READONLY_BACKEND?'http://127.0.0.1:5173':'http://127.0.0.1:5177',reuseExistingServer:false,timeout:30000},
});
