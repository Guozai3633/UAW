import '@testing-library/jest-dom/vitest';

import {webcrypto} from 'node:crypto';
Object.defineProperty(crypto,'subtle',{value:webcrypto.subtle,configurable:true});

// Unit rendering has a stable desktop viewport; actual responsive behavior is tested in Chromium.
Object.defineProperty(window,'matchMedia',{writable:true,value:(media:string)=>({media,matches:false,onchange:null,addEventListener:()=>{},removeEventListener:()=>{},addListener:()=>{},removeListener:()=>{},dispatchEvent:()=>true})});
