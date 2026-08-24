(()=>{
'use strict';
const list=document.querySelector('#batch-list');
const firstSelect=document.querySelector('#university-first-select');
const batch=document.querySelector('.batch');
if(!list||!firstSelect||!batch)return;
let mainKey='';
let channel=null;

function rows(){return [...list.querySelectorAll('.batch-row')];}
function ensurePreviewUi(){
  if(document.querySelector('#real-page-preview'))return;
  const box=document.createElement('section');
  box.id='real-page-preview';
  box.className='real-page-preview';
  box.innerHTML=`<div><span class="step">配置確認</span><h2>実画面で写真配置を確認</h2><p>1〜5枚まで。★メイン1枚を背景、残り最大4枚を小型サムネイルで表示します。ここでは本番登録しません。</p></div><button id="open-real-preview" type="button" class="primary" disabled>大学ページで実画面プレビュー</button><small id="real-preview-status">大学と写真を選ぶとプレビューできます。</small>`;
  batch.appendChild(box);
  const style=document.createElement('style');
  style.textContent=`.real-page-preview{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:center;margin-top:18px;padding:16px;border:1px solid #4b4025;border-radius:14px;background:linear-gradient(135deg,#12130f,#0c0e13)}.real-page-preview h2{margin:4px 0 6px}.real-page-preview p{margin:0;color:var(--muted);font-size:.82rem;line-height:1.6}.real-page-preview small{grid-column:1/-1;color:#b9bdc8}.photo-main-button{border-color:#65562f!important;color:#ecd27c!important;background:#17140b!important;white-space:nowrap}.photo-main-button.active{background:linear-gradient(135deg,#b88a2b,#e0bd65)!important;color:#0b0b0c!important;border-color:#e8c976!important}.batch-row .batch-actions{flex-wrap:wrap}@media(max-width:800px){.real-page-preview{grid-template-columns:1fr}.real-page-preview button{width:100%}}`;
  document.head.appendChild(style);
  box.querySelector('#open-real-preview').addEventListener('click',openPreview);
}
function enhanceRows(){
  const all=rows();
  if(all.length&&!mainKey)mainKey=all[0].dataset.key||'';
  if(mainKey&&!all.some(r=>r.dataset.key===mainKey))mainKey=all[0]?.dataset.key||'';
  for(const row of all){
    const actions=row.querySelector('.batch-actions');if(!actions)continue;
    let btn=actions.querySelector('.photo-main-button');
    if(!btn){btn=document.createElement('button');btn.type='button';btn.className='photo-main-button';btn.addEventListener('click',()=>{mainKey=row.dataset.key||'';enhanceRows();syncPreviewState();});actions.prepend(btn);}
    const active=(row.dataset.key||'')===mainKey;btn.classList.toggle('active',active);btn.textContent=active?'★ メイン写真':'☆ メインにする';
  }
  syncPreviewState();
}
function syncPreviewState(){
  ensurePreviewUi();
  const button=document.querySelector('#open-real-preview'),status=document.querySelector('#real-preview-status');
  const all=rows();const universityId=firstSelect.value;
  if(!all.length){button.disabled=true;status.textContent='写真を1〜5枚追加してください。';return;}
  if(all.length>5){button.disabled=true;status.textContent=`現在${all.length}枚です。実画面プレビューは1大学につき5枚までにしてください。`;return;}
  if(!universityId){button.disabled=true;status.textContent='対象大学を選択してください。';return;}
  button.disabled=false;status.textContent=`${all.length}枚をプレビューします。★メイン1枚＋サムネイル${Math.max(0,all.length-1)}枚。`;
}
async function rowBlob(row){
  const img=row.querySelector('.thumb img');if(!img?.src)throw new Error('写真を取得できません');
  const res=await fetch(img.src);if(!res.ok)throw new Error('写真を取得できません');return res.blob();
}
async function openPreview(){
  const all=rows().slice(0,5),universityId=firstSelect.value;if(!all.length||!universityId)return;
  const button=document.querySelector('#open-real-preview'),status=document.querySelector('#real-preview-status');button.disabled=true;status.textContent='実画面プレビューを準備しています…';
  try{
    const photos=[];for(const row of all)photos.push({blob:await rowBlob(row),main:(row.dataset.key||'')===mainKey});
    if(!photos.some(x=>x.main))photos[0].main=true;
    const token=(crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`).replace(/[^a-zA-Z0-9-]/g,'');
    channel?.close();channel=new BroadcastChannel(`university-photo-preview-${token}`);
    const target=`../?photo_preview_token=${encodeURIComponent(token)}&university=${encodeURIComponent(universityId)}`;
    const win=window.open(target,'_blank');
    if(!win){throw new Error('プレビュー画面を開けませんでした。ポップアップを許可してください。');}
    let sent=0;const send=()=>{if(sent++>10)return;channel.postMessage({universityId,photos});setTimeout(send,500);};
    channel.onmessage=e=>{if(e.data?.type==='receiver-ready'||e.data?.type==='ready'){channel.postMessage({universityId,photos});if(e.data?.type==='ready'){status.textContent='実画面プレビューを開きました。本番登録はまだ行っていません。';button.disabled=false;}}};
    send();
  }catch(err){console.error(err);status.textContent=err.message||'プレビュー準備に失敗しました。';button.disabled=false;}
}
ensurePreviewUi();
new MutationObserver(()=>queueMicrotask(enhanceRows)).observe(list,{childList:true,subtree:true});
firstSelect.addEventListener('change',syncPreviewState);
enhanceRows();
})();
