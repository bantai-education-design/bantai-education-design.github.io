(()=>{
'use strict';
const editor=document.querySelector('#photo-editor');
const canvas=document.querySelector('#preview');
const posX=document.querySelector('#pos-x');
const posY=document.querySelector('#pos-y');
const fileInfo=document.querySelector('#file-info');
if(!editor||!canvas||!posX||!posY)return;

const clamp=(n,min=0,max=100)=>Math.min(max,Math.max(min,n));
const refreshSubmission=()=>queueMicrotask(()=>window.__bantaiCommunityPhotoSubmission?.updateState?.());

let hint=document.querySelector('#editor-drag-hint');
if(!hint){
  hint=document.createElement('div');
  hint.id='editor-drag-hint';
  hint.className='editor-drag-hint';
  hint.innerHTML='<strong>写真を直接動かせます</strong><span>プレビュー上の写真をマウスでつかみ、上下左右へドラッグしてください。左右位置・上下位置の数値にも同期します。</span>';
  const shell=canvas.closest('.preview-shell');
  shell?.insertAdjacentElement('beforebegin',hint);
}
canvas.classList.add('editor-pan-canvas');
canvas.setAttribute('aria-label','写真補正プレビュー。写真をドラッグして上下左右の位置を調整できます');

let drag=null;
function hasEditablePhoto(){
  return fileInfo?.textContent?.trim()&&fileInfo.textContent.trim()!=='編集対象なし';
}
function emitRange(input,value){
  input.value=String(Math.round(clamp(value)));
  input.dispatchEvent(new Event('input',{bubbles:true}));
}
function openEditorFromRow(){
  if(editor.hidden)editor.hidden=false;
  const toggle=document.querySelector('#community-editor-toggle');
  if(toggle)toggle.textContent='写真調整を閉じる';
  editor.classList.add('community-editor-opened-from-row');
}
function startDrag(event){
  if(!hasEditablePhoto())return;
  if(event.button!==undefined&&event.button!==0)return;
  const rect=canvas.getBoundingClientRect();
  if(!rect.width||!rect.height)return;
  drag={
    pointerId:event.pointerId,
    clientX:event.clientX,
    clientY:event.clientY,
    x:Number(posX.value)||50,
    y:Number(posY.value)||50,
    width:rect.width,
    height:rect.height
  };
  canvas.classList.add('is-dragging');
  canvas.setPointerCapture?.(event.pointerId);
  event.preventDefault();
}
function moveDrag(event){
  if(!drag||event.pointerId!==drag.pointerId)return;
  const dx=event.clientX-drag.clientX;
  const dy=event.clientY-drag.clientY;
  // Core renderer uses smaller position values to move the image right/down.
  emitRange(posX,drag.x-(dx/drag.width)*100);
  emitRange(posY,drag.y-(dy/drag.height)*100);
  refreshSubmission();
  event.preventDefault();
}
function endDrag(event){
  if(!drag||event.pointerId!==drag.pointerId)return;
  try{canvas.releasePointerCapture?.(event.pointerId);}catch(_e){}
  drag=null;
  canvas.classList.remove('is-dragging');
  refreshSubmission();
}

canvas.addEventListener('pointerdown',startDrag);
// Track movement at document level once dragging begins. This keeps the drag
// stable even when the pointer leaves the canvas or layout/scroll position moves.
document.addEventListener('pointermove',moveDrag,true);
document.addEventListener('pointerup',endDrag,true);
document.addEventListener('pointercancel',endDrag,true);
canvas.addEventListener('lostpointercapture',()=>{drag=null;canvas.classList.remove('is-dragging');refreshSubmission();});

// Editing is optional. Opening it or changing an adjustment must not invalidate
// an otherwise valid community submission.
editor.addEventListener('input',refreshSubmission,true);
editor.addEventListener('change',refreshSubmission,true);
editor.addEventListener('click',event=>{
  if(event.target.closest?.('#rotate-left,#rotate-right,#reset-adjustments,#delete-active-photo'))setTimeout(refreshSubmission,0);
},true);
document.addEventListener('click',event=>{
  if(event.target.closest?.('.edit-item')){
    openEditorFromRow();
    // Use an immediate scroll here. A smooth scroll can still be moving when the
    // user starts dragging, making pointer coordinates refer to a moving canvas.
    setTimeout(()=>editor.scrollIntoView({behavior:'auto',block:'start'}),0);
    setTimeout(refreshSubmission,0);
    setTimeout(refreshSubmission,250);
    return;
  }
  if(event.target.closest?.('#community-editor-toggle')){
    setTimeout(refreshSubmission,0);
    setTimeout(refreshSubmission,250);
  }
},true);

document.documentElement.dataset.editorDragPan='ready';
})();
