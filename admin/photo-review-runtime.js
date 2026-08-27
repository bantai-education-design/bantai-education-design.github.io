(()=>{
'use strict';
const upload=document.querySelector('#status-upload');
const notify=document.querySelector('#status-notification');
const note=document.querySelector('#status-note');
const warning=document.querySelector('#connection-warning');
const reviewText=document.querySelector('#review-description');
const reviewButton=document.querySelector('#review-button');

function setStatus(node,text,ok){
  if(!node)return;
  const strong=node.querySelector('strong');
  if(strong)strong.textContent=text;
  node.classList.toggle('ok',ok);
  node.classList.toggle('waiting',!ok);
}

function applyDisconnected(){
  setStatus(upload,'未接続',false);
  setStatus(notify,'停止中',false);
  if(note)note.textContent='受信接続が完了するまでは、投稿写真は管理受信箱へ届かず、メール通知も行いません。';
  if(warning)warning.hidden=false;
  if(reviewText)reviewText.textContent='受信フォームの接続後、ここから審査待ち写真へ1クリックで入れるようになります。';
  if(reviewButton){
    reviewButton.removeAttribute('href');
    reviewButton.setAttribute('aria-disabled','true');
    reviewButton.textContent='受信接続待ち';
  }
}

function applyConnected(config){
  const formId=String(config.form_id||'').trim();
  if(!/^\d+$/.test(formId)){applyDisconnected();return;}
  setStatus(upload,'接続済み',true);
  setStatus(notify,'即時通知',true);
  if(note)note.textContent='新しい投稿はJotformで受信し、投稿ごとに管理者へ即時通知します。';
  if(warning)warning.hidden=true;
  if(reviewText)reviewText.textContent='投稿写真・大学名・投稿日時をJotform Inboxで確認します。';
  if(reviewButton){
    reviewButton.href=`https://www.jotform.com/inbox/${formId}`;
    reviewButton.target='_blank';
    reviewButton.rel='noopener';
    reviewButton.removeAttribute('aria-disabled');
    reviewButton.innerHTML='審査待ち写真を見る <span aria-hidden="true">↗</span>';
  }
}

fetch('photo-review-config.json',{cache:'no-store'})
  .then(r=>r.ok?r.json():Promise.reject(new Error('config')))
  .then(config=>{
    if(config.enabled===true&&config.provider==='jotform')applyConnected(config);
    else applyDisconnected();
  })
  .catch(applyDisconnected);
})();
