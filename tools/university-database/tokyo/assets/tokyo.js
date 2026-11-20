const SEARCH_STATE_KEY='bantai:university-db:search-state:v1';
const PAGE_SIZE=24;
let savedSession=null;
try{savedSession=JSON.parse(sessionStorage.getItem(SEARCH_STATE_KEY)||'null');}catch{}
if(!location.search&&savedSession&&savedSession.returning&&savedSession.search){
  try{history.replaceState(null,'',`${location.pathname}${savedSession.search}${location.hash}`);}catch{}
}
const params=new URLSearchParams(location.search);
const initialLimit=Math.max(PAGE_SIZE,Number(params.get('limit'))||(savedSession?.returning&&savedSession?.limit?Number(savedSession.limit):PAGE_SIZE)||PAGE_SIZE);
const initialView=(params.get('view')||(savedSession?.returning?savedSession.view:''))==='compact'?'compact':'card';
const initialCompare=(params.get('compare')||(savedSession?.returning?savedSession.compare:'')||'').split(',').map(x=>x.trim()).filter(x=>/^u\d{6}$/.test(x)).slice(0,4);
const state={rows:[],q:params.get('q')||'',type:params.get('type')||'all',status:params.get('status')||'all',sort:params.get('sort')||'name',field:params.get('field')||'all',dept:params.get('dept')||'',scale:params.get('scale')||'all',admGuide:params.get('adm')||'all',view:initialView,limit:initialLimit,faculties:new Map(),departments:new Map(),graduateSchools:new Map(),compare:new Set(initialCompare),compareDiffOnly:params.get('diff')==='1',completeProfiles:new Map(),images:new Map()};
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
const SCALE_LABELS={small:'小規模（1,500人未満）',medium:'中規模（1,500〜4,999人）',large:'大規模（5,000人以上）'};
const ADM_GUIDE_LABELS={web:'Web出願URL確認済み',guidelines:'募集要項URL確認済み',opencampus:'オープンキャンパスURL確認済み'};
function matchesScale(row,scale=state.scale){
  if(!scale||scale==='all')return true;
  const n=studentTotal(row);
  if(!n)return false;
  if(scale==='small')return n<1500;
  if(scale==='medium')return n>=1500&&n<5000;
  if(scale==='large')return n>=5000;
  return true;
}
function matchesAdmGuide(row,adm=state.admGuide){
  if(!adm||adm==='all')return true;
  if(adm==='web')return !!(row.web_application_url);
  if(adm==='guidelines')return !!(row.application_guidelines_url);
  if(adm==='opencampus')return !!(row.open_campus_url);
  return true;
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
  const scale=ov.scale??state.scale;
  const admGuide=ov.admGuide??state.admGuide;
  const status=ov.status??state.status;
  return (!qual||qualGroups(row).includes(qual))&&(pref==='all'||prefOf(row)===pref||(withCampus&&campusPrefs(row).includes(pref)))&&(type==='all'||row.establishment_type===type)&&matchesField(row,field)&&matchesDept(row,dept)&&matchesScale(row,scale)&&matchesAdmGuide(row,admGuide)&&(status==='all'||(row.admissions_status||'active')===status)&&(!q||searchable(row).includes(q));
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
  if(state.scale&&state.scale!=='all')items.push({key:'scale',label:`大学規模: ${SCALE_LABELS[state.scale]||state.scale}`});
  if(state.admGuide&&state.admGuide!=='all')items.push({key:'admGuide',label:`入試・イベント導線: ${ADM_GUIDE_LABELS[state.admGuide]||state.admGuide}`});
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
  if(state.scale&&state.scale!=='all'){
    reasons.push(`規模：在籍者数 ${formatStudents(row)}（${SCALE_LABELS[state.scale]}）`);
  }
  if(state.admGuide&&state.admGuide!=='all'){
    reasons.push(`公式導線：${ADM_GUIDE_LABELS[state.admGuide]}`);
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
function syncUrl(){const p=new URLSearchParams();if(state.q)p.set('q',state.q);if(state.pref!=='all')p.set('pref',PREF_SLUGS[state.pref]||state.pref);if(state.type!=='all')p.set('type',state.type);if(state.field&&state.field!=='all')p.set('field',state.field);if(state.qual)p.set('qual',state.qual);if(state.dept)p.set('dept',state.dept);if(state.scale&&state.scale!=='all')p.set('scale',state.scale);if(state.admGuide&&state.admGuide!=='all')p.set('adm',state.admGuide);if(state.withCampus)p.set('campus','1');if(state.status!=='all')p.set('status',state.status);if(state.sort!=='name')p.set('sort',state.sort);if(state.view==='compact')p.set('view','compact');if(state.limit>PAGE_SIZE)p.set('limit',String(state.limit));if(state.compare.size)p.set('compare',[...state.compare].join(','));if(state.compareDiffOnly&&state.compare.size>=2)p.set('diff','1');history.replaceState(null,'',`${location.pathname}${p.toString()?`?${p}`:''}${location.hash}`)}
function saveSearchSession(cardId='',returning=false){
  try{
    const prev=JSON.parse(sessionStorage.getItem(SEARCH_STATE_KEY)||'null')||{};
    sessionStorage.setItem(SEARCH_STATE_KEY,JSON.stringify({
      search:location.search||'',
      scrollY:Math.round(window.scrollY||prev.scrollY||0),
      cardId:cardId||prev.cardId||'',
      limit:state.limit,
      view:state.view,
      compare:[...state.compare].join(','),
      returning:!!returning,
      ts:Date.now()
    }));
  }catch{}
}
window.saveSearchSession=saveSearchSession;
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
  const advCount=[state.qual,state.dept.trim(),state.scale!=='all',state.admGuide!=='all',state.withCampus&&state.pref!=='all',state.status!=='all'].filter(Boolean).length;
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
    else if(it.key==='scale')ov.scale='all';
    else if(it.key==='admGuide')ov.admGuide='all';
    else if(it.key==='withCampus')ov.withCampus=false;
    else if(it.key==='status')ov.status='all';
    const n=state.rows.filter(r=>matchesAll(r,ov)).length;
    return `<button type="button" class="btn empty-relax-btn" data-clear-filter="${esc(it.key)}">「${esc(it.label)}」を外す（${n}校）</button>`;
  }).join('');
  return `<div class="empty empty-guide" role="region" aria-label="検索結果0件の案内"><strong>条件に一致する大学が見つかりませんでした（0校 / 全${state.rows.length||209}校）</strong><p>現在選択している条件の一部を外すか、すべての条件を解除して再度お探しください。</p><div class="empty-actions">${relaxBtns}<button type="button" class="btn primary empty-reset-btn" data-clear-filter="all">すべての条件を解除する（全${state.rows.length||209}校を表示）</button></div></div>`;
}
function renderPagination(totalMatching,shownCount){
  const bar=document.querySelector('#pagination-bar');
  if(!bar)return;
  if(!totalMatching){bar.hidden=true;bar.innerHTML='';return;}
  bar.hidden=false;
  const remaining=Math.max(0,totalMatching-shownCount);
  const nextBatch=Math.min(PAGE_SIZE,remaining);
  const pct=Math.min(100,Math.round((shownCount/totalMatching)*100));
  const moreBtn=remaining>0?`<button type="button" id="load-more-btn" class="btn primary pagination-more-btn">さらに表示（次の${nextBatch}校 ／ 残り${remaining}校）</button>`:'';
  const allBtn=remaining>PAGE_SIZE?`<button type="button" id="show-all-btn" class="btn pagination-all-btn">該当${totalMatching}校をすべて表示</button>`:'';
  const collapseBtn=shownCount>PAGE_SIZE&&totalMatching>PAGE_SIZE?`<button type="button" id="collapse-list-btn" class="btn pagination-collapse-btn">最初の${PAGE_SIZE}校表示に戻す</button>`:'';
  bar.innerHTML=`<div class="pagination-status"><span>該当 <strong>${totalMatching}</strong>校のうち <strong>1〜${shownCount}</strong>校を表示中</span><div class="pagination-track" aria-hidden="true"><i style="width:${pct}%"></i></div></div><div class="pagination-actions">${moreBtn}${allBtn}${collapseBtn}</div>`;
}
function syncViewModeUI(){
  grid?.classList.toggle('is-compact-view',state.view==='compact');
  document.querySelectorAll('#view-mode-switch [data-view-mode]').forEach(b=>{
    const on=b.dataset.viewMode===state.view;
    b.classList.toggle('active',on);
    b.setAttribute('aria-pressed',String(on));
  });
}
function render(){
  const allRows=sortRows(state.rows.filter(visible));
  const favOnly=document.body.classList.contains('show-favorites-only');
  const shownRows=favOnly?allRows:allRows.slice(0,state.limit);
  count.textContent=allRows.length>shownRows.length?`該当 ${allRows.length}校（${shownRows.length}校を表示中） / 全${state.rows.length}校`:`該当 ${allRows.length}校 / 全${state.rows.length}校`;
  syncViewModeUI();
  renderActiveFilters();
  grid.innerHTML=shownRows.length?shownRows.map(card).join(''):emptyStateHtml();
  renderPagination(allRows.length,shownRows.length);
  grid.setAttribute('aria-busy','false');
  syncUrl();
}
function activate(container,key,value){container?.querySelectorAll('.filter-chip').forEach(b=>{const on=b.dataset[key]===value;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on))})}
function clearSingleFilter(key){
  if(key==='all'){reset();return;}
  state.limit=PAGE_SIZE;
  if(key==='q'){state.q='';if(input)input.value='';}
  else if(key==='pref'){state.pref='all';state.withCampus=false;activate(document.querySelector('#pref-filters'),'pref','all');document.dispatchEvent(new CustomEvent('bantai:pref-change'));}
  else if(key==='type'){state.type='all';activate(document.querySelector('#type-filters'),'type','all');}
  else if(key==='field'){state.field='all';activate(document.querySelector('#field-filters'),'fieldChip','all');}
  else if(key==='qual'){state.qual='';const qs=document.querySelector('#qual-select');if(qs)qs.value='';}
  else if(key==='dept'){state.dept='';if(deptInput)deptInput.value='';}
  else if(key==='scale'){state.scale='all';}
  else if(key==='admGuide'){state.admGuide='all';}
  else if(key==='withCampus'){state.withCampus=false;document.dispatchEvent(new CustomEvent('bantai:pref-change'));}
  else if(key==='status'){state.status='all';activate(document.querySelector('#status-filters'),'status','all');}
  render();
}
function reset(){state.q='';state.qual='';state.field='all';state.dept='';state.scale='all';state.admGuide='all';state.withCampus=false;state.limit=PAGE_SIZE;{const qs=document.querySelector('#qual-select');if(qs)qs.value='';}if(deptInput)deptInput.value='';state.pref='all';activate(document.querySelector('#pref-filters'),'pref','all');state.type='all';state.status='all';state.sort='name';input.value='';sortSelect.value='name';activate(document.querySelector('#type-filters'),'type','all');activate(document.querySelector('#field-filters'),'fieldChip','all');activate(document.querySelector('#status-filters'),'status','all');document.dispatchEvent(new CustomEvent('bantai:pref-change'));render()}
function applyGuidedSearch(cfg={}){
  state.limit=PAGE_SIZE;
  state.q='';if(input)input.value='';
  state.dept='';if(deptInput)deptInput.value='';
  state.status='all';activate(document.querySelector('#status-filters'),'status','all');
  state.field=cfg.field||'all';activate(document.querySelector('#field-filters'),'fieldChip',state.field);
  state.qual=cfg.qual||'';{const qs=document.querySelector('#qual-select');if(qs)qs.value=state.qual;}
  state.pref=cfg.pref||'all';activate(document.querySelector('#pref-filters'),'pref',state.pref);
  state.withCampus=Boolean(cfg.withCampus&&state.pref!=='all');
  state.type=cfg.type||'all';activate(document.querySelector('#type-filters'),'type',state.type);
  state.scale=cfg.scale||'all';
  state.admGuide=cfg.admGuide||'all';
  document.dispatchEvent(new CustomEvent('bantai:pref-change'));
  render();
  document.querySelector('#search')?.scrollIntoView({behavior:'smooth',block:'start'});
}
window.applyGuidedSearch=applyGuidedSearch;
window.matchesAllUniversities=matchesAll;
window.FIELD_CATEGORIES=FIELD_CATEGORIES;
window.SCALE_LABELS=SCALE_LABELS;
window.ADM_GUIDE_LABELS=ADM_GUIDE_LABELS;
function runQuery(q){state.q=q;state.limit=PAGE_SIZE;input.value=q;render();document.querySelector('#search').scrollIntoView({behavior:'smooth',block:'start'})}
function runField(fieldId){state.field=fieldId;state.limit=PAGE_SIZE;activate(document.querySelector('#field-filters'),'fieldChip',state.field);render();document.querySelector('#search').scrollIntoView({behavior:'smooth',block:'start'})}
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
function selectedRows(){
  const order=[...state.compare];
  return order.map(id=>state.rows.find(r=>r.id===id)).filter(Boolean);
}
function completeProfilePath(uid){
  const m=/^u(\d{6})$/.exec(uid||'');if(!m)return null;const n=Number(m[1]);
  if(n===1||n===2)return `data/complete/${uid}.json`;
  if(n===50||(n>=175&&n<=209))return `../kanagawa/data/complete/${uid}.json`;
  if(n>=145&&n<=172)return `../saitama/data/complete/${uid}.json`;
  if(n===173||n===174)return `../tokyo-additions/data/complete/${uid}.json`;
  return null;
}
async function ensureCompleteProfiles(ids){
  await Promise.all(ids.map(async id=>{
    if(state.completeProfiles.has(id))return;
    const url=completeProfilePath(id);
    if(!url){state.completeProfiles.set(id,null);return;}
    try{
      const r=await fetch(url);
      state.completeProfiles.set(id,r.ok?await r.json():null);
    }catch{
      state.completeProfiles.set(id,null);
    }
  }));
}
const cmpBadge=(st,txt)=>{const cls={verified:'dq-verified',uninvestigated:'dq-uninvestigated',not_published:'dq-not-published',not_applicable:'dq-not-applicable',updating:'dq-updating',expired:'dq-expired'}[st]||'dq-uninvestigated';return `<span class="dq-badge ${cls}">${esc(txt)}</span>`;};
function updateCompare(){const rows=selectedRows(),slots=document.querySelector('#compare-items'),label=document.querySelector('#compare-count'),open=document.querySelector('#open-compare');if(label)label.textContent=rows.length;if(open)open.disabled=rows.length<2;const html=rows.map(r=>`<div class="compare-slot-v2 is-filled"><strong>${esc(r.name)}</strong><small>${esc(typeLabel[r.establishment_type]||'')} · ${esc(prefOf(r))} ${esc(municipality(r))}</small><button type="button" data-remove-compare="${esc(r.id)}" aria-label="${esc(r.name)}を比較候補から外す">外す</button></div>`);while(html.length<4)html.push('<div class="compare-slot-v2">＋ 大学を追加（最大4校）</div>');if(slots)slots.innerHTML=html.join('');syncUrl();}
function toggleCompare(id){if(state.compare.has(id))state.compare.delete(id);else if(state.compare.size<4)state.compare.add(id);else return;updateCompare();render();if(document.querySelector('#compare-dialog')?.open){if(state.compare.size<2)document.querySelector('#compare-dialog').close();else openCompare();}}
function buildCompareRecord(r){
  const id=r.id;
  const cp=state.completeProfiles.get(id)||null;
  const stopped=r.admissions_status==='stopped'||r.status==='recruitment_stopped'||cp?.status==='recruitment_stopped';
  const f=state.faculties.get(id)||[],d=state.departments.get(id)||[],g=state.graduateSchools.get(id)||[];
  const graduateOnly=!f.length&&g.length>0;
  const fields=(r.academic_field_tags||cp?.academic_field_tags||[]);
  const fieldsNorm=fields.join('、')||'uninvestigated';
  const fieldsHtml=fields.length?`<div class="cmp-tags">${fields.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:`${cmpBadge('uninvestigated','未調査')} <small>分野タグ照合中</small>`;

  const facNames=f.map(x=>x.name).filter(Boolean);
  const gradNames=g.map(x=>x.name).filter(Boolean);
  const acadNorm=graduateOnly?`grad:${gradNames.join(',')}`:`fac:${facNames.join(',')}:dept:${d.length}`;
  const acadHtml=graduateOnly
    ? `${cmpBadge('not_applicable','学部該当なし（大学院大学）')}<div class="cmp-sub">研究科 ${gradNames.length}：${esc(gradNames.slice(0,5).join('、'))}</div>`
    : (facNames.length
        ? `<div><strong>学部 ${facNames.length} ／ 学科等 ${d.length}</strong>${gradNames.length?` ／ 研究科 ${gradNames.length}`:''}</div><div class="cmp-sub">${esc(facNames.slice(0,6).join('、'))}${facNames.length>6?`、ほか${facNames.length-6}`:''}</div>`
        : `${cmpBadge('uninvestigated','未調査')}`);

  const idxCampuses=(state.campusIdx.get(id)?.campuses)||[];
  const campList=idxCampuses.length?idxCampuses:(cp?.campuses||[]);
  const campNorm=campList.length?campList.map(c=>`${c.name}:${c.municipality}`).join('|'):`${prefOf(r)}:${municipality(r)}`;
  const campHtml=campList.length
    ? `<div>${cmpBadge('verified',`${campList.length}拠点確認済み`)}</div><ul class="cmp-list">${campList.slice(0,4).map(c=>`<li><strong>${esc(c.name||'本部キャンパス')}</strong><span>（${esc(c.prefecture||'')} ${esc(c.municipality||'')}）</span></li>`).join('')}${campList.length>4?`<li>ほか${campList.length-4}拠点</li>`:''}</ul>`
    : `<div>${cmpBadge('verified','本部確認済み')} ${esc(prefOf(r))} ${esc(municipality(r))}</div>`;

  const accObj=state.accessIdx.get(id);
  const stList=(accObj?.stations?.length?accObj.stations:(cp?.campuses?.[0]?.nearest_stations||[]));
  const isCorr=/通信制/.test(cp?.history_summary||'')||/通信制/.test(r.feature_summary||'');
  const stNorm=stList.length?stList.map(s=>s.station).join(','):(isCorr?'not_applicable':'uninvestigated');
  const stHtml=stList.length
    ? `<div>${cmpBadge('verified','確認済み')}</div><ul class="cmp-list">${stList.slice(0,3).map(s=>`<li><strong>${esc(s.station)}</strong>${s.access?` <span>${esc(s.access)}</span>`:''}</li>`).join('')}</ul>`
    : (isCorr
        ? `${cmpBadge('not_applicable','該当なし')}<div class="cmp-sub">オンライン通信制課程</div>`
        : `${cmpBadge('uninvestigated','未調査')}<div class="cmp-sub">公式アクセスページ照合前（<a href="${esc(mapsUrl(r))}" target="_blank" rel="noopener">地図 ↗</a>）</div>`);

  const admUrl=r.admissions_url||cp?.admissions_url||'';
  const guideUrl=r.application_guidelines_url||cp?.application_guidelines_url||cp?.admissions?.application_guidelines_url||'';
  const webUrl=r.web_application_url||cp?.web_application_url||cp?.admissions?.web_application_url||'';
  const methods=cp?.admissions?.methods||[];
  const admNorm=stopped?'stopped':`adm:${!!admUrl}:guide:${!!guideUrl}:web:${!!webUrl}:m:${methods.length}`;
  let admHtml='';
  if(stopped){
    admHtml=`${cmpBadge('not_applicable','募集停止')}<div class="cmp-sub">学生募集停止を一次資料で確認済み</div>`;
  }else{
    const links=[];
    if(admUrl)links.push(`<a class="cmp-link primary" href="${esc(admUrl)}" target="_blank" rel="noopener">公式入試情報 ↗</a>`);
    if(guideUrl)links.push(`<a class="cmp-link" href="${esc(guideUrl)}" target="_blank" rel="noopener">募集要項 ↗</a>`);
    if(webUrl)links.push(`<a class="cmp-link" href="${esc(webUrl)}" target="_blank" rel="noopener">Web出願 ↗</a>`);
    const mHtml=methods.length
      ? `<div class="cmp-sub" style="margin-top:4px">${cmpBadge('verified',`${cp.admissions.admission_year||2027}年度日程確認済み`)} ${methods.slice(0,2).map(m=>`${esc(m.name)}（試験：${esc(m.exam_date||'要項参照')}）`).join(' ／ ')}</div>`
      : `<div class="cmp-sub" style="margin-top:4px">${cmpBadge('uninvestigated','個別日程：未調査')} 募集要項から順次登録</div>`;
    admHtml=`<div>${cmpBadge(admUrl?'verified':'uninvestigated',admUrl?'入試導線：確認済み':'入試導線：未調査')}</div><div class="cmp-links">${links.join('')}</div>${mHtml}`;
  }

  const t=(cp?.tuition||[])[0];
  const tNorm=stopped?'stopped':(t?`${t.academic_year}:${t.first_year_total}`:'uninvestigated');
  const tHtml=stopped
    ? `${cmpBadge('not_applicable','該当なし（募集停止）')}`
    : (t
        ? `<div>${cmpBadge('verified',`${t.academic_year}年度確認済み`)}</div><div><strong>初年度合計：${Number(t.first_year_total).toLocaleString('ja-JP')}円</strong></div><div class="cmp-sub">入学料 ${Number(t.admission_fee).toLocaleString('ja-JP')}円 ／ 授業料 ${Number(t.annual_tuition).toLocaleString('ja-JP')}円</div>`
        : `${cmpBadge('uninvestigated','未調査')}<div class="cmp-sub">公式学費資料から順次登録（推測補完なし）</div>`);

  const quals=(state.qualIdx.get(id)||cp?.qualifications||[]);
  const qNorm=quals.length?quals.map(q=>q.name).sort().join(','):(graduateOnly?'not_applicable':(prefOf(r)==='神奈川県'?'not_published':'uninvestigated'));
  const qHtml=quals.length
    ? `<div>${cmpBadge('verified',`${quals.length}件確認済み`)}</div><div class="cmp-tags" style="margin-top:4px">${quals.slice(0,5).map(q=>`<span>${esc(q.name.replace(/（.*?）/g,''))}</span>`).join('')}${quals.length>5?`<span>ほか${quals.length-5}件</span>`:''}</div>`
    : (graduateOnly
        ? `${cmpBadge('not_applicable','該当なし')}<div class="cmp-sub">大学院大学のため学部養成課程なし</div>`
        : (prefOf(r)==='神奈川県'
            ? `${cmpBadge('not_published','公式掲載なし')}<div class="cmp-sub">課程認定一覧・公式ページ調査済み</div>`
            : `${cmpBadge('uninvestigated','未調査')}<div class="cmp-sub">課程認定資料・公式ページ照合前</div>`));

  const stCount=studentTotal(r)||Number(cp?.student_counts?.total)||0;
  const stAsOf=r.student_counts?.as_of||cp?.student_counts?.as_of||'2026-05-01';
  const stCountNorm=stCount?String(stCount):'uninvestigated';
  const stCountHtml=stCount
    ? `<div>${cmpBadge('verified','確認済み')} <strong>${stCount.toLocaleString('ja-JP')}人</strong></div><div class="cmp-sub">${esc(stAsOf)}基準</div>`
    : `${cmpBadge('uninvestigated','未調査')}<div class="cmp-sub">公式統計・ポートレート照合前</div>`;

  const ocUrl=r.open_campus_url||cp?.open_campus_url||'';
  const brUrl=r.brochure_request_url||cp?.brochure_request_url||'';
  const ocNorm=stopped?'stopped':`oc:${!!ocUrl}:br:${!!brUrl}`;
  const ocHtml=stopped
    ? `${cmpBadge('not_applicable','該当なし（募集停止）')}`
    : ((ocUrl||brUrl)
        ? `<div>${cmpBadge('verified','公式導線確認済み')}</div><div class="cmp-links">${ocUrl?`<a class="cmp-link" href="${esc(ocUrl)}" target="_blank" rel="noopener">オープンキャンパス ↗</a>`:''}${brUrl?`<a class="cmp-link" href="${esc(brUrl)}" target="_blank" rel="noopener">資料請求 ↗</a>`:''}</div>`
        : `${cmpBadge('uninvestigated','未調査')}<div class="cmp-sub">公式サイト・入試ページから確認可能</div>`);

  const vDate=r.verified_at||cp?.verification?.last_verified_at||(r.sources?.[0]?.verified_at)||(cp?.sources?.[0]?.verified_at)||'2026-10-30';
  const favMemo=(typeof window.getFavoriteNote==='function'?window.getFavoriteNote(id):'')||'';

  return {
    id,name:r.name,
    type:{norm:r.establishment_type,html:`<strong>${esc(typeLabel[r.establishment_type]||'')}</strong> ／ ${stopped?'募集停止':'募集継続'}`},
    fields:{norm:fieldsNorm,html:fieldsHtml},
    academic:{norm:acadNorm,html:acadHtml},
    campus:{norm:campNorm,html:campHtml},
    access:{norm:stNorm,html:stHtml},
    admissions:{norm:admNorm,html:admHtml},
    tuition:{norm:tNorm,html:tHtml},
    qualifications:{norm:qNorm,html:qHtml},
    students:{norm:stCountNorm,html:stCountHtml},
    opencampus:{norm:ocNorm,html:ocHtml},
    verified:{norm:vDate,html:`<div><strong>最終確認：${esc(vDate)}</strong></div><div class="cmp-links"><a class="cmp-link" href="detail.html?id=${encodeURIComponent(id)}">詳細・一次資料出典を見る →</a>${r.official_url?`<a class="cmp-link" href="${esc(r.official_url)}" target="_blank" rel="noopener">大学公式 ↗</a>`:''}</div>`},
    memo:{norm:favMemo,html:`<div class="cmp-memo-box"><textarea class="cmp-memo-input" rows="2" maxlength="120" data-fav-note-input="${esc(id)}" placeholder="志望理由・気になる点・オープンキャンパス日程などの個人メモ（自動保存）">${esc(favMemo)}</textarea></div>`}
  };
}
function compareTable(){
  const rows=selectedRows();
  const data=rows.map(buildCompareRecord);
  const spec=[
    ['設置区分・募集状態','type'],
    ['学びの分野','fields'],
    ['学部・学科・研究科','academic'],
    ['キャンパス所在地','campus'],
    ['通学・最寄駅','access'],
    ['入試導線・選抜日程','admissions'],
    ['学費・初年度納入額','tuition'],
    ['取得可能資格','qualifications'],
    ['在籍学生数','students'],
    ['オープンキャンパス・資料請求','opencampus'],
    ['最終確認日・詳細導線','verified'],
    ['自分の比較メモ（端末保存）','memo']
  ];
  let shownCount=0;
  const bodyRows=spec.map(([label,key])=>{
    const norms=data.map(d=>d[key].norm);
    const isDiff=new Set(norms).size>1;
    if(state.compareDiffOnly&&!isDiff&&key!=='verified'&&key!=='memo')return '';
    shownCount++;
    return `<tr class="${isDiff?'is-diff-row':'is-same-row'}"><th><span>${esc(label)}</span>${isDiff?'<em class="cmp-diff-tag">違いあり</em>':'<em class="cmp-same-tag">共通</em>'}</th>${data.map(d=>`<td>${d[key].html}</td>`).join('')}</tr>`;
  }).filter(Boolean).join('');

  const shareUrl=`${location.origin}${location.pathname}?compare=${encodeURIComponent(rows.map(r=>r.id).join(','))}${state.compareDiffOnly?'&diff=1':''}`;
  const toolbar=`<div class="compare-toolbar"><label class="compare-diff-toggle"><input type="checkbox" id="compare-diff-checkbox" ${state.compareDiffOnly?'checked':''}><span>異なる項目だけ表示</span></label><div class="compare-toolbar-actions"><button type="button" class="btn" id="copy-compare-url-btn" data-share-url="${esc(shareUrl)}">共有URLをコピー</button><button type="button" class="btn" id="print-compare-btn">印刷・PDF保存</button></div></div><p class="compare-status-note">※ 空欄を推測で埋めず、「確認済み」「未調査」「公式掲載なし」「該当なし」の状態を明示しています。独自の点数付けや大学ランキングは行いません。</p>`;
  return `${toolbar}<div class="compare-table-scroll"><table class="compare-table"><thead><tr><th>比較項目（${shownCount}項目）</th>${rows.map(r=>`<th><div class="cmp-th-head"><strong>${esc(r.name)}</strong><button type="button" class="cmp-th-remove" data-remove-compare="${esc(r.id)}">外す ×</button></div></th>`).join('')}</tr></thead><tbody>${bodyRows}</tbody></table></div>`;
}
async function openCompare(){
  if(state.compare.size<2)return;
  const dlg=document.querySelector('#compare-dialog');
  const wrap=document.querySelector('#compare-table-wrap');
  if(!dlg||!wrap)return;
  if(!dlg.open)dlg.showModal();
  wrap.innerHTML='<p style="padding:18px">比較データを読み込んでいます…</p>';
  await ensureCompleteProfiles([...state.compare]);
  wrap.innerHTML=compareTable();
  syncUrl();
}
function installDevelopmentStatus(){if(document.querySelector('#university-db-development-status'))return;const style=document.createElement('style');style.textContent='.university-development-status{background:#18140a;color:#fff;border-top:1px solid #8f7229;border-bottom:1px solid #8f7229;padding:14px 18px;line-height:1.55}.university-development-status .inner{max-width:1180px;margin:auto;display:flex;gap:14px;align-items:flex-start}.university-development-status .label{background:#f3c95a;color:#241b05;border-radius:999px;padding:5px 10px;font-weight:900;font-size:.82rem;white-space:nowrap}.university-development-status p{margin:2px 0;color:#f2ead7;font-size:.9rem}.university-development-status small{display:block;margin-top:4px;color:#d9cda9}.academic-summary.is-pending{border:1px dashed #c79d3d;background:#fff9e8;padding:10px;border-radius:12px}@media(max-width:640px){.university-development-status .inner{display:block}.university-development-status .label{display:inline-block;margin-bottom:8px}}';document.head.appendChild(style);const b=document.createElement('section');b.id='university-db-development-status';b.className='university-development-status';b.innerHTML='<div class="inner"><span class="label">現在 開発・更新中</span><div><strong>東京都・埼玉県・神奈川県の大学の基本情報を優先して再点検しています。</strong><p>学部・学科、所在地、Google Mapsの大学別表示を優先更新中です。未同期の項目は「更新中」と表示します。</p></div></div>';const main=document.querySelector('main'),hero=document.querySelector('.tokyo-hero');if(main&&hero)main.insertBefore(b,hero)}
function updateAcademicStatus(source){const covered=state.rows.filter(r=>(state.faculties.get(r.id)||[]).length||(state.graduateSchools.get(r.id)||[]).length).length,s=document.querySelector('#academic-sync-status');if(s&&state.rows.length)s.textContent=`教育組織データ ${covered}/${state.rows.length}校を読込（${source==='merged'?'集約＋検証済みスナップショット':'検証済みスナップショット'}）・内容は継続更新中`}

let scrollRestored=false;
function restoreScrollIfReturning(){
  if(scrollRestored||!savedSession)return;
  const navType=performance.getEntriesByType?.('navigation')?.[0]?.type;
  if(!savedSession.returning&&navType!=='back_forward')return;
  if(savedSession.cardId){
    const allRows=sortRows(state.rows.filter(visible));
    const idx=allRows.findIndex(r=>r.id===savedSession.cardId);
    if(idx>=state.limit){
      state.limit=Math.ceil((idx+1)/PAGE_SIZE)*PAGE_SIZE;
      render();
    }
  }
  scrollRestored=true;
  const targetY=Number(savedSession.scrollY)||0;
  const targetId=savedSession.cardId;
  try{savedSession.returning=false;sessionStorage.setItem(SEARCH_STATE_KEY,JSON.stringify(savedSession));}catch{}
  requestAnimationFrame(()=>{
    if(targetY>0)window.scrollTo({top:targetY,behavior:'instant'});
    if(targetId){
      const cardEl=grid.querySelector(`.tokyo-card[data-id="${CSS.escape(targetId)}"]`);
      if(cardEl){
        if(targetY<=0)cardEl.scrollIntoView({behavior:'instant',block:'center'});
        cardEl.focus({preventScroll:true});
      }
    }
  });
}

installDevelopmentStatus();input.value=state.q;if(deptInput)deptInput.value=state.dept;sortSelect.value=['name','municipality','type','students-desc','students-asc'].includes(state.sort)?state.sort:'name';state.sort=sortSelect.value;activate(document.querySelector('#pref-filters'),'pref',state.pref);activate(document.querySelector('#type-filters'),'type',state.type);activate(document.querySelector('#field-filters'),'fieldChip',state.field);activate(document.querySelector('#status-filters'),'status',state.status);syncViewModeUI();if(state.qual||state.dept||state.withCampus||state.status!=='all'){const adv=document.querySelector('#advanced-filters');if(adv)adv.open=true;}
Promise.all([loadUniversityBundle(),loadAcademicBundle(),optionalObject('data/university-images.json'),optionalObject('data/university-detail-overrides.json'),optionalObject('data/tokyo_admissions_batch01.json')]).then(([rows,a,img,detail,admissions])=>{state.rows=mergeAdmissionDetails(mergeUniversityDetails(asList(rows),detail),admissions);const validIds=new Set(state.rows.map(r=>r.id));for(const cid of [...state.compare])if(!validIds.has(cid))state.compare.delete(cid);state.faculties=groupByUniversity(a.faculties);state.departments=groupByUniversity(a.departments);state.graduateSchools=groupByUniversity(a.graduateSchools);state.images=new Map(Object.entries(img.images||{}));document.querySelector('#stat-total')?.replaceChildren(document.createTextNode(String(state.rows.length)));bindQuality({});updateSnapshot();updateAcademicStatus(a.source);updateCompare();render();restoreScrollIfReturning();if(params.get('compare')&&state.compare.size>=2&&!savedSession?.returning)openCompare();}).catch(err=>{console.error('Tokyo university DB load failed',err);const s=document.querySelector('#academic-sync-status');if(s)s.textContent=`教育組織データ読込エラー：${err.message}`;grid.innerHTML='<div class="empty">大学データを読み込めませんでした。</div>';count.textContent='読込エラー';grid.setAttribute('aria-busy','false')});
if(!REGION_PACKS.length)fetch('data/tokyo_dataset_summary.generated.json').then(r=>r.ok?r.json():Promise.reject()).then(bindQuality).catch(()=>{});
document.querySelector('#tokyo-search').addEventListener('submit',e=>{e.preventDefault();runQuery(input.value)});input.addEventListener('input',()=>{state.q=input.value;state.limit=PAGE_SIZE;render()});clearQueryBtn?.addEventListener('click',()=>{state.q='';state.limit=PAGE_SIZE;input.value='';input.focus();render()});deptInput?.addEventListener('input',()=>{state.dept=deptInput.value;state.limit=PAGE_SIZE;render()});document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>runQuery(b.dataset.query)));document.querySelectorAll('.discovery-card[data-field]').forEach(b=>b.addEventListener('click',()=>runField(b.dataset.field)));document.querySelector('#pref-filters')?.addEventListener('click',e=>{const b=e.target.closest('[data-pref]');if(!b)return;state.pref=b.dataset.pref;state.limit=PAGE_SIZE;activate(e.currentTarget,'pref',state.pref);render();document.dispatchEvent(new CustomEvent('bantai:pref-change'))});document.querySelector('#type-filters').addEventListener('click',e=>{const b=e.target.closest('[data-type]');if(!b)return;state.type=b.dataset.type;state.limit=PAGE_SIZE;activate(e.currentTarget,'type',state.type);render()});document.querySelector('#field-filters')?.addEventListener('click',e=>{const b=e.target.closest('[data-field-chip]');if(!b)return;state.field=b.dataset.fieldChip;state.limit=PAGE_SIZE;activate(e.currentTarget,'fieldChip',state.field);render()});document.querySelector('#status-filters').addEventListener('click',e=>{const b=e.target.closest('[data-status]');if(!b)return;state.status=b.dataset.status;state.limit=PAGE_SIZE;activate(e.currentTarget,'status',state.status);render()});sortSelect.addEventListener('change',()=>{state.sort=sortSelect.value;render()});document.querySelector('#view-mode-switch')?.addEventListener('click',e=>{const b=e.target.closest('[data-view-mode]');if(!b)return;state.view=b.dataset.viewMode==='compact'?'compact':'card';render()});document.querySelector('#pagination-bar')?.addEventListener('click',e=>{if(e.target.closest('#load-more-btn')){const prevCount=grid.querySelectorAll('.tokyo-card').length;state.limit+=PAGE_SIZE;render();const nextCard=grid.querySelectorAll('.tokyo-card')[prevCount];if(nextCard)nextCard.focus({preventScroll:true});}else if(e.target.closest('#show-all-btn')){const prevCount=grid.querySelectorAll('.tokyo-card').length;state.limit=Math.max(state.rows.length,209);render();const nextCard=grid.querySelectorAll('.tokyo-card')[prevCount];if(nextCard)nextCard.focus({preventScroll:true});}else if(e.target.closest('#collapse-list-btn')){state.limit=PAGE_SIZE;render();document.querySelector('#search')?.scrollIntoView({behavior:'smooth',block:'start'});}});document.querySelector('#clear-filters').addEventListener('click',reset);document.querySelector('#active-filters-list')?.addEventListener('click',e=>{const b=e.target.closest('[data-clear-filter]');if(b)clearSingleFilter(b.dataset.clearFilter)});grid.addEventListener('click',e=>{const clr=e.target.closest('[data-clear-filter]');if(clr){clearSingleFilter(clr.dataset.clearFilter);return;}const b=e.target.closest('[data-compare]');if(b)toggleCompare(b.dataset.compare)});document.addEventListener('click',e=>{const a=e.target.closest('a[href*="detail.html"]');if(a){const m=a.getAttribute('href').match(/[?&]id=([^&#]+)/);saveSearchSession(m?decodeURIComponent(m[1]):'',true);}},true);let scrollTimer=null;window.addEventListener('scroll',()=>{if(scrollTimer)clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>saveSearchSession(),150);},{passive:true});document.querySelector('#compare-items').addEventListener('click',e=>{const b=e.target.closest('[data-remove-compare]');if(b)toggleCompare(b.dataset.removeCompare)});document.querySelector('#clear-compare').addEventListener('click',()=>{state.compare.clear();updateCompare();render()});document.querySelector('#open-compare').addEventListener('click',openCompare);
document.querySelector('#compare-table-wrap')?.addEventListener('change',e=>{
  if(e.target.id==='compare-diff-checkbox'){
    state.compareDiffOnly=e.target.checked;
    document.querySelector('#compare-table-wrap').innerHTML=compareTable();
    syncUrl();
  }
});
document.querySelector('#compare-table-wrap')?.addEventListener('click',e=>{
  const rm=e.target.closest('[data-remove-compare]');
  if(rm){toggleCompare(rm.dataset.removeCompare);return;}
  const copyBtn=e.target.closest('#copy-compare-url-btn');
  if(copyBtn){
    const url=copyBtn.dataset.shareUrl||location.href;
    navigator.clipboard?.writeText(url).catch(()=>{});
    copyBtn.textContent='✓ 共有URLをコピーしました';
    setTimeout(()=>{if(copyBtn.isConnected)copyBtn.textContent='共有URLをコピー';},2200);
    return;
  }
  if(e.target.closest('#print-compare-btn')){
    window.print();
  }
});
document.querySelector('#compare-table-wrap')?.addEventListener('input',e=>{
  const ta=e.target.closest('[data-fav-note-input]');
  if(ta&&typeof window.setFavoriteNote==='function'){
    window.setFavoriteNote(ta.dataset.favNoteInput,ta.value);
  }
});
