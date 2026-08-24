(()=>{
'use strict';
const search=document.querySelector('#university-first-search');
const select=document.querySelector('#university-first-select');
const button=document.querySelector('#university-first-photo-button');
const fileInput=document.querySelector('#university-first-photo');
const mainInput=document.querySelector('#photo-input');
const batchList=document.querySelector('#batch-list');
const status=document.querySelector('#university-first-status');
if(!search||!select||!button||!fileInput||!mainInput||!batchList||!status)return;
let universities=[];
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');
const label=u=>`${u.name}（${u.id}）`;
function optionMarkup(rows,selected=''){
  return '<option value="">大学を選択</option>'+rows.map(u=>`<option value="${u.id}" ${u.id===selected?'selected':''}>${label(u)}</option>`).join('');
}
function matches(q){const n=norm(q);if(!n)return universities;return universities.filter(u=>norm(u.id).includes(n)||norm(u.name).includes(n)||norm(label(u)).includes(n));}
function resolve(q){const n=norm(q);if(!n)return null;const exact=universities.find(u=>norm(u.id)===n||norm(u.name)===n||norm(label(u))===n);if(exact)return exact;const m=matches(q);return m.length===1?m[0]:null;}
function syncButton(){
  const u=universities.find(x=>x.id===select.value);
  button.disabled=!u;
  status.textContent=u?`${u.name} を選択中。写真を選べます。`:'大学を検索またはプルダウンから選択してください。';
}
function applySearch(){
  const current=select.value;
  const rows=matches(search.value);
  select.innerHTML=optionMarkup(rows,current);
  if(current&&rows.some(u=>u.id===current))select.value=current;
  const exact=resolve(search.value);
  if(exact){select.innerHTML=optionMarkup(universities,exact.id);select.value=exact.id;search.value=label(exact);}
  syncButton();
}
search.addEventListener('input',()=>{
  const rows=matches(search.value);
  select.innerHTML=optionMarkup(rows,'');
  const exact=universities.find(u=>norm(u.id)===norm(search.value)||norm(u.name)===norm(search.value)||norm(label(u))===norm(search.value));
  if(exact){select.value=exact.id;}
  syncButton();
});
search.addEventListener('change',applySearch);
search.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();applySearch();}});
select.addEventListener('change',()=>{
  const u=universities.find(x=>x.id===select.value);
  search.value=u?label(u):search.value;
  syncButton();
});
button.addEventListener('click',()=>{if(select.value)fileInput.click();});
fileInput.addEventListener('change',()=>{
  const file=fileInput.files?.[0];
  const universityId=select.value;
  if(!file||!universityId)return;
  const before=batchList.querySelectorAll('.batch-row').length;
  status.textContent='写真を読み込み、大学へ割り当てています…';
  const dt=new DataTransfer();
  dt.items.add(file);
  mainInput.files=dt.files;
  mainInput.dispatchEvent(new Event('change',{bubbles:true}));
  let tries=0;
  const assign=()=>{
    const rows=[...batchList.querySelectorAll('.batch-row')];
    if(rows.length>before){
      const row=rows[rows.length-1];
      const rowSelect=row.querySelector('.row-university');
      if(rowSelect){
        const has=[...rowSelect.options].some(o=>o.value===universityId);
        if(has){
          rowSelect.value=universityId;
          rowSelect.dispatchEvent(new Event('change',{bubbles:true}));
          row.querySelector('.edit-item')?.click();
          const u=universities.find(x=>x.id===universityId);
          status.textContent=`${u?.name||universityId} に写真を割り当てました。`;
          fileInput.value='';
          return;
        }
      }
    }
    if(++tries<120)setTimeout(assign,50);else status.textContent='写真の割り当てを確認してください。';
  };
  setTimeout(assign,50);
});
fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'})
  .then(r=>{if(!r.ok)throw new Error('大学一覧を取得できません');return r.json();})
  .then(rows=>{universities=rows;select.innerHTML=optionMarkup(universities);select.disabled=false;syncButton();})
  .catch(e=>{console.error(e);select.innerHTML='<option value="">大学一覧の読み込みに失敗</option>';status.textContent='大学一覧の読み込みに失敗しました。';});
})();
