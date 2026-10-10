// The HTTP200 wire fixture is A's actual localhost observation (2026-10-10).
// Replay validates the fixed public contract; it is not a new live model run.
import {execFileSync} from 'node:child_process';
import {it,expect,vi} from 'vitest';
import generated from '../../src/lib/api/generated/schema.json';
import source from '../../src/lib/api/generated/source.json';
import actual from '../fixtures/a-runtime-task-frame-event.json';
import {validate} from '../../src/lib/api/validation';
import {UawClient,TransportError} from '../../src/lib/api/client';

it('every reachable runtime definition equals the complete fixed source, including name maps and nested annotations',()=>{
 const original=JSON.parse(execFileSync('git',['show',`${source.contract_ref}:contracts/uaw.schema.json`],{encoding:'utf8',maxBuffer:16777216}));
 for(const [name,definition] of Object.entries(generated.$defs))expect(definition,name).toEqual(original.$defs[name]);
 expect(generated.$defs.OutputSpec.properties).toHaveProperty('description');
});
it('actual task.frame.committed OutputSpec.description survives both HTTP and TaskFrame validation',async()=>{
 expect(actual.payload.parameters.output_specs.every(spec=>typeof spec.description==='string')).toBe(true);
 validate('TaskFrame',actual.payload.parameters);
 const client=new UawClient(()=>null,vi.fn(async()=>new Response(JSON.stringify(actual))));
 expect(await client.payload('event-8d13ffebd75540efa9ffee3d3a02cb32')).toEqual(actual.payload);
});
it('the same actual nested event still rejects unknown fields and wrongly typed description',async()=>{
 for(const change of [{unexpected_field:'untrusted'},{description:42}]){
  const wire=structuredClone(actual);Object.assign(wire.payload.parameters.output_specs[0],change);
  expect(()=>validate('TaskFrame',wire.payload.parameters)).toThrow('协议数据不匹配');
  const client=new UawClient(()=>null,vi.fn(async()=>new Response(JSON.stringify(wire))));
  await expect(client.payload('event-8d13ffebd75540efa9ffee3d3a02cb32')).rejects.toBeInstanceOf(TransportError);
 }
});
