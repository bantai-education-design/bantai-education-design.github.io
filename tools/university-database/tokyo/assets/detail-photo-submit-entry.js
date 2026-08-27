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
  link.textContent='📷 写真を投稿';
  link.setAttribute('aria-label',`${universityName}へ写真を投稿`);
  actions.appendChild(link);
}

install();
const observer=new MutationObserver(()=>queueMicrotask(install));
observer.observe(root,{childList:true,subtree:true});
})();
