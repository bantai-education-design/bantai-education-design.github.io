(()=>{
'use strict';
const MAX_PHOTOS=9;
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const list=document.querySelector('#batch-list');
const batch=document.querySelector('.batch');
const exportPanel=document.querySelector('.export-panel');
if(!select||!search||!list||!batch||!exportPanel)return;

document.body.classList.add('community-photo-submission');
document.documentElement.dataset.communityPhotoSubmission='ready';

const hero=document.querySelector('.hero');
const eyebrow=hero?.querySelector('.eyebrow');
const heroTitle=hero?.querySelector('h1');
const heroLead=hero?.querySelector('p');
if(eyebrow)eyebrow.textContent='COMMUNITY UNIVERSITY PHOTO SUBMISSION';
if(heroTitle)heroTitle.textContent='大学写真を投稿する';
if(heroLead)heroLead.textContent='大学を1校選び、実際のキャンパス写真を最大9枚まで追加してください。投稿内容はBan.Tai側で確認し、承認した写真だけを大学DBへ掲載します。';
const badges=hero?.querySelector('.rule-badges');
if(badges)badges.innerHTML='<span>✓ 1回1大学</span><span>✓ 最大9枚</span><span>✓ メイン1＋サブ8</span><span>✓ 実景写真</span><span>✓ 審査後に公開</span>';

const intro=document.createElement('div');
intro.className='community-submission-intro';
intro.innerHTML='<strong>みんなで育てる大学写真データベース</strong><span>誰でも写真を投稿できますが、投稿直後に公開されることはありません。大学・権利・写真内容を確認し、承認した写真だけを掲載します。</span>';
const workspace=document.querySelector('#simple-register-workspace');
(workspace||batch.querySelector(':scope > .muted'))?.insertAdjacentElement('beforebegin',intro);

const progress=document.querySelector('#simple-register-progress');
if(progress){
  progress.innerHTML='<li data-step="1"><span>1</span><strong>大学</strong></li><li data-step="2"><span>2</span><strong>写真</strong></li><li data-step="3"><span>3</span><strong>メイン</strong></li><li data-step="4"><span>4</span><strong>ルール</strong></li><li data-step="5"><span>5</span><strong>審査用データ</strong></li>';
}
const editorStep=document.querySelector('#photo-editor .section-head .step');
const editorHeading=document.querySelector('#photo-editor .section-head h2');
if(editorStep)editorStep.textContent='任意';
if(editorHeading)editorHeading.textContent='必要なら写真を微調整';

let counter=document.querySelector('#community-photo-counter');
if(!counter){
  counter=document.createElement('div');
  counter.id='community-photo-counter';
  counter.className='community-photo-counter';
  counter.innerHTML='<span>掲載候補</span><strong>0 / 9枚</strong>';
  document.querySelector('.simple-photo-column-head')?.appendChild(counter);
}

let rules=document.querySelector('#community-photo-rules');
if(!rules){
  rules=document.createElement('section');
  rules.id='community-photo-rules';
  rules.className='community-rules-panel';
  rules.innerHTML=`
    <div class="community-rules-head"><span class="step">STEP 4</span><div><h2>投稿ルールを確認</h2><p>3項目を確認すると審査用データを作成できます。公開はBan.Tai側の確認後です。</p></div></div>
    <div class="community-rule-summary">
      <div><strong>自分の写真・許可済み写真</strong><small>他サイトや大学公式サイトからの無断転載はできません。</small></div>
      <div><strong>実景を変えない</strong><small>生成AI、背景置換、建物・人物等の追加削除は禁止です。</small></div>
      <div><strong>1大学 最大9枚</strong><small>メイン1枚＋サブ最大8枚。掲載順は審査時に調整する場合があります。</small></div>
    </div>
    <div class="community-rule-checks">
      <label class="community-rule-check"><input id="community-rule-rights" type="checkbox"><span>私が撮影した写真、またはBan.Tai大学DBへの掲載許可を得た写真です。</span></label>
      <label class="community-rule-check"><input id="community-rule-no-ai" type="checkbox"><span>生成AIによる作成・再描画・背景置換など、実景を変える加工をしていません。</span></label>
      <label class="community-rule-check"><input id="community-rule-license" type="checkbox"><span>Ban.Tai大学DBでの掲載と、表示に必要な軽微な回転・傾き・明るさ・トリミング・縮小を許可します。</span></label>
    </div>
    <details class="community-rules-details"><summary>投稿・掲載ルールを詳しく見る</summary><div class="rule-full">
      <p><strong>掲載できる写真：</strong>選択した大学のキャンパス、校舎、入口、庭園、施設外観など、大学の実際の様子が分かる写真。</p>
      <p><strong>掲載しない写真：</strong>無断転載、AI生成・生成補完、実景要素の追加削除、大学と無関係な写真、撮影禁止場所の写真、同意の確認できない人物・車両番号・個人情報が目立つ写真。</p>
      <p><strong>審査：</strong>投稿直後には公開しません。大学との一致、権利、個人情報、画質を確認し、掲載可否・メイン写真・順序・枚数をBan.Tai側で決定します。</p>
      <p><strong>権利：</strong>著作権を譲渡するものではありません。Ban.Tai大学DBでの掲載利用許諾を受ける形です。</p>
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
if(exportStep)exportStep.textContent='STEP 5';
if(exportHeading)exportHeading.textContent='審査用データを作成';
if(exportLead)exportLead.textContent='確認した写真・メイン指定・投稿同意を、審査用パッケージとして保存します。公開DBへ直接書き込むことはありません。';
if(exportBadge)exportBadge.textContent='審査後に公開';

let submit=document.querySelector('#community-submit-package');
if(!submit){
  submit=document.createElement('button');
  submit.id='community-submit-package';
  submit.type='button';
  submit.textContent='審査用データを作成';
  submit.disabled=true;
  exportPanel.querySelector('.actions')?.appendChild(submit);
}
let submitStatus=document.querySelector('#community-submit-status');
if(!submitStatus){
  submitStatus=document.createElement('p');
  submitStatus.id='community-submit-status';
  submitStatus.className='community-submit-status';
  submitStatus.textContent='大学・写真・★メイン・3つの確認をそろえると作成できます。';
  submit.insertAdjacentElement('afterend',submitStatus);
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

function updateProgress(){
  const items=[...document.querySelectorAll('#simple-register-progress li')];
  if(items.length!==5)return;
  const university=!!select.value;
  const photos=totalPhotos();
  const main=hasValidMain();
  const rulesOk=agreementsReady();
  const done=[university,university&&photos>0&&photos<=MAX_PHOTOS,main,rulesOk,false];
  items.forEach((item,index)=>{item.classList.toggle('done',done[index]);item.classList.remove('current');});
  const current=!university?0:!done[1]?1:!main?2:!rulesOk?3:4;
  items[current]?.classList.add('current');
}

function updateState(){
  const total=totalPhotos();
  counter?.classList.toggle('warn',total>MAX_PHOTOS);
  const strong=counter?.querySelector('strong');
  if(strong)strong.textContent=`${total} / ${MAX_PHOTOS}枚`;

  let message='大学・写真・★メイン・3つの確認をそろえると作成できます。';
  let ready=true;
  if(!select.value){ready=false;message='STEP 1で大学を1校選んでください。';}
  else if(total===0){ready=false;message='写真を1枚以上確認または追加してください。';}
  else if(total>MAX_PHOTOS){ready=false;message=`写真は最大${MAX_PHOTOS}枚です。現在${total}枚あるため、不要な写真を一覧から削除してください。`;}
  else if(!hasValidMain()){ready=false;message='掲載候補から★メイン写真を1枚選んでください。';}
  else if(!agreementsReady()){ready=false;message='STEP 4の3つの投稿ルールを確認してください。';}
  else message='準備完了です。審査用データを作成できます。';
  submit.disabled=!ready;
  submitStatus.textContent=message;
  submitStatus.classList.toggle('warn',!ready&&total>MAX_PHOTOS);
  if(ready)submitStatus.classList.remove('warn');
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
function extFor(name,type){
  const m=String(name||'').match(/\.([a-zA-Z0-9]{2,5})$/);if(m)return m[1].toLowerCase();
  if(type==='image/png')return'png';if(type==='image/webp')return'webp';return'jpg';
}
async function blobForRow(row){
  const img=row.querySelector('.thumb img');
  if(!img?.src)throw new Error('追加写真を取得できませんでした');
  const response=await fetch(img.src);
  if(!response.ok)throw new Error('追加写真を取得できませんでした');
  return response.blob();
}
function download(blob,name){
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
}

async function buildSubmission(){
  updateState();
  if(submit.disabled)return;
  submit.disabled=true;submit.setAttribute('aria-busy','true');submit.textContent='審査用データを作成中…';
  submitStatus.classList.remove('ok','warn');submitStatus.textContent='原画像と投稿情報を安全にまとめています…';
  try{
    const currentRows=rows();
    const existing=existingPhotos();
    const choice=currentChoice();
    const entries=[];
    const newPhotos=[];
    for(let i=0;i<currentRows.length;i++){
      const row=currentRows[i];
      const blob=await blobForRow(row);
      const originalName=row.querySelector('.batch-main strong')?.textContent?.trim()||`photo-${i+1}`;
      const ext=extFor(originalName,blob.type);
      const archivePath=`photos/${String(i+1).padStart(2,'0')}-${safeName(originalName.replace(/\.[^.]+$/,''))}.${ext}`;
      entries.push({name:archivePath,data:blob});
      newPhotos.push({
        key:row.dataset.key||'',
        original_name:originalName,
        archive_path:archivePath,
        content_type:blob.type||'',
        role:choice.type==='new'&&choice.key===(row.dataset.key||'')?'main':'sub'
      });
    }
    const manifest={
      schema_version:1,
      kind:'bantai_university_photo_submission',
      review_status:'pending',
      submitted_at:new Date().toISOString(),
      university_id:select.value,
      university_name:selectedUniversityName(),
      publication_policy:{max_photos:9,main_photos:1,max_sub_photos:8,automatic_publish:false,review_required:true},
      main_choice:choice,
      existing_photos:existing.slice(0,MAX_PHOTOS).map(photo=>({image_url:photo.image_url,alt:photo.alt||'',origin:photo.origin||'existing',role:choice.type==='existing'&&choice.key===photo.image_url?'main':'sub'})),
      new_photos:newPhotos,
      agreements:{rights_confirmed:true,no_ai_redraw:true,bantai_db_publication_permission:true},
      editing_policy:{scene_integrity:'scene_unchanged',ai_redraw:false,allowed:['rotation','straighten','brightness','contrast','crop','resize']},
      note:'This is a review submission package. It does not modify or publish the database automatically.'
    };
    const readme=[
      'Ban.Tai 大学写真 審査用投稿パッケージ',
      '',
      `大学: ${manifest.university_name}`,
      `大学ID: ${manifest.university_id}`,
      `候補写真: ${existing.length+newPhotos.length}枚（最大9枚）`,
      '',
      'このファイルを作成した時点では大学DBへ公開されていません。',
      'Ban.Tai側で大学・権利・個人情報・画質を確認し、承認した写真だけを掲載します。',
      '投稿写真の著作権譲渡ではなく、Ban.Tai大学DBでの掲載利用許諾です。'
    ].join('\n');
    entries.unshift({name:'submission.json',data:enc.encode(JSON.stringify(manifest,null,2))},{name:'README.txt',data:enc.encode(readme)});
    const zip=await makeZip(entries);
    download(zip,`BanTai-University-Photo-Submission-${safeName(manifest.university_name)}-${manifest.university_id}.zip`);
    submitStatus.textContent='審査用データを保存しました。まだ公開はされていません。Ban.Tai側へ渡して確認・承認後に掲載します。';
    submitStatus.classList.add('ok');
    submit.textContent='審査用データを作成しました';
    document.documentElement.dataset.communitySubmissionLast='success';
    setTimeout(()=>{submit.textContent='審査用データを作成';submit.removeAttribute('aria-busy');updateState();},2200);
  }catch(err){
    console.error(err);
    submitStatus.textContent=err.message||'審査用データを作成できませんでした。';
    submitStatus.classList.add('warn');
    submit.textContent='審査用データを作成';
    submit.removeAttribute('aria-busy');
    document.documentElement.dataset.communitySubmissionLast='error';
    updateState();
  }
}
submit.addEventListener('click',buildSubmission);

for(const check of ruleChecks)check.addEventListener('change',updateState);
select.addEventListener('change',()=>setTimeout(updateState,0));
document.addEventListener('click',event=>{
  if(event.target.closest?.('.main-photo-choice-card,.photo-list-delete,.remove-item,.photo-main-button'))setTimeout(updateState,0);
},true);
new MutationObserver(()=>queueMicrotask(updateState)).observe(list,{childList:true,subtree:true});
const choiceHost=document.querySelector('#existing-photo-choice');
if(choiceHost)new MutationObserver(()=>queueMicrotask(updateState)).observe(choiceHost,{childList:true,subtree:true});

// Keep community wording if the legacy one-click layer initializes later.
new MutationObserver(()=>{
  if(exportHeading&&exportHeading.textContent!=='審査用データを作成')exportHeading.textContent='審査用データを作成';
  if(exportLead&&!exportLead.textContent.includes('公開DBへ直接書き込む'))exportLead.textContent='確認した写真・メイン指定・投稿同意を、審査用パッケージとして保存します。公開DBへ直接書き込むことはありません。';
}).observe(exportPanel,{childList:true,subtree:true});

updateState();
})();
