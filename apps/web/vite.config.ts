import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwind from '@tailwindcss/vite';
export default defineConfig({plugins:[react(),tailwind()],server:{host:'127.0.0.1',port:5177,strictPort:true},
 test:{environment:'jsdom',include:['tests/unit/**/*.test.{ts,tsx}'],setupFiles:['tests/setup.ts'],
 reporters:['default','junit'],outputFile:{junit:'.test-results/unit.xml'}}});
