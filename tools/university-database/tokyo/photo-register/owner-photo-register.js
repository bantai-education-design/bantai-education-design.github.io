(()=>{
'use strict';
const select=document.querySelector('#university-first-select');
const batch=document.querySelector('.batch');
const exportPanel=document.querySelector('.export-panel');
if(!select||!batch||!exportPanel)return;

const setText=(node,text)=>{if(node&&node.textContent!==text)node.textContent=text;};
document.body.classList.add('owner-photo-registration');
document.documentElement.dataset.ownerPhotoRegister='ready';
document.title='Ban.Tai 本人撮影写真を登録・掲載 | Ban.Tai';

setText(document.querySelector('.topbar span'),'東京都大学DB 本人撮影写真 登録・掲載');
const topbar=document.querySelector('.topbar');
if(topbar&&!topbar.querySelector('.owner-review-link')){
  const reviewLink=document.createElement('a');
  reviewLink.className='owner-review-link';
  reviewLink.href='../photo-admin/';
  reviewLink.textContent='訪問者写真を審査';
  topbar.querySelector('a')?.insertAdjacentElement('beforebegin',reviewLink);
}
const hero=document.querySelector('.hero');
setText(hero?.querySelector('.eyebrow'),'BANTAI OWNER PHOTO PUBLISH');
setText(hero?.querySelector('h1'),'Ban.Tai 本人撮影写真を登録・掲載');
setText(hero?.querySelector('p'),'大学を選び、写真を追加・削除し、必要なら傾きや明るさを調整します。メイン写真を1枚決め、最後に「この内容で掲載する」を押します。');
const badges=hero?.querySelector('.rule-badges');
if(badges)badges.innerHTML='<span>1回1大学</span><span>最大9枚</span><span>メイン1＋サブ8</span><span>追加・削除可</span><span>AI再描画なし</span>';

setText(batch.querySelector(':scope > .section-head h2'),'本人撮影写真を登録・更新');
setText(batch.querySelector(':scope > .muted'),'①大学を選ぶ → ②写真を追加・削除してメインを選ぶ → ③必要なら写真を調整 → ④掲載する');

const progress=document.querySelector('#simple-register-progress');
if(progress){
  progress.innerHTML='<li data-step="1"><span>1</span><strong>大学</strong></li><li data-step="2"><span>2</span><strong>写真・メイン</strong></li><li data-step="3"><span>3</span><strong>編集（任意）</strong></li><li data-step="4"><span>4</span><strong>掲載</strong></li>';
}

setText(document.querySelector('#university-first-title'),'大学を選ぶ');
const universityTitle=document.querySelector('#university-first-title');
setText(universityTitle?.parentElement?.querySelector('small'),'文字入力または一覧から1校選択');
setText(document.querySelector('.simple-photo-column-head h2'),'写真を確認・追加・削除');
setText(document.querySelector('.simple-photo-column-head p'),'最大9枚。不要な写真は削除し、★メインを1枚選びます。');

let intro=document.querySelector('#owner-register-intro');
if(!intro){
  intro=document.createElement('div');
  intro.id='owner-register-intro';
  intro.className='owner-register-intro';
  intro.innerHTML='<strong>本人登録はこの画面だけで完結します</strong><span>写真の追加・削除・編集・メイン指定を行い、最後に「この内容で掲載する」を押します。ZIPの保存やChatGPTへの添付は不要です。</span>';
  (document.querySelector('#simple-register-workspace')||progress)?.insertAdjacentElement('beforebegin',intro);
}

const editor=document.querySelector('#photo-editor');
setText(editor?.querySelector('.section-head .step'),'STEP 3・任意');
setText(editor?.querySelector('.section-head h2'),'必要なら写真を編集');

const step=exportPanel.querySelector('.section-head .step');
const heading=exportPanel.querySelector('.section-head h2');
const lead=exportPanel.querySelector(':scope > p');
const badge=exportPanel.querySelector('.surface-badge');
const register=document.querySelector('#generate-batch');
setText(step,'STEP 4');
setText(heading,'この内容で掲載');
setText(lead,'大学・写真・削除内容・メイン写真を確認して掲載します。掲載後も、この画面から写真の追加・削除・編集・メイン変更ができます。');
setText(badge,'公開DBへ反映');
if(register){
  register.hidden=false;
  register.removeAttribute('aria-hidden');
  setText(register,'この内容で掲載する');
}

for(const id of ['download-zip','download-json','copy-json']){
  const node=document.getElementById(id);
  if(node){node.hidden=true;node.setAttribute('aria-hidden','true');}
}
if(document.querySelector('#result'))document.querySelector('#result').hidden=true;
let status=document.querySelector('#owner-publish-status');
if(!status){
  status=document.createElement('p');
  status.id='owner-publish-status';
  status.className='note';
  status.setAttribute('role','status');
  status.textContent='掲載前です。内容を確認して「この内容で掲載する」を押してください。';
  exportPanel.querySelector('.actions')?.insertAdjacentElement('afterend',status);
}

const newButton=document.querySelector('#start-new-photo-registration');
setText(newButton,'＋ 次の大学を登録');
})();