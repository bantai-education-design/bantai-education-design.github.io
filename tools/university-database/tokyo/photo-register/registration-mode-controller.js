(()=>{
'use strict';
const $=s=>document.querySelector(s);
const singleBtn=$('#mode-single');
const batchBtn=$('#mode-batch');
const firstSearch=$('#university-first-search');
const firstSelect=$('#university-first-select');
const firstButton=$('#university-first-photo-button');
const batchList=$('#batch-list');
const modeStatus=$('#registration-mode-status');
const batchIntro=$('#batch-mode-intro');
if(!singleBtn||!batchBtn||!firstSearch||!firstSelect||!batchList||!modeStatus)return;

let mode='single';
const labelForSelected=()=>{
  const option=firstSelect.options[firstSelect.selectedIndex];
  return firstSelect.value&&option?option.textContent.trim():'';
};
function applySingleUniversity(){
  if(mode!=='single'||!firstSelect.value)return;
  for(const row of batchList.querySelectorAll('.batch-row')){
    const select=row.querySelector('.row-university');
    const search=row.querySelector('.row-university-search');
    if(!select||![...select.options].some(o=>o.value===firstSelect.value))continue;
    if(select.value!==firstSelect.value){
      select.value=firstSelect.value;
      select.dispatchEvent(new Event('change',{bubbles:true}));
    }
    if(search)search.value=labelForSelected();
  }
}
function renderMode(){
  document.body.dataset.registrationMode=mode;
  singleBtn.classList.toggle('active',mode==='single');
  batchBtn.classList.toggle('active',mode==='batch');
  singleBtn.setAttribute('aria-pressed',String(mode==='single'));
  batchBtn.setAttribute('aria-pressed',String(mode==='batch'));
  if(batchIntro)batchIntro.hidden=mode!=='batch';
  const label=labelForSelected();
  if(mode==='single'){
    modeStatus.innerHTML=label
      ? `<strong>${label}</strong> を編集中。追加した写真にはこの大学名を共通適用します。各写真ごとの大学入力は不要です。`
      : '大学を1回だけ指定してください。その後、同じ大学の写真を1〜5枚追加します。';
    if(firstButton)firstButton.textContent=label?'この大学の写真を追加':'大学を選んで写真を追加';
    applySingleUniversity();
  }else{
    modeStatus.textContent='複数大学を一括登録します。各写真の大学名を確認します。ファイル名に大学名・大学IDがあれば自動判定します。';
    if(firstButton)firstButton.textContent='この大学の写真を選ぶ';
  }
}
function setMode(next){mode=next;renderMode();}
singleBtn.addEventListener('click',()=>setMode('single'));
batchBtn.addEventListener('click',()=>setMode('batch'));
firstSelect.addEventListener('change',()=>queueMicrotask(renderMode));
firstSearch.addEventListener('change',()=>queueMicrotask(renderMode));
new MutationObserver(()=>queueMicrotask(()=>{if(mode==='single')applySingleUniversity();})).observe(batchList,{childList:true,subtree:true});
new MutationObserver(()=>queueMicrotask(renderMode)).observe(firstSelect,{childList:true,subtree:true});
renderMode();
})();
