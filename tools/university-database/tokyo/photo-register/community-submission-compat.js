(()=>{
'use strict';
const MAX=9;
let queued=false;
function helper(){return window.__universityPhotoMainChoice||null;}
function total(){return (helper()?.getExistingPhotos?.()||[]).length+document.querySelectorAll('#batch-list .batch-row').length;}
function ensure(){
  queued=false;
  document.body.classList.add('community-photo-submission');

  const progress=document.querySelector('#simple-register-progress');
  if(progress&&progress.querySelectorAll('li').length!==5){
    progress.innerHTML='<li data-step="1"><span>1</span><strong>大学</strong></li><li data-step="2"><span>2</span><strong>写真</strong></li><li data-step="3"><span>3</span><strong>メイン</strong></li><li data-step="4"><span>4</span><strong>ルール</strong></li><li data-step="5"><span>5</span><strong>審査用データ</strong></li>';
  }

  let counter=document.querySelector('#community-photo-counter');
  const photoHead=document.querySelector('.simple-photo-column-head');
  if(photoHead&&!counter){
    counter=document.createElement('div');
    counter.id='community-photo-counter';
    counter.className='community-photo-counter';
    counter.innerHTML='<span>掲載候補</span><strong>0 / 9枚</strong>';
    photoHead.appendChild(counter);
  }
  const count=total();
  if(counter){
    counter.classList.toggle('warn',count>MAX);
    const strong=counter.querySelector('strong');if(strong)strong.textContent=`${count} / ${MAX}枚`;
  }

  const drop=document.querySelector('#drop-zone');
  if(drop){
    const title=drop.querySelector('strong');
    const desc=drop.querySelector(':scope > span:not(.simple-file-picker)');
    const note=drop.querySelector('small');
    if(title)title.textContent='ここに写真をドロップ';
    if(desc)desc.textContent='または、同じ枠からファイルを選択できます';
    if(note)note.textContent='JPEG / PNG / WebP ・ 1大学 最大9枚';
  }

  const real=document.querySelector('#real-page-preview');
  const realHeading=real?.querySelector('h2');
  const realLead=real?.querySelector('p');
  const realButton=document.querySelector('#open-real-preview');
  const realStatus=document.querySelector('#real-preview-status');
  const university=document.querySelector('#university-first-select')?.value||'';
  if(realHeading)realHeading.textContent='大学ページで掲載イメージを確認';
  if(realLead)realLead.textContent='最大9枚。★メイン1枚を大きく表示し、サブ最大8枚を横スクロールのギャラリーで確認します。';
  if(realButton&&realStatus){
    if(!university){realButton.disabled=true;realStatus.textContent='大学を選ぶとプレビューできます。';}
    else if(count===0){realButton.disabled=true;realStatus.textContent='写真を1枚以上確認または追加してください。';}
    else if(count>MAX){realButton.disabled=true;realStatus.textContent=`写真は最大${MAX}枚です（現在${count}枚）。不要な写真を削除してください。`;}
    else{realButton.disabled=false;realStatus.textContent=`${count}枚（メイン1＋サブ最大8）で掲載イメージを確認できます。`;}
  }

  const rows=document.querySelectorAll('#batch-list .batch-row').length;
  const batchStatus=document.querySelector('#batch-status');
  if(batchStatus){
    batchStatus.classList.remove('warn');
    batchStatus.textContent=rows?`${rows}枚を今回追加`:'今回の追加写真なし';
  }

  const editorStep=document.querySelector('#photo-editor .section-head .step');
  if(editorStep)editorStep.textContent='任意';
}
function schedule(){if(queued)return;queued=true;queueMicrotask(ensure);}
new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
document.addEventListener('change',schedule,true);
document.addEventListener('click',event=>{if(event.target.closest?.('.main-photo-choice-card,.photo-list-delete,.remove-item,.photo-main-button'))setTimeout(schedule,0);},true);
ensure();
setTimeout(ensure,300);
setTimeout(ensure,1000);
})();
