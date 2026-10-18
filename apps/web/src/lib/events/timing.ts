/** Bounded same-page timing evidence; never retains text, credentials or reasoning. */
export function markTiming(name:string,detail:Record<string,string|number>){
 try{
  const key='uaw.'+name;
  if(performance.getEntriesByName(key).length>=256)performance.clearMarks(key);
  performance.mark(key,{detail});
  if(name==='turn.submit'||name==='turn.accepted'){
   const attribute=name==='turn.submit'?'uawSubmitAt':'uawAcceptedAt';
   document.documentElement.dataset[attribute]=String(performance.timeOrigin+performance.now());
   if(detail.run_id)document.documentElement.dataset.uawRunId=String(detail.run_id);
  }
 }catch{/* Timing support cannot change an execution decision. */}
}
