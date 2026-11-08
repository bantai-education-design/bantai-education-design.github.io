(()=>{
'use strict';
const root=document.querySelector('#detail-root');
if(!root)return;

function install(){
  const hero=root.querySelector('.detail-hero');
  const actions=hero?.querySelector('.detail-actions');
  const heading=hero?.querySelector('h1');
  if(!actions||!heading||actions.querySelector('.university-photo-submit-link'))return;
  const universityName=(heading.textContent||'').trim();
  if(!universityName)return;
  const link=document.createElement('a');
  link.className='secondary university-photo-submit-link';
  link.href=`photo-submit/?university=${encodeURIComponent(universityName)}`;
  link.textContent='📷 この大学の写真を送る';
  link.setAttribute('aria-label',`${universityName}の写真を送る`);
  actions.appendChild(link);
}

install();
const observer=new MutationObserver(()=>queueMicrotask(install));
observer.observe(root,{childList:true,subtree:true});
})();
