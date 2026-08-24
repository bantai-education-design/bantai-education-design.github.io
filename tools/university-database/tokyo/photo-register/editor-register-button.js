(()=>{
'use strict';
const controls=document.querySelector('#photo-editor .controls');
const generate=document.querySelector('#generate-batch');
const exportPanel=document.querySelector('.export-panel');
const firstSelect=document.querySelector('#university-first-select');
const list=document.querySelector('#batch-list');
const batch=document.querySelector('.batch');
if(!controls||!generate||!exportPanel||!firstSelect||!list||!batch)return;

let registry=null;
let currentUniversityId='';
let currentRecord=null;
let choice={type:'new',key:''};

window.__universityPhotoMainChoice={
  getChoice:()=>({...choice}),
  getExistingRecord:()=>currentRecord
};

async function loadRegistry(){
  if(registry)return registry;
  try{
    const res=await fetch('../data/user-photo-overrides.json',{cache:'no-store'});
    registry=res.ok?await res.json():{records:{}};
  }catch(_e){registry={records:{}};}
  return registry;
}

function ensureExistingBox(){
  let box=document.querySelector('#existing-photo-choice');
  if(box)return box;
  box=document.createElement('section');
  box.id='existing-photo-choice';
  box.className='existing-photo-choice';
  box.hidden=true;
  const summary=document.querySelector('.batch-summary');
  batch.insertBefore(box,summary||list);
  return box;
}

function syncNewButtons(){
  const rows=[...list.querySelectorAll('.batch-row')];
  for(const row of rows){
    const btn=row.querySelector('.photo-main-button');
    if(!btn)continue;
    const active=choice.type==='new'&&choice.key===(row.dataset.key||'');
    btn.classList.toggle('active',active);
    btn.textContent=active?'★ メイン写真':'☆ メインにする';
  }
}

function renderExisting(){
  const box=ensureExistingBox();
  if(!currentRecord){
    box.hidden=true;
    box.innerHTML='';
    syncNewButtons();
    return;
  }
  const active=choice.type==='existing';
  const src=`../${currentRecord.image_url}`;
  const alt=String(currentRecord.alt||currentRecord.university_name||'現在の登録写真').replace(/"/g,'&quot;');
  box.hidden=false;
  box.innerHTML=`<div class="existing-photo-title"><span class="step">メイン写真を選択</span><strong>既存写真または今回追加した写真から1枚選べます</strong></div><div class="existing-photo-card"><img src="${src}" alt="${alt}"><div class="existing-photo-copy"><strong>現在の登録写真</strong><small>${currentRecord.university_name||''}<br>この写真をメインのまま残すこともできます。</small></div><button id="existing-main-button" class="secondary existing-main-button${active?' active':''}" type="button">${active?'★ 現在の写真をメイン':'☆ 現在の写真をメインにする'}</button></div>`;
  box.querySelector('#existing-main-button').addEventListener('click',()=>{
    choice={type:'existing',key:''};
    renderExisting();
    syncNewButtons();
  });
  syncNewButtons();
}

async function refreshUniversity(){
  const id=firstSelect.value;
  if(id===currentUniversityId)return;
  currentUniversityId=id;
  const data=await loadRegistry();
  currentRecord=id?(data.records?.[id]||null):null;
  if(currentRecord){
    choice={type:'existing',key:''};
  }else{
    const first=list.querySelector('.batch-row');
    choice={type:'new',key:first?.dataset.key||''};
  }
  renderExisting();
}

firstSelect.addEventListener('change',()=>{
  currentUniversityId='';
  refreshUniversity();
});

document.addEventListener('click',event=>{
  const btn=event.target.closest?.('.photo-main-button');
  if(!btn)return;
  const row=btn.closest('.batch-row');
  if(!row)return;
  queueMicrotask(()=>{
    choice={type:'new',key:row.dataset.key||''};
    renderExisting();
    syncNewButtons();
  });
},true);

new MutationObserver(()=>{
  const rows=[...list.querySelectorAll('.batch-row')];
  if(choice.type==='new'){
    if(choice.key&&!rows.some(r=>(r.dataset.key||'')===choice.key))choice={type:'new',key:rows[0]?.dataset.key||''};
    if(!choice.key&&rows.length&&!currentRecord)choice={type:'new',key:rows[0].dataset.key||''};
  }
  renderExisting();
}).observe(list,{childList:true});

if(!document.querySelector('#finish-edit-register')){
  const wrap=document.createElement('div');
  wrap.className='finish-edit-register-wrap';
  wrap.innerHTML=`<button id="finish-edit-register" class="primary finish-edit-register" type="button">編集を終えて登録</button><small>現在の補正内容でSTEP 3へ進み、登録パッケージを作ります。</small>`;
  controls.appendChild(wrap);
  const button=wrap.querySelector('#finish-edit-register');
  button.addEventListener('click',()=>{
    exportPanel.scrollIntoView({behavior:'smooth',block:'start'});
    exportPanel.classList.add('register-target');
    setTimeout(()=>exportPanel.classList.remove('register-target'),1600);
    if(!generate.disabled){
      setTimeout(()=>generate.click(),250);
    }else{
      wrap.querySelector('small').textContent='大学・写真の割り当てを確認してください。登録可能になるとSTEP 3の生成を開始します。';
    }
  });
}

refreshUniversity();
})();
