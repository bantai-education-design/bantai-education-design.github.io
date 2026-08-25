(()=>{
'use strict';
const chooser=document.querySelector('.university-first');
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const selectLabel=select?.closest('label');
const searchLabel=search?.closest('label');
if(!chooser||!select||!search||!selectLabel||!searchLabel)return;

let repairing=false;
let scheduled=false;
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
    // Do not write the observed class attribute when nothing needs changing.
    // An unconditional classList.remove() here re-triggered this observer forever,
    // starving later dynamically loaded scripts and preventing networkidle.
    if(chooser.classList.contains('community-legacy-university-shell')){
      chooser.classList.remove('community-legacy-university-shell');
    }
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
function schedule(){
  if(scheduled)return;
  scheduled=true;
  queueMicrotask(()=>{scheduled=false;stabilize();});
}

// Watch only the controls that can affect chooser actionability. Observing every
// class/style mutation under document.body caused a feedback storm while legacy
// layout helpers were rendering photo cards and moving compatibility panels.
const controlObserver=new MutationObserver(schedule);
controlObserver.observe(select,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled','aria-hidden']});
controlObserver.observe(search,{attributes:true,attributeFilter:['disabled','aria-hidden']});
controlObserver.observe(selectLabel,{attributes:true,attributeFilter:['hidden','aria-hidden']});
controlObserver.observe(searchLabel,{attributes:true,attributeFilter:['hidden','aria-hidden']});
controlObserver.observe(chooser,{attributes:true,attributeFilter:['hidden','aria-hidden','class']});

select.addEventListener('focus',stabilize,true);
select.addEventListener('pointerdown',stabilize,true);
search.addEventListener('focus',stabilize,true);
window.addEventListener('load',stabilize,{once:true});
stabilize();
setTimeout(stabilize,120);
setTimeout(stabilize,500);
setTimeout(stabilize,1200);
})();
