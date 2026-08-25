(()=>{
'use strict';
const MAX_PHOTOS=9;
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const list=document.querySelector('#batch-list');
const batch=document.querySelector('.batch');
const exportPanel=document.querySelector('.export-panel');
const editor=document.querySelector('#photo-editor');
if(!select||!search||!list||!batch||!exportPanel)return;

document.body.classList.add('community-photo-submission','community-simple-submission');
document.documentElement.dataset.communityPhotoSubmission='ready';

const setText=(node,text)=>{if(node&&node.textContent!==text)node.textContent=text;};
const hero=document.querySelector('.hero');
setText(hero?.querySelector('.eyebrow'),'COMMUNITY PHOTO SUBMISSION');
setText(hero?.querySelector('h1'),'大学写真を投稿する');
setText(hero?.querySelector('p'),'大学を1校選び、写真を追加してメインを決めるだけです。最大9枚。投稿は確認後に公開します。');
const badges=hero?.querySelector('.rule-badges');
if(badges)badges.innerHTML='<span>最大9枚</span><span>メイン1＋サブ8</span><span>審査後に公開</span>';

const batchHead=batch.querySelector(':scope > .section-head h2');
const batchLead=batch.querySelector(':scope > .muted');
setText(batchHead,'写真投稿');
setText(batchLead,'①大学を選ぶ → ②写真を追加・メインを選ぶ → ③ルールを確認 → ④審査に提出');

const progress=document.querySelector('#simple-register-progress');
if(progress){
  progress.innerHTML='<li data-step="1"><span>1</span><strong>大学</strong></li><li data-step="2"><span>2</span><strong>写真・メイン</strong></li><li data-step="3"><span>3</span><strong>確認</strong></li><li data-step="4"><span>4</span><strong>提出</strong></li>';
}

const universityTitle=document.querySelector('#university-first-title');
const universitySmall=universityTitle?.parentElement?.querySelector('small');
setText(universityTitle,'大学を選ぶ');
setText(universitySmall,'文字入力または一覧のどちらか一方で選択');

let intro=document.querySelector('#community-submission-intro');
if(!intro){
  intro=document.createElement('div');
  intro.id='community-submission-intro';
  intro.className='community-submission-intro';
  intro.innerHTML='<strong>みんなで育てる大学写真データベース</strong><span>投稿した写真はすぐには公開されません。Ban.Tai側で大学・権利・内容を確認し、承認した写真だけを掲載します。</span>';
  (document.querySelector('#simple-register-workspace')||progress)?.insertAdjacentElement('beforebegin',intro);
}

let counter=document.querySelector('#community-photo-counter');
if(!counter){
  counter=document.createElement('div');
  counter.id='community-photo-counter';
  counter.className='community-photo-counter';
  counter.innerHTML='<span>写真</span><strong>0 / 9枚</strong>';
  document.querySelector('.simple-photo-column-head')?.appendChild(counter);
}

let editorToggle=document.querySelector('#community-editor-toggle');
if(editor&&!editorToggle){
  editorToggle=document.createElement('button');
  editorToggle.id='community-editor-toggle';
  editorToggle.className='secondary community-editor-toggle';
  editorToggle.type='button';
  editorToggle.textContent='写真を調整する（必要な場合）';
  editor.insertAdjacentElement('beforebegin',editorToggle);
  editor.hidden=true;
  editor.classList.add('community-editor');
  editorToggle.addEventListener('click',()=>{
    editor.hidden=!editor.hidden;
    editorToggle.textContent=editor.hidden?'写真を調整する（必要な場合）':'写真調整を閉じる';
    if(!editor.hidden)editor.scrollIntoView({behavior:'smooth',block:'start'});
  });
}
setText(editor?.querySelector('.section-head .step'),'任意');
setText(editor?.querySelector('.section-head h2'),'写真の向き・明るさを調整');

let rules=document.querySelector('#community-photo-rules');
if(!rules){
  rules=document.createElement('section');
  rules.id='community-photo-rules';
  rules.className='community-rules-panel';
  rules.innerHTML=`
    <div class="community-rules-head"><span class="step">STEP 3</span><div><h2>3つだけ確認</h2><p>詳しいルールは必要なときだけ開けます。</p></div></div>
    <div class="community-rule-checks">
      <label class="community-rule-check"><input id="community-rule-rights" type="checkbox"><span><strong>撮影・権利</strong>　自分で撮影した写真、または掲載許可を得た写真です。</span></label>
      <label class="community-rule-check"><input id="community-rule-no-ai" type="checkbox"><span><strong>実景保持</strong>　生成AI・背景置換・実景要素の追加削除はしていません。</span></label>
      <label class="community-rule-check"><input id="community-rule-license" type="checkbox"><span><strong>掲載許諾</strong>　Ban.Tai大学DBでの掲載と軽微な表示調整を許可します。</span></label>
    </div>
    <details class="community-rules-details"><summary>投稿・掲載ルールを詳しく見る</summary><div class="rule-full">
      <p>1大学最大9枚（メイン1枚＋サブ最大8枚）。無断転載、AI生成・再描画、大学と無関係な写真、撮影禁止場所の写真、個人情報が目立つ写真は掲載しません。</p>
      <p>投稿直後には公開しません。大学との一致、権利、個人情報、画質を確認し、掲載可否・順序・メイン写真はBan.Tai側で最終判断します。</p>
    </div></details>`;
  exportPanel.insertAdjacentElement('beforebegin',rules);
}

const ruleChecks=[
  document.querySelector('#community-rule-rights'),
  document.querySelector('#community-rule-no-ai'),
  document.querySelector('#community-rule-license')
].filter(Boolean);

const exportStep=exportPanel.querySelector('.section-head .step');
const exportHeading=exportPanel.querySelector('.section-head h2');
const exportLead=exportPanel.querySelector(':scope > p');
const exportBadge=exportPanel.querySelector('.surface-badge');
setText(exportStep,'STEP 4');
setText(exportHeading,'審査に提出');
setText(exportLead,'大学・写真・メイン・3つの確認がそろったら提出します。公開はBan.Tai側の審査後です。');
setText(exportBadge,'審査後に公開');

let submit=document.querySelector('#community-submit-package');
if(!submit){
  submit=document.createElement('button');
  submit.id='community-submit-package';
  submit.type='button';
  submit.disabled=true;
  exportPanel.querySelector('.actions')?.appendChild(submit);
}
let submitStatus=document.querySelector('#community-submit-status');
if(!submitStatus){
  submitStatus=document.createElement('p');
  submitStatus.id='community-submit-status';
  submitStatus.className='community-submit-status';
  submit.insertAdjacentElement('afterend',submitStatus);
}
let delivery=document.querySelector('#community-delivery-note');
if(!delivery){
  delivery=document.createElement('div');
  delivery.id='community-delivery-note';
  delivery.className='community-delivery-note';
  delivery.innerHTML='<strong>提出方法</strong><span>通知接続を確認中…</span>';
  submitStatus.insertAdjacentElement('afterend',delivery);
}

function helper(){return window.__universityPhotoMainChoice||null;}
function existingPhotos(){return helper()?.getExistingPhotos?.()||[];}
function rows(){return [...list.querySelectorAll('.batch-row')];}
function currentChoice(){return helper()?.getChoice?.()||{type:'',key:''};}
function selectedUniversityName(){return select.selectedOptions?.[0]?.textContent?.trim()||'';}
function agreementsReady(){return ruleChecks.length===3&&ruleChecks.every(x=>x.checked);}
function totalPhotos(){return existingPhotos().length+rows().length;}
function hasValidMain(){
  const c=currentChoice();
  if(c.type==='existing')return existingPhotos().some(x=>x.image_url===c.key);
  if(c.type==='new')return rows().some(x=>(x.dataset.key||'')===c.key);
  return false;
}
function remoteTransport(){return window.__bantaiPhotoSubmissionTransport?.mode==='remote';}

function updateProgress(){
  const items=[...document.querySelectorAll('#simple-register-progress li')];
  if(items.length!==4)return;
  const university=!!select.value;
  const photos=totalPhotos();
  const photoReady=university&&photos>0&&photos<=MAX_PHOTOS&&hasValidMain();
  const rulesOk=agreementsReady();
  const done=[university,photoReady,rulesOk,false];
  items.forEach((item,index)=>{item.classList.toggle('done',done[index]);item.classList.remove('current');});
  const current=!university?0:!photoReady?1:!rulesOk?2:3;
  items[current]?.classList.add('current');
}

function updateDelivery(){
  const span=delivery?.querySelector('span');
  if(remoteTransport()){
    setText(submit,'審査に提出する');
    setText(span,'送信後、Ban.Taiへ通知され「審査待ち」に入ります。');
    delivery?.classList.add('remote-ready');
  }else{
    setText(submit,'審査用データを保存');
    setText(span,'通知受信先の接続前です。現在は審査用ファイルを安全に保存します。');
    delivery?.classList.remove('remote-ready');
  }
}

function updateState(){
  const total=totalPhotos();
  const strong=counter?.querySelector('strong');
  if(strong)strong.textContent=`${total} / ${MAX_PHOTOS}枚`;
  counter?.classList.toggle('warn',total>MAX_PHOTOS);
  let ready=true;
  let message='提出できます。';
  if(!select.value){ready=false;message='まず大学を1校選んでください。';}
  else if(total===0){ready=false;message='写真を1枚以上追加または確認してください。';}
  else if(total>MAX_PHOTOS){ready=false;message=`写真は最大${MAX_PHOTOS}枚です。現在${total}枚です。`;}
  else if(!hasValidMain()){ready=false;message='写真をクリックして★メインを1枚選んでください。';}
  else if(!agreementsReady()){ready=false;message='STEP 3の3項目を確認してください。';}
  submit.disabled=!ready;
  setText(submitStatus,message);
  submitStatus.classList.toggle('warn',!ready&&total>MAX_PHOTOS);
  updateDelivery();
  updateProgress();
}

const enc=new TextEncoder();
function crcTable(){const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=(c&1)?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;}
const CRC=crcTable();
function crc32(bytes){let c=0xffffffff;for(const b of bytes)c=CRC[(c^b)&255]^(c>>>8);return(c^0xffffffff)>>>0;}
function le16(n){const b=new Uint8Array(2);new DataView(b.buffer).setUint16(0,n,true);return b;}
function le32(n){const b=new Uint8Array(4);new DataView(b.buffer).setUint32(0,n>>>0,true);return b;}
function concat(parts){const len=parts.reduce((s,p)=>s+p.length,0),out=new Uint8Array(len);let o=0;for(const p of parts){out.set(p,o);o+=p.length;}return out;}
async function makeZip(entries){
  const locals=[],centrals=[];let offset=0;
  for(const entry of entries){
    const name=enc.encode(entry.name);
    const data=entry.data instanceof Uint8Array?entry.data:new Uint8Array(await entry.data.arrayBuffer());
    const crc=crc32(data);
    const local=concat([le32(0x04034b50),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),name,data]);
    locals.push(local);
    const central=concat([le32(0x02014b50),le16(20),le16(20),le16(0),le16(0),le16(0),le16(0),le32(crc),le32(data.length),le32(data.length),le16(name.length),le16(0),le16(0),le16(0),le16(0),le32(0),le32(offset),name]);
    centrals.push(central);offset+=local.length;
  }
  const centralBytes=concat(centrals);
  const end=concat([le32(0x06054b50),le16(0),le16(0),le16(entries.length),le16(entries.length),le32(centralBytes.length),le32(offset),le16(0)]);
  return new Blob([concat([...locals,centralBytes,end])],{type:'application/zip'});
}
function safeName(value){return String(value||'university').normalize('NFKC').replace(/[\\/:*?"<>|]/g,'-').replace(/\s+/g,'-').replace(/-+/g,'-').replace(/^-|-$/g,'').slice(0,60)||'university';}
function extFor(name,type){const m=String(name||'').match(/\.([a-zA-Z0-9]{2,5})$/);if(m)return m[1].toLowerCase();if(type==='image/png')return'png';if(type==='image/webp')return'webp';return'jpg';}
async function blobForRow(row){const img=row.querySelector('.thumb img');if(!img?.src)throw new Error('追加写真を取得できませんでした');const r=await fetch(img.src);if(!r.ok)throw new Error('追加写真を取得できませんでした');return r.blob();}
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);}

async function buildPackage(){
  updateState();
  if(submit.disabled)throw new Error('投稿内容が未完成です');
  const currentRows=rows();
  const existing=existingPhotos();
  const choice=currentChoice();
  const submissionId=`BT-UP-${new Date().toISOString().replace(/\D/g,'').slice(0,14)}-${Math.random().toString(36).slice(2,6).toUpperCase()}`;
  const photoEntries=[];
  const zipEntries=[];
  for(let i=0;i<currentRows.length;i++){
    const row=currentRows[i];
    const blob=await blobForRow(row);
    const originalName=row.querySelector('.batch-main strong')?.textContent?.trim()||`photo-${i+1}`;
    const key=row.dataset.key||'';
    const filename=`${String(i+1).padStart(2,'0')}-${safeName(originalName)}.${extFor(originalName,blob.type)}`;
    zipEntries.push({name:`photos/${filename}`,data:blob});
    photoEntries.push({kind:'new',key,filename:`photos/${filename}`,original_name:originalName,role:choice.type==='new'&&choice.key===key?'main':'sub'});
  }
  for(const item of existing){
    photoEntries.push({kind:'existing',image_url:item.image_url,origin:item.origin||'existing',role:choice.type==='existing'&&choice.key===item.image_url?'main':'sub'});
  }
  const metadata={
    schema_version:1,
    kind:'bantai_university_photo_submission',
    review_status:'pending',
    submission_id:submissionId,
    submitted_at:new Date().toISOString(),
    university_id:select.value,
    university_name:selectedUniversityName(),
    photo_count:photoEntries.length,
    max_photos:MAX_PHOTOS,
    photos:photoEntries,
    agreements:{rights:true,no_ai:true,license:true},
    publication:{automatic:false,requires_review:true}
  };
  zipEntries.unshift({name:'submission.json',data:enc.encode(JSON.stringify(metadata,null,2))});
  const blob=await makeZip(zipEntries);
  return {blob,metadata,filename:`${submissionId}-${safeName(selectedUniversityName())}.zip`};
}

window.__bantaiCommunityPhotoSubmission={buildPackage,updateState,totalPhotos,currentChoice,MAX_PHOTOS};

async function submitNow(){
  if(submit.disabled)return;
  submit.disabled=true;
  submit.setAttribute('aria-busy','true');
  const oldText=submit.textContent;
  setText(submit,remoteTransport()?'送信中…':'作成中…');
  setText(submitStatus,'写真と投稿情報をまとめています…');
  submitStatus.classList.remove('ok','warn');
  try{
    const pkg=await buildPackage();
    if(remoteTransport()){
      const result=await window.__bantaiPhotoSubmissionTransport.submit(pkg);
      setText(submitStatus,`投稿を受け付けました。受付番号：${result?.submission_id||pkg.metadata.submission_id}`);
      submitStatus.classList.add('ok');
      setText(submit,'提出完了');
      document.documentElement.dataset.communitySubmissionLast='submitted';
      window.dispatchEvent(new CustomEvent('bantai-photo-register-complete',{detail:{submission_id:result?.submission_id||pkg.metadata.submission_id,notified:!!result?.notified}}));
    }else{
      download(pkg.blob,pkg.filename);
      setText(submitStatus,'審査用データを保存しました。通知接続後は、このボタンから直接提出できます。');
      submitStatus.classList.add('ok');
      setText(submit,'保存完了');
      document.documentElement.dataset.communitySubmissionLast='saved';
    }
  }catch(err){
    console.error(err);
    setText(submitStatus,err?.message||'提出処理に失敗しました。');
    submitStatus.classList.add('warn');
    setText(submit,oldText);
  }finally{
    submit.removeAttribute('aria-busy');
    setTimeout(updateState,300);
  }
}
submit.addEventListener('click',submitNow);

for(const check of ruleChecks)check.addEventListener('change',updateState);
select.addEventListener('change',()=>setTimeout(updateState,0));
document.addEventListener('click',event=>{if(event.target.closest?.('.main-photo-choice-card,.photo-list-delete,.remove-item,.photo-main-button'))setTimeout(updateState,0);},true);
new MutationObserver(()=>queueMicrotask(updateState)).observe(list,{childList:true,subtree:true});
window.addEventListener('bantai-submission-transport-ready',updateState);
updateState();
setTimeout(updateState,300);
setTimeout(updateState,1000);
})();