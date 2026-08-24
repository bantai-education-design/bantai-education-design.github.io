(()=>{
'use strict';
const firstSelect=document.querySelector('#university-first-select');
const batchList=document.querySelector('#batch-list');
if(!firstSelect||!batchList)return;
let syncing=false;

function rows(){return [...batchList.querySelectorAll('.batch-row')];}
function assignFirstUniversityToUnassigned(){
  const id=firstSelect.value;
  if(!id||syncing)return;
  syncing=true;
  try{
    for(const row of rows()){
      const select=row.querySelector('.row-university');
      if(!select||select.value)continue;
      if(![...select.options].some(o=>o.value===id))continue;
      select.value=id;
      select.dispatchEvent(new Event('change',{bubbles:true}));
    }
  }finally{syncing=false;}
}

function syncFirstUniversityFromRows(){
  if(firstSelect.value||syncing)return;
  const current=rows();
  if(!current.length)return;
  const ids=current.map(row=>row.querySelector('.row-university')?.value||'');
  if(ids.some(id=>!id))return;
  const unique=[...new Set(ids)];
  if(unique.length!==1)return;
  const id=unique[0];
  if(![...firstSelect.options].some(o=>o.value===id))return;
  syncing=true;
  try{
    firstSelect.value=id;
    firstSelect.dispatchEvent(new Event('change',{bubbles:true}));
  }finally{syncing=false;}
}

firstSelect.addEventListener('change',()=>queueMicrotask(assignFirstUniversityToUnassigned));
batchList.addEventListener('change',event=>{
  if(event.target.matches?.('.row-university'))queueMicrotask(syncFirstUniversityFromRows);
});
new MutationObserver(()=>queueMicrotask(()=>{
  assignFirstUniversityToUnassigned();
  syncFirstUniversityFromRows();
})).observe(batchList,{childList:true,subtree:true});

queueMicrotask(()=>{
  assignFirstUniversityToUnassigned();
  syncFirstUniversityFromRows();
});
})();
