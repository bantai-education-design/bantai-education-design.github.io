(()=>{
'use strict';
const chooser=document.querySelector('.university-first');
const select=document.querySelector('#university-first-select');
const search=document.querySelector('#university-first-search');
if(!chooser||!select||!search)return;

let scheduled=false;
function stabilize(){
  scheduled=false;
  const left=document.querySelector('#simple-register-workspace .simple-university-column');
  if(left&&chooser.parentElement!==left)left.prepend(chooser);
  chooser.hidden=false;
  chooser.removeAttribute('aria-hidden');
  const selectLabel=select.closest('label');
  const searchLabel=search.closest('label');
  if(selectLabel)selectLabel.hidden=false;
  if(searchLabel)searchLabel.hidden=false;
  select.disabled=false;
  search.disabled=false;
  document.documentElement.dataset.communityUniversityChooser='stable';
}
function schedule(){
  if(scheduled)return;
  scheduled=true;
  requestAnimationFrame(stabilize);
}

new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});
window.addEventListener('load',stabilize,{once:true});
stabilize();
setTimeout(stabilize,150);
setTimeout(stabilize,600);
setTimeout(stabilize,1400);
})();