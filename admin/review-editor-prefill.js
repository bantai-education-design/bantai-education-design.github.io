(()=>{
'use strict';
const params=new URLSearchParams(location.search);
const submission=(params.get('submission')||'').trim();
const input=document.querySelector('#review-submission-id');
if(input&&submission&&!input.value.trim()){
  input.value=submission;
  input.dispatchEvent(new Event('input',{bubbles:true}));
}
})();
