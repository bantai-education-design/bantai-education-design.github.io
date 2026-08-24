(()=>{
'use strict';
const $=s=>document.querySelector(s);
const firstSearch=$('#university-first-search');
const firstSelect=$('#university-first-select');
const firstButton=$('#university-first-photo-button');
const firstFile=$('#university-first-photo');
const mainFile=$('#photo-input');
const batchList=$('#batch-list');
const firstStatus=$('#university-first-status');
const editorSearch=$('#editor-university-search');
const editorSelect=$('#university-select');
const deleteActive=$('#delete-active-photo');
if(!firstSearch||!firstSelect||!firstButton||!firstFile||!mainFile||!batchList||!firstStatus||!editorSearch||!editorSelect||!deleteActive)return;
let universities=[];
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');
const label=u=>`${u.name}（${u.id}）`;
const optionMarkup=(rows,selected='')=>'<option value="">大学を選択</option>'+rows.map(u=>`<option value="${u.id}" ${u.id===selected?'selected':''}>${label(u)}</option>`).join('');
const matches=q=>{const n=norm(q);if(!n)return universities;return universities.filter(u=>norm(u.id).includes(n)||norm(u.name).includes(n)||norm(label(u)).includes(n));};
const exact=q=>{const n=norm(q);if(!n)return null;return universities.find(u=>norm(u.id)===n||norm(u.name)===n||norm(label(u))===n)||null;};
function selectedUniversity(select){return universities.find(u=>u.id===select.value)||null;}
function setFirstStatus(){const u=selectedUniversity(firstSelect);firstButton.disabled=!u;firstStatus.textContent=u?`${u.name} を選択中。写真を選べます。`:'大学名を入力するか、下の144大学一覧から選択してください。';}
function renderFirst(rows,selected=''){firstSelect.innerHTML=optionMarkup(rows,selected);if(selected&&rows.some(u=>u.id===selected))firstSelect.value=selected;setFirstStatus();}
function commitFirstSearch(){const u=exact(firstSearch.value)||((m=>m.length===1?m[0]:null)(matches(firstSearch.value)));if(!u)return;renderFirst(universities,u.id);firstSearch.value=label(u);}
firstSearch.addEventListener('input',()=>{const rows=matches(firstSearch.value);const u=exact(firstSearch.value);renderFirst(rows,u?.id||'');});
firstSearch.addEventListener('change',commitFirstSearch);
firstSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitFirstSearch();}});
firstSelect.addEventListener('change',()=>{const u=selectedUniversity(firstSelect);if(u)firstSearch.value=label(u);setFirstStatus();});
firstButton.addEventListener('click',()=>{if(!firstButton.disabled)firstFile.click();});
firstFile.addEventListener('change',()=>{const file=firstFile.files?.[0],universityId=firstSelect.value;if(!file||!universityId)return;const before=batchList.querySelectorAll('.batch-row').length;firstStatus.textContent='写真を読み込み、大学へ割り当てています…';const dt=new DataTransfer();dt.items.add(file);mainFile.files=dt.files;mainFile.dispatchEvent(new Event('change',{bubbles:true}));let tries=0;const finish=()=>{const rows=[...batchList.querySelectorAll('.batch-row')];if(rows.length>before){const row=rows[rows.length-1],rowSelect=row.querySelector('.row-university');if(rowSelect&&[...rowSelect.options].some(o=>o.value===universityId)){rowSelect.value=universityId;rowSelect.dispatchEvent(new Event('change',{bubbles:true}));row.querySelector('.edit-item')?.click();const u=universities.find(x=>x.id===universityId);firstStatus.textContent=`${u?.name||universityId} に写真を割り当てました。間違えた場合は「写真を削除」で取り消せます。`;firstFile.value='';return;}}if(++tries<160)setTimeout(finish,50);else firstStatus.textContent='写真は追加されました。大学の割り当てを写真一覧で確認してください。';};setTimeout(finish,50);});
function syncEditorSearch(){const u=selectedUniversity(editorSelect);if(document.activeElement!==editorSearch)editorSearch.value=u?label(u):'';editorSearch.placeholder=editorSelect.disabled?'写真一覧で「編集」を押してください':'大学名・大学IDを入力';}
function renderEditor(rows,selected=''){if(editorSelect.disabled)return;editorSelect.innerHTML=optionMarkup(rows,selected);if(selected&&rows.some(u=>u.id===selected))editorSelect.value=selected;}
function ensureEditorActive(){if(!editorSelect.disabled)return true;const edit=batchList.querySelector('.batch-row .edit-item');if(!edit)return false;edit.click();return !editorSelect.disabled;}
function commitEditorSearch(){if(!ensureEditorActive())return;const u=exact(editorSearch.value)||((m=>m.length===1?m[0]:null)(matches(editorSearch.value)));if(!u)return;renderEditor(universities,u.id);editorSelect.value=u.id;editorSelect.dispatchEvent(new Event('change',{bubbles:true}));editorSearch.value=label(u);}
editorSearch.addEventListener('focus',()=>{ensureEditorActive();syncEditorSearch();});
editorSearch.addEventListener('input',()=>{if(!ensureEditorActive())return;const rows=matches(editorSearch.value);const u=exact(editorSearch.value);renderEditor(rows,u?.id||editorSelect.value);});
editorSearch.addEventListener('change',commitEditorSearch);
editorSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitEditorSearch();}});
editorSelect.addEventListener('change',()=>queueMicrotask(syncEditorSearch));
function enhanceDeleteControls(){
  batchList.querySelectorAll('.remove-item').forEach(btn=>{
    if(btn.textContent!=='写真を削除')btn.textContent='写真を削除';
    if(btn.getAttribute('aria-label')!=='この写真を一覧から削除')btn.setAttribute('aria-label','この写真を一覧から削除');
  });
  const activeRemove=batchList.querySelector('.batch-row.active .remove-item');
  deleteActive.disabled=!activeRemove;
}
deleteActive.addEventListener('click',()=>{
  const activeRemove=batchList.querySelector('.batch-row.active .remove-item');
  if(!activeRemove)return;
  activeRemove.click();
  firstFile.value='';
  mainFile.value='';
  firstStatus.textContent='写真を削除しました。必要なら写真を選び直してください。';
  queueMicrotask(()=>{syncEditorSearch();enhanceDeleteControls();});
});
new MutationObserver(()=>queueMicrotask(()=>{syncEditorSearch();enhanceDeleteControls();})).observe(editorSelect,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled']});
new MutationObserver(()=>queueMicrotask(()=>{syncEditorSearch();enhanceDeleteControls();})).observe(batchList,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('大学一覧を取得できません');return r.json();}).then(rows=>{universities=rows;renderFirst(universities);syncEditorSearch();enhanceDeleteControls();}).catch(e=>{console.error(e);firstSelect.innerHTML='<option value="">大学一覧の読み込みに失敗</option>';firstStatus.textContent='大学一覧の読み込みに失敗しました。ページを再読み込みしてください。';firstButton.disabled=true;});
})();
