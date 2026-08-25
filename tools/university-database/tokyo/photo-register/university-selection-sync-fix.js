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
queueMicrotask(()=>{assignFirstUniversityToUnassigned();syncFirstUniversityFromRows();});
})();

(()=>{
  const addStyle=(key,href)=>{
    if(document.querySelector(`link[data-${key}]`))return;
    const link=document.createElement('link');link.rel='stylesheet';link.href=href;link.dataset[key.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='true';document.head.appendChild(link);
  };
  const addScript=(key,src)=>{
    if(document.querySelector(`script[data-${key}]`))return;
    const s=document.createElement('script');s.src=src;s.defer=true;s.dataset[key.replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]='true';document.body.appendChild(s);
  };
  addScript('university-ime-selection-fix','university-ime-selection-fix.js?v=20260824-1817');
  addStyle('simple-register-flow','simple-register-flow.css?v=20260825-1056');
  addScript('simple-register-flow','simple-register-flow.js?v=20260825-1056');
  addStyle('fresh-register-ui','fresh-register-ui.css?v=20260825-1056');
  addScript('fresh-register-ui','fresh-register-ui.js?v=20260825-1056');
  addStyle('one-click-register','one-click-register.css?v=20260825-1056');
  addScript('one-click-register','one-click-register.js?v=20260825-1056');
  addScript('community-submission-compat','community-submission-compat.js?v=20260825-1056');
  addScript('community-submission-transport','community-submission-transport.js?v=20260825-1056');
  addStyle('community-submission-fixes','community-submission-fixes.css?v=20260825-1142');
  addScript('community-ui-stability','community-ui-stability.js?v=20260825-1142');
  addScript('editor-drag-pan','editor-drag-pan.js?v=20260825-1142');
})();