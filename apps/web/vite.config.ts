import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwind from '@tailwindcss/vite';
const apiTarget=process.env.UAW_WEB_API_TARGET;
if(apiTarget){const target=new URL(apiTarget);if(target.protocol!=='http:'||target.hostname!=='127.0.0.1'||target.port!=='8000'||target.pathname!=='/'||target.search||target.hash||target.username||target.password)throw new Error('Only the published loopback API target is allowed');}
export default defineConfig({plugins:[react(),tailwind()],server:{host:'127.0.0.1',port:5173,strictPort:true,proxy:apiTarget?{'/v1':{target:apiTarget,changeOrigin:true,xfwd:false}}:undefined},
 test:{environment:'jsdom',include:['tests/unit/**/*.test.{ts,tsx}'],setupFiles:['tests/setup.ts'],
 reporters:['default','junit'],outputFile:{junit:'.test-results/unit.xml'}}});
