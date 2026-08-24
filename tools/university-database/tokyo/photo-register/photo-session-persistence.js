(()=>{
'use strict';
const input=document.querySelector('#photo-input');
const university=document.querySelector('#university-first-select');
const list=document.querySelector('#batch-list');
const pickerHost=document.querySelector('.university-first');
if(!input||!university||!list||!pickerHost||!('indexedDB'in window))return;

const DB_NAME='bantai-university-photo-register';
const STORE='session';
const KEY='tokyo-photo-register-current';
let restoring=false;
let saveTimer=0;

function openDb(){return new Promise((resolve,reject)=>{const req=indexedDB.open(DB_NAME,1);req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains(STORE))req.result.createObjectStore(STORE);};req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});}
async function put(value){const db=await openDb();await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(value,KEY);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});db.close();}
async function get(){const db=await openDb();const value=await new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly');const req=tx.objectStore(STORE).get(KEY);req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>reject(req.error);});db.close();return value;}

function currentMainDescriptor(){const card=document.querySelector('.main-photo-choice-card.active');if(!card)return null;const type=card.dataset.mainType||'';if(type==='existing')return{type,key:card.dataset.mainKey||''};const label=card.querySelector('strong')?.textContent?.trim()||'';return{type:'new',label};}
function excludedDescriptors(){return [...document.querySelectorAll('.photo-choice-delete-wrap')].filter(w=>w.hidden).map(()=>null).filter(Boolean);}

async function filesFromInput(){return [...input.files].map(file=>({name:file.name,type:file.type,lastModified:file.lastModified,blob:file}));}
async function snapshot(){
  if(restoring)return;
  const files=await filesFromInput();
  await put({version:1,universityId:university.value||'',files,main:currentMainDescriptor(),savedAt:Date.now()});
  document.documentElement.dataset.photoSessionSaved='true';
}
function scheduleSave(){clearTimeout(saveTimer);saveTimer=setTimeout(()=>snapshot().catch(console.error),180);}

input.addEventListener('change',()=>setTimeout(scheduleSave,500));
university.addEventListener('change',scheduleSave);
document.addEventListener('click',event=>{
  if(event.target.closest?.('.main-photo-choice-card')||event.target.closest?.('.photo-list-delete')||event.target.closest?.('.remove-item'))setTimeout(scheduleSave,250);
},true);
new MutationObserver(()=>scheduleSave()).observe(list,{childList:true});

function waitFor(fn,timeout=10000){return new Promise((resolve,reject)=>{const started=Date.now();const tick=()=>{const value=fn();if(value)return resolve(value);if(Date.now()-started>timeout)return reject(new Error('restore timeout'));setTimeout(tick,80);};tick();});}

async function restore(){
  const saved=await get();
  if(!saved||!Array.isArray(saved.files)||(!saved.files.length&&!saved.universityId))return;
  restoring=true;
  try{
    if(saved.universityId){
      await waitFor(()=>university.querySelector(`option[value="${CSS.escape(saved.universityId)}"]`));
      university.value=saved.universityId;
      university.dispatchEvent(new Event('change',{bubbles:true}));
    }
    if(saved.files.length){
      const dt=new DataTransfer();
      for(const item of saved.files){dt.items.add(new File([item.blob],item.name,{type:item.type||item.blob?.type||'application/octet-stream',lastModified:item.lastModified||Date.now()}));}
      input.files=dt.files;
      input.dispatchEvent(new Event('change',{bubbles:true}));
      await waitFor(()=>document.querySelectorAll('.batch-row').length>=saved.files.length);
    }
    if(saved.main){
      await waitFor(()=>document.querySelector('.main-photo-choice-card'));
      let target=null;
      if(saved.main.type==='existing'&&saved.main.key){target=[...document.querySelectorAll('.main-photo-choice-card[data-main-type="existing"]')].find(card=>(card.dataset.mainKey||'')===saved.main.key);}
      if(saved.main.type==='new'&&saved.main.label){target=[...document.querySelectorAll('.main-photo-choice-card[data-main-type="new"]')].find(card=>card.querySelector('strong')?.textContent?.trim()===saved.main.label);}
      target?.click();
    }
    document.documentElement.dataset.photoSessionRestored='true';
  }catch(err){console.error('photo session restore failed',err);document.documentElement.dataset.photoSessionRestored='error';}
  finally{restoring=false;scheduleSave();}
}

restore().catch(err=>console.error('photo session load failed',err));
})();
