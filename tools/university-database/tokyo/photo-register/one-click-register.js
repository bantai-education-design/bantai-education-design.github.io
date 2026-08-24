(()=>{
'use strict';
const panel=document.querySelector('.export-panel');
const register=document.querySelector('#generate-batch');
const downloadZip=document.querySelector('#download-zip');
const downloadJson=document.querySelector('#download-json');
const copyJson=document.querySelector('#copy-json');
const result=document.querySelector('#result');
const jsonOutput=document.querySelector('#json-output');
if(!panel||!register||!downloadZip||!downloadJson||!copyJson||!result||!jsonOutput)return;

const step=panel.querySelector('.section-head .step');
const heading=panel.querySelector('.section-head h2');
const lead=panel.querySelector(':scope > p');
const badge=panel.querySelector('.surface-badge');
const resultHeading=result.querySelector('h3');
const resultDetails=result.querySelector('dl');
const resultNote=result.querySelector('p');

if(step)step.textContent='STEP 4';
if(heading)heading.textContent='この内容で大学DBへ登録';
if(lead)lead.textContent='写真とメインを確認したら、このボタン1つで登録用データを準備します。公開反映はChatGPTで最終確認します。';
if(badge)badge.textContent='安全確認後に反映';
register.textContent='この内容で大学DBへ登録';
register.classList.add('one-click-register-button');
panel.classList.add('one-click-register-panel');
result.classList.add('one-click-register-result');
if(resultDetails)resultDetails.hidden=true;
jsonOutput.hidden=true;
for(const control of [downloadZip,downloadJson,copyJson]){
  control.hidden=true;
  control.setAttribute('aria-hidden','true');
  control.tabIndex=-1;
}
if(resultNote)resultNote.textContent='登録用データは自動で保存されます。保存された登録ファイルをこのチャットに添付してください。こちらで大学DBへの反映・CI・PR・mainへのマージまで行います。';

document.documentElement.dataset.oneClickRegister='ready';
let pending=false;
let startedAt=0;
let timer=0;

function restoreLabel(){
  if(pending)return;
  if(register.textContent==='一括ZIPを生成'||register.textContent==='登録データを準備しました')register.textContent='この内容で大学DBへ登録';
}

function finish(success,message){
  pending=false;
  clearTimeout(timer);
  panel.classList.remove('is-registering');
  register.removeAttribute('aria-busy');
  if(success){
    register.textContent='登録データを準備しました';
    result.hidden=false;
    if(resultHeading)resultHeading.textContent='登録データを準備しました';
    if(resultNote)resultNote.textContent='登録用データを保存しました。このチャットに添付してください。こちらで大学DBへの反映・CI・PR・mainへのマージまで行います。';
    document.documentElement.dataset.oneClickRegisterLast='success';
    timer=setTimeout(restoreLabel,2600);
  }else{
    register.textContent='この内容で大学DBへ登録';
    result.hidden=false;
    if(resultHeading)resultHeading.textContent='登録データを準備できませんでした';
    if(resultNote)resultNote.textContent=message||'写真と大学の選択内容を確認して、もう一度登録してください。';
    document.documentElement.dataset.oneClickRegisterLast='error';
  }
}

function waitForPackage(){
  if(!pending)return;
  if(!downloadZip.disabled){
    try{
      downloadZip.click();
      finish(true);
    }catch(err){
      console.error(err);
      finish(false,'登録用データの保存を開始できませんでした。ブラウザのダウンロード設定を確認してください。');
    }
    return;
  }
  if(Date.now()-startedAt>25000){
    finish(false,'登録用データの準備に時間がかかっています。写真と大学の選択内容を確認してください。');
    return;
  }
  timer=setTimeout(waitForPackage,80);
}

register.addEventListener('click',()=>{
  if(pending)return;
  pending=true;
  startedAt=Date.now();
  panel.classList.add('is-registering');
  register.setAttribute('aria-busy','true');
  timer=setTimeout(waitForPackage,80);
},{capture:true});

new MutationObserver(()=>{
  if(!pending&&register.textContent==='一括ZIPを生成')register.textContent='この内容で大学DBへ登録';
}).observe(register,{childList:true,subtree:true});
})();
