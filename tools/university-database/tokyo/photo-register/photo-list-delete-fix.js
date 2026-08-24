(()=>{
'use strict';
const box=document.querySelector('#existing-photo-choice');
const list=document.querySelector('#batch-list');
const universitySelect=document.querySelector('#university-first-select');
if(!box||!list||!universitySelect)return;

const excludedByUniversity=new Map();
const keyFor=(type,key)=>`${type}:${key}`;
const excludedSet=()=>{
  const id=universitySelect.value||'';
  if(!excludedByUniversity.has(id))excludedByUniversity.set(id,new Set());
  return excludedByUniversity.get(id);
};
const isExcluded=card=>excludedSet().has(keyFor(card.dataset.mainType||'',card.dataset.mainKey||''));

const helper=window.__universityPhotoMainChoice;
if(helper&&typeof helper.getExistingPhotos==='function'&&!helper.__deleteFilterPatched){
  const originalGetExistingPhotos=helper.getExistingPhotos.bind(helper);
  helper.getExistingPhotos=()=>{
    const excluded=excludedSet();
    return originalGetExistingPhotos().filter(photo=>!excluded.has(keyFor('existing',photo.image_url||'')));
  };
  helper.getExcludedPhotos=()=>[...excludedSet()];
  helper.__deleteFilterPatched=true;
}

function chooseFallback(deletedWasMain){
  if(!deletedWasMain)return;
  const next=[...box.querySelectorAll('.main-photo-choice-card')].find(card=>!isExcluded(card)&&card.isConnected);
  if(next)next.click();
}

function deleteCard(card){
  const type=card.dataset.mainType||'';
  const key=card.dataset.mainKey||'';
  if(!type||!key)return;
  const wasMain=card.classList.contains('active');
  excludedSet().add(keyFor(type,key));

  if(type==='new'){
    const row=[...list.querySelectorAll('.batch-row')].find(item=>(item.dataset.key||'')===key);
    const remove=row?.querySelector('.remove-item');
    if(remove){
      remove.click();
      queueMicrotask(()=>{
        applyDeleteControls();
        chooseFallback(wasMain);
      });
      return;
    }
  }

  const wrap=card.closest('.photo-choice-delete-wrap');
  if(wrap)wrap.remove();else card.remove();
  chooseFallback(wasMain);
}

function wrapCard(card){
  if(card.closest('.photo-choice-delete-wrap'))return;
  const wrap=document.createElement('div');
  wrap.className='photo-choice-delete-wrap';
  card.parentNode.insertBefore(wrap,card);
  wrap.appendChild(card);

  const del=document.createElement('button');
  del.type='button';
  del.className='photo-list-delete';
  del.textContent='一覧から削除';
  del.setAttribute('aria-label','この写真を候補一覧から削除');
  del.addEventListener('click',event=>{
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    deleteCard(card);
  });
  wrap.appendChild(del);
}

function applyDeleteControls(){
  for(const card of [...box.querySelectorAll('.main-photo-choice-card')]){
    if(isExcluded(card)){
      card.closest('.photo-choice-delete-wrap')?.remove()||card.remove();
      continue;
    }
    wrapCard(card);
  }
}

const observer=new MutationObserver(()=>queueMicrotask(applyDeleteControls));
observer.observe(box,{childList:true,subtree:true});
universitySelect.addEventListener('change',()=>queueMicrotask(applyDeleteControls));
applyDeleteControls();
})();

(()=>{
  if(document.querySelector('script[data-photo-session-persistence]'))return;
  const s=document.createElement('script');
  s.src='photo-session-persistence.js?v=20260824-1601';
  s.defer=true;
  s.dataset.photoSessionPersistence='true';
  document.body.appendChild(s);
})();
