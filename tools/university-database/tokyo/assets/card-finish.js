(()=>{
const themeNames={tech:'情報・AI・工学',health:'医療・保健・生命',arts:'芸術・デザイン',global:'国際・語学',education:'教育・子ども',science:'理学・環境',sports:'スポーツ',social:'人文・社会',classic:'総合'};
const themeRules=[['health',/医学|医療|看護|薬学|保健|歯学|鍼灸|柔道整復|生命/],['arts',/芸術|美術|音楽|デザイン|映像|演劇|舞踊|表現/],['tech',/情報|AI|工学|理工|通信|電気|電子|データ|DX|数理/],['science',/理学|農学|環境|海洋|獣医|化学|生物|科学/],['global',/国際|語学|外国語|地域研究|日本研究|グローバル/],['education',/教育|保育|幼児|子ども|児童/],['sports',/スポーツ|体育|健康スポーツ|武道|ダンス/],['social',/法学|政治|経済|経営|商学|社会|福祉|政策|観光|心理|文学|人文|宗教/]];
const SVG_EXT='<svg class="ui-svg-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 3h7v7M13 3L6 10M11 9v4H3V5h4"/></svg>';
const SVG_MAP='<svg class="ui-svg-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M8 14s5-4.2 5-8A5 5 0 0 0 3 6c0 3.8 5 8 5 8z"/><circle cx="8" cy="6" r="1.8"/></svg>';
const SVG_FILTER='<svg class="ui-svg-icon" width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M2 3.5h12L9.5 8.5v4.5l-3-1.5V8.5L2 3.5z"/></svg>';
const SVG_SORT='<svg class="ui-svg-icon" width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 3v10M5 13l-2.5-2.5M5 13l2.5-2.5M11 13V3M11 3L8.5 5.5M11 3l2.5 2.5"/></svg>';
const SVG_COMPARE='<svg class="ui-svg-icon" width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="2" y="2.5" width="5" height="11" rx="1"/><rect x="9" y="2.5" width="5" height="11" rx="1"/></svg>';
function finishedTheme(row){const f=state.faculties.get(row.id)||[],g=state.graduateSchools.get(row.id)||[];const text=[...(row.academic_field_tags||[]),...f.flatMap(x=>[x.name,...(x.academic_field_tags||[])]),...g.flatMap(x=>[x.name,...(x.academic_field_tags||[])]),row.name||''].join(' ');for(const [theme,re] of themeRules)if(re.test(text))return theme;return'classic';}
function finishedVisual(row){const image=typeof verifiedImage==='function'?verifiedImage(row):null;const label=esc(typeLabel[row.establishment_type]||'');if(image){const alt=esc(image.alt||`${row.name}の大学紹介イメージ`);const isAI=image.rights_status==='ai_original';const sourceLabel=image.rights_basis==='photographer_permission'?esc(image.source_label||'撮影者提供'):'画像出典';const credit=isAI?`<span class="image-ai-label">${esc(image.label||'イメージ画像（AI生成）')}</span>`:`<a class="image-source-link" href="${esc(image.source_url)}" target="_blank" rel="noopener">${sourceLabel} ${SVG_EXT}</a>`;return `<div class="card-visual has-image ${isAI?'ai-original-image':'real-university-image'}"><img class="university-card-image" src="${esc(image.image_url)}" alt="${alt}" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.closest('.card-visual').classList.add('image-failed')"><span class="visual-label">${label}</span>${credit}</div>`;}const theme=finishedTheme(row);return `<div class="card-visual finished-campus-visual" aria-label="${esc(row.name)}の案内ビジュアル（公認写真受付中）"><div class="campus-scene" aria-hidden="true"><span class="campus-sun"></span><span class="campus-building"><i></i><i></i><i></i></span><span class="campus-tree tree-a"></span><span class="campus-tree tree-b"></span><span class="campus-student student-a"></span><span class="campus-student student-b"></span></div><span class="visual-label">${label}</span><span class="visual-theme">${esc(themeNames[theme]||themeNames.classic)}</span><span class="visual-unregistered-tag">写真受付中</span></div>`;}
function shortSummary(text=''){const s=String(text).trim();return s.length>72?s.slice(0,70)+'…':s;}
function detailUrl(row){return `detail.html?id=${encodeURIComponent(row.id)}`;}
function finishedPlace(row){const pref=row.prefecture||row.headquarters?.prefecture||'東京都';const place=municipality(row);return place&&place!=='所在地確認中'?(pref==='東京都'?place:`${pref} ${place}`):pref;}
function cardDecisionLinks(row){
  const links=[];
  if(row.application_guidelines_url)links.push(`<a class="card-sub-link" href="${esc(row.application_guidelines_url)}" target="_blank" rel="noopener">募集要項 ${SVG_EXT}</a>`);
  if(row.open_campus_url)links.push(`<a class="card-sub-link" href="${esc(row.open_campus_url)}" target="_blank" rel="noopener">オープンキャンパス ${SVG_EXT}</a>`);
  if(row.brochure_request_url)links.push(`<a class="card-sub-link" href="${esc(row.brochure_request_url)}" target="_blank" rel="noopener">資料請求 ${SVG_EXT}</a>`);
  return links.length?`<div class="card-decision-links" aria-label="受験・進学関連の公式リンク">${links.join('')}</div>`:'';
}
function cardActionLinks(row){const detail=detailUrl(row);const official=row.official_url||detail;const admissions=row.admissions_url||row.official_url||detail;const officialExternal=!!row.official_url;const admissionsExternal=!!(row.admissions_url||row.official_url);return `<div class="card-actions finished-card-actions"><a class="btn official-card-link" href="${esc(official)}"${officialExternal?' target="_blank" rel="noopener"':''}>${officialExternal?`大学公式情報 ${SVG_EXT}`:'公式情報を詳細で確認 →'}</a><a class="btn primary admissions-card-link" href="${esc(admissions)}"${admissionsExternal?' target="_blank" rel="noopener"':''}>${row.admissions_url?`入試情報 ${SVG_EXT}`:admissionsExternal?`入試案内・公式 ${SVG_EXT}`:'入試情報を詳細で確認 →'}</a><a class="btn map-card-link" href="${esc(mapsUrl(row))}" target="_blank" rel="noopener">${SVG_MAP} 地図 ${SVG_EXT}</a></div>${cardDecisionLinks(row)}`;}
function cardExpandableDetails(row,f,d,g,graduateOnly){
  const allUnits=[...new Set((graduateOnly?g.map(x=>x.name):[...f.map(x=>x.name),...d.map(x=>x.name)]).filter(Boolean))];
  const quals=(state.qualIdx.get(row.id)||[]).map(x=>x.name).filter(Boolean);
  const stList=(state.accessIdx.get(row.id)?.stations||[]);
  const extraUnits=allUnits.slice(3);
  const extraQuals=quals.slice(4);
  const extraStations=stList.slice(2);
  if(!extraUnits.length&&!extraQuals.length&&!extraStations.length)return '';
  const parts=[];
  if(extraUnits.length)parts.push(`<div class="card-more-group"><strong>全学部・学科・研究科（${allUnits.length}）</strong><div class="finished-fields">${allUnits.map(u=>`<span>${esc(u)}</span>`).join('')}</div></div>`);
  if(extraQuals.length)parts.push(`<div class="card-more-group"><strong>確認済み取得可能資格（${quals.length}件）</strong><div class="finished-fields">${quals.map(q=>`<span>${esc(q.replace(/（.*?）/g,''))}</span>`).join('')}</div></div>`);
  if(extraStations.length)parts.push(`<div class="card-more-group"><strong>最寄り駅・アクセス（${stList.length}件）</strong><ul class="card-more-stations">${stList.map(s=>`<li><b>${esc(s.station)}</b> ${esc(s.access||'')}</li>`).join('')}</ul></div>`);
  const summaryLabels=[];
  if(extraUnits.length)summaryLabels.push(`学部・学科ほか${extraUnits.length}件`);
  if(extraQuals.length)summaryLabels.push(`資格ほか${extraQuals.length}件`);
  if(extraStations.length)summaryLabels.push(`駅ほか${extraStations.length}件`);
  return `<details class="card-more-details"><summary>＋ ${esc(summaryLabels.join('・'))}を展開</summary><div class="card-more-body">${parts.join('')}</div></details>`;
}
function ensureMobileDock(){
  let dock=document.querySelector('#mobile-bottom-dock');
  if(!dock){
    dock=document.createElement('nav');
    dock.id='mobile-bottom-dock';
    dock.className='mobile-bottom-dock';
    dock.setAttribute('aria-label','スマートフォン用クイック操作バー');
    dock.innerHTML=`<button type="button" class="mobile-dock-btn" id="mobile-dock-filter">${SVG_FILTER}<span>絞り込み</span><b id="mobile-dock-filter-count" hidden>0</b></button><button type="button" class="mobile-dock-btn" id="mobile-dock-sort">${SVG_SORT}<span>並び替え</span></button><button type="button" class="mobile-dock-btn is-compare" id="mobile-dock-compare">${SVG_COMPARE}<span>比較</span><b id="mobile-dock-compare-count">0/4</b></button>`;
    document.body.appendChild(dock);
    dock.querySelector('#mobile-dock-filter').addEventListener('click',()=>{
      document.querySelector('#search')?.scrollIntoView({behavior:'smooth',block:'start'});
      setTimeout(()=>document.querySelector('#tokyo-search-input')?.focus({preventScroll:true}),300);
    });
    dock.querySelector('#mobile-dock-sort').addEventListener('click',()=>{
      const s=document.querySelector('#sort-select');
      if(s){s.scrollIntoView({behavior:'smooth',block:'center'});setTimeout(()=>s.focus({preventScroll:true}),300);}
    });
    dock.querySelector('#mobile-dock-compare').addEventListener('click',e=>{
      if(state.compare.size>=2){
        window.__lastModalTrigger=e.currentTarget;
        openCompare();
      }else{
        document.querySelector('#compare')?.scrollIntoView({behavior:'smooth',block:'start'});
      }
    });
  }
  const fCount=typeof activeFilterItems==='function'?activeFilterItems().length:0;
  const fb=dock.querySelector('#mobile-dock-filter-count');
  if(fb){fb.hidden=fCount===0;fb.textContent=String(fCount);}
  const cb=dock.querySelector('#mobile-dock-compare-count');
  if(cb)cb.textContent=`${state.compare.size}/4`;
  dock.querySelector('#mobile-dock-compare')?.classList.toggle('is-ready',state.compare.size>=2);
}
function setupDialogFocusReturn(){
  document.addEventListener('click',e=>{
    const openCmp=e.target.closest('#open-compare');
    if(openCmp){window.__lastModalTrigger=openCmp;return;}
    const polBtn=e.target.closest('.policy-button');
    if(polBtn){window.__lastModalTrigger=polBtn;return;}
  },true);
  for(const dlg of document.querySelectorAll('#compare-dialog,#policy-dialog')){
    dlg.addEventListener('close',()=>{
      const t=window.__lastModalTrigger;
      if(t&&typeof t.focus==='function'&&t.isConnected){
        requestAnimationFrame(()=>t.focus());
      }
    });
  }
}
function ensureTopButton(){let b=document.querySelector('button.scroll-top-button,[data-scroll-top-button]');if(!b){b=document.createElement('button');b.type='button';b.className='scroll-top-button';b.dataset.scrollTopButton='true';document.body.appendChild(b);}b.setAttribute('aria-label','ページ上部へ戻る');b.title='ページ上部へ戻る';b.innerHTML='<span aria-hidden="true">↑</span><small>上へ</small>';Object.assign(b.style,{position:'fixed',right:'22px',bottom:'22px',zIndex:'80',display:'flex',alignItems:'center',gap:'7px',padding:'10px 14px',border:'1px solid rgba(255,255,255,.7)',borderRadius:'999px',background:'#082844',color:'#fff',fontWeight:'900',boxShadow:'0 8px 24px rgba(6,27,46,.28)',cursor:'pointer',opacity:'0',visibility:'hidden',transform:'translateY(8px)',transition:'opacity .18s ease,transform .18s ease,visibility .18s ease'});const sync=()=>{const show=window.scrollY>520;b.style.opacity=show?'1':'0';b.style.visibility=show?'visible':'hidden';b.style.transform=show?'translateY(0)':'translateY(8px)';b.style.pointerEvents=show?'auto':'none';};b.onclick=()=>window.scrollTo({top:0,behavior:'smooth'});window.addEventListener('scroll',sync,{passive:true});sync();return b;}
function rowVerifiedDate(row){
  if(row.verified_at)return row.verified_at;
  const srcs=row.sources||[];
  const dates=srcs.map(s=>s.verified_at).filter(Boolean).sort();
  return dates.length?dates[dates.length-1]:(row.updated_at||'2026-10-30');
}
function studentCardHtml(row){
  const n=studentTotal(row);
  if(n>0){
    const asOf=row.student_counts?.as_of;
    return `<strong>${n.toLocaleString('ja-JP')}人</strong>${asOf?`<span class="card-fact-sub">${esc(asOf)}基準</span>`:''}`;
  }
  const st=row.student_counts?.status==='not_published'?'not_published':'uninvestigated';
  return st==='not_published'?'<strong><span class="dq-badge dq-not-published">公式掲載なし</span></strong>':'<strong><span class="dq-badge dq-uninvestigated">未調査</span></strong>';
}
card=function(row){const stopped=row.admissions_status==='stopped';const f=state.faculties.get(row.id)||[];const d=state.departments.get(row.id)||[];const g=state.graduateSchools.get(row.id)||[];const graduateOnly=!f.length&&g.length>0;const fields=(row.academic_field_tags||[]).slice(0,2);const compared=state.compare.has(row.id);const summary=shortSummary(row.feature_summary||row.philosophy||'大学の特色・学び・基本情報を詳細ページで確認できます。');const reasons=typeof window.matchReasons==='function'?window.matchReasons(row):[];const reasonHtml=reasons.length?`<div class="card-match-reasons" aria-label="検索条件との一致理由"><strong>一致した条件</strong><span>${reasons.map(r=>esc(r)).join(' ／ ')}</span></div>`:'';const fieldHtml=fields.length?`<div class="finished-fields">${fields.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:'';const academicUnits=[...new Set((graduateOnly?g.slice(0,3).map(x=>x.name):[...f.slice(0,2).map(x=>x.name),...d.slice(0,1).map(x=>x.name)]).filter(Boolean))];const academicHtml=academicUnits.length?`<div class="finished-fields academic-units">${academicUnits.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:'<div class="academic-summary is-pending"><strong><span class="dq-badge dq-updating">更新確認中</span> 教育組織情報</strong></div>';const expandHtml=cardExpandableDetails(row,f,d,g,graduateOnly);const organizationText=graduateOnly?`大学院大学（学部該当なし） / 研究科 ${g.length}`:(f.length?`学部 ${f.length} / ${d.length?`学科等 ${d.length}`:'学科等 未調査'}`:'学部・学科等 未調査');const vDate=rowVerifiedDate(row);const studentCompact=studentTotal(row)>0?`学生数 ${formatStudents(row)}${row.student_counts?.as_of?`（${esc(row.student_counts.as_of)}）`:''}`:'学生数 未調査';if(state.view==='compact'){const typeText=esc(typeLabel[row.establishment_type]||'');return `<article class="university-card tokyo-card finished-university-card is-compact-card theme-${finishedTheme(row)}" data-type="${esc(row.establishment_type)}" data-id="${esc(row.id)}" data-detail-url="${esc(detailUrl(row))}" data-card-ready="true" tabindex="0" role="link" aria-label="${esc(row.name)}の詳細を見る"><div class="card-body compact-card-body"><div class="compact-card-main"><div class="finished-card-top compact-card-top"><span class="compact-type-pill type-${esc(row.establishment_type)}">${typeText}</span><span class="status-pill tag ${stopped?'stopped':'active'}">${stopped?'募集停止':'募集継続'}</span><span class="place-pill">${esc(finishedPlace(row))}</span><span class="compact-meta-fact">${studentCompact}</span><span class="compact-meta-fact">${esc(organizationText)}</span><span class="compact-meta-fact">最終確認 ${esc(vDate)}</span></div><h3>${esc(row.name)}</h3>${reasonHtml}<div class="compact-tags-row">${fieldHtml}${academicHtml}</div>${expandHtml}</div><div class="compact-card-side"><a class="btn card-detail-open" href="${esc(detailUrl(row))}">大学の詳細を見る →</a>${cardActionLinks(row)}<button class="compare-toggle ${compared?'active':''}" type="button" data-compare="${esc(row.id)}">${compared?'✓ 比較候補に追加済み':'＋ 比較候補に追加'}</button></div></div></article>`;}return `<article class="university-card tokyo-card finished-university-card theme-${finishedTheme(row)}" data-type="${esc(row.establishment_type)}" data-id="${esc(row.id)}" data-detail-url="${esc(detailUrl(row))}" data-card-ready="true" tabindex="0" role="link" aria-label="${esc(row.name)}の詳細を見る">${finishedVisual(row)}<div class="card-body"><div class="finished-card-top"><span class="status-pill tag ${stopped?'stopped':'active'}">${stopped?'募集停止':'募集継続'}</span><span class="place-pill">${esc(finishedPlace(row))}</span></div><h3>${esc(row.name)}</h3>${reasonHtml}<p class="finished-summary">${esc(summary)}</p>${fieldHtml}${academicHtml}${expandHtml}<div class="finished-facts"><div><small>学生数</small>${studentCardHtml(row)}</div><div><small>教育組織</small><strong>${esc(organizationText)}</strong><span class="card-fact-sub">最終確認 ${esc(vDate)}</span></div></div><a class="btn card-detail-open" href="${esc(detailUrl(row))}">大学の詳細を見る →</a>${cardActionLinks(row)}<button class="compare-toggle ${compared?'active':''}" type="button" data-compare="${esc(row.id)}">${compared?'✓ 比較候補に追加済み':'＋ 比較候補に追加'}</button></div></article>`;};
const priorRender=render;render=function(){priorRender();document.querySelectorAll('.tokyo-card').forEach(card=>card.classList.add('finished-card-mounted'));ensureMobileDock();};const priorUpdateCompare=typeof updateCompare==='function'?updateCompare:null;if(priorUpdateCompare){updateCompare=function(){priorUpdateCompare();ensureMobileDock();};}if(state.rows.length)render();ensureTopButton();ensureMobileDock();setupDialogFocusReturn();const interactive='a,button,input,select,textarea,summary,details,[role="button"]';grid.addEventListener('click',e=>{const card=e.target.closest('.tokyo-card[data-detail-url]');if(!card||e.target.closest(interactive))return;if(typeof window.saveSearchSession==='function')window.saveSearchSession(card.dataset.id,true);location.href=card.dataset.detailUrl;});grid.addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.key!==' ')return;const card=e.target.closest('.tokyo-card[data-detail-url]');if(!card||e.target.closest(interactive))return;e.preventDefault();if(typeof window.saveSearchSession==='function')window.saveSearchSession(card.dataset.id,true);location.href=card.dataset.detailUrl;});
})();