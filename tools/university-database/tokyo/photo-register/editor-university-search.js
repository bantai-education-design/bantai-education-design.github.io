(()=>{
'use strict';
const input=document.querySelector('#editor-university-search');
const select=document.querySelector('#university-select');
const list=document.querySelector('#batch-list');
if(!input||!select||!list)return;
function norm(s){return String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');}
function usableOptions(){return [...select.options].filter(o=>o.value);}
function selectedLabel(){const o=select.options[select.selectedIndex];return select.value&&o?o.textContent:'';}
function resolve(value){const n=norm(value);if(!n)return null;const opts=usableOptions();const exact=opts.find(o=>norm(o.value)===n||norm(o.textContent)===n||norm(o.textContent.replace(/（[^）]+）$/,''))===n);if(exact)return exact;const matches=opts.filter(o=>norm(o.value).includes(n)||norm(o.textContent).includes(n));return matches.length===1?matches[0]:null;}
function syncFromSelect(){if(document.activeElement!==input)input.value=selectedLabel();input.placeholder=list.querySelector('.batch-row')?'大学名・大学IDを入力して検索':'写真を入れると、この写真の大学を変更できます';}
function ensureActive(){if(!select.disabled)return true;const first=list.querySelector('.batch-row .edit-item');if(first){first.click();return true;}return false;}
function commit(){if(!ensureActive())return;const option=resolve(input.value);if(!option)return;if(select.value!==option.value){select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));}input.value=option.textContent;}
input.addEventListener('focus',()=>{ensureActive();syncFromSelect();});
input.addEventListener('change',commit);
input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commit();}});
select.addEventListener('change',()=>queueMicrotask(syncFromSelect));
new MutationObserver(()=>queueMicrotask(syncFromSelect)).observe(select,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled']});
new MutationObserver(()=>queueMicrotask(syncFromSelect)).observe(list,{childList:true,subtree:true});
syncFromSelect();
})();
