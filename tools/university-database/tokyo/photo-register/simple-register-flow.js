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
const editor=document.querySelector('#photo-editor');
const editorStep=editor?.querySelector('.section-head .step');
const editorHeading=editor?.querySelector('.section-head h2');
if(!batch||!university||!search||!select||!addButton||!uploadZone||!mainFile)return;

if(head)head.textContent='大学写真を登録';
if(intro)intro.textContent='① 大学を選ぶ → ② 写真を確認・追加してメインを選ぶ → ③ 必要なら微調整 → ④ 登録。大学は最初の1回だけ選びます。';
if(title)title.textContent='STEP 1　大学を選ぶ';
if(titleSmall)titleSmall.textContent='文字入力または一覧のどちらか一方で選べます';
if(editorStep)editorStep.textContent='STEP 3';
if(editorHeading)editorHeading.textContent='必要なら写真を微調整';

let progress=document.querySelector('#simple-register-progress');
if(!progress){
  progress=document.createElement('ol');
  progress.id='simple-register-progress';
  progress.className='simple-register-progress';
  progress.innerHTML='<li data-step="1"><span>1</span><strong>大学</strong></li><li data-step="2"><span>2</span><strong>写真・メイン</strong></li><li data-step="3"><span>3</span><strong>微調整</strong></li><li data-step="4"><span>4</span><strong>登録</strong></li>';
  intro?.insertAdjacentElement('afterend',progress);
}

if(searchLabel){
  searchLabel.hidden=false;
  const text=[...searchLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='大学名を入力して検索\n';
}
search.placeholder='例：立教大学';
if(selectLabel){
  const text=[...selectLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='または一覧から選択\n';
}

let targetBanner=document.querySelector('#simple-current-university');
if(!targetBanner){
  targetBanner=document.createElement('div');
  targetBanner.id='simple-current-university';
  targetBanner.className='simple-current-university';
  targetBanner.innerHTML='<span>現在の登録先</span><strong>大学を選んでください</strong>';
  status?.insertAdjacentElement('afterend',targetBanner);
}

let addStep=document.querySelector('#simple-add-photo-step');
if(!addStep){
  addStep=document.createElement('section');
  addStep.id='simple-add-photo-step';
  addStep.className='simple-add-photo-step';
  addStep.innerHTML='<div class="simple-step-heading"><span>写真追加</span><strong>必要な写真を追加</strong><small>ドラッグ＆ドロップでもファイル選択でも追加できます</small></div>';
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

// Keep the legacy university-first file control available to existing code/tests,
// but expose only the single shared upload zone to the user.
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
  if(document.querySelector('#simple-register-workspace'))return false;
  let moved=false;
  if(progress&&progress.nextElementSibling!==university){progress.insertAdjacentElement('afterend',university);moved=true;}
  const existing=existingBox();
  if(existing){
    if(existing.parentElement!==university){university.appendChild(existing);moved=true;}
    if(targetBanner&&targetBanner.nextElementSibling!==existing){targetBanner.insertAdjacentElement('afterend',existing);moved=true;}
  }
  moved=placeAfter(university,addStep)||moved;
  return moved;
}

function updateProgress(selected,photoCount){
  const activeMain=!!document.querySelector('.main-photo-choice-card.active');
  const steps=[...progress.querySelectorAll('li')];
  const completed=[selected,selected&&(photoCount>0||document.querySelectorAll('.main-photo-choice-card[data-main-type="existing"]').length>0)&&activeMain,false,false];
  steps.forEach((item,index)=>{
    item.classList.toggle('done',!!completed[index]);
    item.classList.remove('current');
  });
  const current=!selected?0:!completed[1]?1:2;
  steps[current]?.classList.add('current');
}

function update(){
  const option=select.selectedOptions?.[0];
  const selected=!!select.value;
  const selectedName=option?.textContent?.trim()||'';
  const photoCount=document.querySelectorAll('#batch-list .batch-row').length;
  if(status){
    status.textContent=selected
      ? '登録先を確認して、下の写真を確認してください。'
      : '大学名を入力するか、一覧から1校選んでください。';
  }
  if(targetBanner){
    targetBanner.classList.toggle('is-selected',selected);
    targetBanner.querySelector('strong').textContent=selected?selectedName:'大学を選んでください';
  }
  university.classList.toggle('simple-university-selected',selected);
  addButton.disabled=!selected;
  mainFile.disabled=!selected;
  addStep.classList.toggle('is-disabled',!selected);
  uploadZone.setAttribute('aria-disabled',String(!selected));
  updateProgress(selected,photoCount);
  enforceOrder();
}

select.addEventListener('change',()=>queueMicrotask(update));
document.addEventListener('click',event=>{
  if(event.target.closest?.('.main-photo-choice-card')||event.target.closest?.('.remove-item')||event.target.closest?.('.photo-list-delete'))setTimeout(update,0);
},true);
new MutationObserver(()=>queueMicrotask(update)).observe(select,{childList:true,subtree:true});
new MutationObserver(()=>queueMicrotask(update)).observe(document.querySelector('#batch-list'),{childList:true,subtree:true});
const orderObserver=new MutationObserver(()=>{
  queueMicrotask(()=>{
    if(!enforceOrder()&&existingBox())orderObserver.disconnect();
  });
});
orderObserver.observe(batch,{childList:true,subtree:true});

enforceOrder();
update();
})();
