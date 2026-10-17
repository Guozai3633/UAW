import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests/u4-readonly',testMatch:'authenticated.spec.ts',workers:1,retries:0,timeout:60000,
 outputDir:'.test-results/u4-readonly',reporter:[['list'],['junit',{outputFile:'.test-results/ms-u4-live.xml'}]],
 use:{screenshot:'off',trace:'off',video:'off'},projects:[{name:'owner-page'}]});
