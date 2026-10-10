import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter} from 'react-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {UawClient} from './lib/api/client';
import {WorkspaceController,type WorkspaceHost} from './features/workspace/controller';
import type {ReviewPort} from './features/review/port';
import {Workspace} from './features/workspace/Workspace';
import './styles.css';
declare global {interface Window {uawWebHost?:WorkspaceHost&{review?:ReviewPort};}}
// A's authenticated same-origin host may inject this memory-only adapter.
// No token input, fake login, private config or default product provider.
const host=window.uawWebHost??{session:()=>null};
const client=new UawClient(host.session);
const controller=new WorkspaceController(client,host);
const queryClient=new QueryClient({defaultOptions:{queries:{retry:false,staleTime:0,gcTime:0}}});
host.subscribe?.(()=>queryClient.clear());
createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><Workspace controller={controller} reviewPort={host.review}/></BrowserRouter></QueryClientProvider></React.StrictMode>);
