(()=>{
'use strict';
const batch=document.querySelector('.batch');
const head=batch?.querySelector('.section-head h2');
const intro=batch?.querySelector(':scope > .muted');
const university=document.querySelector('.university-first');
const title=document.querySelector('#university-first-title');
const titleSmall=title?.parentElement?.querySelector('small');
const selectLabel=document.querySelector('label:has(#university-first-select)');
const select=document.querySelector('#university-first-select');
const addButton=document.querySelector('#university-first-photo-button');
const status=document.querySelector('#university-first-status');
const searchLabel=document.querySelector('label:has(#university-first-search)');
if(!batch||!university||!select||!addButton)return;

if(head)head.textContent='大学を選んで写真を登録する';
if(intro)intro.textContent='上から順に、大学を選ぶ → 既存写真を確認 → 写真を追加、の3ステップです。';
if(title)title.textContent='STEP 1　大学を選ぶ';
if(titleSmall)titleSmall.textContent='ここで登録する大学を1校だけ選びます';
if(selectLabel){
  const text=[...selectLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='登録する大学\n';
}
if(searchLabel)searchLabel.hidden=true;

let addStep=document.querySelector('#simple-add-photo-step');
if(!addStep){
  addStep=document.createElement('section');
  addStep.id='simple-add-photo-step';
  addStep.className='simple-add-photo-step';
  addStep.innerHTML='<div class="simple-step-heading"><span>STEP 3</span><strong>写真を追加する</strong><small>必要なときだけ1〜5枚追加します</small></div>';
}
addButton.textContent='この大学に写真を追加';
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
    moved=placeAfter(university,existing)||moved;
    moved=placeAfter(existing,addStep)||moved;
  }else{
    moved=placeAfter(university,addStep)||moved;
  }
  return moved;
}

function update(){
  const option=select.selectedOptions?.[0];
  const selected=!!select.value;
  if(status){
    status.textContent=selected
      ? `${option?.textContent||'大学'}を選択しました。次にSTEP 2で既存写真を確認してください。`
      : 'この一覧から大学を1校選んでください。';
  }
  university.classList.toggle('simple-university-selected',selected);
  addButton.disabled=!selected;
  addStep.classList.toggle('is-disabled',!selected);
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
