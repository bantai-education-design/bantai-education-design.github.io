(()=>{
'use strict';
const chooser=document.querySelector('.university-first');
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const selectLabel=select?.closest('label');
const searchLabel=search?.closest('label');
if(!chooser||!select||!search||!selectLabel||!searchLabel)return;

let repairing=false;
function stabilize(){
  if(repairing)return false;
  repairing=true;
  try{
    const left=document.querySelector('#simple-register-workspace .simple-university-column');
    if(!left){
      document.documentElement.dataset.communityUniversityChooser='waiting-workspace';
      return false;
    }

    // Keep the original university panel intact. Moving only its form fields between
    // containers caused actionability races while older layout observers were active.
    if(chooser.parentElement!==left)left.prepend(chooser);
    if(chooser.hidden)chooser.hidden=false;
    if(chooser.getAttribute('aria-hidden')==='true')chooser.removeAttribute('aria-hidden');
    chooser.classList.remove('community-legacy-university-shell');
    if(selectLabel.hidden)selectLabel.hidden=false;
    if(searchLabel.hidden)searchLabel.hidden=false;
    if(select.getAttribute('aria-hidden')==='true')select.removeAttribute('aria-hidden');
    if(search.getAttribute('aria-hidden')==='true')search.removeAttribute('aria-hidden');
    const ready=select.options.length>1;
    if(ready&&select.disabled)select.disabled=false;
    if(search.disabled)search.disabled=false;
    document.documentElement.dataset.communityUniversityChooser=ready?'stable':'loading-options';
    return ready;
  }finally{
    repairing=false;
  }
}

const observer=new MutationObserver(()=>queueMicrotask(stabilize));
observer.observe(document.body,{
  childList:true,
  subtree:true,
  attributes:true,
  attributeFilter:['hidden','disabled','aria-hidden','class','style']
});
select.addEventListener('focus',stabilize,true);
select.addEventListener('pointerdown',stabilize,true);
search.addEventListener('focus',stabilize,true);
window.addEventListener('load',stabilize,{once:true});
stabilize();
setTimeout(stabilize,120);
setTimeout(stabilize,500);
setTimeout(stabilize,1200);
})();