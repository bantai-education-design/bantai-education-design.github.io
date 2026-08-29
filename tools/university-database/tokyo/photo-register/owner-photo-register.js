(()=>{
'use strict';
const select=document.querySelector('#university-first-select');
const batch=document.querySelector('.batch');
const exportPanel=document.querySelector('.export-panel');
if(!select||!batch||!exportPanel)return;

const setText=(node,text)=>{if(node&&node.textContent!==text)node.textContent=text;};
document.body.classList.add('owner-photo-registration');
document.documentElement.dataset.ownerPhotoRegister='ready';
document.title='Ban.Tai 本人撮影写真を登録 | Ban.Tai';

setText(document.querySelector('.topbar span'),'東京都大学DB 本人撮影写真登録');
const topbar=document.querySelector('.topbar');
if(topbar&&!topbar.querySelector('.owner-review-link')){
  const reviewLink=document.createElement('a');
  reviewLink.className='owner-review-link';
  reviewLink.href='../photo-admin/';
  reviewLink.textContent='訪問者写真を審査';
  topbar.querySelector('a')?.insertAdjacentElement('beforebegin',reviewLink);
}
const hero=document.querySelector('.hero');
setText(hero?.querySelector('.eyebrow'),'BANTAI OWNER QUICK REGISTER');
setText(hero?.querySelector('h1'),'Ban.Tai 本人撮影写真を登録');
setText(hero?.querySelector('p'),'自分で撮影した大学写真を1大学ずつ掲載準備します。大学を選び、写真とメインを決め、必要なら傾きなどを調整して掲載用ZIPを作成します。');
const badges=hero?.querySelector('.rule-badges');
if(badges)badges.innerHTML='<span>1回1大学</span><span>最大9枚</span><span>メイン1＋サブ8</span><span>AI再描画なし</span><span>GitHub反映前に確認</span>';

setText(batch.querySelector(':scope > .section-head h2'),'本人撮影写真のクイック登録');
setText(batch.querySelector(':scope > .muted'),'①大学を選ぶ → ②写真を追加・メインを選ぶ → ③必要なら写真を調整 → ④掲載用ZIPを作成');

const progress=document.querySelector('#simple-register-progress');
if(progress){
  progress.innerHTML='<li data-step="1"><span>1</span><strong>大学</strong></li><li data-step="2"><span>2</span><strong>写真・メイン</strong></li><li data-step="3"><span>3</span><strong>調整（任意）</strong></li><li data-step="4"><span>4</span><strong>掲載準備</strong></li>';
}

setText(document.querySelector('#university-first-title'),'大学を選ぶ');
const universityTitle=document.querySelector('#university-first-title');
setText(universityTitle?.parentElement?.querySelector('small'),'文字入力または一覧から1校選択');
setText(document.querySelector('.simple-photo-column-head h2'),'写真を確認・追加');
setText(document.querySelector('.simple-photo-column-head p'),'最大9枚。★メインを1枚選び、必要な写真だけ編集します。');

let intro=document.querySelector('#owner-register-intro');
if(!intro){
  intro=document.createElement('div');
  intro.id='owner-register-intro';
  intro.className='owner-register-intro';
  intro.innerHTML='<strong>Ban.Tai本人撮影の掲載準備</strong><span>黄色の「掲載用ZIPを作成（まだ公開されません）」を押すと掲載用ZIPを保存します。そのZIPをこのチャットに添付してください。大学DB反映・CI・PR・mainへのマージはChatGPT側で確認して行います。</span>';
  (document.querySelector('#simple-register-workspace')||progress)?.insertAdjacentElement('beforebegin',intro);
}

const editor=document.querySelector('#photo-editor');
setText(editor?.querySelector('.section-head .step'),'STEP 3・任意');
setText(editor?.querySelector('.section-head h2'),'必要なら写真を調整');

const step=exportPanel.querySelector('.section-head .step');
const heading=exportPanel.querySelector('.section-head h2');
const lead=exportPanel.querySelector(':scope > p');
const badge=exportPanel.querySelector('.surface-badge');
const register=document.querySelector('#generate-batch');
setText(step,'STEP 4');
setText(heading,'掲載用ZIPを作成');
setText(lead,'大学・写真・メインを確認して掲載用ZIPを作成します。この時点では公開DBは変更されません。ZIPをこのチャットへ添付後、ChatGPT側でGitHub反映・CI・PR・mainマージを行います。');
setText(badge,'GitHub反映前に確認');
if(register){
  register.hidden=false;
  register.removeAttribute('aria-hidden');
  setText(register,'掲載用ZIPを作成（まだ公開されません）');
}

const newButton=document.querySelector('#start-new-photo-registration');
setText(newButton,'＋ 次の大学を登録');
})();