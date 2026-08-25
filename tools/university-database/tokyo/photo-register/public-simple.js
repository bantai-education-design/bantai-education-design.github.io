(()=>{
'use strict';
const $=s=>document.querySelector(s);
const form=$('#simple-photo-form');
if(!form)return;
const universityInput=$('#simple-university');
const universityId=$('#simple-university-id');
const suggestions=$('#university-suggestions');
const selectedBox=$('#selected-university');
const fileInput=$('#simple-photos');
const dropzone=$('#simple-dropzone');
const fileList=$('#simple-file-list');
const consent=$('#simple-consent');
const submit=$('#simple-submit');
const status=$('#simple-status');
const formCard=$('#simple-form-card');
const thanks=$('#simple-thanks');
let universities=[];
let files=[];
let runtime={enabled:false,mode:'local_package',endpoint:''};

const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function setStatus(message,type=''){
  status.textContent=message||'';
  status.className='status'+(type?' '+type:'');
}
function selectedUniversity(){return universities.find(u=>u.id===universityId.value)||null;}
function updateSubmit(){
  const selected=selectedUniversity();
  submit.disabled=!(selected&&files.length&&consent.checked&&runtime.enabled&&runtime.mode==='remote'&&/^https:\/\//.test(runtime.endpoint||''));
}
function chooseUniversity(u){
  universityId.value=u?.id||'';
  universityInput.value=u?.name||'';
  selectedBox.hidden=!u;
  selectedBox.textContent=u?`${u.name} を選択しています。`:'';
  suggestions.classList.remove('open');
  updateSubmit();
}
function renderSuggestions(){
  const q=norm(universityInput.value);
  if(!q){suggestions.classList.remove('open');suggestions.innerHTML='';return;}
  const rows=universities.filter(u=>norm(u.name).includes(q)||norm(u.id).includes(q)).slice(0,12);
  suggestions.innerHTML=rows.map(u=>`<button class="suggestion" type="button" data-id="${esc(u.id)}">${esc(u.name)}</button>`).join('');
  suggestions.classList.toggle('open',rows.length>0);
}
function renderFiles(){
  fileList.innerHTML=files.map((f,i)=>`<div class="file-row"><span>${esc(f.name)}</span><small>${(f.size/1024/1024).toFixed(1)}MB</small><button type="button" data-remove="${i}" aria-label="${esc(f.name)}を削除">削除</button></div>`).join('');
  updateSubmit();
}
function acceptFiles(inputFiles){
  const allowed=[...inputFiles].filter(f=>/^image\/(jpeg|png|webp)$/i.test(f.type));
  const merged=[...files,...allowed].slice(0,9);
  files=merged;
  renderFiles();
  if([...inputFiles].length>allowed.length)setStatus('JPEG・PNG・WebP以外のファイルは追加しませんでした。','error');
  else setStatus(files.length?`${files.length}枚を選択しています。`:'' );
}
universityInput.addEventListener('input',()=>{universityId.value='';selectedBox.hidden=true;renderSuggestions();updateSubmit();});
suggestions.addEventListener('click',e=>{const btn=e.target.closest('[data-id]');if(!btn)return;const u=universities.find(x=>x.id===btn.dataset.id);if(u)chooseUniversity(u);});
document.addEventListener('click',e=>{if(!e.target.closest('.university-wrap'))suggestions.classList.remove('open');});
fileInput.addEventListener('change',()=>{acceptFiles(fileInput.files||[]);fileInput.value='';});
fileList.addEventListener('click',e=>{const btn=e.target.closest('[data-remove]');if(!btn)return;files.splice(Number(btn.dataset.remove),1);renderFiles();setStatus(files.length?`${files.length}枚を選択しています。`:'');});
['dragenter','dragover'].forEach(type=>dropzone.addEventListener(type,e=>{e.preventDefault();dropzone.classList.add('drag');}));
['dragleave','drop'].forEach(type=>dropzone.addEventListener(type,e=>{e.preventDefault();dropzone.classList.remove('drag');}));
dropzone.addEventListener('drop',e=>acceptFiles(e.dataTransfer?.files||[]));
consent.addEventListener('change',updateSubmit);

form.addEventListener('submit',async e=>{
  e.preventDefault();
  const u=selectedUniversity();
  if(!u||!files.length||!consent.checked)return;
  if(!(runtime.enabled&&runtime.mode==='remote'&&/^https:\/\//.test(runtime.endpoint||''))){
    setStatus('現在、写真受付の接続準備中です。受付開始までしばらくお待ちください。','error');
    return;
  }
  submit.disabled=true;
  submit.textContent='アップロード中…';
  setStatus('写真を送信しています。この画面を閉じないでください。');
  try{
    const fd=new FormData();
    fd.append('university_id',u.id);
    fd.append('university_name',u.name);
    fd.append('source','community_simple_upload');
    fd.append('agreed_real_photo','true');
    fd.append('agreed_no_unauthorized_repost','true');
    fd.append('agreed_review_before_publish','true');
    files.forEach((file,i)=>fd.append('photos',file,file.name||`photo-${i+1}.jpg`));
    const res=await fetch(runtime.endpoint,{method:'POST',body:fd});
    let payload=null;try{payload=await res.json();}catch{}
    if(!res.ok)throw new Error(payload?.error||`送信に失敗しました (${res.status})`);
    formCard.hidden=true;
    thanks.classList.add('show');
    thanks.removeAttribute('hidden');
    window.scrollTo({top:0,behavior:'smooth'});
  }catch(error){
    console.error(error);
    setStatus('送信できませんでした。通信環境を確認して、もう一度お試しください。','error');
    submit.disabled=false;
  }finally{
    submit.textContent='写真を投稿する';
    updateSubmit();
  }
});

Promise.all([
  fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('大学一覧');return r.json();}),
  fetch('submission-runtime-config.json',{cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({}))
]).then(([rows,config])=>{
  universities=Array.isArray(rows)?rows:[];
  runtime={...runtime,...(config||{})};
  if(runtime.enabled&&runtime.mode==='remote'&&/^https:\/\//.test(runtime.endpoint||'')){
    setStatus('大学名と写真を選んで投稿してください。');
  }else{
    setStatus('写真受付の接続準備中です。大学名と写真は選べますが、送信はまだできません。');
  }
  updateSubmit();
}).catch(error=>{console.error(error);setStatus('大学一覧を読み込めませんでした。ページを再読み込みしてください。','error');});
})();