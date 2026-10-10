import {defineConfig} from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],test:{environment:'jsdom',include:['tests/replay/**/*.test.tsx'],setupFiles:['tests/setup.ts'],reporters:['default','junit'],outputFile:{junit:'.test-results/u2-delivery-replay.xml'}}});
