(()=>{
'use strict';
const controls=document.querySelector('#photo-editor .controls');
const generate=document.querySelector('#generate-batch');
const exportPanel=document.querySelector('.export-panel');
if(!controls||!generate||!exportPanel||document.querySelector('#finish-edit-register'))return;
const wrap=document.createElement('div');
wrap.className='finish-edit-register-wrap';
wrap.innerHTML=`<button id="finish-edit-register" class="primary finish-edit-register" type="button">編集を終えて登録</button><small>現在の補正内容でSTEP 3へ進み、登録パッケージを作ります。</small>`;
controls.appendChild(wrap);
const button=wrap.querySelector('#finish-edit-register');
button.addEventListener('click',()=>{
  exportPanel.scrollIntoView({behavior:'smooth',block:'start'});
  exportPanel.classList.add('register-target');
  setTimeout(()=>exportPanel.classList.remove('register-target'),1600);
  if(!generate.disabled){
    setTimeout(()=>generate.click(),250);
  }else{
    const note=wrap.querySelector('small');
    note.textContent='大学・写真の割り当てを確認してください。登録可能になるとSTEP 3の生成を開始します。';
  }
});
})();
