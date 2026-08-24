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
if(head)head.textContent='大学を選んで写真を登録する';
if(intro)intro.textContent='大学を1校選ぶだけで、登録済み写真を確認し、新しい写真を追加できます。';
if(title)title.textContent='STEP 1　大学を選ぶ';
if(titleSmall)titleSmall.textContent='大学を選択すると、これまでの写真が下に表示されます';
if(selectLabel){
  const text=[...selectLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='登録する大学を選択\n';
}
if(addButton)addButton.textContent='STEP 3　この大学に写真を追加';
if(searchLabel){
  const text=[...searchLabel.childNodes].find(n=>n.nodeType===Node.TEXT_NODE);
  if(text)text.nodeValue='大学名で絞り込み（任意）\n';
}
function update(){
  const option=select?.selectedOptions?.[0];
  const selected=!!select?.value;
  if(status){
    status.textContent=selected
      ? `${option?.textContent||'大学'}を選択中。既存写真を確認して、必要なら写真を追加してください。`
      : 'まず上の一覧から大学を1校選んでください。';
  }
  university?.classList.toggle('simple-university-selected',selected);
}
select?.addEventListener('change',()=>queueMicrotask(update));
new MutationObserver(update).observe(select,{childList:true,subtree:true});
update();
})();
