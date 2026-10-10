import {defineConfig,devices} from '@playwright/test';
import path from 'node:path';
process.env.PLAYWRIGHT_BROWSERS_PATH??=path.resolve('.playwright');
export default defineConfig({testDir:'./tests/u3-readonly',workers:1,retries:0,outputDir:'.test-results/u3-readonly',
 reporter:[['list'],['junit',{outputFile:process.env.UAW_U3_AUTH?'.test-results/u3-authenticated.xml':'.test-results/u3-anonymous.xml'}]],
 use:{...devices['Desktop Chrome'],screenshot:'off',trace:'off',video:'off'},
 projects:[{name:'anonymous',testMatch:'anonymous.spec.ts',use:{baseURL:'http://127.0.0.1:5178'}},{name:'authenticated',testMatch:'authenticated.spec.ts',use:{baseURL:process.env.UAW_U3_WEB_URL}}],
 webServer:process.env.UAW_U3_AUTH?undefined:{command:'pnpm preview --port 5178',url:'http://127.0.0.1:5178',reuseExistingServer:false,timeout:30000}
});
