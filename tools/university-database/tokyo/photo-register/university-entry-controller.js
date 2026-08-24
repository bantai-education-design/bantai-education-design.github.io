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
let registrationMode='single';
const norm=s=>String(s||'').normalize('NFKC').toLowerCase().replace(/[\s　_\-()（）.・]/g,'');
const label=u=>`${u.name}（${u.id}）`;
const optionMarkup=(rows,selected='')=>'<option value="">大学を選択</option>'+rows.map(u=>`<option value="${u.id}" ${u.id===selected?'selected':''}>${label(u)}</option>`).join('');
const matches=q=>{const n=norm(q);if(!n)return universities;return universities.filter(u=>norm(u.id).includes(n)||norm(u.name).includes(n)||norm(label(u)).includes(n));};
const exact=q=>{const n=norm(q);if(!n)return null;return universities.find(u=>norm(u.id)===n||norm(u.name)===n||norm(label(u))===n)||null;};
function selectedUniversity(select){return universities.find(u=>u.id===select.value)||null;}
function currentUniversityLabel(){const u=selectedUniversity(firstSelect);return u?label(u):'';}
function setFirstStatus(){const u=selectedUniversity(firstSelect);firstButton.disabled=!u;firstStatus.textContent=u?`${u.name} を選択中。写真を選べます。`:'大学名を入力するか、下の144大学一覧から選択してください。';}
function renderFirst(rows,selected=''){firstSelect.innerHTML=optionMarkup(rows,selected);if(selected&&rows.some(u=>u.id===selected))firstSelect.value=selected;setFirstStatus();}
function commitFirstSearch(){const u=exact(firstSearch.value)||((m=>m.length===1?m[0]:null)(matches(firstSearch.value)));if(!u)return;renderFirst(universities,u.id);firstSearch.value=label(u);renderRegistrationMode();}
firstSearch.addEventListener('input',()=>{const rows=matches(firstSearch.value);const u=exact(firstSearch.value);renderFirst(rows,u?.id||'');});
firstSearch.addEventListener('change',commitFirstSearch);
firstSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();commitFirstSearch();}});
firstSelect.addEventListener('change',()=>{const u=selectedUniversity(firstSelect);if(u)firstSearch.value=label(u);setFirstStatus();renderRegistrationMode();});
firstButton.addEventListener('click',()=>{if(!firstButton.disabled)firstFile.click();});
firstFile.addEventListener('change',()=>{const file=firstFile.files?.[0],universityId=firstSelect.value;if(!file||!universityId)return;const before=batchList.querySelectorAll('.batch-row').length;firstStatus.textContent='写真を読み込み、大学へ割り当てています…';const dt=new DataTransfer();dt.items.add(file);mainFile.files=dt.files;mainFile.dispatchEvent(new Event('change',{bubbles:true}));let tries=0;const finish=()=>{const rows=[...batchList.querySelectorAll('.batch-row')];if(rows.length>before){const row=rows[rows.length-1],rowSelect=row.querySelector('.row-university');if(rowSelect&&[...rowSelect.options].some(o=>o.value===universityId)){rowSelect.value=universityId;rowSelect.dispatchEvent(new Event('change',{bubbles:true}));row.querySelector('.edit-item')?.click();const u=universities.find(x=>x.id===universityId);firstStatus.textContent=`${u?.name||universityId} に写真を割り当てました。間違えた場合は「写真を削除」で取り消せます。`;firstFile.value='';enhanceRegistrationRows();return;}}if(++tries<160)setTimeout(finish,50);else firstStatus.textContent='写真は追加されました。大学の割り当てを写真一覧で確認してください。';};setTimeout(finish,50);});
function syncEditorSearch(){const u=selectedUniversity(editorSelect);if(document.activeElement!==editorSearch)editorSearch.value=u?label(u):'';editorSearch.placeholder=editorSelect.disabled?'写真一覧で「編集」を押してください':'大学名・大学IDを入力';updateSingleUniversitySummary();}
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
  queueMicrotask(()=>{syncEditorSearch();enhanceDeleteControls();enhanceRegistrationRows();});
});

function ensureModeUi(){
  if(document.querySelector('#registration-mode-switch'))return;
  const grid=document.querySelector('.start-choice-grid');
  if(!grid)return;
  const wrap=document.createElement('section');
  wrap.id='registration-mode-switch';
  wrap.className='registration-mode-switch';
  wrap.innerHTML=`<div class="mode-heading"><span class="step">登録モード</span><h2>まず、登録のしかたを選ぶ</h2></div><div class="mode-buttons"><button id="mode-single" type="button" class="mode-card active" aria-pressed="true"><strong>1大学を編集</strong><span>大学名は1回だけ指定</span><small>同じ大学の写真を1〜5枚扱うとき</small></button><button id="mode-batch" type="button" class="mode-card" aria-pressed="false"><strong>複数大学を一括登録</strong><span>写真ごとに大学を確認</span><small>複数大学の写真をまとめて扱うとき</small></button></div><div id="registration-mode-status" class="mode-status"></div>`;
  grid.parentNode.insertBefore(wrap,grid);
  wrap.querySelector('#mode-single').addEventListener('click',()=>{registrationMode='single';renderRegistrationMode();});
  wrap.querySelector('#mode-batch').addEventListener('click',()=>{registrationMode='batch';renderRegistrationMode();});
  const style=document.createElement('style');
  style.textContent=`.registration-mode-switch{margin:0 0 18px;padding:16px;border:1px solid #3a3422;border-radius:15px;background:#0d0f14}.mode-heading{display:grid;gap:4px;margin-bottom:12px}.mode-buttons{display:grid;grid-template-columns:1fr 1fr;gap:10px}.mode-card{display:grid;gap:5px;text-align:left;padding:15px;border:1px solid #343742;background:#11131a;color:var(--text)}.mode-card strong{font-size:1rem}.mode-card span{color:#e8d48f;font-size:.82rem}.mode-card small{color:var(--muted);font-weight:400}.mode-card.active{border-color:#d7b45a;box-shadow:0 0 0 2px rgba(215,180,90,.12);background:#18160e}.mode-status{margin-top:12px;padding:10px 12px;border-radius:10px;background:#090a0d;color:#cfd1d7;font-size:.82rem;line-height:1.6}.mode-status strong{color:#f0d98b}.single-university-badge,.auto-assigned-badge{display:inline-flex;align-items:center;gap:6px;width:max-content;max-width:100%;padding:6px 9px;border-radius:999px;font-size:.72rem}.single-university-badge{border:1px solid #594d2b;background:#17140b;color:#edd487}.auto-assigned-badge{border:1px solid #36533f;background:#0d1811;color:#b9e6c7}.single-editor-summary{display:none;margin:12px 0 16px;padding:11px 12px;border-radius:10px;border:1px solid #4f4428;background:#151209;color:#f0d98b}.single-editor-summary strong{color:#fff}body[data-registration-mode="single"] .batch-row .university-assign{display:none}body[data-registration-mode="single"] #photo-editor .controls>.field{display:none}body[data-registration-mode="single"] .single-editor-summary{display:block}body[data-registration-mode="batch"] .single-university-badge{display:none}@media(max-width:800px){.mode-buttons{grid-template-columns:1fr}.registration-mode-switch{padding:13px}}`;
  document.head.appendChild(style);
  const controls=document.querySelector('#photo-editor .controls');
  if(controls&&!controls.querySelector('.single-editor-summary')){
    const summary=document.createElement('div');summary.className='single-editor-summary';summary.id='single-editor-summary';
    const fileInfo=document.querySelector('#file-info');controls.insertBefore(summary,fileInfo);
  }
}
function applySingleUniversityToRows(){
  if(registrationMode!=='single'||!firstSelect.value)return;
  for(const row of batchList.querySelectorAll('.batch-row')){
    const rowSelect=row.querySelector('.row-university');
    const rowSearch=row.querySelector('.row-university-search');
    if(rowSelect&&[...rowSelect.options].some(o=>o.value===firstSelect.value)&&rowSelect.value!==firstSelect.value){
      rowSelect.value=firstSelect.value;
      rowSelect.dispatchEvent(new Event('change',{bubbles:true}));
    }
    if(rowSearch)rowSearch.value=currentUniversityLabel();
  }
}
function updateSingleUniversitySummary(){
  const summary=document.querySelector('#single-editor-summary');
  if(!summary)return;
  const text=currentUniversityLabel()||'大学未選択';
  summary.innerHTML=`対象大学： <strong>${text}</strong><br><small>1大学モードでは大学名はここで共通管理します。写真ごとに入力し直す必要はありません。</small>`;
}
function enhanceRegistrationRows(){
  for(const row of batchList.querySelectorAll('.batch-row')){
    const main=row.querySelector('.batch-main');
    const select=row.querySelector('.row-university');
    if(!main||!select)continue;
    let singleBadge=main.querySelector('.single-university-badge');
    if(!singleBadge){singleBadge=document.createElement('span');singleBadge.className='single-university-badge';main.appendChild(singleBadge);}
    singleBadge.textContent=currentUniversityLabel()?`共通大学：${currentUniversityLabel()}`:'共通大学を選択してください';
    let autoBadge=main.querySelector('.auto-assigned-badge');
    if(registrationMode==='batch'&&select.value){
      if(!autoBadge){autoBadge=document.createElement('span');autoBadge.className='auto-assigned-badge';main.appendChild(autoBadge);}
      autoBadge.textContent='大学候補を自動入力済み・要確認';
    }else if(autoBadge){autoBadge.remove();}
  }
}
function renderRegistrationMode(){
  ensureModeUi();
  document.body.dataset.registrationMode=registrationMode;
  const single=document.querySelector('#mode-single'),batch=document.querySelector('#mode-batch'),status=document.querySelector('#registration-mode-status');
  if(single&&batch){single.classList.toggle('active',registrationMode==='single');batch.classList.toggle('active',registrationMode==='batch');single.setAttribute('aria-pressed',String(registrationMode==='single'));batch.setAttribute('aria-pressed',String(registrationMode==='batch'));}
  if(registrationMode==='single'){
    const labelText=currentUniversityLabel();
    if(status)status.innerHTML=labelText?`<strong>${labelText}</strong> を編集中です。追加する写真にはこの大学名を共通適用します。`:'大学名は1回だけ指定します。大学を選んでから、同じ大学の写真を1〜5枚追加してください。';
    firstButton.textContent=labelText?'この大学の写真を追加':'大学を選んで写真を追加';
    applySingleUniversityToRows();
  }else{
    if(status)status.textContent='複数大学を一括登録します。写真ごとに大学名を確認してください。ファイル名に大学名・大学IDがあれば自動入力します。';
    firstButton.textContent='この大学の写真を選ぶ';
  }
  updateSingleUniversitySummary();
  enhanceRegistrationRows();
}

new MutationObserver(()=>queueMicrotask(()=>{syncEditorSearch();enhanceDeleteControls();enhanceRegistrationRows();if(registrationMode==='single')applySingleUniversityToRows();})).observe(editorSelect,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled']});
new MutationObserver(()=>queueMicrotask(()=>{syncEditorSearch();enhanceDeleteControls();enhanceRegistrationRows();if(registrationMode==='single')applySingleUniversityToRows();})).observe(batchList,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
fetch('../data/universities_tokyo_all.generated.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('大学一覧を取得できません');return r.json();}).then(rows=>{universities=rows;renderFirst(universities);syncEditorSearch();enhanceDeleteControls();ensureModeUi();renderRegistrationMode();}).catch(e=>{console.error(e);firstSelect.innerHTML='<option value="">大学一覧の読み込みに失敗</option>';firstStatus.textContent='大学一覧の読み込みに失敗しました。ページを再読み込みしてください。';firstButton.disabled=true;});
})();
