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

(()=>{
  if(!document.querySelector('script[data-university-ime-selection-fix]')){
    const s=document.createElement('script');
    s.src='university-ime-selection-fix.js?v=20260824-1817';
    s.defer=true;
    s.dataset.universityImeSelectionFix='true';
    document.body.appendChild(s);
  }
  if(!document.querySelector('link[data-simple-register-flow]')){
    const link=document.createElement('link');
    link.rel='stylesheet';
    link.href='simple-register-flow.css?v=20260824-1920';
    link.dataset.simpleRegisterFlow='true';
    document.head.appendChild(link);
  }
  if(!document.querySelector('script[data-simple-register-flow]')){
    const simple=document.createElement('script');
    simple.src='simple-register-flow.js?v=20260824-1858';
    simple.defer=true;
    simple.dataset.simpleRegisterFlow='true';
    document.body.appendChild(simple);
  }
})();
