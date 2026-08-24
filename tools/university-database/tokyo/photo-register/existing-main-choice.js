(()=>{
'use strict';
const firstSelect=document.querySelector('#university-first-select');
const list=document.querySelector('#batch-list');
const batch=document.querySelector('.batch');
if(!firstSelect||!list||!batch)return;

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

function ensureBox(){
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

function setNewButtonState(){
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
  const box=ensureBox();
  if(!currentRecord){box.hidden=true;box.innerHTML='';setNewButtonState();return;}
  const active=choice.type==='existing';
  const src=`../${currentRecord.image_url}`;
  box.hidden=false;
  box.innerHTML=`<div class="existing-photo-title"><span class="step">メイン写真を選択</span><strong>現在の写真と今回追加した写真から1枚選べます</strong></div><div class="existing-photo-card"><img src="${src}" alt="${(currentRecord.alt||currentRecord.university_name||'現在の登録写真').replace(/"/g,'&quot;')}"><div class="existing-photo-copy"><strong>現在の登録写真</strong><small>${currentRecord.university_name||''}<br>この写真をそのままメインに残すこともできます。</small></div><button id="existing-main-button" class="secondary existing-main-button${active?' active':''}" type="button">${active?'★ 現在の写真をメイン':'☆ 現在の写真をメインにする'}</button></div>`;
  box.querySelector('#existing-main-button').addEventListener('click',()=>{
    choice={type:'existing',key:''};
    renderExisting();
    setNewButtonState();
  });
  setNewButtonState();
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

firstSelect.addEventListener('change',()=>{currentUniversityId='';refreshUniversity();});

document.addEventListener('click',event=>{
  const btn=event.target.closest?.('.photo-main-button');
  if(!btn)return;
  const row=btn.closest('.batch-row');
  if(!row)return;
  queueMicrotask(()=>{
    choice={type:'new',key:row.dataset.key||''};
    renderExisting();
    setNewButtonState();
  });
},true);

new MutationObserver(()=>{
  if(choice.type==='new'){
    const rows=[...list.querySelectorAll('.batch-row')];
    if(choice.key&&!rows.some(r=>(r.dataset.key||'')===choice.key))choice={type:'new',key:rows[0]?.dataset.key||''};
    if(!choice.key&&rows.length&&!currentRecord)choice={type:'new',key:rows[0].dataset.key||''};
  }
  renderExisting();
}).observe(list,{childList:true});

refreshUniversity();
})();
