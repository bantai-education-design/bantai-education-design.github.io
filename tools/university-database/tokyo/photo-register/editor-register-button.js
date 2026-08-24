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

function ensureChoiceBox(){
  let box=document.querySelector('#existing-photo-choice');
  if(box)return box;
  box=document.createElement('section');
  box.id='existing-photo-choice';
  box.className='existing-photo-choice';
  const previewBox=document.querySelector('#real-page-preview');
  if(previewBox){batch.insertBefore(box,previewBox);}else{list.insertAdjacentElement('afterend',box);}
  return box;
}

function syncLegacyButtons(){
  const rows=[...list.querySelectorAll('.batch-row')];
  for(const row of rows){
    const btn=row.querySelector('.photo-main-button');
    if(!btn)continue;
    const active=choice.type==='new'&&choice.key===(row.dataset.key||'');
    btn.classList.toggle('active',active);
    btn.textContent=active?'★ メイン':'サブ → メインにする';
  }
}

function escapeAttr(value){return String(value||'').replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function selectChoice(type,key=''){
  choice={type,key};
  renderChoices();
  syncLegacyButtons();
}

function makeCard({type,key='',src,alt,title,active}){
  const role=active?'★ メイン':'サブ';
  const usage=active?'一覧カード＋詳細背景':'詳細ページのサムネイル';
  return `<button type="button" class="main-photo-choice-card${active?' active':''}" data-main-type="${type}"${key?` data-main-key="${escapeAttr(key)}"`:''} aria-pressed="${active}" aria-label="${escapeAttr(title)}を${active?'メイン写真':'メイン写真に選択'}"><span class="main-photo-choice-image"><img src="${escapeAttr(src)}" alt="${escapeAttr(alt)}"><span class="main-photo-check ${active?'main':'sub'}">${role}</span></span><strong>${escapeAttr(title)}</strong><small>${usage}</small></button>`;
}

function renderChoices(){
  const box=ensureChoiceBox();
  const rows=[...list.querySelectorAll('.batch-row')];
  box.hidden=false;

  if(!currentRecord&&!rows.length){
    box.innerHTML=`<div class="existing-photo-title"><span class="step">STEP 1.5</span><strong>メイン写真・サブ写真を選ぶ</strong><small>大学と写真を選ぶと候補が並びます。1枚だけが「★ メイン」、残りはすべて「サブ」です。</small></div><div class="main-photo-choice-empty">まだ候補写真がありません</div>`;
    return;
  }

  const cards=[];
  if(currentRecord){
    cards.push(makeCard({
      type:'existing',
      src:`../${currentRecord.image_url}`,
      alt:currentRecord.alt||currentRecord.university_name||'現在の登録写真',
      title:'現在の登録写真',
      active:choice.type==='existing'
    }));
  }
  for(const row of rows){
    const key=row.dataset.key||'';
    const img=row.querySelector('.thumb img');
    if(!img?.src)continue;
    const filename=row.querySelector('.batch-main strong')?.textContent?.trim()||'今回追加した写真';
    cards.push(makeCard({
      type:'new',
      key,
      src:img.src,
      alt:filename,
      title:filename,
      active:choice.type==='new'&&choice.key===key
    }));
  }

  box.innerHTML=`<div class="existing-photo-title"><span class="step">STEP 1.5</span><strong>メイン写真・サブ写真を選ぶ</strong><small>写真を1枚クリックすると、その写真が「★ メイン」になります。ほかの写真は自動で「サブ」になります。</small></div><div class="main-photo-choice-grid">${cards.join('')}</div>`;
  for(const card of box.querySelectorAll('.main-photo-choice-card')){
    card.addEventListener('click',()=>{
      const type=card.dataset.mainType;
      selectChoice(type,type==='new'?(card.dataset.mainKey||''):'');
    });
  }
  syncLegacyButtons();
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
  renderChoices();
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
  queueMicrotask(()=>selectChoice('new',row.dataset.key||''));
},true);

new MutationObserver(()=>{
  const rows=[...list.querySelectorAll('.batch-row')];
  if(choice.type==='new'){
    if(choice.key&&!rows.some(r=>(r.dataset.key||'')===choice.key))choice={type:'new',key:rows[0]?.dataset.key||''};
    if(!choice.key&&rows.length&&!currentRecord)choice={type:'new',key:rows[0].dataset.key||''};
  }
  renderChoices();
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

renderChoices();
refreshUniversity();
})();
