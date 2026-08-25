(()=>{
'use strict';
const batch=document.querySelector('.batch');
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const list=document.querySelector('#batch-list');
const clearBatch=document.querySelector('#clear-batch');
const progress=document.querySelector('#simple-register-progress');
if(!batch||!select||!search||!list)return;

const DB_NAME='bantai-university-photo-register';
const STORE='session';
const KEY='tokyo-photo-register-current';
const TAB_FLAG='bantai-photo-register-restore-this-tab';
const setText=(node,text)=>{if(node&&node.textContent!==text)node.textContent=text;};

function deleteStoredSession(){
  if(!('indexedDB' in window))return Promise.resolve();
  return new Promise(resolve=>{
    const req=indexedDB.open(DB_NAME,1);
    req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains(STORE))req.result.createObjectStore(STORE);};
    req.onerror=()=>resolve();
    req.onsuccess=()=>{
      const db=req.result;
      const tx=db.transaction(STORE,'readwrite');
      tx.objectStore(STORE).delete(KEY);
      tx.oncomplete=()=>{db.close();resolve();};
      tx.onerror=()=>{db.close();resolve();};
    };
  });
}

sessionStorage.removeItem(TAB_FLAG);
deleteStoredSession();
document.documentElement.dataset.photoFreshStart='load';

// Browsers may restore a native <select> value across reloads even when the app
// deliberately discarded its saved session. Reset the chooser exactly once,
// immediately after the full university list is available, so every reload truly
// starts a new registration without fighting later user interaction.
let freshLoadSelectionReset=false;
function resetRestoredSelectionOnce(){
  if(freshLoadSelectionReset||select.options.length<=1)return false;
  freshLoadSelectionReset=true;
  const changed=select.value!==''||search.value!=='';
  search.value='';
  select.value='';
  if(changed)select.dispatchEvent(new Event('change',{bubbles:true}));
  document.documentElement.dataset.photoFreshSelection='cleared';
  return true;
}
const freshSelectionObserver=new MutationObserver(()=>{
  if(resetRestoredSelectionOnce())freshSelectionObserver.disconnect();
});
freshSelectionObserver.observe(select,{childList:true,subtree:true});
if(resetRestoredSelectionOnce())freshSelectionObserver.disconnect();

function resetVisibleWork(reason='manual'){
  try{clearBatch?.click();}catch(err){console.error(err);}
  search.value='';
  select.value='';
  select.dispatchEvent(new Event('change',{bubbles:true}));
  const editorSearch=document.querySelector('#editor-university-search');
  if(editorSearch)editorSearch.value='';
  sessionStorage.removeItem(TAB_FLAG);
  deleteStoredSession();
  document.documentElement.dataset.photoFreshStart=reason;
  queueMicrotask(()=>search.focus());
}
window.__bantaiStartNewPhotoRegistration=resetVisibleWork;
window.addEventListener('bantai-photo-register-complete',()=>setTimeout(()=>resetVisibleWork('registered'),350));

const head=batch.querySelector('.section-head');
if(clearBatch)clearBatch.classList.add('simple-legacy-clear');
let newButton=document.querySelector('#start-new-photo-registration');
if(!newButton){
  newButton=document.createElement('button');
  newButton.id='start-new-photo-registration';
  newButton.type='button';
  newButton.className='secondary simple-new-registration';
  newButton.textContent='＋ 新しい投稿を始める';
  newButton.addEventListener('click',()=>resetVisibleWork('manual'));
  head?.appendChild(newButton);
}

let workspace=document.querySelector('#simple-register-workspace');
if(!workspace){
  workspace=document.createElement('div');
  workspace.id='simple-register-workspace';
  workspace.className='simple-register-workspace';
  workspace.innerHTML='<div class="simple-university-column"></div><section class="simple-photo-column"><div class="simple-photo-column-head"><span>STEP 2</span><div><h2>写真を確認・追加</h2><p>写真は最大9枚。実画面プレビューで掲載イメージを確認できます。</p></div></div></section>';
  (progress||batch.querySelector(':scope > .muted'))?.insertAdjacentElement('afterend',workspace);
}
const left=workspace.querySelector('.simple-university-column');
const right=workspace.querySelector('.simple-photo-column');

function compactModeSwitch(mode){
  if(!mode)return;
  const step=mode.querySelector('.mode-heading .step');
  const title=mode.querySelector('.mode-heading h2');
  setText(step,'登録方法');
  setText(title,'通常は1大学ずつ登録');
  const single=mode.querySelector('#mode-single');
  const batchButton=mode.querySelector('#mode-batch');
  setText(single?.querySelector('small'),'1校の写真を登録');
  setText(batchButton?.querySelector('small'),'必要なときだけ');
}

function refreshPreviewButton(){
  const button=document.querySelector('#open-real-preview');
  const status=document.querySelector('#real-preview-status');
  if(!button||!status)return;
  const count=document.querySelectorAll('#existing-photo-choice .main-photo-choice-card').length;
  if(!select.value){button.disabled=true;setText(status,'大学を選ぶとプレビューできます。');return;}
  if(!count){button.disabled=true;setText(status,'写真を確認・追加するとプレビューできます。');return;}
  if(count>9){button.disabled=true;setText(status,`写真は9枚までです（現在${count}枚）。`);return;}
  button.disabled=false;
  setText(status,`現在の${count}枚で大学ページを確認できます。`);
}

function placeWorkspace(){
  if(!workspace.isConnected)(progress||batch.querySelector(':scope > .muted'))?.insertAdjacentElement('afterend',workspace);
  const university=document.querySelector('.university-first');
  const mode=document.querySelector('#registration-mode-switch');
  const existing=document.querySelector('#existing-photo-choice');
  const add=document.querySelector('#simple-add-photo-step');
  const summary=document.querySelector('.batch-summary');
  const preview=document.querySelector('#real-page-preview');
  compactModeSwitch(mode);
  if(university&&university.parentElement!==left)left.appendChild(university);
  if(existing&&university&&existing.parentElement!==university)university.appendChild(existing);
  if(mode&&mode.parentElement!==left)left.appendChild(mode);
  const headRight=right.querySelector('.simple-photo-column-head');
  let anchor=headRight;
  for(const node of [preview,add,summary,list]){
    if(!node)continue;
    if(node.parentElement!==right||anchor.nextElementSibling!==node)anchor.insertAdjacentElement('afterend',node);
    anchor=node;
  }
  refreshPreviewButton();
}

// Avoid observing the whole batch subtree. Multiple legacy layout observers used
// to react to each other's DOM moves and could starve university-list initialization.
select.addEventListener('change',()=>setTimeout(()=>{placeWorkspace();refreshPreviewButton();},0));
document.addEventListener('click',event=>{
  if(event.target.closest?.('.main-photo-choice-card,.photo-list-delete,.remove-item,.photo-main-button'))setTimeout(refreshPreviewButton,0);
},true);
new MutationObserver(()=>setTimeout(refreshPreviewButton,0)).observe(list,{childList:true});
// Existing-photo cards arrive asynchronously after a university is selected.
// Re-evaluate preview readiness when those cards are mounted; otherwise the
// button can remain disabled depending on registry/network timing.
const existingChoices=document.querySelector('#existing-photo-choice');
if(existingChoices)new MutationObserver(()=>setTimeout(refreshPreviewButton,0)).observe(existingChoices,{childList:true,subtree:true});
placeWorkspace();
setTimeout(placeWorkspace,250);
setTimeout(placeWorkspace,900);
})();
