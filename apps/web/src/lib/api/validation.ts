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
export function validate(name:string,value:unknown): void {
 const check=ajv.getSchema(`urn:uaw:web:0.1#/$defs/${name}`);
 if(!check || !check(value)) throw new Error(`协议数据不匹配：${name}`);
}
