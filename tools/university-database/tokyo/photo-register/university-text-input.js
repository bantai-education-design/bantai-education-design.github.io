(()=>{
'use strict';
const list=document.querySelector('#batch-list');
if(!list)return;
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');
let seq=0;
function resolve(select,value){
  const n=norm(value);
  if(!n)return null;
  const options=[...select.options].filter(o=>o.value);
  const exact=options.find(o=>norm(o.value)===n||norm(o.textContent)===n||norm(o.textContent.replace(/（[^）]+）$/,''))===n);
  if(exact)return exact;
  const matches=options.filter(o=>norm(o.value).includes(n)||norm(o.textContent).includes(n));
  return matches.length===1?matches[0]:null;
}
function enhance(row){
  const select=row.querySelector('.row-university');
  if(!select||row.querySelector('.row-university-search'))return;
  const id=`university-search-${++seq}`;
  const dataId=`${id}-list`;
  const input=document.createElement('input');
  input.type='text';
  input.className='row-university-search';
  input.setAttribute('list',dataId);
  input.setAttribute('autocomplete','off');
  input.setAttribute('aria-label','大学名または大学IDを入力');
  input.placeholder='大学名・IDを入力して検索';
  const current=select.options[select.selectedIndex];
  if(select.value&&current)input.value=current.textContent;
  const datalist=document.createElement('datalist');
  datalist.id=dataId;
  for(const option of [...select.options].filter(o=>o.value)){
    const item=document.createElement('option');
    item.value=option.textContent;
    datalist.appendChild(item);
  }
  function apply(){
    const option=resolve(select,input.value);
    if(!option)return;
    if(select.value!==option.value){
      select.value=option.value;
      select.dispatchEvent(new Event('change',{bubbles:true}));
    }
    input.value=option.textContent;
  }
  input.addEventListener('change',apply);
  input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();apply();}});
  select.addEventListener('change',()=>{
    const selected=select.options[select.selectedIndex];
    input.value=select.value&&selected?selected.textContent:'';
  });
  select.insertAdjacentElement('beforebegin',input);
  input.insertAdjacentElement('afterend',datalist);
}
function enhanceAll(){list.querySelectorAll('.batch-row').forEach(enhance);}
new MutationObserver(enhanceAll).observe(list,{childList:true,subtree:true});
enhanceAll();
})();
