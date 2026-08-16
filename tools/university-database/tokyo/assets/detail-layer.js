(()=>{
const $=s=>document.querySelector(s);
const safe=v=>esc(v??'');
function themeLabel(row){
  const text=[...(row.academic_field_tags||[]),...(state.faculties.get(row.id)||[]).map(x=>x.name),row.name].join(' ');
  if(/情報|AI|データ|工学|理工/.test(text))return 'TECH & AI';
  if(/医|看護|薬|生命|保健/.test(text))return 'LIFE & HEALTH';
  if(/芸術|美術|音楽|デザイン/.test(text))return 'ART & CREATE';
  if(/国際|外国語|語学|文化/.test(text))return 'GLOBAL';
  if(/教育|児童|こども|保育/.test(text))return 'EDUCATION';
  if(/体育|スポーツ|武道/.test(text))return 'SPORTS';
  if(/理学|農学|環境|数理/.test(text))return 'SCIENCE';
  return 'UNIVERSITY PROFILE';
}
function facts(row){
  const f=state.faculties.get(row.id)||[];
  const d=state.departments.get(row.id)||[];
  const g=state.graduateSchools.get(row.id)||[];
  return [
    ['設置区分',typeLabel[row.establishment_type]||'—'],
    ['所在地',`東京都 ${municipality(row)}`],
    ['在籍者数',formatStudents(row)],
    ['学部',f.length?`${f.length}学部`:'—'],
    ['学科',d.length?`${d.length}学科`:'—'],
    ['研究科',g.length?`${g.length}研究科`:'—']
  ];
}
function visual(row){
  const image=verifiedImage(row);
  if(image){
    const isAI=image.rights_status==='ai_original';
    return `<div class="detail-visual has-image"><img src="${safe(image.image_url)}" alt="${safe(image.alt||`${row.name}の大学紹介イメージ`)}"><span>${isAI?safe(image.label||'イメージ画像（AI生成）'):'大学紹介画像'}</span></div>`;
  }
  return `<div class="detail-visual themed"><span class="detail-theme-kicker">${safe(themeLabel(row))}</span><strong>${safe(row.name)}</strong><small>学問分野と大学情報をもとにした案内ビジュアル</small></div>`;
}
function renderUnits(row){
  const f=state.faculties.get(row.id)||[];
  const d=state.departments.get(row.id)||[];
  const g=state.graduateSchools.get(row.id)||[];
  if(!f.length&&!g.length)return '<p class="detail-empty">学部・研究科情報は確認・同期中です。</p>';
  const facultyHtml=f.slice(0,12).map(x=>{
    const deps=d.filter(y=>y.faculty_id===x.id).slice(0,8);
    return `<div class="detail-unit"><strong>${safe(x.name)}</strong>${deps.length?`<div>${deps.map(y=>`<span>${safe(y.name)}</span>`).join('')}</div>`:''}</div>`;
  }).join('');
  const gradHtml=g.slice(0,8).map(x=>`<div class="detail-unit"><strong>${safe(x.name)}</strong>${(x.programs||[]).length?`<div>${x.programs.slice(0,6).map(y=>`<span>${safe(y)}</span>`).join('')}</div>`:''}</div>`).join('');
  return facultyHtml+gradHtml;
}
function openDetail(id){
  const row=state.rows.find(r=>r.id===id);if(!row)return;
  let dialog=$('#university-detail-dialog');
  if(!dialog){
    dialog=document.createElement('dialog');dialog.id='university-detail-dialog';dialog.className='university-detail-dialog';document.body.appendChild(dialog);
  }
  const fields=(row.academic_field_tags||[]).slice(0,10).map(x=>`<span class="detail-chip">${safe(x)}</span>`).join('');
  const factHtml=facts(row).map(([k,v])=>`<div><span>${safe(k)}</span><strong>${safe(v)}</strong></div>`).join('');
  const summary=row.feature_summary||row.philosophy||'特色情報は一次情報を確認しながら順次追加しています。';
  dialog.innerHTML=`<div class="detail-shell"><button class="detail-close" type="button" aria-label="閉じる">×</button>${visual(row)}<div class="detail-content"><div class="detail-title-row"><div><span class="detail-eyebrow">${safe(themeLabel(row))}</span><h2>${safe(row.name)}</h2><p>${safe(typeLabel[row.establishment_type]||'')} · 東京都 ${safe(municipality(row))}</p></div><button class="detail-favorite-proxy" type="button" data-detail-favorite="${safe(row.id)}">♡ お気に入り</button></div><p class="detail-lead">${safe(summary)}</p>${fields?`<div class="detail-chip-row">${fields}</div>`:''}<div class="detail-facts">${factHtml}</div><section class="detail-section"><div class="detail-section-head"><span>ACADEMICS</span><h3>学部・学科・研究科</h3></div><div class="detail-units">${renderUnits(row)}</div></section><div class="detail-actions">${row.admissions_url?`<a class="detail-primary" href="${safe(row.admissions_url)}" target="_blank" rel="noopener">入試・願書情報を見る ↗</a>`:''}${row.official_url?`<a href="${safe(row.official_url)}" target="_blank" rel="noopener">大学公式サイト ↗</a>`:''}<a href="${mapsUrl(row)}" target="_blank" rel="noopener">Google Maps ↗</a></div><p class="detail-note">掲載内容は大学公式・公的資料など一次情報を優先して確認しています。未確認項目は推測で補完しません。</p></div></div>`;
  dialog.querySelector('.detail-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();},{once:true});
  dialog.showModal();
}
function enhanceCards(){
  document.querySelectorAll('.tokyo-card').forEach(card=>{
    if(card.querySelector('.card-detail-open'))return;
    const actions=card.querySelector('.card-actions');if(!actions)return;
    const b=document.createElement('button');b.type='button';b.className='btn card-detail-open';b.dataset.detail=card.dataset.id;b.textContent='詳しく見る';
    actions.prepend(b);
  });
}
const observer=new MutationObserver(enhanceCards);observer.observe($('#tokyo-grid'),{childList:true,subtree:true});enhanceCards();
$('#tokyo-grid').addEventListener('click',e=>{const b=e.target.closest('[data-detail]');if(!b)return;e.preventDefault();openDetail(b.dataset.detail);});
})();
