import {defineConfig,devices} from '@playwright/test';
import path from 'node:path';
process.env.PLAYWRIGHT_BROWSERS_PATH??=path.resolve('.playwright');
export default defineConfig({testDir:'./tests/u3b-readonly',workers:1,retries:0,outputDir:'.test-results/u3b-readonly',
 reporter:[['list'],['junit',{outputFile:process.env.UAW_U3B_AUTH?'.test-results/u3b-authenticated.xml':'.test-results/u3b-anonymous.xml'}]],
 use:{...devices['Desktop Chrome'],screenshot:'off',trace:'off',video:'off'},
 projects:[{name:'anonymous',testMatch:'anonymous.spec.ts',use:{baseURL:'http://127.0.0.1:5178'}},{name:'authenticated',testMatch:'authenticated.spec.ts',use:{baseURL:process.env.UAW_U3B_WEB_URL}}],
 webServer:process.env.UAW_U3B_AUTH?undefined:{command:'pnpm preview --port 5178',url:'http://127.0.0.1:5178',reuseExistingServer:false,timeout:30000}
});
