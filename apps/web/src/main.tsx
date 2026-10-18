import {HttpPresentationPort,type PresentationPort} from './features/presentation/port';
import {HttpConversationPort,type ConversationPort} from './features/conversation/port';
import {ContinuationStore} from './features/conversation/store';
import {HttpInstalledLaunchPort,type InstalledLaunchPort} from './features/devices/installed';
import {HttpEnrollmentPort,clearEnrollmentLookup,type EnrollmentSourcePort,type EnrollmentPort} from './features/devices/port';
import {clearAcceptanceLookups} from './lib/cache/acceptance-lookups';
import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter} from 'react-router';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {BrowserSessionHost} from './lib/api/browser-session';
import {HttpRecoveryPort,HttpReviewPort} from './lib/api/a2-adapters';
import {UawClient} from './lib/api/client';
import {HttpQualityPort} from './features/quality/port';
import {WorkspaceController,type WorkspaceHost} from './features/workspace/controller';
import type {ReviewPort} from './features/review/port';
import {Workspace} from './features/workspace/Workspace';
import './styles.css';
declare global {interface Window {uawWebHost?:WorkspaceHost&{review?:ReviewPort;enrollments?:EnrollmentPort;enrollmentSource?:EnrollmentSourcePort;installedLaunch?:InstalledLaunchPort;conversation?:ConversationPort;presentation?:PresentationPort};}}
// A's authenticated same-origin host may inject this memory-only adapter.
// No token input, fake login, private config or default product provider.
const browserHost=window.uawWebHost?undefined:new BrowserSessionHost();
const host:WorkspaceHost=window.uawWebHost??browserHost!;
const queryClient=new QueryClient({defaultOptions:{queries:{retry:false,staleTime:0,gcTime:0}}});
const wrappedHost:WorkspaceHost={session:host.session,subscribe:host.subscribe,unavailableReason:host.unavailableReason,recovery:host.recovery,logout:async()=>{queryClient.clear();clearAcceptanceLookups();clearEnrollmentLookup();installedPort.clear();continuationStore.clear();await host.logout?.();}};
const client=new UawClient(host.session);
const qualityPort=new HttpQualityPort(client);
wrappedHost.recovery??=new HttpRecoveryPort(client);
const reviewPort=window.uawWebHost?.review??new HttpReviewPort(client);
const enrollmentPort=window.uawWebHost?.enrollments??new HttpEnrollmentPort(client,window.uawWebHost?.enrollmentSource);
const installedPort=window.uawWebHost?.installedLaunch??new HttpInstalledLaunchPort(client);
const conversationPort=window.uawWebHost?.conversation??new HttpConversationPort(client);
const presentationPort=window.uawWebHost?.presentation??new HttpPresentationPort(client);
const continuationStore=new ContinuationStore();
const controller=new WorkspaceController(client,wrappedHost);
let observedIdentity=host.session()?.identityKey;
host.subscribe?.(()=>{const next=host.session()?.identityKey;if(observedIdentity&&next!==observedIdentity){clearAcceptanceLookups();clearEnrollmentLookup();installedPort.clear();continuationStore.clear();}observedIdentity=next;queryClient.clear();});
createRoot(document.getElementById('root')!).render(<React.StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><Workspace controller={controller} reviewPort={reviewPort} enrollmentPort={enrollmentPort} installedPort={installedPort} conversationPort={conversationPort} conversationStore={continuationStore} presentationPort={presentationPort} qualityPort={qualityPort}/></BrowserRouter></QueryClientProvider></React.StrictMode>);

void browserHost?.initialize();
