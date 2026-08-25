(()=>{
'use strict';
const MAX=9;
let queued=false;
const setText=(node,text)=>{if(node&&node.textContent!==text)node.textContent=text;};
function helper(){return window.__universityPhotoMainChoice||null;}
function total(){return (helper()?.getExistingPhotos?.()||[]).length+document.querySelectorAll('#batch-list .batch-row').length;}
function ensure(){
  queued=false;
  document.body.classList.add('community-photo-submission');
  const count=total();
  const counter=document.querySelector('#community-photo-counter strong');
  setText(counter,`${count} / ${MAX}枚`);
  document.querySelector('#community-photo-counter')?.classList.toggle('warn',count>MAX);

  const drop=document.querySelector('#drop-zone');
  if(drop){
    setText(drop.querySelector('strong'),'ここに写真をドロップ');
    setText(drop.querySelector(':scope > span:not(.simple-file-picker)'),'または、同じ枠からファイルを選択できます');
    setText(drop.querySelector('small'),'JPEG / PNG / WebP ・ 1大学 最大9枚');
  }

  const real=document.querySelector('#real-page-preview');
  setText(real?.querySelector('h2'),'大学ページで掲載イメージを確認');
  setText(real?.querySelector('p'),'★メイン1枚を大きく表示し、サブ最大8枚を横スクロールで確認します。');
  const button=document.querySelector('#open-real-preview');
  const status=document.querySelector('#real-preview-status');
  const university=document.querySelector('#university-first-select')?.value||'';
  if(button&&status){
    if(!university){button.disabled=true;setText(status,'大学を選ぶとプレビューできます。');}
    else if(count===0){button.disabled=true;setText(status,'写真を1枚以上確認または追加してください。');}
    else if(count>MAX){button.disabled=true;setText(status,`写真は最大${MAX}枚です（現在${count}枚）。`);}
    else{button.disabled=false;setText(status,`${count}枚で掲載イメージを確認できます。`);}
  }

  const rows=document.querySelectorAll('#batch-list .batch-row').length;
  const batchStatus=document.querySelector('#batch-status');
  if(batchStatus){batchStatus.classList.remove('warn');setText(batchStatus,rows?`${rows}枚を今回追加`:'今回の追加写真なし');}
}
function schedule(){if(queued)return;queued=true;queueMicrotask(ensure);}
new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
document.addEventListener('change',schedule,true);
document.addEventListener('click',event=>{if(event.target.closest?.('.main-photo-choice-card,.photo-list-delete,.remove-item,.photo-main-button'))setTimeout(schedule,0);},true);
ensure();
setTimeout(ensure,300);
})();