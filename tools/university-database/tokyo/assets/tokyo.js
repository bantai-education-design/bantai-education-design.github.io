const params=new URLSearchParams(location.search);
const state={rows:[],q:params.get('q')||'',type:params.get('type')||'all',status:params.get('status')||'all',sort:params.get('sort')||'name',field:params.get('field')||'all',dept:params.get('dept')||'',faculties:new Map(),departments:new Map(),graduateSchools:new Map(),compare:new Set(),images:new Map()};
const PREF_CODES={tokyo:'東京都',saitama:'埼玉県',kanagawa:'神奈川県'};
const PREF_SLUGS={'東京都':'tokyo','埼玉県':'saitama','神奈川県':'kanagawa'};
state.pref=PREF_CODES[params.get('pref')]||(['東京都','埼玉県','神奈川県'].includes(params.get('pref'))?params.get('pref'):'all');
state.withCampus=params.get('campus')==='1';
state.campusIdx=new Map();
state.qual=params.get('qual')||'';
state.qualIdx=new Map();
state.accessIdx=new Map();
const FIELD_CATEGORIES=[
  {id:'all',label:'すべて',re:null},
  {id:'tech',label:'情報・AI・工学',re:/情報|AI|データ|DX|工学|理工|電気|電子|通信|ロボ|建築|数理/i},
  {id:'health',label:'医療・看護・薬・保健',re:/医学|歯学|薬学|看護|医療|保健|リハビリ|理学療法|作業療法|臨床|助産|鍼灸|柔道整復|生命/i},
  {id:'law_econ',label:'経済・経営・法・政治',re:/経済|経営|商学|会計|マーケ|イノベーション|MBA|法学|法律|政治|政策|行政|公共/i},
  {id:'human_soc',label:'人文・心理・社会・福祉',re:/文学|人文|歴史|宗教|仏教|神学|心理|人間|社会|福祉|ソーシャル|観光|メディア|リベラルアーツ/i},
  {id:'edu',label:'教育・保育・子ども',re:/教育|保育|児童|子ども|こども/i},
  {id:'global',label:'国際・語学',re:/国際|語学|外国語|地域研究|日本研究|グローバル/i},
  {id:'arts',label:'芸術・デザイン・音楽',re:/芸術|美術|デザイン|音楽|映像|表現|アニメ|マンガ|写真|舞台|演奏|ファッション/i},
  {id:'sci_agri',label:'理学・農学・環境・食',re:/理学|自然科学|農学|園芸|環境|海洋|獣医|動物|食|栄養|家政|生活科学/i},
  {id:'sports',label:'スポーツ・健康',re:/体育|スポーツ|健康|武道|ダンス/i}
];
const qualGroups=row=>(state.qualIdx.get(row.id)||[]).map(x=>x.group).filter(Boolean);
// キャンパス所在地（文科省一覧）。本部が他県でも、その県で学べる大学を絞り込みに含めるために使う
const campusPrefs=row=>state.campusIdx.get(row.id)?.prefectures||[];
// 東京都版の正本（144校）に加えて読み込む地域データ。各フォルダに <slug>_core_01.json などを置く
// packs=0 のときは東京都版の正本（144校）だけを表示する（東京都版の検証用）
const REGION_PACKS=params.get('packs')==='0'?[]:[{base:'../saitama/data/',slug:'saitama'},{base:'../tokyo-additions/data/',slug:'tokyo_additions'},{base:'../kanagawa/data/',slug:'kanagawa'}];
const prefOf=row=>row.prefecture||row.headquarters?.prefecture||'東京都';
const grid=document.querySelector('#tokyo-grid');
const count=document.querySelector('#tokyo-result-count');
const input=document.querySelector('#tokyo-search-input');
const deptInput=document.querySelector('#dept-search-input');
const clearQueryBtn=document.querySelector('#clear-query-btn');
const sortSelect=document.querySelector('#sort-select');
const typeLabel={national:'国立',public:'公立',private:'私立'};
const typeOrder={national:0,public:1,private:2};
const CORE_SHARDS=['tokyo_core_01.json','tokyo_core_02.json','tokyo_core_03.json','tokyo_core_04.json','tokyo_core_05.json','tokyo_core_06.json','tokyo_core_07.json','tokyo_core_08.json','tokyo_core_09.json','tokyo_core_10.json','tokyo_core_11.json','tokyo_core_12.json'];
const SNAPSHOTS=[
'academic-structure-batches-03-08.json','academic-structure-batches-09-12.json','academic-structure-batches-13-14.json','academic-structure-batches-15-17.json','academic-structure-batches-18-22.json',
'academic-structure-major-01.json','academic-structure-medical-01-02.json','academic-structure-private-02.json','academic-structure-private-03.json','academic-structure-private-04.json','academic-structure-private-05.json','academic-structure-private-06.json','academic-structure-private-07.json','academic-structure-private-08.json','academic-structure-tid-professional.json','departments-mejiro-verified.json'];

const esc=(v='')=>String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const asList=v=>Array.isArray(v)?v:(v&&typeof v==='object'?Object.entries(v).map(([key,row])=>row&&typeof row==='object'&&!Array.isArray(row)&&!row.university_id&&/^u\d{6}$/.test(key)?{university_id:key,...row}:row):[]);
const municipality=row=>row.municipality||row.headquarters?.municipality||'所在地確認中';
const studentTotal=row=>Number(row.student_counts?.total)||0;
const formatStudents=row=>studentTotal(row)?`${studentTotal(row).toLocaleString('ja-JP')}人`:'—';
const mapsUrl=row=>`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${row.name} ${String(row.headquarters?.address||`${prefOf(row)} ${municipality(row)}`).trim()}`.trim())}`;
const groupByUniversity=rows=>{const m=new Map();for(const row of asList(rows)){if(!row?.university_id)continue;if(!m.has(row.university_id))m.set(row.university_id,[]);m.get(row.university_id).push(row)}return m};
const putById=(m,row)=>{if(row?.id)m.set(row.id,row)};

function academicNames(row){const g=state.graduateSchools.get(row.id)||[];return [...(state.faculties.get(row.id)||[]).map(x=>x.name),...(state.departments.get(row.id)||[]).map(x=>x.name),...g.flatMap(x=>[x.name,...asList(x.programs).map(p=>typeof p==='string'?p:p?.name).filter(Boolean)])]}
function matchesField(row,fieldId=state.field){
  if(!fieldId||fieldId==='all')return true;
  const cat=FIELD_CATEGORIES.find(c=>c.id===fieldId);
  if(!cat||!cat.re)return true;
  return [...(row.academic_field_tags||[]),...academicNames(row)].some(t=>cat.re.test(t));
}
function matchesDept(row,deptQuery=state.dept){
  const dq=String(deptQuery||'').trim().toLowerCase();
  if(!dq)return true;
  return academicNames(row).some(n=>String(n).toLowerCase().includes(dq));
}
window.matchesField=matchesField;
function searchable(row){return [row.name,prefOf(row),municipality(row),...(state.campusIdx.get(row.id)?.campuses||[]).flatMap(c=>[c.name,c.municipality]),...(state.qualIdx.get(row.id)||[]).map(x=>x.name),...(state.accessIdx.get(row.id)?.stations||[]).flatMap(s=>[s.station,s.station.replace(/駅$/,''),s.line]),row.headquarters?.address,row.founder,row.operator,row.university_goal,row.philosophy,row.feature_summary,...(row.academic_field_tags||[]),...academicNames(row)].filter(Boolean).join(' ').toLowerCase()}
function matchesAll(row,ov={}){
  const q=(ov.q??state.q).trim().toLowerCase();
  const pref=ov.pref??state.pref;
  const withCampus=ov.withCampus??state.withCampus;
  const type=ov.type??state.type;
  const field=ov.field??state.field;
  const qual=ov.qual??state.qual;
  const dept=ov.dept??state.dept;
  const status=ov.status??state.status;
  return (!qual||qualGroups(row).includes(qual))&&(pref==='all'||prefOf(row)===pref||(withCampus&&campusPrefs(row).includes(pref)))&&(type==='all'||row.establishment_type===type)&&matchesField(row,field)&&matchesDept(row,dept)&&(status==='all'||(row.admissions_status||'active')===status)&&(!q||searchable(row).includes(q));
}
function visible(row){return matchesAll(row)}
function activeFilterItems(){
  const items=[];
  if(state.q.trim())items.push({key:'q',label:`キーワード: ${state.q.trim()}`});
  if(state.pref!=='all')items.push({key:'pref',label:`都道府県: ${state.pref}`});
  if(state.type!=='all')items.push({key:'type',label:`設置区分: ${typeLabel[state.type]||state.type}`});
  if(state.field&&state.field!=='all'){const cat=FIELD_CATEGORIES.find(c=>c.id===state.field);items.push({key:'field',label:`分野: ${cat?cat.label:state.field}`});}
  if(state.qual)items.push({key:'qual',label:`資格: ${state.qual}`});
  if(state.dept.trim())items.push({key:'dept',label:`学部・学科: ${state.dept.trim()}`});
  if(state.withCampus&&state.pref!=='all')items.push({key:'withCampus',label:`${state.pref}のキャンパス所在地を含む`});
  if(state.status!=='all')items.push({key:'status',label:`募集状態: ${state.status==='stopped'?'募集停止':'募集継続'}`});
  return items;
}
function matchReasons(row){
  const items=activeFilterItems();
  if(!items.length)return [];
  const reasons=[];
  if(state.pref!=='all'){
    if(prefOf(row)===state.pref)reasons.push(`所在地：${state.pref} ${municipality(row)}`);
    else if(state.withCampus&&campusPrefs(row).includes(state.pref)){
      const cs=(state.campusIdx.get(row.id)?.campuses||[]).filter(c=>c.prefecture===state.pref).map(c=>c.name||'キャンパス').slice(0,2);
      reasons.push(`キャンパス：${state.pref}${cs.length?`（${cs.join('・')}）`:''}`);
    }
  }
  if(state.type!=='all')reasons.push(`設置区分：${typeLabel[row.establishment_type]||''}`);
  if(state.field&&state.field!=='all'){
    const cat=FIELD_CATEGORIES.find(c=>c.id===state.field);
    if(cat&&cat.re){
      const tags=(row.academic_field_tags||[]).filter(t=>cat.re.test(t)).slice(0,2);
      reasons.push(`分野：${tags.length?tags.join('・'):cat.label}`);
    }
  }
  if(state.qual){
    const qs=(state.qualIdx.get(row.id)||[]).filter(x=>x.group===state.qual).map(x=>x.name).slice(0,2);
    reasons.push(`資格：${qs.length?qs.join('・'):state.qual}`);
  }
  if(state.dept.trim()){
    const dq=state.dept.trim().toLowerCase();
    const us=[...new Set(academicNames(row).filter(n=>String(n).toLowerCase().includes(dq)))].slice(0,2);
    reasons.push(`学部・学科等：${us.length?us.join('・'):state.dept.trim()}`);
  }
  if(state.status!=='all')reasons.push(`募集状態：${(row.admissions_status||'active')==='stopped'?'募集停止':'募集継続'}`);
  const q=state.q.trim().toLowerCase();
  if(q){
    const rawQ=state.q.trim();
    const units=academicNames(row);
    const hitUnit=units.find(n=>String(n).toLowerCase().includes(q));
    const hitTag=(row.academic_field_tags||[]).find(t=>String(t).toLowerCase().includes(q));
    const hitQual=(state.qualIdx.get(row.id)||[]).find(x=>String(x.name||'').toLowerCase().includes(q));
    const hitStation=(state.accessIdx.get(row.id)?.stations||[]).find(s=>String(s.station||'').toLowerCase().includes(q)||String(s.line||'').toLowerCase().includes(q));
    const hitCampus=(state.campusIdx.get(row.id)?.campuses||[]).find(c=>String(c.name||'').toLowerCase().includes(q)||String(c.municipality||'').toLowerCase().includes(q));
    if(String(row.name||'').toLowerCase().includes(q))reasons.push(`大学名：「${row.name}」`);
    else if(hitUnit)reasons.push(`学部・学科等：「${hitUnit}」`);
    else if(hitTag)reasons.push(`分野：「${hitTag}」`);
    else if(hitQual)reasons.push(`資格：「${hitQual.name}」`);
    else if(hitStation)reasons.push(`最寄り駅：「${hitStation.station}」`);
    else if(hitCampus)reasons.push(`キャンパス：「${hitCampus.name||hitCampus.municipality}」`);
    else if(String(prefOf(row)+' '+municipality(row)+' '+(row.headquarters?.address||'')).toLowerCase().includes(q))reasons.push(`所在地：「${prefOf(row)} ${municipality(row)}」`);
    else reasons.push(`特色・基本情報に「${rawQ}」`);
  }
  return reasons;
}
window.matchReasons=matchReasons;
function sortRows(rows){const c=new Intl.Collator('ja');return [...rows].sort((a,b)=>{if(state.sort==='municipality')return c.compare(prefOf(a),prefOf(b))||c.compare(municipality(a),municipality(b))||c.compare(a.name,b.name);if(state.sort==='type')return ((typeOrder[a.establishment_type]??9)-(typeOrder[b.establishment_type]??9))||c.compare(a.name,b.name);if(state.sort==='students-desc')return studentTotal(b)-studentTotal(a)||c.compare(a.name,b.name);if(state.sort==='students-asc')return studentTotal(a)-studentTotal(b)||c.compare(a.name,b.name);return c.compare(a.name,b.name)})}
function syncUrl(){const p=new URLSearchParams();if(state.q)p.set('q',state.q);if(state.pref!=='all')p.set('pref',PREF_SLUGS[state.pref]||state.pref);if(state.type!=='all')p.set('type',state.type);if(state.field&&state.field!=='all')p.set('field',state.field);if(state.qual)p.set('qual',state.qual);if(state.dept)p.set('dept',state.dept);if(state.withCampus)p.set('campus','1');if(state.status!=='all')p.set('status',state.status);if(state.sort!=='name')p.set('sort',state.sort);history.replaceState(null,'',`${location.pathname}${p.toString()?`?${p}`:''}${location.hash}`)}
function mergeUniversityDetails(rows,registry){const o=registry?.universities||{};return rows.map(row=>{const x=o[row.id];return x?{...row,...x,headquarters:{...(row.headquarters||{}),...(x.headquarters||{})}}:row})}
function mergeAdmissionDetails(rows,registry){const o={...(registry?.universities||{}),...(registry?.records||{})};return rows.map(row=>{const x=o[row.id];return x?{...row,...x}:row})}
function academicSummary(row){const f=state.faculties.get(row.id)||[],d=state.departments.get(row.id)||[],g=state.graduateSchools.get(row.id)||[];if(f.length)return {label:`学部 ${f.length}・学科等 ${d.length}`,items:f.slice(0,3).map(x=>x.name),pending:false};if(g.length)return {label:`研究科 ${g.length}`,items:g.slice(0,3).map(x=>x.name),pending:false};return {label:'学部・学科情報 更新中',items:[],pending:true}}
function historyDetails(row){const xs=[];if(row.founded_year)xs.push(`<div><dt>創立</dt><dd>${esc(row.founded_year)}年</dd></div>`);if(row.opened_year&&row.opened_year!==row.founded_year)xs.push(`<div><dt>開学</dt><dd>${esc(row.opened_year)}年</dd></div>`);if(row.operator)xs.push(`<div><dt>設置者</dt><dd>${esc(row.operator)}</dd></div>`);if(row.philosophy)xs.push(`<div class="wide"><dt>理念</dt><dd>${esc(row.philosophy)}</dd></div>`);return xs.length?`<details class="basic-profile"><summary>歴史・理念を見る</summary><dl>${xs.join('')}</dl></details>`:''}
function verifiedImage(row){const x=state.images.get(row.id);return x&&x.rights_status==='verified'&&x.image_url&&x.source_url&&x.rights_note?x:null}
function cardVisual(row){const x=verifiedImage(row),label=esc(typeLabel[row.establishment_type]||'');if(x)return `<div class="card-visual has-image"><img class="university-card-image" src="${esc(x.image_url)}" alt="${esc(x.alt||`${row.name}の大学紹介画像。`)}" loading="lazy" decoding="async" onerror="this.closest('.card-visual').classList.remove('has-image');this.remove()"><span class="visual-label">${label}</span><a class="image-source-link" href="${esc(x.source_url)}" target="_blank" rel="noopener">画像出典 ↗</a></div>`;return `<div class="card-visual image-pending"><div class="image-placeholder" aria-hidden="true"><span>🎓</span><small>大学イメージ準備中</small></div><span class="visual-label">${label}</span></div>`}
function card(row){const a=academicSummary(row),stopped=row.admissions_status==='stopped',fields=(row.academic_field_tags||[]).slice(0,4).map(x=>`<span class="tag">${esc(x)}</span>`).join(''),units=a.items.map(x=>`<span class="tag academic-unit-tag">${esc(x)}</span>`).join(''),compared=state.compare.has(row.id);return `<article class="university-card tokyo-card" data-type="${esc(row.establishment_type)}" data-id="${esc(row.id)}" data-card-ready="true">${cardVisual(row)}<div class="card-body"><div class="badge-row">${stopped?'<span class="tag">募集停止</span>':'<span class="tag">募集継続</span>'}</div><h3>${esc(row.name)}</h3><div class="meta">${esc(prefOf(row))} ${esc(municipality(row))}</div><div class="student-scale"><strong>${formatStudents(row)}</strong><span>在籍者数${row.student_counts?.as_of?` · ${esc(row.student_counts.as_of)}`:''}</span></div>${fields?`<div class="tag-row field-tags">${fields}</div>`:''}${row.feature_summary?`<p class="summary">${esc(row.feature_summary)}</p>`:''}<div class="academic-summary${a.pending?' is-pending':''}"><strong>${esc(a.label)}</strong>${units?`<div class="tag-row academic-unit-tags">${units}</div>`:'<small>公式情報との照合・同期を進めています。</small>'}</div>${historyDetails(row)}<button class="compare-toggle ${compared?'active':''}" type="button" data-compare="${esc(row.id)}">${compared?'✓ 比較候補に追加済み':'＋ 比較候補に追加'}</button><div class="card-actions">${row.admissions_url?`<a class="btn primary" href="${esc(row.admissions_url)}" target="_blank" rel="noopener">入試情報 ↗</a>`:row.official_url?`<a class="btn primary" href="${esc(row.official_url)}" target="_blank" rel="noopener">公式情報 ↗</a>`:'<span class="btn" aria-disabled="true">公式情報</span>'}<a class="btn map-card-link" href="${mapsUrl(row)}" target="_blank" rel="noopener">Google Maps ↗</a></div></div></article>`}
function renderActiveFilters(){
  const listEl=document.querySelector('#active-filters-list');
  const clearAllBtn=document.querySelector('#clear-filters');
  const advBadge=document.querySelector('#advanced-active-count');
  const items=activeFilterItems();
  if(clearQueryBtn)clearQueryBtn.hidden=!state.q;
  if(clearAllBtn)clearAllBtn.disabled=items.length===0;
  const advCount=[state.qual,state.dept.trim(),state.withCampus&&state.pref!=='all',state.status!=='all'].filter(Boolean).length;
  if(advBadge){advBadge.hidden=advCount===0;advBadge.textContent=`${advCount}件選択中`;}
  if(!listEl)return;
  if(!items.length){
    listEl.innerHTML=`<span class="no-active-filters">選択中の条件：なし（全${state.rows.length||209}校を表示中）</span>`;
    return;
  }
  listEl.innerHTML=`<span class="active-filters-title">選択中の条件：</span>`+items.map(it=>`<button type="button" class="active-filter-chip" data-clear-filter="${esc(it.key)}" aria-label="条件「${esc(it.label)}」を解除">${esc(it.label)} <span aria-hidden="true">×</span></button>`).join('');
}
function emptyStateHtml(){
  const items=activeFilterItems();
  const relaxBtns=items.map(it=>{
    const ov={};
    if(it.key==='q')ov.q='';
    else if(it.key==='pref')ov.pref='all';
    else if(it.key==='type')ov.type='all';
    else if(it.key==='field')ov.field='all';
    else if(it.key==='qual')ov.qual='';
    else if(it.key==='dept')ov.dept='';
    else if(it.key==='withCampus')ov.withCampus=false;
    else if(it.key==='status')ov.status='all';
    const n=state.rows.filter(r=>matchesAll(r,ov)).length;
    return `<button type="button" class="btn empty-relax-btn" data-clear-filter="${esc(it.key)}">「${esc(it.label)}」を外す（${n}校）</button>`;
  }).join('');
  return `<div class="empty empty-guide" role="region" aria-label="検索結果0件の案内"><strong>条件に一致する大学が見つかりませんでした（0校 / 全${state.rows.length||209}校）</strong><p>現在選択している条件の一部を外すか、すべての条件を解除して再度お探しください。</p><div class="empty-actions">${relaxBtns}<button type="button" class="btn primary empty-reset-btn" data-clear-filter="all">すべての条件を解除する（全${state.rows.length||209}校を表示）</button></div></div>`;
}
function render(){const rows=sortRows(state.rows.filter(visible));count.textContent=`該当 ${rows.length}校 / 全${state.rows.length}校`;renderActiveFilters();grid.innerHTML=rows.length?rows.map(card).join(''):emptyStateHtml();grid.setAttribute('aria-busy','false');syncUrl()}
function activate(container,key,value){container?.querySelectorAll('.filter-chip').forEach(b=>{const on=b.dataset[key]===value;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on))})}
function clearSingleFilter(key){
  if(key==='all'){reset();return;}
  if(key==='q'){state.q='';if(input)input.value='';}
  else if(key==='pref'){state.pref='all';state.withCampus=false;activate(document.querySelector('#pref-filters'),'pref','all');document.dispatchEvent(new CustomEvent('bantai:pref-change'));}
  else if(key==='type'){state.type='all';activate(document.querySelector('#type-filters'),'type','all');}
  else if(key==='field'){state.field='all';activate(document.querySelector('#field-filters'),'fieldChip','all');}
  else if(key==='qual'){state.qual='';const qs=document.querySelector('#qual-select');if(qs)qs.value='';}
  else if(key==='dept'){state.dept='';if(deptInput)deptInput.value='';}
  else if(key==='withCampus'){state.withCampus=false;document.dispatchEvent(new CustomEvent('bantai:pref-change'));}
  else if(key==='status'){state.status='all';activate(document.querySelector('#status-filters'),'status','all');}
  render();
}
function reset(){state.q='';state.qual='';state.field='all';state.dept='';state.withCampus=false;{const qs=document.querySelector('#qual-select');if(qs)qs.value='';}if(deptInput)deptInput.value='';state.pref='all';activate(document.querySelector('#pref-filters'),'pref','all');state.type='all';state.status='all';state.sort='name';input.value='';sortSelect.value='name';activate(document.querySelector('#type-filters'),'type','all');activate(document.querySelector('#field-filters'),'fieldChip','all');activate(document.querySelector('#status-filters'),'status','all');document.dispatchEvent(new CustomEvent('bantai:pref-change'));render()}
function runQuery(q){state.q=q;input.value=q;render();document.querySelector('#search').scrollIntoView({behavior:'smooth',block:'start'})}
function runField(fieldId){state.field=fieldId;activate(document.querySelector('#field-filters'),'fieldChip',state.field);render();document.querySelector('#search').scrollIntoView({behavior:'smooth',block:'start'})}
function updateSnapshot(){const s=document.querySelector('#snapshot-students'),f=document.querySelector('#snapshot-fields');if(s)s.textContent=state.rows.every(r=>studentTotal(r)>0)?`${(state.rows.reduce((n,r)=>n+studentTotal(r),0)/10000).toFixed(1)}万`:'詳細同期中';if(f)f.textContent=state.rows.every(r=>(r.academic_field_tags||[]).length)?`${new Set(state.rows.flatMap(r=>r.academic_field_tags||[])).size}分野`:'詳細同期中'}
function bindQuality(summary){const rows=state.rows,total=REGION_PACKS.length?rows.length:(summary?.counts?.total||rows.length);if(!total)return;const v=REGION_PACKS.length?{municipalities_total:rows.filter(r=>r.municipality||r.headquarters?.municipality).length,addresses_total:rows.filter(r=>r.headquarters?.address).length,admissions_links_total:rows.filter(r=>r.admissions_url||r.admissions_status==='stopped').length}:(summary?.verification||{});const o=document.querySelector('#quality-official'),l=document.querySelector('#quality-location'),a=document.querySelector('#quality-address'),ad=document.querySelector('#quality-admissions'),c=document.querySelector('#quality-complete');if(o)o.textContent=`${REGION_PACKS.length?rows.filter(r=>r.official_url).length:total}/${total}`;if(l)l.textContent=`${v.municipalities_total??total}/${total}`;if(a)a.textContent=`本部所在地を確認 ${v.addresses_total??total}/${total}校。`;if(ad)ad.textContent=`${v.admissions_links_total??total}/${total}`;if(c)c.textContent=`${total}/${total}`}
async function optionalJson(url){try{const r=await fetch(url);return r.ok?await r.json():[]}catch{return []}}
async function optionalObject(url){try{const r=await fetch(url);return r.ok?await r.json():{}}catch{return {}}}
function flatten(doc,fm,dm,gm){if(!doc)return;if(doc.kind==='academic_structure'){for(const u of asList(doc.universities)){const uid=u?.university_id||u?.id;for(const f of asList(u?.faculties)){putById(fm,{...f,university_id:f.university_id||uid});for(const d of asList(f?.departments))putById(dm,{...d,university_id:d.university_id||uid,faculty_id:d.faculty_id||f.id})}for(const g of asList(u?.graduate_schools))putById(gm,{...g,university_id:g.university_id||uid})}return}const target=doc.kind==='faculties'?fm:doc.kind==='departments'?dm:doc.kind==='graduate_schools'?gm:null;if(target)for(const row of asList(doc.records))putById(target,row)}
async function loadUniversityBundle(){
  const [base,...docs]=await Promise.all([fetch('data/universities_tokyo_all.generated.json').then(r=>{if(!r.ok)throw new Error('university data load failed');return r.json()}),...CORE_SHARDS.map(n=>optionalJson('data/'+n))]);
  const core=new Map();
  for(const doc of docs)for(const row of asList(doc?.records||doc?.universities||doc))if(row?.id)core.set(row.id,row);
  if(core.size!==base.length)throw new Error('university core sync incomplete: '+core.size+'/'+base.length);
  const tokyo=asList(base).map(row=>{const x=core.get(row.id)||{};return {...row,...x,headquarters:{...(row.headquarters||{}),...(x.headquarters||{})}}});
  const packs=await Promise.all(REGION_PACKS.map(async p=>{const [b,c]=await Promise.all([optionalJson(`${p.base}universities_${p.slug}_all.generated.json`),optionalObject(`${p.base}${p.slug}_core_01.json`)]);const m=new Map(asList(c.records).map(r=>[r.id,r]));const rows=asList(b).map(r=>({...r,...(m.get(r.id)||{}),region_pack:p.slug}));if(rows.length&&m.size!==rows.length)throw new Error(`${p.slug} core sync incomplete: ${m.size}/${rows.length}`);return rows}));
  // 同じIDがすでにある場合は所在地などを上書き（例: 本部所在地の都道府県へ移した大学）
  const byId=new Map(tokyo.map(r=>[r.id,r]));const added=[];
  for(const r of packs.flat()){const cur=byId.get(r.id);if(cur){Object.assign(cur,{...r,region_override:true,headquarters:{...(cur.headquarters||{}),...(r.headquarters||{})}})}else{byId.set(r.id,r);added.push(r)}}
  return [...tokyo,...added];
}
async function loadAcademicBundle(){const [gg,bf,bd,...docs]=await Promise.all([optionalJson('data/graduate_schools_tokyo_all.generated.json'),optionalJson('data/faculties.json'),optionalJson('data/departments.json'),...SNAPSHOTS.map(n=>optionalObject(`data/${n}`))]);const fm=new Map(),dm=new Map(),gm=new Map();for(const r of asList(bf))putById(fm,r);for(const r of asList(bd))putById(dm,r);for(const r of asList(gg))putById(gm,r);for(const d of docs)flatten(d,fm,dm,gm);const packDocs=await Promise.all(REGION_PACKS.filter(p=>p.academic!==false).map(p=>Promise.all(['faculties','departments','graduate_schools'].map(k=>optionalJson(`${p.base}${k}_${p.slug}_all.generated.json`)))));for(const [pf,pd,pg] of packDocs){for(const r of asList(pf))putById(fm,r);for(const r of asList(pd))putById(dm,r);for(const r of asList(pg))putById(gm,r)}return {faculties:[...fm.values()],departments:[...dm.values()],graduateSchools:[...gm.values()],source:asList(gg).length?'merged':'snapshots'}}
function selectedRows(){return state.rows.filter(r=>state.compare.has(r.id))}
function updateCompare(){const rows=selectedRows(),slots=document.querySelector('#compare-items'),label=document.querySelector('#compare-count'),open=document.querySelector('#open-compare');if(label)label.textContent=rows.length;if(open)open.disabled=rows.length<2;const html=rows.map(r=>`<div class="compare-slot-v2"><strong>${esc(r.name)}</strong><small>${esc(typeLabel[r.establishment_type]||'')} · ${esc(municipality(r))}</small><button type="button" data-remove-compare="${esc(r.id)}">外す</button></div>`);while(html.length<4)html.push('<div class="compare-slot-v2">＋ 大学を追加</div>');slots.innerHTML=html.join('')}
function toggleCompare(id){if(state.compare.has(id))state.compare.delete(id);else if(state.compare.size<4)state.compare.add(id);else return;updateCompare();render()}
function compareTable(){const rows=selectedRows(),data=rows.map(r=>({type:typeLabel[r.establishment_type]||'',place:`${prefOf(r)} ${municipality(r)}`,students:formatStudents(r),fields:(r.academic_field_tags||[]).join('、')||'—',academic:academicNames(r).slice(0,10).join('、')||'情報更新中',feature:r.feature_summary||'—',admission:r.admissions_url||r.official_url||'',map:mapsUrl(r)}));const row=(label,key,fmt=v=>esc(v))=>`<tr><th>${label}</th>${data.map(d=>`<td>${fmt(d[key])}</td>`).join('')}</tr>`;return `<table class="compare-table"><thead><tr><th>比較項目</th>${rows.map(r=>`<th>${esc(r.name)}</th>`).join('')}</tr></thead><tbody>${row('設置区分','type')}${row('所在地','place')}${row('在籍者数','students')}${row('学問分野','fields')}${row('学部・研究科','academic')}${row('特色','feature')}${row('入試情報','admission',v=>v?`<a href="${esc(v)}" target="_blank" rel="noopener">公式入試情報 ↗</a>`:'—')}${row('Google Maps','map',v=>`<a href="${esc(v)}" target="_blank" rel="noopener">地図で確認 ↗</a>`)}</tbody></table>`}
function openCompare(){if(state.compare.size<2)return;document.querySelector('#compare-table-wrap').innerHTML=compareTable();document.querySelector('#compare-dialog').showModal()}
function installDevelopmentStatus(){if(document.querySelector('#university-db-development-status'))return;const style=document.createElement('style');style.textContent='.university-development-status{background:#18140a;color:#fff;border-top:1px solid #8f7229;border-bottom:1px solid #8f7229;padding:14px 18px;line-height:1.55}.university-development-status .inner{max-width:1180px;margin:auto;display:flex;gap:14px;align-items:flex-start}.university-development-status .label{background:#f3c95a;color:#241b05;border-radius:999px;padding:5px 10px;font-weight:900;font-size:.82rem;white-space:nowrap}.university-development-status p{margin:2px 0;color:#f2ead7;font-size:.9rem}.university-development-status small{display:block;margin-top:4px;color:#d9cda9}.academic-summary.is-pending{border:1px dashed #c79d3d;background:#fff9e8;padding:10px;border-radius:12px}@media(max-width:640px){.university-development-status .inner{display:block}.university-development-status .label{display:inline-block;margin-bottom:8px}}';document.head.appendChild(style);const b=document.createElement('section');b.id='university-db-development-status';b.className='university-development-status';b.innerHTML='<div class="inner"><span class="label">現在 開発・更新中</span><div><strong>東京都・埼玉県・神奈川県の大学の基本情報を優先して再点検しています。</strong><p>学部・学科、所在地、Google Mapsの大学別表示を優先更新中です。未同期の項目は「更新中」と表示します。</p></div></div>';const main=document.querySelector('main'),hero=document.querySelector('.tokyo-hero');if(main&&hero)main.insertBefore(b,hero)}
function updateAcademicStatus(source){const covered=state.rows.filter(r=>(state.faculties.get(r.id)||[]).length||(state.graduateSchools.get(r.id)||[]).length).length,s=document.querySelector('#academic-sync-status');if(s&&state.rows.length)s.textContent=`教育組織データ ${covered}/${state.rows.length}校を読込（${source==='merged'?'集約＋検証済みスナップショット':'検証済みスナップショット'}）・内容は継続更新中`}

installDevelopmentStatus();input.value=state.q;if(deptInput)deptInput.value=state.dept;sortSelect.value=['name','municipality','type','students-desc','students-asc'].includes(state.sort)?state.sort:'name';state.sort=sortSelect.value;activate(document.querySelector('#pref-filters'),'pref',state.pref);activate(document.querySelector('#type-filters'),'type',state.type);activate(document.querySelector('#field-filters'),'fieldChip',state.field);activate(document.querySelector('#status-filters'),'status',state.status);if(state.qual||state.dept||state.withCampus||state.status!=='all'){const adv=document.querySelector('#advanced-filters');if(adv)adv.open=true;}
Promise.all([loadUniversityBundle(),loadAcademicBundle(),optionalObject('data/university-images.json'),optionalObject('data/university-detail-overrides.json'),optionalObject('data/tokyo_admissions_batch01.json')]).then(([rows,a,img,detail,admissions])=>{state.rows=mergeAdmissionDetails(mergeUniversityDetails(asList(rows),detail),admissions);state.faculties=groupByUniversity(a.faculties);state.departments=groupByUniversity(a.departments);state.graduateSchools=groupByUniversity(a.graduateSchools);state.images=new Map(Object.entries(img.images||{}));document.querySelector('#stat-total')?.replaceChildren(document.createTextNode(String(state.rows.length)));bindQuality({});updateSnapshot();updateAcademicStatus(a.source);updateCompare();render()}).catch(err=>{console.error('Tokyo university DB load failed',err);const s=document.querySelector('#academic-sync-status');if(s)s.textContent=`教育組織データ読込エラー：${err.message}`;grid.innerHTML='<div class="empty">大学データを読み込めませんでした。</div>';count.textContent='読込エラー';grid.setAttribute('aria-busy','false')});
if(!REGION_PACKS.length)fetch('data/tokyo_dataset_summary.generated.json').then(r=>r.ok?r.json():Promise.reject()).then(bindQuality).catch(()=>{});
document.querySelector('#tokyo-search').addEventListener('submit',e=>{e.preventDefault();runQuery(input.value)});input.addEventListener('input',()=>{state.q=input.value;render()});clearQueryBtn?.addEventListener('click',()=>{state.q='';input.value='';input.focus();render()});deptInput?.addEventListener('input',()=>{state.dept=deptInput.value;render()});document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>runQuery(b.dataset.query)));document.querySelectorAll('.discovery-card[data-field]').forEach(b=>b.addEventListener('click',()=>runField(b.dataset.field)));document.querySelector('#pref-filters')?.addEventListener('click',e=>{const b=e.target.closest('[data-pref]');if(!b)return;state.pref=b.dataset.pref;activate(e.currentTarget,'pref',state.pref);render();document.dispatchEvent(new CustomEvent('bantai:pref-change'))});document.querySelector('#type-filters').addEventListener('click',e=>{const b=e.target.closest('[data-type]');if(!b)return;state.type=b.dataset.type;activate(e.currentTarget,'type',state.type);render()});document.querySelector('#field-filters')?.addEventListener('click',e=>{const b=e.target.closest('[data-field-chip]');if(!b)return;state.field=b.dataset.fieldChip;activate(e.currentTarget,'fieldChip',state.field);render()});document.querySelector('#status-filters').addEventListener('click',e=>{const b=e.target.closest('[data-status]');if(!b)return;state.status=b.dataset.status;activate(e.currentTarget,'status',state.status);render()});sortSelect.addEventListener('change',()=>{state.sort=sortSelect.value;render()});document.querySelector('#clear-filters').addEventListener('click',reset);document.querySelector('#active-filters-list')?.addEventListener('click',e=>{const b=e.target.closest('[data-clear-filter]');if(b)clearSingleFilter(b.dataset.clearFilter)});grid.addEventListener('click',e=>{const clr=e.target.closest('[data-clear-filter]');if(clr){clearSingleFilter(clr.dataset.clearFilter);return;}const b=e.target.closest('[data-compare]');if(b)toggleCompare(b.dataset.compare)});document.querySelector('#compare-items').addEventListener('click',e=>{const b=e.target.closest('[data-remove-compare]');if(b)toggleCompare(b.dataset.removeCompare)});document.querySelector('#clear-compare').addEventListener('click',()=>{state.compare.clear();updateCompare();render()});document.querySelector('#open-compare').addEventListener('click',openCompare);
