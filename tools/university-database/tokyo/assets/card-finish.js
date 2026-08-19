(()=>{
const themeNames={tech:'情報・AI・工学',health:'医療・保健・生命',arts:'芸術・デザイン',global:'国際・語学',education:'教育・子ども',science:'理学・環境',sports:'スポーツ',social:'人文・社会',classic:'総合'};
const themeRules=[['health',/医学|医療|看護|薬学|保健|歯学|鍼灸|柔道整復|生命/],['arts',/芸術|美術|音楽|デザイン|映像|演劇|舞踊|表現/],['tech',/情報|AI|工学|理工|通信|電気|電子|データ|DX|数理/],['science',/理学|農学|環境|海洋|獣医|化学|生物|科学/],['global',/国際|語学|外国語|地域研究|日本研究|グローバル/],['education',/教育|保育|幼児|子ども|児童/],['sports',/スポーツ|体育|健康スポーツ|武道|ダンス/],['social',/法学|政治|経済|経営|商学|社会|福祉|政策|観光|心理|文学|人文|宗教/]];
function finishedTheme(row){const f=state.faculties.get(row.id)||[],g=state.graduateSchools.get(row.id)||[];const text=[...(row.academic_field_tags||[]),...f.flatMap(x=>[x.name,...(x.academic_field_tags||[])]),...g.flatMap(x=>[x.name,...(x.academic_field_tags||[])]),row.name||''].join(' ');for(const [theme,re] of themeRules)if(re.test(text))return theme;return'classic';}
function finishedVisual(row){
  const image=typeof verifiedImage==='function'?verifiedImage(row):null;
  const label=esc(typeLabel[row.establishment_type]||'');
  if(image){
    const alt=esc(image.alt||`${row.name}の大学紹介イメージ`);
    const isAI=image.rights_status==='ai_original';
    const credit=isAI?`<span class="image-ai-label">${esc(image.label||'イメージ画像（AI生成）')}</span>`:`<a class="image-source-link" href="${esc(image.source_url)}" target="_blank" rel="noopener">画像出典 ↗</a>`;
    return `<div class="card-visual has-image ${isAI?'ai-original-image':''}"><img class="university-card-image" src="${esc(image.image_url)}" alt="${alt}" loading="lazy" decoding="async"><span class="visual-label">${label}</span>${credit}</div>`;
  }
  const theme=finishedTheme(row);
  const themeLabel=themeNames[theme]||themeNames.classic;
  return `<div class="card-visual finished-campus-visual" aria-label="${esc(row.name)}の案内ビジュアル"><div class="campus-scene" aria-hidden="true"><span class="campus-sun"></span><span class="campus-building"><i></i><i></i><i></i></span><span class="campus-tree tree-a"></span><span class="campus-tree tree-b"></span><span class="campus-student student-a"></span><span class="campus-student student-b"></span></div><span class="visual-label">${label}</span><span class="visual-theme">${esc(themeLabel)}</span></div>`;
}
function shortSummary(text=''){const s=String(text).trim();return s.length>92?s.slice(0,90)+'…':s;}
function detailUrl(row){return `detail.html?id=${encodeURIComponent(row.id)}`;}
card=function(row){
  const stopped=row.admissions_status==='stopped';
  const f=state.faculties.get(row.id)||[];
  const d=state.departments.get(row.id)||[];
  const g=state.graduateSchools.get(row.id)||[];
  const fields=(row.academic_field_tags||[]).slice(0,3);
  const compared=state.compare.has(row.id);
  const summary=shortSummary(row.feature_summary||row.philosophy||'大学公式・公的資料をもとに、学びの特色を確認できます。');
  const fieldHtml=fields.length?`<div class="finished-fields">${fields.map(x=>`<span>${esc(x)}</span>`).join('')}</div>`:'';
  const official=row.official_url||row.admissions_url||'';
  const admissions=row.admissions_url||row.official_url||'';
  return `<article class="university-card tokyo-card finished-university-card theme-${finishedTheme(row)}" data-type="${esc(row.establishment_type)}" data-id="${esc(row.id)}" data-detail-url="${esc(detailUrl(row))}" data-card-ready="true" tabindex="0" role="link" aria-label="${esc(row.name)}の詳細を見る">${finishedVisual(row)}<div class="card-body"><div class="finished-card-top"><span class="status-pill ${stopped?'stopped':'active'}">${stopped?'募集停止':'募集継続'}</span><span class="place-pill">東京都 ${esc(municipality(row))}</span></div><h3>${esc(row.name)}</h3><p class="finished-summary">${esc(summary)}</p><div class="finished-facts"><div><small>在籍者数</small><strong>${formatStudents(row)}</strong></div><div><small>学部</small><strong>${f.length?`${f.length}`:'—'}</strong></div><div><small>学科</small><strong>${d.length?`${d.length}`:'—'}</strong></div></div>${fieldHtml}<div class="finished-academic-line"><span>学部 ${f.length||'—'}</span><span>研究科 ${g.length||'—'}</span></div><a class="btn card-detail-open" href="${esc(detailUrl(row))}">詳しく見る →</a><button class="compare-toggle ${compared?'active':''}" type="button" data-compare="${esc(row.id)}">${compared?'✓ 比較候補に追加済み':'＋ 比較候補に追加'}</button><div class="card-actions">${official?`<a class="btn primary official-card-link" href="${esc(official)}" target="_blank" rel="noopener">公式情報 ↗</a>`:''}${admissions?`<a class="btn admissions-card-link" href="${esc(admissions)}" target="_blank" rel="noopener">入試情報 ↗</a>`:''}<a class="btn map-card-link" href="${mapsUrl(row)}" target="_blank" rel="noopener">地図 ↗</a></div></div></article>`;
};
const priorRender=render;
render=function(){priorRender();document.querySelectorAll('.tokyo-card').forEach(card=>card.classList.add('finished-card-mounted'));};
if(state.rows.length)render();
const interactive='a,button,input,select,textarea,summary,[role="button"]';
grid.addEventListener('click',e=>{const card=e.target.closest('.tokyo-card[data-detail-url]');if(!card||e.target.closest(interactive))return;location.href=card.dataset.detailUrl;});
grid.addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.key!==' ')return;const card=e.target.closest('.tokyo-card[data-detail-url]');if(!card||e.target.closest(interactive))return;e.preventDefault();location.href=card.dataset.detailUrl;});
})();
