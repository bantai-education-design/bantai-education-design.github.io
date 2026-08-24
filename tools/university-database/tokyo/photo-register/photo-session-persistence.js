(()=>{
'use strict';
const input=document.querySelector('#photo-input');
const university=document.querySelector('#university-first-select');
const list=document.querySelector('#batch-list');
const pickerHost=document.querySelector('.university-first');
const clearBatch=document.querySelector('#clear-batch');
const legacyFile=document.querySelector('#university-first-photo');
if(!input||!university||!list||!pickerHost||!('indexedDB'in window))return;

const DB_NAME='bantai-university-photo-register';
const STORE='session';
const KEY='tokyo-photo-register-current';
const TAB_FLAG='bantai-photo-register-restore-this-tab';
const SESSION_VERSION=3;
let restoring=false;
let switching=false;
let saveTimer=0;
let currentUniversityId='';

function openDb(){return new Promise((resolve,reject)=>{const req=indexedDB.open(DB_NAME,1);req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains(STORE))req.result.createObjectStore(STORE);};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});}
async function put(value){const db=await openDb();await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(value,KEY);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});db.close();}
async function get(){const db=await openDb();const value=await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly');const req=tx.objectStore(STORE).get(KEY);req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>reject(req.error);});db.close();return value;}

function emptySession(universityId=''){return{version:SESSION_VERSION,universityId:universityId||'',files:[],main:null,savedAt:Date.now()};}
function currentMainDescriptor(){const card=document.querySelector('.main-photo-choice-card.active');if(!card)return null;const type=card.dataset.mainType||'';if(type==='existing')return{type,key:card.dataset.mainKey||''};const label=card.querySelector('strong')?.textContent?.trim()||'';return{type:'new',label};}
async function filesFromInput(){return [...input.files].map(file=>({name:file.name,type:file.type,lastModified:file.lastModified,blob:file}));}
async function snapshot(){
  if(restoring||switching)return;
  const files=await filesFromInput();
  await put({version:SESSION_VERSION,universityId:university.value||'',files,main:currentMainDescriptor(),savedAt:Date.now()});
  sessionStorage.setItem(TAB_FLAG,'1');
  document.documentElement.dataset.photoSessionSaved='true';
}
function scheduleSave(){if(restoring||switching)return;clearTimeout(saveTimer);saveTimer=setTimeout(()=>snapshot().catch(console.error),180);}

async function saveEmptySession(universityId){
  await put(emptySession(universityId));
  sessionStorage.setItem(TAB_FLAG,'1');
  document.documentElement.dataset.photoSessionSaved='true';
}
function clearVisibleAddedPhotos(){
  if(clearBatch)clearBatch.click();
  else for(const button of [...list.querySelectorAll('.batch-row .remove-item')])button.click();
  try{input.value='';}catch(err){console.error(err);}
  try{if(legacyFile)legacyFile.value='';}catch(err){console.error(err);}
}
function clearAddedPhotosForUniversitySwitch(nextUniversityId){
  switching=true;
  clearTimeout(saveTimer);
  clearVisibleAddedPhotos();
  currentUniversityId=nextUniversityId;
  document.documentElement.dataset.photoUniversitySwitched='clearing';
  queueMicrotask(async()=>{
    try{
      await saveEmptySession(nextUniversityId);
      document.documentElement.dataset.photoUniversitySwitched='cleared';
    }catch(err){
      console.error('photo session switch reset failed',err);
      document.documentElement.dataset.photoUniversitySwitched='error';
    }finally{
      switching=false;
    }
  });
}

input.addEventListener('change',()=>setTimeout(scheduleSave,500));
university.addEventListener('change',()=>{
  const next=university.value||'';
  if(restoring){
    if(next)currentUniversityId=next;
    return;
  }
  if(!next)return;
  const previous=currentUniversityId;
  const hasAddedPhotos=!!list.querySelector('.batch-row');
  if((previous&&previous!==next)||(!previous&&hasAddedPhotos)){
    clearAddedPhotosForUniversitySwitch(next);
    return;
  }
  currentUniversityId=next;
  scheduleSave();
});
document.addEventListener('click',event=>{
  if(event.target.closest?.('.main-photo-choice-card')||event.target.closest?.('.photo-list-delete')||event.target.closest?.('.remove-item'))setTimeout(scheduleSave,250);
},true);
new MutationObserver(()=>scheduleSave()).observe(list,{childList:true});

function waitFor(fn,timeout=10000){return new Promise((resolve,reject)=>{const started=Date.now();const tick=()=>{const value=fn();if(value)return resolve(value);if(Date.now()-started>timeout)return reject(new Error('restore timeout'));setTimeout(tick,80);};tick();});}
function findSavedMain(main){
  if(!main)return null;
  if(main.type==='existing'&&main.key)return [...document.querySelectorAll('.main-photo-choice-card[data-main-type="existing"]')].find(card=>(card.dataset.mainKey||'')===main.key)||null;
  if(main.type==='new'&&main.label)return [...document.querySelectorAll('.main-photo-choice-card[data-main-type="new"]')].find(card=>card.querySelector('strong')?.textContent?.trim()===main.label)||null;
  return null;
}

async function restore(){
  const saved=await get();
  if(saved&&saved.version!==SESSION_VERSION){
    await put(emptySession());
    sessionStorage.removeItem(TAB_FLAG);
    clearVisibleAddedPhotos();
    document.documentElement.dataset.photoSessionRestored='legacy-cleared';
    document.documentElement.dataset.photoLegacySessionCleared='true';
    return;
  }
  if(sessionStorage.getItem(TAB_FLAG)!=='1')return;
  if(!saved||!Array.isArray(saved.files)||(!saved.files.length&&!saved.universityId))return;
  restoring=true;
  try{
    if(saved.universityId){
      await waitFor(()=>university.querySelector(`option[value="${CSS.escape(saved.universityId)}"]`));
      university.value=saved.universityId;
      university.dispatchEvent(new Event('change',{bubbles:true}));
      currentUniversityId=saved.universityId;
    }
    if(saved.files.length){
      const dt=new DataTransfer();
      for(const item of saved.files){dt.items.add(new File([item.blob],item.name,{type:item.type||item.blob?.type||'application/octet-stream',lastModified:item.lastModified||Date.now()}));}
      input.files=dt.files;
      input.dispatchEvent(new Event('change',{bubbles:true}));
      await waitFor(()=>document.querySelectorAll('.batch-row').length>=saved.files.length);
    }
    if(saved.main){
      await waitFor(()=>findSavedMain(saved.main));
      findSavedMain(saved.main)?.click();
      await new Promise(resolve=>setTimeout(resolve,400));
      const settled=findSavedMain(saved.main);
      if(settled&&!settled.classList.contains('active'))settled.click();
      await waitFor(()=>findSavedMain(saved.main)?.classList.contains('active'),5000);
    }
    document.documentElement.dataset.photoSessionRestored='true';
  }catch(err){console.error('photo session restore failed',err);document.documentElement.dataset.photoSessionRestored='error';}
  finally{restoring=false;scheduleSave();}
}

restore().catch(err=>console.error('photo session load failed',err));
})();
