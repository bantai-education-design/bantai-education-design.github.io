(()=>{
'use strict';
const legacyChooser=document.querySelector('.university-first');
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const selectLabel=select?.closest('label');
const searchLabel=search?.closest('label');
if(!legacyChooser||!select||!search||!selectLabel||!searchLabel)return;

let panel=document.querySelector('#community-university-chooser');
if(!panel){
  panel=document.createElement('section');
  panel.id='community-university-chooser';
  panel.className='community-university-chooser';
  panel.innerHTML='<div class="community-university-heading"><span>STEP 1</span><div><h2>大学を選ぶ</h2><p>大学名を入力するか、一覧から1校選んでください。</p></div></div>';
}

function moveFields(){
  const left=document.querySelector('#simple-register-workspace .simple-university-column');
  const fallback=document.querySelector('#simple-register-workspace')||document.querySelector('#simple-register-progress')?.parentElement||legacyChooser.parentElement;
  const host=left||fallback;
  if(host&&panel.parentElement!==host){
    if(left)left.prepend(panel);else host.insertBefore(panel,host.firstChild||null);
  }
  if(searchLabel.parentElement!==panel)panel.appendChild(searchLabel);
  if(selectLabel.parentElement!==panel)panel.appendChild(selectLabel);
  searchLabel.hidden=false;
  selectLabel.hidden=false;
  search.disabled=false;
  select.disabled=false;
  search.removeAttribute('aria-hidden');
  select.removeAttribute('aria-hidden');

  // The old shell still contains existing-photo choices and internal compatibility
  // controls, but no longer owns the public university inputs that were being moved.
  legacyChooser.classList.add('community-legacy-university-shell');
  legacyChooser.querySelector('.start-choice-head')?.setAttribute('aria-hidden','true');
  document.documentElement.dataset.communityUniversityChooser=left?'stable':'waiting-workspace';
  return !!left;
}

moveFields();
const observer=new MutationObserver(()=>{
  if(moveFields()){
    requestAnimationFrame(()=>{
      if(moveFields())observer.disconnect();
    });
  }
});
observer.observe(document.body,{childList:true,subtree:true});
window.addEventListener('load',moveFields,{once:true});
setTimeout(moveFields,120);
setTimeout(moveFields,500);
})();