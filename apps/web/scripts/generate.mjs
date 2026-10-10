import { writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import {execFileSync} from 'node:child_process';
import openapiTS, { astToString } from 'openapi-typescript';
const contractRef='ms-i2k-start';
const contractCommit=execFileSync('git',['rev-parse',`${contractRef}^{commit}`],{encoding:'utf8',maxBuffer:16777216}).trim();
if(contractCommit!=='b7b79b150470a80f37b28fd52a2177f6de5b3124')throw Error('Published API tag changed');
const target = new URL('../src/lib/api/generated/', import.meta.url);
const raw=execFileSync('git',['show',`${contractRef}:contracts/openapi.json`],{encoding:'utf8',maxBuffer:16777216});
const schemaRaw=execFileSync('git',['show',`${contractRef}:contracts/uaw.schema.json`],{encoding:'utf8',maxBuffer:16777216});
const api = JSON.parse(raw), schema = JSON.parse(schemaRaw);
// Exact public routes checked in src/uaw/api/routes.py at ms-i2k-start.
const allowed = {
 '/v1/conversations': ['get','post'], '/v1/conversations/{conversation_id}': ['get'],
 '/v1/conversations/{conversation_id}/items': ['get'],
 '/v1/conversations/{conversation_id}/turns': ['post'], '/v1/runs/{run_id}': ['get'],
 '/v1/runs/{run_id}/control': ['post'], '/v1/tasks/{task_id}/frame': ['get'],
 '/v1/approvals/{approval_id}': ['get'], '/v1/approvals/{approval_id}/decisions': ['post'],
 '/v1/conversations/{conversation_id}/events': ['get'], '/v1/events/{event_id}/payload': ['get'],
 '/v1/conversations/{conversation_id}/turn-requests/{request_id}':['get'],
 '/v1/runs/{run_id}/delivery':['get'], '/v1/runs/{run_id}/delivery/acceptance':['post'],
 '/v1/artifacts/{artifact_id}':['get'], '/v1/artifacts/{artifact_id}/content':['get'],
 '/v1/models': ['get'], '/v1/web/session':['get','post','delete'] };
const paths = Object.fromEntries(Object.entries(allowed).map(([path, methods]) => [path,
 Object.fromEntries(methods.map(method => { if (!api.paths[path]?.[method]) throw Error(`Missing ${path}`);
 return [method, api.paths[path][method]]; }))]));
const used = new Set();
function visit(value) { if (!value || typeof value !== 'object') return;
 if (value.$ref?.startsWith('#/components/schemas/')) {
 const key = value.$ref.split('/').at(-1); if (!used.has(key)) { used.add(key); visit(api.components.schemas[key]); }}
 for (const [key, child] of Object.entries(value)) if (key !== '$ref') visit(child); }
visit(paths);
// Requests are inline in OpenAPI; include their unchanged named schema DTOs too.
for(const key of ['ConversationsCreateRequest','ConversationsGetRequest','ConversationsItemsRequest',
 'TurnsSubmitRequest','RunsGetRequest','RunsControlRequest','TasksFrameRequest','ApprovalsGetRequest',
 'ApprovalsDecideRequest','EventsReadRequest','EventsPayloadRequest','ModelsListRequest',
 'ConversationsListRequest','TurnsLookupRequest','RunsDeliveryRequest','RunsDeliveryAcceptRequest','ArtifactsGetRequest','ArtifactsContentRequest','CompletionAcceptance','ArtifactRecord','VerificationReport','WebSessionGetRequest','WebSessionExchangeRequest','WebSessionLogoutRequest']) {
 used.add(key);visit(api.components.schemas[key]);
}
// Keep source annotations as well as constraints. Names in properties/$defs
// are business fields, so recursive deletion by a keyword corrupts the contract.
// Type shape cannot express JSON Schema if/then, nor required-only anyOf predicates.
// Strip only these type predicates; runtime schema below retains every constraint.
function typeShape(value) {
 if(Array.isArray(value))return value.map(typeShape);
 if(!value||typeof value!=='object')return value;
 return Object.fromEntries(Object.entries(value).filter(([k,v])=>
  !(['if','then','else','not'].includes(k)) &&
  !(k==='anyOf' && value.properties && v.every(x=>!x.$ref && !x.type)) &&
  !(k==='allOf' && v.every(x=>x.if))).map(([k,v])=>[k,typeShape(v)]));
}
const components = { schemas: Object.fromEntries([...used].sort().map(k => [k, typeShape(api.components.schemas[k])])) };
await mkdir(target, {recursive:true});
await writeFile(new URL('openapi.d.ts', target), astToString(await openapiTS({...api,paths,components})));
// Runtime uses the exact draft2020-12 source refs, with only reachable DTOs.
const defs = new Set([...used]);
function collect(value) { if (!value || typeof value !== 'object') return;
 if (value.$ref?.startsWith('#/$defs/')) { const key=value.$ref.split('/').at(-1);
 if(!defs.has(key)) { defs.add(key); collect(schema.$defs[key]); } }
 for (const [k,v] of Object.entries(value)) if(k !== '$ref') collect(v); }
for (const key of [...defs]) collect(schema.$defs[key]);
await writeFile(new URL('schema.json',target),JSON.stringify({$schema:schema.$schema,$id:'urn:uaw:web:0.1',
 $defs:Object.fromEntries([...defs].sort().map(k=>[k,schema.$defs[k]]))},null,2)+'\n');
await writeFile(new URL('source.json',target),JSON.stringify({baseline:'b7b79b150470a80f37b28fd52a2177f6de5b3124',
 contract_ref:contractRef,contract_commit:contractCommit,
 schema_sha256:createHash('sha256').update(schemaRaw).digest('hex'),
 openapi_sha256:createHash('sha256').update(raw).digest('hex'),paths:allowed},null,2)+'\n');
console.log(`Generated ${Object.keys(paths).length} actual paths; ${defs.size} schema definitions.`);
