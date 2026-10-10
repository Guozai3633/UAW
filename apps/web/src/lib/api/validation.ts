import Ajv2020 from 'ajv/dist/2020';
import addFormats from 'ajv-formats';
import schema from './generated/schema.json';
const ajv = new Ajv2020({allErrors:true,strict:false,validateFormats:true});
addFormats(ajv);
function checkFormats(value:unknown):void {
 if(!value || typeof value!=='object')return;
 if('format' in value && !['date-time','uri'].includes(String(value.format)))throw new Error('未登记的协议格式');
 for(const child of Object.values(value))checkFormats(child);
}
checkFormats(schema);
ajv.addSchema(schema);
// Future Item types are display-only data. All fields/statuses stay validated.
// This local display schema never validates approvals, Run or execute requests.
const display=structuredClone(schema);
display.$id='urn:uaw:web:display:0.1';
(display.$defs.ItemType as {enum?:string[]}).enum=undefined;
ajv.addSchema(display);
export function validate(name:string,value:unknown): void {
 const urn=name==='HttpConversationsItemsResult'?'urn:uaw:web:display:0.1':'urn:uaw:web:0.1';
 const check=ajv.getSchema(`${urn}#/$defs/${name}`);
 if(!check || !check(value)) throw new Error(`协议数据不匹配：${name}`);
}
