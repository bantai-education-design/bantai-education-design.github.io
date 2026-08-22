const params=new URLSearchParams(location.search);
const state={rows:[],q:params.get('q')||'',type:params.get('type')||'all',status:params.get('status')||'all',sort:params.get('sort')||'name',faculties:new Map(),departments:new Map(),graduateSchools:new Map(),compare:new Set(),images:new Map()};
const grid=document.querySelector('#tokyo-grid');
const count=document.querySelector('#tokyo-result-count');
const input=document.querySelector('#tokyo-search-input');
const sortSelect=document.querySelector('#sort-select');
const typeLabel={national:'国立',public:'公立',private:'私立'};
const typeOrder={national:0,public:1,private:2};
const ACADEMIC_SNAPSHOTS=[
  'academic-structure-batches-03-08.json','academic-structure-batches-09-12.json','academic-structure-batches-13-14.json','academic-structure-batches-15-17.json','academic-structure-batches-18-22.json',
  'academic-structure-major-01.json','academic-structure-medical-01-02.json',
  'academic-structure-private-02.json','academic-structure-private-03.json','academic-structure-private-04.json','academic-structure-private-05.json','academic-structure-private-06.json','academic-structure-private-07.json','academic-structure-private-08.json',
  'academic-structure-tid-professional.json','departments-mejiro-verified.json'
];

function esc(v=''){return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function municipality(row){return row.municipality||row.headquarters?.municipality||'所在地確認中';}
function studentTotal(row){return Number(row.student_counts?.total)||0;}
function formatStudents(row){const n=studentTotal(row);return n?`${n.toLocaleString('ja-JP')}人`:'—';}
function mapsUrl(row){
  const address=String(row.headquarters?.address||'').trim();
  const location=address||`東京都 ${municipality(row)}`;
  const q=`${row.name} ${location}`.trim();
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
}
function academicNames(row){
  const graduate=state.graduateSchools.get(row.id)||[];
  return [
    ...(state.faculties.get(row.id)||[]).map(x=>x.name),
    ...(state.departments.get(row.id)||[]).map(x=>x.name),
    ...graduate.flatMap(x=>[x.name,...(x.programs||[]).map(p=>typeof p==='string'?p:p.name)])
  ];
}
function searchable(row){return [row.name,municipality(row),row.headquarters?.address,row.prefecture,row.university_type,row.founder,row.operator,row.university_goal,row.philosophy,row.feature_summary,...(row.academic_field_tags||[]),...academicNames(row)].filter(Boolean).join(' ').toLowerCase();}
function visible(row){const q=state.q.trim().toLowerCase();const typeOk=state.type==='all'||row.establishment_type===state.type;const rowStatus=row.admissions_status||'active';const statusOk=state.status==='all'||rowStatus===state.status;return typeOk&&statusOk&&(!q||searchable(row).includes(q));}
function sortRows(rows){const collator=new Intl.Collator('ja');return [...rows].sort((a,b)=>{if(state.sort==='municipality'){const x=collator.compare(municipality(a),municipality(b));return x||collator.compare(a.name,b.name);}if(state.sort==='type'){const x=(typeOrder[a.establishment_type]??9)-(typeOrder[b.establishment_type]??9);return x||collator.compare(a.name,b.name);}if(state.sort==='students-desc')return studentTotal(b)-studentTotal(a)||collator.compare(a.name,b.name);if(state.sort==='students-asc')return studentTotal(a)-studentTotal(b)||collator.compare(a.name,b.name);return collator.compare(a.name,b.name);});}
function syncUrl(){const next=new URLSearchParams();if(state.q)next.set('q',state.q);if(state.type!=='all')next.set('type',state.type);if(state.status!=='all')next.set('status',state.status);if(state.sort!=='name')next.set('sort',state.sort);const q=next.toString();history.replaceState(null,'',`${location.pathname}${q?`?${q}`:''}${location.hash}`);}
function groupByUniversity(rows){const map=new Map();for(const row of rows){if(!map.has(row.university_id))map.set(row.university_id,[]);map.get(row.university_id).push(row);}return map;}
function mergeUniversityDetails(rows,detailRegistry){const overrides=detailRegistry?.universities||{};return rows.map(row=>{const extra=overrides[row.id];if(!extra)return row;const merged={...row,...extra};if(row.headquarters||extra.headquarters)merged.headquarters={...(row.headquarters||{}),...(extra.headquarters||{})};return merged;});}
function academicSummary(row){
  const f=state.faculties.get(row.id)||[];
  const d=state.departments.get(row.id)||[];
  const g=state.graduateSchools.get(row.id)||[];
  if(f.length)return {label:`学部 ${f.length}・学科等 ${d.length}`,items:f.slice(0,3).map(x=>x.name),pending:false};
  if(g.length)return {label:`研究科 ${g.length}`,items:g.slice(0,3).map(x=>x.name),pending:false};
  return {label:'学部・学科情報 更新中',items:[],pending:true};
}
function historyDetails(row){const items=[];if(row.founded_year)items.push(`<div><dt>創立</dt><dd>${esc(row.founded_year)}年</dd></div>`);if(row.opened_year&&row.opened_year!==row.founded_year)items.push(`<div><dt>開学</dt><dd>${esc(row.opened_year)}年</dd></div>`);if(row.operator)items.push(`<div><dt>設置者</dt><dd>${esc(row.operator)}</dd></div>`);if(row.philosophy)items.push(`<div class="wide"><dt>理念</dt><dd>${esc(row.philosophy)}</dd></div>`);return items.length?`<details class="basic-profile"><summary>歴史・理念を見る</summary><dl>${items.join('')}</dl></details>`:'';}
function verifiedImage(row){const item=state.images.get(row.id);return item&&item.rights_status==='verified'&&item.image_url&&item.source_url&&item.rights_note?item:null;}
function cardVisual(row){const image=verifiedImage(row);const label=esc(typeLabel[row.establishment_type]||'');if(image){const alt=esc(image.alt||`${row.name}の大学紹介画像。`);return `<div class="card-visual has-image"><img class="university-card-image" src="${esc(image.image_url)}" alt="${alt}" loading="lazy" decoding="async" onerror="this.closest('.card-visual').classList.remove('has-image');this.remove()"><span class="visual-label">${label}</span><a class="image-source-link" href="${esc(image.source_url)}" target="_blank" rel="noopener">画像出典 ↗</a></div>`;}return `<div class="card-visual image-pending"><div class="image-placeholder" aria-hidden="true"><span>🎓</span><small>大学イメージ準備中</small></div><span class="visual-label">${label}</span></div>`;}
function card(row){
  const stopped=row.admissions_status==='stopped';
  const academic=academicSummary(row);
  const fields=(row.academic_field_tags||[]).slice(0,4).map(x=>`<span class="tag">${esc(x)}</span>`).join('');
  const unitTags=academic.items.map(x=>`<span class="tag academic-unit-tag">${esc(x)}</span>`).join('');
  const compared=state.compare.has(row.id);
  return `<article class="university-card tokyo-card" data-type="${esc(row.establishment_type)}" data-id="${esc(row.id)}">${cardVisual(row)}<div class="card-body"><div class="badge-row">${stopped?'<span class="tag">募集停止</span>':'<span class="tag">募集継続</span>'}</div><h3>${esc(row.name)}</h3><div class="meta">東京都 ${esc(municipality(row))}</div><div class="student-scale"><strong>${formatStudents(row)}</strong><span>在籍者数${row.student_counts?.as_of?` · ${esc(row.student_counts.as_of)}`:''}</span></div>${fields?`<div class="tag-row field-tags">${fields}</div>`:''}${row.feature_summary?`<p class="summary">${esc(row.feature_summary)}</p>`:''}<div class="academic-summary${academic.pending?' is-pending':''}"><strong>${esc(academic.label)}</strong>${unitTags?`<div class="tag-row academic-unit-tags">${unitTags}</div>`:'<small>公式情報との照合・同期を進めています。</small>'}</div>${historyDetails(row)}<button class="compare-toggle ${compared?'active':''}" type="button" data-compare="${esc(row.id)}">${compared?'✓ 比較候補に追加済み':'＋ 比較候補に追加'}</button><div class="card-actions">${row.admissions_url?`<a class="btn primary" href="${esc(row.admissions_url)}" target="_blank" rel="noopener">入試情報 ↗</a>`:row.official_url?`<a class="btn primary" href="${esc(row.official_url)}" target="_blank" rel="noopener">公式情報 ↗</a>`:'<span class="btn" aria-disabled="true">公式情報</span>'}<a class="btn map-card-link" href="${mapsUrl(row)}" target="_blank" rel="noopener">Google Maps ↗</a></div></div></article>`;
}
function render(){const rows=sortRows(state.rows.filter(visible));count.textContent=`${rows.length}校 / ${state.rows.length}校`;grid.innerHTML=rows.length?rows.map(card).join(''):'<div class="empty">条件に合う大学がありません。別のキーワードや条件を試してください。</div>';grid.setAttribute('aria-busy','false');syncUrl();}
function activateByValue(container,key,value){container?.querySelectorAll('.filter-chip').forEach(b=>b.classList.toggle('active',b.dataset[key]===value));}
function reset(){state.q='';state.type='all';state.status='all';state.sort='name';input.value='';sortSelect.value='name';activateByValue(document.querySelector('#type-filters'),'type','all');activateByValue(document.querySelector('#status-filters'),'status','all');render();}
function runQuery(query){state.q=query;input.value=query;render();document.querySelector('#search').scrollIntoView({behavior:'smooth',block:'start'});}
function updateSnapshot(){const students=document.querySelector('#snapshot-students');const f=document.querySelector('#snapshot-fields');const studentComplete=state.rows.length>0&&state.rows.every(r=>studentTotal(r)>0);const fieldComplete=state.rows.length>0&&state.rows.every(r=>(r.academic_field_tags||[]).length>0);if(students){if(studentComplete){const total=state.rows.reduce((s,r)=>s+studentTotal(r),0);students.textContent=total>=10000?`${(total/10000).toFixed(1)}万`:total.toLocaleString('ja-JP');}else students.textContent='詳細同期中';}if(f){if(fieldComplete){const fields=new Set(state.rows.flatMap(r=>r.academic_field_tags||[]));f.textContent=`${fields.size}分野`;}else f.textContent='詳細同期中';}}
function bindQuality(summary){const total=summary.counts?.total||state.rows.length||144;const v=summary.verification||{};const official=document.querySelector('#quality-official');const locationEl=document.querySelector('#quality-location');const addressEl=document.querySelector('#quality-address');const admissionsEl=document.querySelector('#quality-admissions');if(official)official.textContent=`${total}/${total}`;if(locationEl)locationEl.textContent=`${v.municipalities_total??total}/${total}`;if(addressEl)addressEl.textContent=`本部所在地を確認 ${v.addresses_total??total}/${total}校。`;if(admissionsEl)admissionsEl.textContent=`${v.admissions_links_total??total}/${total}`;}
async function optionalJson(url,fallback){try{const r=await fetch(url);if(r.ok)return await r.json();}catch{}if(fallback){try{const r=await fetch(fallback);if(r.ok)return await r.json();}catch{}}return [];}
async function optionalObject(url){try{const r=await fetch(url);if(r.ok)return await r.json();}catch{}return {};}
function putById(map,row){if(row?.id)map.set(row.id,row);}
function flattenAcademicDocument(doc,faculties,departments,graduateSchools){
  if(!doc)return;
  if(doc.kind==='academic_structure'){
    for(const u of doc.universities||[]){
      for(const f of u.faculties||[]){
        putById(faculties,{...f,university_id:u.university_id});
        for(const d of f.departments||[])putById(departments,{...d,university_id:u.university_id,faculty_id:f.id});
      }
      for(const g of u.graduate_schools||[])putById(graduateSchools,{...g,university_id:u.university_id});
    }
    return;
  }
  const target=doc.kind==='faculties'?faculties:doc.kind==='departments'?departments:doc.kind==='graduate_schools'?graduateSchools:null;
  if(target)for(const row of doc.records||[])putById(target,row);
}
async function loadAcademicBundle(){
  const [generatedF,generatedD,generatedG,baseF,baseD,...snapshots]=await Promise.all([
    optionalJson('data/faculties_tokyo_all.generated.json'),
    optionalJson('data/departments_tokyo_all.generated.json'),
    optionalJson('data/graduate_schools_tokyo_all.generated.json'),
    optionalJson('data/faculties.json'),
    optionalJson('data/departments.json'),
    ...ACADEMIC_SNAPSHOTS.map(name=>optionalObject(`data/${name}`))
  ]);
  const fm=new Map(),dm=new Map(),gm=new Map();
  for(const row of baseF)putById(fm,row);
  for(const row of baseD)putById(dm,row);
  for(const row of generatedF)putById(fm,row);
  for(const row of generatedD)putById(dm,row);
  for(const row of generatedG)putById(gm,row);
  for(const doc of snapshots)flattenAcademicDocument(doc,fm,dm,gm);
  const hasGenerated=generatedF.length||generatedD.length||generatedG.length;
  return {faculties:[...fm.values()],departments:[...dm.values()],graduateSchools:[...gm.values()],source:hasGenerated?'merged':'verified snapshots'};
}
function selectedRows(){return state.rows.filter(r=>state.compare.has(r.id));}
function updateCompare(){const rows=selectedRows();const slots=document.querySelector('#compare-items');const label=document.querySelector('#compare-count');const open=document.querySelector('#open-compare');if(label)label.textContent=rows.length;if(open)open.disabled=rows.length<2;const html=rows.map(r=>`<div class="compare-slot-v2"><strong>${esc(r.name)}</strong><small>${esc(typeLabel[r.establishment_type]||'')} · ${esc(municipality(r))}</small><button type="button" data-remove-compare="${esc(r.id)}">外す</button></div>`);while(html.length<4)html.push('<div class="compare-slot-v2">＋ 大学を追加</div>');slots.innerHTML=html.join('');}
function toggleCompare(id){if(state.compare.has(id))state.compare.delete(id);else if(state.compare.size<4)state.compare.add(id);else{document.querySelector('#compare').scrollIntoView({behavior:'smooth'});return;}updateCompare();render();}
function compareTable(){const rows=selectedRows();const cell=r=>({type:typeLabel[r.establishment_type]||'',place:`東京都 ${municipality(r)}`,students:formatStudents(r),fields:(r.academic_field_tags||[]).join('、')||'—',academic:(academicNames(r).slice(0,10).join('、')||'情報更新中'),feature:r.feature_summary||'—',admission:r.admissions_url||r.official_url||'',map:mapsUrl(r)});const data=rows.map(cell);const header=`<thead><tr><th>比較項目</th>${rows.map(r=>`<th>${esc(r.name)}</th>`).join('')}</tr></thead>`;const row=(label,key,format=v=>esc(v))=>`<tr><th>${label}</th>${data.map(d=>`<td>${format(d[key])}</td>`).join('')}</tr>`;const body=[row('設置区分','type'),row('所在地','place'),row('在籍者数','students'),row('学問分野','fields'),row('学部・研究科','academic'),row('特色','feature'),row('入試情報','admission',v=>v?`<a href="${esc(v)}" target="_blank" rel="noopener">公式入試情報 ↗</a>`:'—'),row('Google Maps','map',v=>`<a href="${esc(v)}" target="_blank" rel="noopener">地図で確認 ↗</a>`)].join('');return `<table class="compare-table">${header}<tbody>${body}</tbody></table>`;}
function openCompare(){if(state.compare.size<2)return;document.querySelector('#compare-table-wrap').innerHTML=compareTable();document.querySelector('#compare-dialog').showModal();}

function installDevelopmentStatus(){
  if(document.querySelector('#university-db-development-status'))return;
  const style=document.createElement('style');
  style.textContent=`
    .university-development-status{background:#18140a;color:#fff;border-top:1px solid #8f7229;border-bottom:1px solid #8f7229;padding:14px 18px;line-height:1.55}
    .university-development-status .inner{max-width:1180px;margin:auto;display:flex;gap:14px;align-items:flex-start}
    .university-development-status .label{display:inline-block;flex:0 0 auto;background:#f3c95a;color:#241b05;border-radius:999px;padding:5px 10px;font-weight:900;font-size:.82rem}
    .university-development-status strong{display:block;font-size:1rem;margin-bottom:2px}
    .university-development-status p{margin:0;color:#f2ead7;font-size:.9rem}
    .university-development-status small{display:block;margin-top:4px;color:#d9cda9}
    .academic-summary.is-pending{border:1px dashed #c79d3d;background:#fff9e8;padding:10px;border-radius:12px}
    .academic-summary.is-pending strong{color:#785b17}
    .academic-summary.is-pending small{display:block;margin-top:5px;color:#74684b}
    @media(max-width:640px){.university-development-status .inner{display:block}.university-development-status .label{margin-bottom:8px}}
  `;
  document.head.appendChild(style);
  const banner=document.createElement('section');
  banner.id='university-db-development-status';
  banner.className='university-development-status';
  banner.innerHTML='<div class="inner"><span class="label">現在 開発・更新中</span><div><strong>東京都144大学の基本情報を優先して再点検しています。</strong><p>学部・学科、所在地、Google Mapsの大学別表示を優先更新中です。未同期の項目は「更新中」と表示します。</p><small id="academic-sync-status">教育組織データを確認中</small></div></div>';
  const main=document.querySelector('main');
  const hero=document.querySelector('.tokyo-hero');
  if(main&&hero)main.insertBefore(banner,hero);else document.body.prepend(banner);
  const notice=document.querySelector('.ref-notice');
  if(notice)notice.innerHTML='ⓘ <strong>現在開発・更新中です。</strong> 144大学の掲載を維持しながら、学部・学科・所在地・地図リンクを順次再確認しています。出願・入試は各大学公式情報もご確認ください。';
  const trustItems=document.querySelectorAll('#quality .trust-item');
  if(trustItems[3])trustItems[3].innerHTML='<span>04</span><strong>基本情報 <b>更新中</b></strong><small>学部・学科・地図を優先点検。</small>';
}
function updateAcademicStatus(source){
  const covered=state.rows.filter(r=>(state.faculties.get(r.id)||[]).length||(state.graduateSchools.get(r.id)||[]).length).length;
  const status=document.querySelector('#academic-sync-status');
  const sourceLabel=source==='merged'?'集約データ＋検証済みスナップショット':'検証済みスナップショット';
  if(status)status.textContent=`教育組織データ ${covered}/${state.rows.length||144}校を読込（${sourceLabel}）・内容は継続更新中`;
}

installDevelopmentStatus();
input.value=state.q;
sortSelect.value=['name','municipality','type','students-desc','students-asc'].includes(state.sort)?state.sort:'name';
state.sort=sortSelect.value;
activateByValue(document.querySelector('#type-filters'),'type',state.type);
activateByValue(document.querySelector('#status-filters'),'status',state.status);

Promise.all([
  fetch('data/universities_tokyo_all.generated.json').then(r=>{if(!r.ok)throw new Error('load failed');return r.json();}),
  loadAcademicBundle(),
  optionalObject('data/university-images.json'),
  optionalObject('data/university-detail-overrides.json')
]).then(([rows,academic,imageRegistry,detailRegistry])=>{
  state.rows=mergeUniversityDetails(rows,detailRegistry);
  state.faculties=groupByUniversity(academic.faculties);
  state.departments=groupByUniversity(academic.departments);
  state.graduateSchools=groupByUniversity(academic.graduateSchools);
  state.images=new Map(Object.entries(imageRegistry.images||{}));
  const statTotal=document.querySelector('#stat-total');if(statTotal)statTotal.textContent=state.rows.length;
  updateSnapshot();updateAcademicStatus(academic.source);updateCompare();render();
}).catch(()=>{grid.innerHTML='<div class="empty">東京都大学データを読み込めませんでした。生成データを確認してください。</div>';count.textContent='読込エラー';grid.setAttribute('aria-busy','false');});
fetch('data/tokyo_dataset_summary.generated.json').then(r=>r.ok?r.json():Promise.reject()).then(bindQuality).catch(()=>{});
document.querySelector('#tokyo-search').addEventListener('submit',e=>{e.preventDefault();runQuery(input.value);});
input.addEventListener('input',()=>{state.q=input.value;render();});
document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>runQuery(b.dataset.query)));
document.querySelector('#type-filters').addEventListener('click',e=>{const b=e.target.closest('[data-type]');if(!b)return;state.type=b.dataset.type;activateByValue(e.currentTarget,'type',state.type);render();});
document.querySelector('#status-filters').addEventListener('click',e=>{const b=e.target.closest('[data-status]');if(!b)return;state.status=b.dataset.status;activateByValue(e.currentTarget,'status',state.status);render();});
sortSelect.addEventListener('change',()=>{state.sort=sortSelect.value;render();});
document.querySelector('#clear-filters').addEventListener('click',reset);
grid.addEventListener('click',e=>{const b=e.target.closest('[data-compare]');if(b)toggleCompare(b.dataset.compare);});
document.querySelector('#compare-items').addEventListener('click',e=>{const b=e.target.closest('[data-remove-compare]');if(b)toggleCompare(b.dataset.removeCompare);});
document.querySelector('#clear-compare').addEventListener('click',()=>{state.compare.clear();updateCompare();render();});
document.querySelector('#open-compare').addEventListener('click',openCompare);
