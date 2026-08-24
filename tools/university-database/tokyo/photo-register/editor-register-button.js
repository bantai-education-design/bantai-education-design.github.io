(()=>{
'use strict';
const controls=document.querySelector('#photo-editor .controls');
const generate=document.querySelector('#generate-batch');
const exportPanel=document.querySelector('.export-panel');
const firstSelect=document.querySelector('#university-first-select');
const list=document.querySelector('#batch-list');
const batch=document.querySelector('.batch');
const universityFirst=document.querySelector('.university-first');
const universityStatus=document.querySelector('#university-first-status');
if(!controls||!generate||!exportPanel||!firstSelect||!list||!batch||!universityFirst)return;

let ownerRegistry=null;
let baseRegistry=null;
let currentUniversityId='';
let currentRecord=null;
let existingPhotos=[];
let choice={type:'new',key:''};

window.__universityPhotoMainChoice={
  getChoice:()=>({...choice}),
  getExistingRecord:()=>currentRecord,
  getExistingPhotos:()=>existingPhotos.map(x=>({...x}))
};

async function loadRegistries(){
  if(ownerRegistry&&baseRegistry)return {ownerRegistry,baseRegistry};
  const [ownerRes,baseRes]=await Promise.all([
    fetch('../data/user-photo-overrides.json',{cache:'no-store'}).catch(()=>null),
    fetch('../data/university-images.json',{cache:'no-store'}).catch(()=>null)
  ]);
  try{ownerRegistry=ownerRes?.ok?await ownerRes.json():{records:{}};}catch(_e){ownerRegistry={records:{}};}
  try{baseRegistry=baseRes?.ok?await baseRes.json():{images:{}};}catch(_e){baseRegistry={images:{}};}
  return {ownerRegistry,baseRegistry};
}

function entriesFromRecord(record,origin,defaultRole='sub'){
  if(!record)return [];
  const candidates=[];
  if(record.image_url)candidates.push({...record,role:record.role||defaultRole});
  if(Array.isArray(record.gallery))candidates.push(...record.gallery);
  if(Array.isArray(record.images))candidates.push(...record.images);
  return candidates.map((item,index)=>({
    image_url:item?.image_url||item?.source_url||'',
    alt:item?.alt||record.alt||record.university_name||`登録済み写真${index+1}`,
    label:item?.label||item?.caption||(origin==='owner'?(index===0?'現在の登録写真':`登録済み写真${index+1}`):(index===0?'これまでの公開写真':`公開写真${index+1}`)),
    role:item?.role||(index===0?defaultRole:'sub'),
    origin
  })).filter(x=>x.image_url);
}

function collectExistingPhotos(ownerRecord,baseRecord){
  const owner=entriesFromRecord(ownerRecord,'owner','main');
  const base=entriesFromRecord(baseRecord,'base',owner.length?'sub':'main');
  const seen=new Set();
  return [...owner,...base].filter(item=>{
    if(seen.has(item.image_url))return false;
    seen.add(item.image_url);
    return true;
  });
}

function displayUrl(url){return /^(?:https?:|data:|blob:)/i.test(url)?url:`../${url}`;}

function ensureChoiceBox(){
  let box=document.querySelector('#existing-photo-choice');
  if(box)return box;
  box=document.createElement('section');
  box.id='existing-photo-choice';
  box.className='existing-photo-choice university-photo-picker';
  if(universityStatus){universityStatus.insertAdjacentElement('afterend',box);}else{universityFirst.appendChild(box);}
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

function makeCard({type,key='',src,alt,title,active,origin}){
  const role=active?'★ メイン':'サブ';
  const usage=active?'一覧カード＋詳細背景':'詳細ページのサムネイル';
  return `<button type="button" class="main-photo-choice-card${active?' active':''}" data-main-type="${type}"${key?` data-main-key="${escapeAttr(key)}"`:''} aria-pressed="${active}" aria-label="${escapeAttr(title)}を${active?'メイン写真':'メイン写真に選択'}"><span class="main-photo-choice-image"><img src="${escapeAttr(src)}" alt="${escapeAttr(alt)}"><span class="main-photo-check ${active?'main':'sub'}">${role}</span></span><strong>${escapeAttr(title)}</strong><small>${escapeAttr(origin)}・${usage}</small></button>`;
}

function renderChoices(){
  const box=ensureChoiceBox();
  const rows=[...list.querySelectorAll('.batch-row')];
  box.hidden=false;
  const universitySelected=!!firstSelect.value;

  if(!universitySelected){
    box.innerHTML=`<div class="existing-photo-title"><span class="step">写真の役割</span><strong>大学を選ぶと、ここにこれまでの写真が表示されます</strong><small>表示された写真をクリックして「★ メイン」を1枚選びます。ほかは自動で「サブ」になります。</small></div><div class="main-photo-choice-empty">まず上の大学名を選択してください</div>`;
    return;
  }

  const cards=[];
  for(const photo of existingPhotos){
    const key=photo.image_url;
    cards.push(makeCard({
      type:'existing',
      key,
      src:displayUrl(photo.image_url),
      alt:photo.alt,
      title:photo.label,
      origin:photo.origin==='owner'?'撮影者提供・現在登録済み':'従来の公開画像台帳',
      active:choice.type==='existing'&&choice.key===key
    }));
  }

  for(const row of rows){
    const key=row.dataset.key||'';
    const img=row.querySelector('.thumb img');
    if(!img?.src)continue;
    const filename=row.querySelector('.batch-main strong')?.textContent?.trim()||'今回追加した写真';
    cards.push(makeCard({
      type:'new',key,src:img.src,alt:filename,title:filename,origin:'今回追加',
      active:choice.type==='new'&&choice.key===key
    }));
  }

  const selectedName=firstSelect.options[firstSelect.selectedIndex]?.textContent?.trim()||'';
  if(!cards.length){
    box.innerHTML=`<div class="existing-photo-title"><span class="step">写真の役割</span><strong>${escapeAttr(selectedName)}：登録済み写真はありません</strong><small>新しい写真を追加すると、ここで「★ メイン」と「サブ」を選べます。</small></div><div class="main-photo-choice-empty">「この大学の写真を追加」から写真を入れてください</div>`;
    return;
  }

  box.innerHTML=`<div class="existing-photo-title"><span class="step">写真の役割</span><strong>${escapeAttr(selectedName)}：これまでの写真＋今回写真</strong><small>写真を1枚クリックしてください。1枚だけが「★ メイン」、それ以外は「サブ」です。</small></div><div class="main-photo-choice-grid">${cards.join('')}</div>`;
  for(const card of box.querySelectorAll('.main-photo-choice-card')){
    card.addEventListener('click',()=>selectChoice(card.dataset.mainType,card.dataset.mainKey||''));
  }
  syncLegacyButtons();
}

async function refreshUniversity(){
  const id=firstSelect.value;
  if(id===currentUniversityId)return;
  currentUniversityId=id;
  const {ownerRegistry:owners,baseRegistry:bases}=await loadRegistries();
  const ownerRecord=id?(owners.records?.[id]||null):null;
  const baseRecord=id?(bases.images?.[id]||null):null;
  currentRecord=ownerRecord||baseRecord||null;
  existingPhotos=collectExistingPhotos(ownerRecord,baseRecord);
  if(existingPhotos.length){
    const preferred=existingPhotos.find(x=>x.role==='main')||existingPhotos[0];
    choice={type:'existing',key:preferred.image_url};
  }else{
    const first=list.querySelector('.batch-row');
    choice={type:'new',key:first?.dataset.key||''};
  }
  renderChoices();
}

firstSelect.addEventListener('change',()=>{currentUniversityId='';refreshUniversity();});

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
    if(!choice.key&&rows.length&&!existingPhotos.length)choice={type:'new',key:rows[0].dataset.key||''};
  }
  renderChoices();
}).observe(list,{childList:true});

if(!document.querySelector('#finish-edit-register')){
  const wrap=document.createElement('div');
  wrap.className='finish-edit-register-wrap';
  wrap.innerHTML=`<button id="finish-edit-register" class="primary finish-edit-register" type="button">編集を終えて登録</button><small>現在の補正内容でSTEP 3へ進み、登録パッケージを作ります。</small>`;
  controls.appendChild(wrap);
  wrap.querySelector('#finish-edit-register').addEventListener('click',()=>{
    exportPanel.scrollIntoView({behavior:'smooth',block:'start'});
    exportPanel.classList.add('register-target');
    setTimeout(()=>exportPanel.classList.remove('register-target'),1600);
    if(!generate.disabled){setTimeout(()=>generate.click(),250);}else{wrap.querySelector('small').textContent='大学・写真の割り当てを確認してください。登録可能になるとSTEP 3の生成を開始します。';}
  });
}

renderChoices();
refreshUniversity();
})();
