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
  const dataKey=key=>key.replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
  const addStyle=(key,href)=>{
    if(document.querySelector(`link[data-${key}]`))return;
    const link=document.createElement('link');
    link.rel='stylesheet';
    link.href=href;
    link.dataset[dataKey(key)]='true';
    document.head.appendChild(link);
  };
  const loadScript=(key,src)=>new Promise(resolve=>{
    const existing=document.querySelector(`script[data-${key}]`);
    if(existing){
      if(existing.dataset.loaded==='true')resolve();
      else{
        existing.addEventListener('load',resolve,{once:true});
        existing.addEventListener('error',resolve,{once:true});
        setTimeout(resolve,3000);
      }
      return;
    }
    const s=document.createElement('script');
    s.src=src;
    s.async=false;
    s.dataset[dataKey(key)]='true';
    s.addEventListener('load',()=>{s.dataset.loaded='true';resolve();},{once:true});
    s.addEventListener('error',resolve,{once:true});
    document.body.appendChild(s);
  });

  (async()=>{
    const ownerMode=new URLSearchParams(location.search).get('mode')==='owner';
    await loadScript('university-ime-selection-fix','university-ime-selection-fix.js?v=20260824-1817');
    addStyle('simple-register-flow','simple-register-flow.css?v=20260825-1056');
    await loadScript('simple-register-flow','simple-register-flow.js?v=20260825-1056');
    addStyle('fresh-register-ui','fresh-register-ui.css?v=20260825-1056');
    await loadScript('fresh-register-ui','fresh-register-ui.js?v=20260825-1056');
    addStyle('one-click-register','one-click-register.css?v=20260825-1056');
    await loadScript('one-click-register','one-click-register.js?v=20260825-1056');
    addStyle('photo-register-mode-fix','photo-register-mode-fix.css?v=20260825-1624');

    if(ownerMode){
      await loadScript('owner-photo-register','owner-photo-register.js?v=20260825-1435');
      await loadScript('editor-drag-pan','editor-drag-pan.js?v=20260825-1230');
      document.documentElement.dataset.communityUiSequence='owner-ready';
      return;
    }

    await loadScript('community-submission-compat','community-submission-compat.js?v=20260825-1056');
    await loadScript('community-submission-transport','community-submission-transport.js?v=20260825-1056');
    addStyle('community-submission-fixes','community-submission-fixes.css?v=20260825-1230');
    await loadScript('community-ui-stability','community-ui-stability.js?v=20260825-1230');
    await loadScript('community-submission-ui','community-submission-ui.js?v=20260825-1230');
    await loadScript('editor-drag-pan','editor-drag-pan.js?v=20260825-1230');
    document.documentElement.dataset.communityUiSequence='ready';
  })().catch(error=>console.error('大学写真投稿UIの初期化に失敗しました',error));
})();