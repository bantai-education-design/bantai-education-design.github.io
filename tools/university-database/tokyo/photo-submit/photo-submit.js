(()=>{
'use strict';
const selected=document.querySelector('#selected-university');
const pageTitle=document.querySelector('#page-title');
const loading=document.querySelector('#receiver-loading');
const unavailable=document.querySelector('#receiver-unavailable');
const host=document.querySelector('#receiver-host');
const manual=document.querySelector('#manual-university');
const manualInput=document.querySelector('#university-name-input');
const manualButton=document.querySelector('#university-continue');
const manualStatus=document.querySelector('#manual-status');

const params=new URLSearchParams(location.search);
let university=(params.get('university')||'').trim();
let universityId=(params.get('university_id')||'').trim();
let receiverConfig=null;

function setUniversity(){
  const hasUniversity=!!university;
  selected.textContent=hasUniversity?university:'大学名を入力してください';
  pageTitle.textContent=hasUniversity?`${university}へ写真を送る`:'大学写真を送る';
  if(manual)manual.hidden=hasUniversity;
}

function buildEmbedUrl(config){
  const url=new URL(config.embed_url);
  if(university)url.searchParams.set(config.university_param||'university',university);
  if(universityId)url.searchParams.set(config.university_id_param||'university_id',universityId);
  return url.toString();
}

function showUnavailable(message){
  loading.hidden=true;
  host.hidden=true;
  unavailable.hidden=false;
  const p=unavailable.querySelector('p');
  if(message&&p)p.textContent=message;
}

function showManual(){
  loading.hidden=true;
  host.hidden=true;
  unavailable.hidden=true;
  if(manual)manual.hidden=false;
}

function mountReceiver(config){
  if(!university){
    showManual();
    return;
  }
  const frame=document.createElement('iframe');
  frame.className='provider-frame';
  frame.title=`${university} 写真投稿フォーム`;
  frame.loading='eager';
  frame.referrerPolicy='strict-origin-when-cross-origin';
  frame.src=buildEmbedUrl(config);
  host.replaceChildren(frame);
  host.hidden=false;
  unavailable.hidden=true;
  loading.hidden=true;
}

function submitUniversity(){
  const value=(manualInput?.value||'').trim();
  if(!value){
    if(manualStatus)manualStatus.textContent='大学名を入力してください。';
    manualInput?.focus();
    return;
  }
  university=value;
  universityId='';
  if(manualStatus)manualStatus.textContent='';
  setUniversity();
  if(receiverConfig)mountReceiver(receiverConfig);
}

manualButton?.addEventListener('click',submitUniversity);
manualInput?.addEventListener('keydown',event=>{
  if(event.key==='Enter'){
    event.preventDefault();
    submitUniversity();
  }
});

setUniversity();
fetch('receiver-config.json',{cache:'no-store'})
  .then(r=>r.ok?r.json():Promise.reject(new Error('config')))
  .then(config=>{
    const enabled=config.enabled===true;
    const provider=config.provider==='jotform';
    const secure=/^https:\/\/(form\.)?jotform\.com\//.test(config.embed_url||'');
    if(enabled&&provider&&secure){
      receiverConfig=config;
      mountReceiver(config);
    }else{
      showUnavailable();
    }
  })
  .catch(()=>showUnavailable('写真受付の設定を読み込めませんでした。しばらくしてからもう一度お試しください。'));
})();
