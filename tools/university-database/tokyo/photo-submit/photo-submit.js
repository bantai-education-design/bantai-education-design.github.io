(()=>{
'use strict';
const selected=document.querySelector('#selected-university');
const pageTitle=document.querySelector('#page-title');
const loading=document.querySelector('#receiver-loading');
const unavailable=document.querySelector('#receiver-unavailable');
const host=document.querySelector('#receiver-host');

const params=new URLSearchParams(location.search);
const university=(params.get('university')||'').trim();
const universityId=(params.get('university_id')||'').trim();

function setUniversity(){
  selected.textContent=university||'大学名が指定されていません';
  pageTitle.textContent=university?`${university}へ写真を送る`:'大学写真を送る';
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

function mountReceiver(config){
  if(!university){
    showUnavailable('大学DBの各大学ページから「写真を送る」を開いてください。');
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

setUniversity();
fetch('receiver-config.json',{cache:'no-store'})
  .then(r=>r.ok?r.json():Promise.reject(new Error('config')))
  .then(config=>{
    const enabled=config.enabled===true;
    const provider=config.provider==='jotform';
    const secure=/^https:\/\//.test(config.embed_url||'');
    if(enabled&&provider&&secure){
      mountReceiver(config);
    }else{
      showUnavailable();
    }
  })
  .catch(()=>showUnavailable('写真受付の設定を読み込めませんでした。しばらくしてからもう一度お試しください。'));
})();
