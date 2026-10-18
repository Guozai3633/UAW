/** Bounded same-page timing evidence; never retains text, credentials or reasoning. */
export function markTiming(name:string,detail:Record<string,string|number>){
 try{
  const key='uaw.'+name;
  if(performance.getEntriesByName(key).length>=256)performance.clearMarks(key);
  performance.mark(key,{detail});
 }catch{/* Timing support cannot change an execution decision. */}
}
