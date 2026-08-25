(()=>{
'use strict';
const chooser=document.querySelector('.university-first');
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
const selectLabel=select?.closest('label');
const searchLabel=search?.closest('label');
if(!chooser||!select||!search||!selectLabel||!searchLabel)return;

function stabilize(){
  const left=document.querySelector('#simple-register-workspace .simple-university-column');
  if(!left){
    document.documentElement.dataset.communityUniversityChooser='waiting-workspace';
    return false;
  }

  // Keep the original university panel intact. Moving only its form fields between
  // containers caused actionability races while older layout observers were active.
  if(chooser.parentElement!==left)left.prepend(chooser);
  chooser.hidden=false;
  chooser.removeAttribute('aria-hidden');
  chooser.classList.remove('community-legacy-university-shell');
  selectLabel.hidden=false;
  searchLabel.hidden=false;
  select.removeAttribute('aria-hidden');
  search.removeAttribute('aria-hidden');
  select.disabled=select.options.length<=1;
  search.disabled=false;
  document.documentElement.dataset.communityUniversityChooser=select.disabled?'loading-options':'stable';
  return !select.disabled;
}

stabilize();
const observer=new MutationObserver(()=>{
  if(stabilize()){
    requestAnimationFrame(()=>{
      if(stabilize())observer.disconnect();
    });
  }
});
observer.observe(document.body,{childList:true,subtree:true});
window.addEventListener('load',stabilize,{once:true});
setTimeout(stabilize,120);
setTimeout(stabilize,500);
})();