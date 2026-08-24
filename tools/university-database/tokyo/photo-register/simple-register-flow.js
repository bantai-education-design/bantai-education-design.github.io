(()=>{
'use strict';
const batch=document.querySelector('.batch');
const head=batch?.querySelector('.section-head h2');
const intro=batch?.querySelector(':scope > .muted');
const university=document.querySelector('.university-first');
const title=document.querySelector('#university-first-title');
const titleSmall=title?.parentElement?.querySelector('small');
const searchLabel=document.querySelector('label:has(#university-first-search)');
const search=document.querySelector('#university-first-search');
const selectLabel=document.querySelector('label:has(#university-first-select)');
const select=document.querySelector('#university-first-select');
const addButton=document.querySelector('#university-first-photo-button');
const uploadZone=document.querySelector('#drop-zone');
const mainFile=document.querySelector('#photo-input');
const status=document.querySelector('#university-first-status');
if(!batch||!university||!search||!select||!addButton||!uploadZone||!mainFile)return;

if(head)head.textContent='大学を選んで写真を登録する';
if(intro)intro.textContent='大学名を入力するか一覧から1校選ぶ → 既存写真を確認 → 写真を追加、の順です。';
if(title)title.textContent='STEP 1　大学を選ぶ';
if(titleSmall)titleSmall.textContent='文字入力または一覧のどちらか一方で選べます';
if(searchLabel){
  searchLabel.hidden=false;
  const text=[...searchLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='大学名を入力して検索\n';
}
search.placeholder='例：亜細亜大学';
if(selectLabel){
  const text=[...selectLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='または一覧から選択\n';
}

let addStep=document.querySelector('#simple-add-photo-step');
if(!addStep){
  addStep=document.createElement('section');
  addStep.id='simple-add-photo-step';
  addStep.className='simple-add-photo-step';
  addStep.innerHTML='<div class="simple-step-heading"><span>STEP 3</span><strong>写真を追加する</strong><small>ドラッグ＆ドロップでもファイル選択でも追加できます</small></div>';
}

uploadZone.classList.add('simple-upload-zone');
uploadZone.setAttribute('aria-label','写真をドラッグ＆ドロップ、またはクリックしてファイルを選択');
const uploadTitle=uploadZone.querySelector('strong');
const uploadDescription=uploadZone.querySelector(':scope > span:not(.simple-file-picker)');
const uploadNote=uploadZone.querySelector('small');
if(uploadTitle)uploadTitle.textContent='ここに写真をドロップ';
if(uploadDescription)uploadDescription.textContent='または、同じ枠からファイルを選択できます';
if(uploadNote)uploadNote.textContent='JPEG / PNG / WebP ・ 1〜5枚';
let filePicker=uploadZone.querySelector('.simple-file-picker');
if(!filePicker){
  filePicker=document.createElement('span');
  filePicker.className='simple-file-picker';
  filePicker.textContent='ファイルを選択';
  uploadNote?.insertAdjacentElement('beforebegin',filePicker);
}
if(uploadZone.parentElement!==addStep)addStep.appendChild(uploadZone);

// Keep the legacy university-first file control available to the existing controller/tests,
// but do not expose a second photo-add UI to the user.
addButton.textContent='この大学に写真を追加';
addButton.hidden=true;
addButton.classList.add('simple-compat-photo-button');
if(addButton.parentElement!==addStep)addStep.appendChild(addButton);

function existingBox(){return document.querySelector('#existing-photo-choice');}
function placeAfter(anchor,node){
  if(!anchor||!node||anchor.nextElementSibling===node)return false;
  anchor.insertAdjacentElement('afterend',node);
  return true;
}
function enforceOrder(){
  let moved=false;
  if(intro&&intro.nextElementSibling!==university){intro.insertAdjacentElement('afterend',university);moved=true;}
  const existing=existingBox();
  if(existing){
    if(existing.parentElement!==university){university.appendChild(existing);moved=true;}
    if(status&&status.nextElementSibling!==existing){status.insertAdjacentElement('afterend',existing);moved=true;}
  }
  moved=placeAfter(university,addStep)||moved;
  return moved;
}

function update(){
  const option=select.selectedOptions?.[0];
  const selected=!!select.value;
  if(status){
    status.textContent=selected
      ? `${option?.textContent||'大学'}を選択しました。次にSTEP 2で既存写真を確認してください。`
      : '大学名を入力するか、一覧から1校選んでください。';
  }
  university.classList.toggle('simple-university-selected',selected);
  addButton.disabled=!selected;
  mainFile.disabled=!selected;
  addStep.classList.toggle('is-disabled',!selected);
  uploadZone.setAttribute('aria-disabled',String(!selected));
  enforceOrder();
}

select.addEventListener('change',()=>queueMicrotask(update));
new MutationObserver(()=>queueMicrotask(update)).observe(select,{childList:true,subtree:true});
const orderObserver=new MutationObserver(()=>{
  queueMicrotask(()=>{
    if(!enforceOrder()&&existingBox())orderObserver.disconnect();
  });
});
orderObserver.observe(batch,{childList:true,subtree:true});

enforceOrder();
update();
})();
