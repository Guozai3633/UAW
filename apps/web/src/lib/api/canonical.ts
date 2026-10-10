// Fixed DTO hashing uses Python parameter_hash's sorted UTF-8 JSON domain.
// These DTOs carry strings, bools, bounded integer counts and structured refs.
export function canonical(value:unknown):string {
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 if(value&&typeof value==='object')return '{'+Object.keys(value).sort(compareKeys).map(key=>JSON.stringify(key)+':'+canonical((value as Record<string,unknown>)[key])).join(',')+'}';
 const encoded=JSON.stringify(value);if(encoded===undefined)throw new Error('不可序列化的固定来源');return encoded;
}
function compareKeys(a:string,b:string){const x=Array.from(a),y=Array.from(b);for(let i=0;i<Math.min(x.length,y.length);i++){const delta=x[i].codePointAt(0)!-y[i].codePointAt(0)!;if(delta)return delta;}return x.length-y.length;}
export async function recordHash(value:unknown){const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(value)));return [...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');}
