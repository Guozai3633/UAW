import '@testing-library/jest-dom/vitest';

import {webcrypto} from 'node:crypto';
Object.defineProperty(crypto,'subtle',{value:webcrypto.subtle,configurable:true});
