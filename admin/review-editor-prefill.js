(()=>{
'use strict';
const FORM_ID='262380787667069';
const params=new URLSearchParams(location.search);
const submission=(params.get('submission')||'').trim();
const input=document.querySelector('#review-submission-id');

function ensureSourceLink(){
  if(!input)return null;
  let link=document.querySelector('#review-source-link');
  if(link)return link;
  link=document.createElement('a');
  link.id='review-source-link';
  link.className='secondary-button';
  link.target='_blank';
  link.rel='noopener';
  link.textContent='この受付をJotformで確認 ↗';
  input.closest('label')?.insertAdjacentElement('afterend',link);
  return link;
}

function updateSourceLink(){
  const link=ensureSourceLink();
  if(!link||!input)return;
  const value=input.value.trim();
  const valid=/^\d+$/.test(value);
  link.hidden=!valid;
  if(valid){
    link.href=`https://www.jotform.com/inbox/${FORM_ID}/${encodeURIComponent(value)}`;
    link.setAttribute('aria-label',`Jotform受付 ${value} を確認`);
  }else{
    link.removeAttribute('href');
  }
}

if(input&&submission&&!input.value.trim()){
  input.value=submission;
  input.dispatchEvent(new Event('input',{bubbles:true}));
}
input?.addEventListener('input',updateSourceLink);
updateSourceLink();
})();
