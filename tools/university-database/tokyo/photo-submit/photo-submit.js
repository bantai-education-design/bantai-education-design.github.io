(()=>{
'use strict';
const MAX_PHOTOS=9;
const selected=document.querySelector('#selected-university');
const picker=document.querySelector('#university-picker');
const nameInput=document.querySelector('#university-name');
const changeButton=document.querySelector('#change-university');
const filesInput=document.querySelector('#photo-files');
const list=document.querySelector('#photo-list');
const consent=document.querySelector('#consent');
const submit=document.querySelector('#submit-photo');
const status=document.querySelector('#submit-status');
const uploadCard=document.querySelector('.upload-card');
const thankYou=document.querySelector('#thank-you');
const pageTitle=document.querySelector('#page-title');

const params=new URLSearchParams(location.search);
let university=params.get('university')?.trim()||'';
const universityId=params.get('university_id')?.trim()||'';
let chosenFiles=[];

function escapeText(value){return String(value||'').replace(/[<>]/g,'');}
function showUniversity(){
  const label=university||'大学名を入力してください';
  selected.textContent=label;
  pageTitle.textContent=university?`${university}へ写真を送る`:'大学写真を送る';
  picker.hidden=!!university;
  changeButton.hidden=!university;
  updateState();
}
function updateState(){
  const ready=!!university&&chosenFiles.length>0&&chosenFiles.length<=MAX_PHOTOS&&consent.checked;
  submit.disabled=!ready;
  if(chosenFiles.length>MAX_PHOTOS){
    status.textContent=`写真は最大${MAX_PHOTOS}枚です。`;
    status.className='status error';
  }else if(!university){
    status.textContent='大学名を確認してください。';
    status.className='status';
  }else if(chosenFiles.length===0){
    status.textContent='写真を1枚以上選んでください。';
    status.className='status';
  }else if(!consent.checked){
    status.textContent='掲載許諾を確認してください。';
    status.className='status';
  }else{
    status.textContent='送信できます。';
    status.className='status';
  }
}
function renderFiles(){
  list.innerHTML='';
  chosenFiles.forEach((file,index)=>{
    const item=document.createElement('div');
    item.className='photo-item';
    const img=document.createElement('img');
    img.alt=`選択写真 ${index+1}`;
    img.src=URL.createObjectURL(file);
    img.addEventListener('load',()=>URL.revokeObjectURL(img.src),{once:true});
    const remove=document.createElement('button');
    remove.type='button';
    remove.setAttribute('aria-label',`${file.name}を削除`);
    remove.textContent='×';
    remove.addEventListener('click',()=>{chosenFiles.splice(index,1);renderFiles();});
    item.append(img,remove);
    list.appendChild(item);
  });
  updateState();
}
function buildEmbedUrl(config){
  const url=new URL(config.embed_url);
  if(university)url.searchParams.set(config.university_param||'university',university);
  if(universityId)url.searchParams.set(config.university_id_param||'university_id',universityId);
  return url.toString();
}
function mountReceiver(config){
  const manualControls=[document.querySelector('.file-block'),document.querySelector('.consent-row'),submit,status,document.querySelector('.privacy-note')];
  manualControls.forEach(node=>{if(node)node.hidden=true;});
  const frame=document.createElement('iframe');
  frame.className='provider-frame';
  frame.title='大学写真 投稿フォーム';
  frame.loading='eager';
  frame.referrerPolicy='strict-origin-when-cross-origin';
  frame.src=buildEmbedUrl(config);
  uploadCard.appendChild(frame);
}
function showReceiverUnavailable(){
  submit.disabled=true;
  status.textContent='写真受付の接続準備中です。現在この画面からは送信できません。';
  status.className='status error';
}

changeButton?.addEventListener('click',()=>{
  university='';
  nameInput.value='';
  picker.hidden=false;
  changeButton.hidden=true;
  selected.textContent='大学名を入力してください';
  nameInput.focus();
  updateState();
});
nameInput?.addEventListener('input',()=>{
  university=escapeText(nameInput.value.trim());
  selected.textContent=university||'大学名を入力してください';
  pageTitle.textContent=university?`${university}へ写真を送る`:'大学写真を送る';
  updateState();
});
filesInput?.addEventListener('change',()=>{
  chosenFiles=[...filesInput.files].slice(0,MAX_PHOTOS+1);
  renderFiles();
});
consent?.addEventListener('change',updateState);
submit?.addEventListener('click',()=>{
  // Native direct upload is intentionally disabled. A connected receiver is required.
  showReceiverUnavailable();
});

showUniversity();
fetch('receiver-config.json',{cache:'no-store'})
  .then(r=>r.ok?r.json():Promise.reject(new Error('config')))
  .then(config=>{
    if(config.enabled&&config.provider==='jotform'&&/^https:\/\//.test(config.embed_url||'')){
      mountReceiver(config);
    }else{
      showReceiverUnavailable();
    }
  })
  .catch(showReceiverUnavailable);
})();
