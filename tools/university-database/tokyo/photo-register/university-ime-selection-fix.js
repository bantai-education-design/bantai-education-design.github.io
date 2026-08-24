(()=>{
'use strict';
const input=document.querySelector('#university-first-search');
const select=document.querySelector('#university-first-select');
if(!input||!select)return;
let composing=false;
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');
const rows=[];

function loadRows(){
  return fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'})
    .then(r=>r.ok?r.json():[])
    .then(data=>{rows.splice(0,rows.length,...data);return rows;})
    .catch(()=>rows);
}
function label(u){return `${u.name}（${u.id}）`;}
function candidates(value){
  const q=norm(value);
  if(!q)return [];
  return rows.filter(u=>norm(u.name).includes(q)||norm(u.id).includes(q)||norm(label(u)).includes(q));
}
function confirmCandidate(value){
  if(!rows.length)return;
  const q=norm(value);
  if(!q)return;
  const exact=rows.find(u=>norm(u.name)===q||norm(u.id)===q||norm(label(u))===q);
  const hits=candidates(value);
  const chosen=exact||(hits.length===1?hits[0]:null);
  if(!chosen)return;

  // Restore the full 144-university list before confirming the selected id.
  const current=select.value;
  select.innerHTML='<option value="">大学を選択</option>'+rows.map(u=>`<option value="${u.id}">${label(u)}</option>`).join('');
  select.value=chosen.id;
  input.value=label(chosen);
  if(current!==chosen.id)select.dispatchEvent(new Event('change',{bubbles:true}));
}

// The original input listener rewrites the field while Japanese IME conversion is
// still active. Capture composing input first and keep the text untouched until
// compositionend.
input.addEventListener('compositionstart',()=>{composing=true;},true);
input.addEventListener('input',event=>{
  if(composing||event.isComposing){
    event.stopImmediatePropagation();
    return;
  }
},true);
input.addEventListener('compositionend',()=>{
  composing=false;
  queueMicrotask(()=>confirmCandidate(input.value));
},true);

// After the normal search handler narrows candidates, automatically confirm when
// only one university remains. This removes the extra "select from dropdown" step.
input.addEventListener('input',()=>{
  if(composing)return;
  queueMicrotask(()=>confirmCandidate(input.value));
});
input.addEventListener('blur',()=>{if(!composing)confirmCandidate(input.value);});

loadRows().then(()=>{
  if(input.value&&!select.value)confirmCandidate(input.value);
  document.documentElement.dataset.universityImeFix='ready';
});
})();
