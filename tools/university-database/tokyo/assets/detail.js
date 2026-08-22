(()=>{
  const root=document.querySelector('#detail-root');
  const id=new URLSearchParams(location.search).get('id');
  const esc=(v='')=>String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const typeLabel={national:'国立',public:'公立',private:'私立'};
  const ACADEMIC_SNAPSHOTS=[
    'academic-structure-batches-03-08.json','academic-structure-batches-09-12.json','academic-structure-batches-13-14.json','academic-structure-batches-15-17.json','academic-structure-batches-18-22.json',
    'academic-structure-major-01.json','academic-structure-medical-01-02.json',
    'academic-structure-private-02.json','academic-structure-private-03.json','academic-structure-private-04.json','academic-structure-private-05.json','academic-structure-private-06.json','academic-structure-private-07.json','academic-structure-private-08.json',
    'academic-structure-tid-professional.json','departments-mejiro-verified.json'
  ];
  const group=(rows=[])=>{const m=new Map();for(const r of rows){if(!m.has(r.university_id))m.set(r.university_id,[]);m.get(r.university_id).push(r);}return m;};
  const json=async(url,fallback)=>{try{const r=await fetch(url);if(r.ok)return await r.json();}catch{}if(fallback){try{const r=await fetch(fallback);if(r.ok)return await r.json();}catch{}}return [];};
  const obj=async url=>{try{const r=await fetch(url);if(r.ok)return await r.json();}catch{}return {};};
  const val=(...xs)=>xs.find(x=>x!==undefined&&x!==null&&String(x).trim()!=='');
  const link=(url,label,cls='secondary')=>url?`<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)} ↗</a>`:'';
  const fact=(label,value)=>value?`<div class="detail-fact"><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`:'';
  const story=(title,text)=>text?`<section class="detail-section detail-story"><h2>${esc(title)}</h2><p>${esc(text)}</p></section>`:'';
  const list=(items,key='name')=>items.length?`<ul class="detail-list">${items.map(x=>`<li>${esc(typeof x==='string'?x:x[key]||'')}</li>`).join('')}</ul>`:'<p class="detail-empty">情報更新中です。大学公式情報と照合しています。</p>';
  const academicFact=(items,label,max=8)=>{
    if(!items.length)return `${label}：情報更新中（該当なしを含め公式確認中）`;
    const names=items.map(x=>x.name).filter(Boolean);
    const shown=names.slice(0,max).join('、');
    const rest=names.length>max?`、ほか${names.length-max}`:'';
    return `${label} ${items.length}：${shown}${rest}`;
  };
  const putById=(map,row)=>{if(row?.id)map.set(row.id,row);};
  const flattenAcademicDocument=(doc,faculties,departments,graduateSchools)=>{
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
  };
  const loadAcademicBundle=async()=>{
    const [generatedF,generatedD,generatedG]=await Promise.all([
      json('data/faculties_tokyo_all.generated.json'),
      json('data/departments_tokyo_all.generated.json'),
      json('data/graduate_schools_tokyo_all.generated.json')
    ]);
    if(generatedF.length||generatedD.length||generatedG.length)return {faculties:generatedF,departments:generatedD,graduateSchools:generatedG,source:'generated'};
    const [baseF,baseD,...snapshots]=await Promise.all([
      json('data/faculties.json'),json('data/departments.json'),...ACADEMIC_SNAPSHOTS.map(name=>obj(`data/${name}`))
    ]);
    const fm=new Map(),dm=new Map(),gm=new Map();
    for(const row of baseF)putById(fm,row);
    for(const row of baseD)putById(dm,row);
    for(const doc of snapshots)flattenAcademicDocument(doc,fm,dm,gm);
    return {faculties:[...fm.values()],departments:[...dm.values()],graduateSchools:[...gm.values()],source:'verified snapshots'};
  };

  if(!id){
    root.innerHTML='<div class="detail-error"><strong>大学が指定されていません。</strong><p><a href="./">大学一覧へ戻る</a></p></div>';
    return;
  }

  Promise.all([
    json('data/universities_tokyo_all.generated.json'),
    loadAcademicBundle(),
    obj('data/university-detail-national-public-batch1.json'),
    obj('data/university-detail-overrides.json'),
    obj('data/private-detail-2026-updates.json')
  ]).then(([rows,academic,coreRegistry,detailRegistry,private2026])=>{
    let row=rows.find(x=>x.id===id);
    if(!row)throw new Error('not found');
    for(const extra of [coreRegistry?.universities?.[id],detailRegistry?.universities?.[id],private2026?.universities?.[id]]){
      if(extra)row={...row,...extra,headquarters:{...(row.headquarters||{}),...(extra.headquarters||{})},student_counts:{...(row.student_counts||{}),...(extra.student_counts||{})}};
    }

    const fm=group(academic.faculties),dm=group(academic.departments),gm=group(academic.graduateSchools);
    const f=fm.get(id)||[],d=dm.get(id)||[],g=gm.get(id)||[];
    const municipality=val(row.municipality,row.headquarters?.municipality,'所在地確認中');
    const address=val(row.headquarters?.address,`東京都 ${municipality}`);
    const students=Number(row.student_counts?.total)||0;
    const official=val(row.official_url,row.admissions_url,'');
    const admissions=val(row.admissions_url,row.official_url,'');
    const mapsQuery=`${row.name} ${address||`東京都 ${municipality}`}`.trim();
    const maps=`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapsQuery)}`;
    const founded=val(row.founded_year,row.foundation_year);
    const opened=val(row.opened_year,row.established_year);
    const founder=val(row.founder,row.founder_name,row.founding_person);
    const operator=val(row.operator,row.establisher,row.installing_body);
    const purpose=val(row.university_goal,row.purpose,row.educational_purpose,row.mission);
    const philosophy=val(row.philosophy,row.founding_spirit,row.educational_philosophy);
    const feature=val(row.feature_summary,row.features,row.characteristics);
    const history=val(row.history_summary,row.history,row.history_text);
    const fields=row.academic_field_tags||[];

    document.title=`${row.name} | 東京都144大学`;
    root.innerHTML=`
      <section class="detail-hero">
        <div class="detail-hero-main">
          <span class="detail-kicker">TOKYO UNIVERSITY PROFILE</span>
          <h1>${esc(row.name)}</h1>
          <div class="detail-meta">
            <span class="detail-pill">${esc(typeLabel[row.establishment_type]||'')}</span>
            <span class="detail-pill">東京都 ${esc(municipality)}</span>
            <span class="detail-pill">${row.admissions_status==='stopped'?'募集停止':'募集継続'}</span>
            <span class="detail-pill">基本情報 更新中</span>
          </div>
          <p class="detail-summary">${esc(feature||philosophy||purpose||'大学公式・公的資料をもとに整理した大学情報です。')}</p>
          <div class="detail-actions">
            ${link(official,'大学公式情報','primary')}
            ${link(admissions,'入試情報')}
            ${link(row.application_guidelines_url,'募集要項')}
            ${link(row.brochure_request_url,'資料請求')}
            ${link(row.open_campus_url,'オープンキャンパス')}
            <a class="secondary" href="${maps}" target="_blank" rel="noopener">Google Maps ↗</a>
          </div>
        </div>
        <aside class="detail-hero-side">
          <div class="detail-stat"><small>在籍者数</small><strong>${students?students.toLocaleString('ja-JP')+'人':'—'}</strong></div>
          <div class="detail-stat"><small>学部</small><strong>${f.length||'更新中'}</strong></div>
          <div class="detail-stat"><small>学科等</small><strong>${d.length||'更新中'}</strong></div>
          <div class="detail-stat"><small>研究科</small><strong>${g.length||'—'}</strong></div>
        </aside>
      </section>
      <section class="detail-section detail-core">
        <div class="detail-section-head"><span>01</span><div><h2>大学の基本情報</h2><p>所在地・教育組織・大学の成り立ちを最初に確認できます。</p></div></div>
        <dl class="detail-facts">
          ${fact('正式名称',row.name)}
          ${fact('所在地',address)}
          ${fact('設置区分',typeLabel[row.establishment_type]||'—')}
          ${fact('学部',academicFact(f,'学部'))}
          ${fact('学科・課程等',academicFact(d,'学科等'))}
          ${fact('研究科',g.length?academicFact(g,'研究科'):'研究科：情報更新中／該当なし')}
          ${fact('創立・源流',founded?`${founded}年`:'')}
          ${fact('現在の大学の開学',opened?`${opened}年`:'')}
          ${fact('創立者',founder)}
          ${fact('設置者',operator)}
          ${fact('学生数',students?`${students.toLocaleString('ja-JP')}人${row.student_counts?.as_of?`（${row.student_counts.as_of}現在）`:''}`:'情報更新中')}
        </dl>
      </section>
      <div class="detail-grid detail-narrative">
        ${story('沿革・歴史',history)}
        ${story('建学の精神・理念',philosophy)}
        ${story('大学の目的',purpose)}
        ${story('この大学の特色',feature)}
        <section class="detail-section"><h2>主な学問分野</h2>${fields.length?`<div class="detail-fields">${fields.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:'<p class="detail-empty">情報更新中</p>'}</section>
      </div>
      <section class="detail-section detail-academic">
        <div class="detail-section-head"><span>02</span><div><h2>学べる分野・教育組織</h2><p>学部・学科・研究科をまとめて確認できます。</p></div></div>
        <div class="detail-grid">
          <div><h3>学部</h3>${list(f)}</div>
          <div><h3>学科・課程等</h3>${list(d)}</div>
          <div><h3>研究科</h3>${list(g)}</div>
          <div><h3>受験・大学を知る</h3><div class="detail-link-stack">${link(official,'大学公式情報','primary')}${link(admissions,'入試情報')}${link(row.application_guidelines_url,'募集要項')}${link(row.brochure_request_url,'資料請求')}${link(row.open_campus_url,'オープンキャンパス')}<a class="secondary" href="${maps}" target="_blank" rel="noopener">Google Maps ↗</a></div></div>
        </div>
      </section>
      <div class="detail-note">現在、東京都144大学の基本情報を優先更新中です。学部・学科・所在地・地図リンクを再確認し、未同期の項目は推測で埋めず「情報更新中」と表示します。教育組織は${academic.source==='generated'?'集約済みデータ':'公開済み検証スナップショット'}から読み込んでいます。</div>`;
  }).catch(()=>{
    root.innerHTML='<div class="detail-error"><strong>大学情報を読み込めませんでした。</strong><p><a href="./">大学一覧へ戻る</a></p></div>';
  });
})();
