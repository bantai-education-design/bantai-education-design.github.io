(()=>{
'use strict';
const CONFIG_URL='admin-runtime-config.json';
const SESSION_KEY='bantai-university-photo-admin-code';
const els={
  backend:document.querySelector('#backend-status'),
  login:document.querySelector('#admin-login'),
  form:document.querySelector('#admin-login-form'),
  code:document.querySelector('#admin-code'),
  remember:document.querySelector('#remember-session'),
  unlock:document.querySelector('#unlock-admin'),
  loginStatus:document.querySelector('#login-status'),
  dashboard:document.querySelector('#admin-dashboard'),
  refresh:document.querySelector('#refresh-queue'),
  lock:document.querySelector('#lock-admin'),
  queue:document.querySelector('#review-queue'),
  empty:document.querySelector('#review-empty'),
  queueStatus:document.querySelector('#queue-status'),
  filters:[...document.querySelectorAll('.filter')],
  counts:{pending:document.querySelector('#count-pending'),approved:document.querySelector('#count-approved'),rejected:document.querySelector('#count-rejected'),published:document.querySelector('#count-published')},
  dialog:document.querySelector('#review-dialog'),
  dialogStatus:document.querySelector('#dialog-status-badge'),
  dialogUniversity:document.querySelector('#dialog-university'),
  dialogMeta:document.querySelector('#dialog-meta'),
  dialogGallery:document.querySelector('#dialog-gallery'),
  dialogId:document.querySelector('#dialog-id'),
  dialogCount:document.querySelector('#dialog-count'),
  dialogDate:document.querySelector('#dialog-date'),
  dialogUniversityId:document.querySelector('#dialog-university-id'),
  dialogAgreements:document.querySelector('#dialog-agreements'),
  reviewerNote:document.querySelector('#reviewer-note'),
  download:document.querySelector('#download-package'),
  markPending:document.querySelector('#mark-pending'),
  reject:document.querySelector('#reject-submission'),
  approve:document.querySelector('#approve-submission'),
  publish:document.querySelector('#publish-submission'),
  dialogActionStatus:document.querySelector('#dialog-action-status')
};
let config=null;
let adminCode='';
let submissions=[];
let activeFilter='pending';
let activeSubmissionId='';
const statusLabel={pending:'審査待ち',approved:'承認',rejected:'却下',published:'掲載済み'};

function setStatus(node,text,type=''){
  if(!node)return;
  node.textContent=text;
  node.classList.remove('ok','warn');
  if(type)node.classList.add(type);
}
function formatDate(value){
  if(!value)return '—';
  const date=new Date(value);
  if(Number.isNaN(date.getTime()))return String(value);
  return new Intl.DateTimeFormat('ja-JP',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(date);
}
function safeMediaUrl(value){
  if(!value)return '';
  try{
    const url=new URL(value,location.origin);
    if(url.protocol==='https:'||url.protocol==='http:'||url.protocol==='blob:')return url.href;
  }catch(_e){}
  return '';
}
async function loadConfig(){
  const response=await fetch(CONFIG_URL,{cache:'no-store'});
  if(!response.ok)throw new Error('管理設定を読み込めませんでした。');
  const value=await response.json();
  if(!value||typeof value!=='object')throw new Error('管理設定が不正です。');
  return value;
}
async function api(action,payload={}){
  if(!config?.enabled||!/^https:\/\//i.test(config.endpoint||''))throw new Error('審査APIが未接続です。');
  if(!adminCode)throw new Error('管理コードを入力してください。');
  const headerName=config.code_header||'x-bantai-admin-code';
  const response=await fetch(config.endpoint,{
    method:'POST',
    headers:{'content-type':'application/json',[headerName]:adminCode},
    body:JSON.stringify({action,...payload}),
    credentials:'omit',
    redirect:'follow',
    cache:'no-store'
  });
  let data={};
  try{data=await response.json();}catch(_e){}
  if(!response.ok||data?.ok===false)throw new Error(data?.message||`管理APIエラー（${response.status}）`);
  return data;
}
function setUnlocked(unlocked){
  els.dashboard.hidden=!unlocked;
  els.login.hidden=unlocked;
  if(unlocked)els.dashboard.scrollIntoView({behavior:'smooth',block:'start'});
}
async function unlock(code,{silent=false}={}){
  adminCode=String(code||'').trim();
  if(!adminCode){if(!silent)setStatus(els.loginStatus,'管理コードを入力してください。','warn');return false;}
  els.unlock.disabled=true;
  if(!silent)setStatus(els.loginStatus,'管理コードを確認しています…');
  try{
    await api('health');
    if(els.remember?.checked)sessionStorage.setItem(SESSION_KEY,adminCode);else sessionStorage.removeItem(SESSION_KEY);
    setStatus(els.loginStatus,'管理画面を開きました。','ok');
    setUnlocked(true);
    await loadQueue();
    return true;
  }catch(err){
    adminCode='';
    sessionStorage.removeItem(SESSION_KEY);
    if(!silent)setStatus(els.loginStatus,err?.message||'管理コードを確認できませんでした。','warn');
    return false;
  }finally{els.unlock.disabled=!config?.enabled;}
}
function lock(){
  adminCode='';
  submissions=[];
  activeSubmissionId='';
  sessionStorage.removeItem(SESSION_KEY);
  if(els.code)els.code.value='';
  if(els.queue)els.queue.replaceChildren();
  setUnlocked(false);
  setStatus(els.loginStatus,'管理画面を閉じました。');
  els.login?.scrollIntoView({behavior:'smooth',block:'start'});
}
async function loadQueue(){
  setStatus(els.queueStatus,'審査一覧を読み込んでいます…');
  els.refresh.disabled=true;
  try{
    const result=await api('list',{status:'all',limit:100});
    submissions=Array.isArray(result.submissions)?result.submissions:[];
    updateCounts();
    renderQueue();
    setStatus(els.queueStatus,`${submissions.length}件を読み込みました。`,'ok');
    const wanted=new URLSearchParams(location.search).get('submission');
    if(wanted){const row=submissions.find(x=>x.submission_id===wanted);if(row)openDialog(row);}
  }catch(err){
    setStatus(els.queueStatus,err?.message||'審査一覧を読み込めませんでした。','warn');
  }finally{els.refresh.disabled=false;}
}
function updateCounts(){
  for(const key of Object.keys(els.counts))els.counts[key].textContent=String(submissions.filter(x=>x.status===key).length);
}
function currentRows(){return activeFilter==='all'?submissions:submissions.filter(x=>x.status===activeFilter);}
function firstPhoto(row){
  const photos=Array.isArray(row.photos)?row.photos:[];
  return photos.find(x=>x.role==='main')||photos[0]||null;
}
function renderQueue(){
  els.queue.replaceChildren();
  const rows=currentRows();
  els.empty.hidden=rows.length!==0;
  for(const row of rows){
    const card=document.createElement('article');card.className='review-card';card.dataset.submissionId=row.submission_id||'';
    const thumb=document.createElement('div');thumb.className='review-thumb';
    const photo=firstPhoto(row);const media=safeMediaUrl(photo?.url||photo?.image_url);
    if(media){const img=document.createElement('img');img.src=media;img.alt=`${row.university_name||'大学'} 投稿写真`;img.loading='lazy';thumb.appendChild(img);}else{const none=document.createElement('div');none.className='no-photo';none.textContent='写真プレビューなし';thumb.appendChild(none);}
    const main=document.createElement('div');main.className='review-main';
    const badge=document.createElement('span');badge.className=`status-badge ${row.status||'pending'}`;badge.textContent=statusLabel[row.status]||row.status||'審査待ち';
    const h=document.createElement('h3');h.textContent=row.university_name||'大学名未設定';
    const p=document.createElement('p');p.textContent=`${formatDate(row.submitted_at)} / ${row.submission_id||''}`;
    const meta=document.createElement('div');meta.className='review-meta';
    for(const text of [`${row.photo_count||0}枚`,row.university_id||'',row.main_photo?.original_name?`メイン: ${row.main_photo.original_name}`:'メイン指定あり']){const span=document.createElement('span');span.textContent=text;meta.appendChild(span);}
    main.append(badge,h,p,meta);
    const button=document.createElement('button');button.type='button';button.className='review-open';button.textContent='写真を審査';button.addEventListener('click',()=>openDialog(row));
    card.append(thumb,main,button);els.queue.appendChild(card);
  }
}
function openDialog(row){
  activeSubmissionId=row.submission_id||'';
  els.dialogStatus.className=`status-badge ${row.status||'pending'}`;
  els.dialogStatus.textContent=statusLabel[row.status]||row.status||'審査待ち';
  els.dialogUniversity.textContent=row.university_name||'大学名未設定';
  els.dialogMeta.textContent=`${row.photo_count||0}枚 / ${formatDate(row.submitted_at)}`;
  els.dialogId.textContent=row.submission_id||'—';
  els.dialogCount.textContent=`${row.photo_count||0}枚`;
  els.dialogDate.textContent=formatDate(row.submitted_at);
  els.dialogUniversityId.textContent=row.university_id||'—';
  els.reviewerNote.value=row.reviewer_note||'';
  setStatus(els.dialogActionStatus,'');
  els.dialogGallery.replaceChildren();
  const photos=Array.isArray(row.photos)?row.photos:[];
  photos.forEach((photo,index)=>{
    const box=document.createElement('figure');box.className='dialog-photo';
    const media=safeMediaUrl(photo?.url||photo?.image_url);
    if(media){const img=document.createElement('img');img.src=media;img.alt=`${row.university_name||'大学'} 写真${index+1}`;box.appendChild(img);}
    const role=document.createElement('span');role.className='photo-role';role.textContent=photo?.role==='main'?'★ メイン':`サブ ${index+1}`;box.appendChild(role);els.dialogGallery.appendChild(box);
  });
  if(photos.length===0){const none=document.createElement('p');none.textContent='写真プレビューを取得できませんでした。審査用ZIPを確認してください。';els.dialogGallery.appendChild(none);}
  els.dialogAgreements.replaceChildren();
  const agreements=row.agreements||{};
  const agreementRows=[['撮影・権利',agreements.rights],['生成AI・実景保持',agreements.no_ai],['掲載許諾',agreements.license]];
  for(const [label,ok] of agreementRows){const li=document.createElement('li');li.textContent=`${ok?'✓':'×'} ${label}`;els.dialogAgreements.appendChild(li);}
  const packageUrl=safeMediaUrl(row.package_url);
  els.download.hidden=!packageUrl;
  els.download.href=packageUrl||'#';
  els.publish.hidden=row.status!=='approved';
  els.markPending.hidden=row.status==='pending';
  if(typeof els.dialog.showModal==='function')els.dialog.showModal();else els.dialog.setAttribute('open','');
}
async function updateActive(status){
  if(!activeSubmissionId)return;
  for(const button of [els.markPending,els.reject,els.approve,els.publish])button.disabled=true;
  setStatus(els.dialogActionStatus,'更新しています…');
  try{
    const result=await api('update',{submission_id:activeSubmissionId,status,reviewer_note:els.reviewerNote.value.trim()});
    const updated=result.submission;
    const index=submissions.findIndex(x=>x.submission_id===activeSubmissionId);
    if(index>=0&&updated)submissions[index]={...submissions[index],...updated};
    await loadQueue();
    const row=submissions.find(x=>x.submission_id===activeSubmissionId);
    if(row)openDialog(row);
    setStatus(els.dialogActionStatus,`${statusLabel[status]||status}に更新しました。`,'ok');
  }catch(err){setStatus(els.dialogActionStatus,err?.message||'更新に失敗しました。','warn');}
  finally{for(const button of [els.markPending,els.reject,els.approve,els.publish])button.disabled=false;}
}

els.form?.addEventListener('submit',event=>{event.preventDefault();unlock(els.code.value);});
els.refresh?.addEventListener('click',loadQueue);
els.lock?.addEventListener('click',lock);
els.filters.forEach(button=>button.addEventListener('click',()=>{
  activeFilter=button.dataset.status||'pending';
  els.filters.forEach(x=>x.classList.toggle('active',x===button));
  renderQueue();
}));
els.markPending?.addEventListener('click',()=>updateActive('pending'));
els.reject?.addEventListener('click',()=>updateActive('rejected'));
els.approve?.addEventListener('click',()=>updateActive('approved'));
els.publish?.addEventListener('click',()=>updateActive('published'));

(async()=>{
  try{
    config=await loadConfig();
    const connected=!!(config?.enabled&&/^https:\/\//i.test(config.endpoint||''));
    els.backend.textContent=connected?'審査API 接続済み':'審査API 未接続';
    els.backend.classList.toggle('online',connected);els.backend.classList.toggle('offline',!connected);
    els.unlock.disabled=!connected;
    if(!connected){
      setStatus(els.loginStatus,'審査APIの接続設定がまだ完了していません。本人写真登録は上のボタンから利用できます。','warn');
      return;
    }
    const saved=config.session_storage?sessionStorage.getItem(SESSION_KEY):'';
    if(saved){els.code.value=saved;await unlock(saved,{silent:true});}
  }catch(err){
    els.backend.textContent='管理設定エラー';
    setStatus(els.loginStatus,err?.message||'管理設定を確認できませんでした。','warn');
    els.unlock.disabled=true;
  }
})();
})();
