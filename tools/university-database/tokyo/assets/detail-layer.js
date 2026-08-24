(()=>{
const ADMISSION_SHARDS=Array.from({length:6},(_,i)=>`data/tokyo_admissions_${String(i+1).padStart(2,'0')}.json`);
const safe=v=>esc(v??'');
let detailReturnFocus=null;
async function loadCanonicalAdmissions(){
  const shards=await Promise.all(ADMISSION_SHARDS.map(async file=>{
    const response=await fetch(file);
    if(!response.ok)throw new Error(`admissions shard missing: ${file}`);
    const rows=await response.json();
    if(!Array.isArray(rows)||rows.length!==24)throw new Error(`admissions shard count invalid: ${file}`);
    return rows;
  }));
  const rows=shards.flat();
  if(rows.length!==144||new Set(rows.map(x=>x.id)).size!==144)throw new Error('admissions overlay count invalid');
  for(const row of rows){
    if(!row?.id||!row?.name||row.verification_status!=='verified')throw new Error(`admissions record invalid: ${row?.id||'unknown'}`);
    if(row.admissions_status!=='stopped'&&!/^https:\/\//.test(row.admissions_url||''))throw new Error(`admissions URL missing: ${row.id}`);
  }
  return new Map(rows.map(row=>[row.id,row]));
}
async function applyCanonicalAdmissions(){
  try{
    const byId=await loadCanonicalAdmissions();
    const waitForRows=()=>{
      if(!state.rows.length){setTimeout(waitForRows,50);return;}
      const apply=()=>{
        state.rows=state.rows.map(row=>byId.has(row.id)?{...row,...byId.get(row.id)}:row);
        const covered=state.rows.filter(row=>row.admissions_url||row.admissions_status==='stopped').length;
        if(covered!==144)throw new Error(`admissions coverage ${covered}/144`);
        const quality=document.querySelector('#quality-admissions');
        if(quality)quality.textContent='144/144';
        updateCompare();
        render();
      };
      apply();
      setTimeout(()=>{
        try{apply();document.documentElement.dataset.admissionsOverlay='ready';}
        catch(err){console.error('Tokyo canonical admissions reapply failed',err);document.documentElement.dataset.admissionsOverlay='error';}
      },500);
    };
    waitForRows();
  }catch(err){console.error('Tokyo canonical admissions overlay failed',err);document.documentElement.dataset.admissionsOverlay='error';}
}
function themeLabel(row){const text=[...(row.academic_field_tags||[]),...(state.faculties.get(row.id)||[]).map(x=>x.name),row.name].join(' ');if(/情報|AI|データ|工学|理工/.test(text))return'TECH & AI';if(/医|看護|薬|生命|保健/.test(text))return'LIFE & HEALTH';if(/芸術|美術|音楽|デザイン/.test(text))return'ART & CREATE';if(/国際|外国語|語学|文化/.test(text))return'GLOBAL';if(/教育|児童|こども|保育/.test(text))return'EDUCATION';if(/体育|スポーツ|武道/.test(text))return'SPORTS';if(/理学|農学|環境|数理/.test(text))return'SCIENCE';return'UNIVERSITY PROFILE';}
function detailVerifiedImage(row){const item=window.__universityOwnerPhotos?.get(row.id)||state.images?.get(row.id);if(item?.image_url){if(item.rights_status==='verified'&&item.source_url&&item.rights_note)return item;if(item.rights_status==='ai_original'&&item.generation_note&&item.label)return item;}return verifiedImage(row);}
function visual(row){const image=detailVerifiedImage(row);if(image){const ai=image.rights_status==='ai_original';return`<div class="detail-visual has-image"><img src="${safe(image.image_url)}" alt="${safe(image.alt||`${row.name}の大学紹介イメージ`)}"><span>${ai?safe(image.label||'イメージ画像（AI生成）'):'大学紹介画像'}</span></div>`;}return`<div class="detail-visual themed"><span class="detail-theme-kicker">${safe(themeLabel(row))}</span><strong>${safe(row.name)}</strong><small>学問分野と大学情報をもとにした案内ビジュアル</small></div>`;}
function units(row){const f=state.faculties.get(row.id)||[],d=state.departments.get(row.id)||[],g=state.graduateSchools.get(row.id)||[];if(!f.length&&!g.length)return'<p class="detail-empty">学部・研究科情報は確認・同期中です。</p>';return f.slice(0,12).map(x=>{const deps=d.filter(y=>y.faculty_id===x.id).slice(0,8);return`<div class="detail-unit"><strong>${safe(x.name)}</strong>${deps.length?`<div>${deps.map(y=>`<span>${safe(y.name)}</span>`).join('')}</div>`:''}</div>`;}).join('')+g.slice(0,8).map(x=>`<div class="detail-unit"><strong>${safe(x.name)}</strong>${(x.programs||[]).length?`<div>${x.programs.slice(0,6).map(y=>`<span>${safe(y)}</span>`).join('')}</div>`:''}</div>`).join('');}
function closeDetail(dialog){if(dialog?.open)dialog.close();}
function openDetail(id,trigger){const row=state.rows.find(r=>r.id===id);if(!row)return;detailReturnFocus=trigger||document.activeElement;let dialog=document.querySelector('#university-detail-dialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='university-detail-dialog';dialog.className='university-detail-dialog';dialog.setAttribute('aria-modal','true');document.body.appendChild(dialog);dialog.addEventListener('close',()=>{if(detailReturnFocus&&typeof detailReturnFocus.focus==='function'&&document.contains(detailReturnFocus))detailReturnFocus.focus();detailReturnFocus=null;});dialog.addEventListener('click',e=>{if(e.target===dialog)closeDetail(dialog);});}
const f=state.faculties.get(row.id)||[],d=state.departments.get(row.id)||[],g=state.graduateSchools.get(row.id)||[];const facts=[['設置区分',typeLabel[row.establishment_type]||'—'],['所在地',`東京都 ${municipality(row)}`],['在籍者数',formatStudents(row)],['学部',f.length?`${f.length}学部`:'—'],['学科',d.length?`${d.length}学科`:'—'],['研究科',g.length?`${g.length}研究科`:'—']];const fields=(row.academic_field_tags||[]).slice(0,10).map(x=>`<span class="detail-chip">${safe(x)}</span>`).join('');const summary=row.feature_summary||row.philosophy||'特色情報は一次情報を確認しながら順次追加しています。';const titleId=`detail-title-${safe(row.id)}`;dialog.setAttribute('aria-labelledby',titleId);dialog.innerHTML=`<div class="detail-shell"><button class="detail-close" type="button" aria-label="詳細画面を閉じる">×</button>${visual(row)}<div class="detail-content"><span class="detail-eyebrow">${safe(themeLabel(row))}</span><h2 id="${titleId}">${safe(row.name)}</h2><p class="detail-meta">${safe(typeLabel[row.establishment_type]||'')} · 東京都 ${safe(municipality(row))}</p><p class="detail-lead">${safe(summary)}</p>${fields?`<div class="detail-chip-row">${fields}</div>`:''}<div class="detail-facts">${facts.map(([k,v])=>`<div><span>${safe(k)}</span><strong>${safe(v)}</strong></div>`).join('')}</div><section class="detail-section"><div class="detail-section-head"><span>ACADEMICS</span><h3>学部・学科・研究科</h3></div><div class="detail-units">${units(row)}</div></section><div class="detail-actions">${row.admissions_url?`<a class="detail-primary" href="${safe(row.admissions_url)}" target="_blank" rel="noopener">入試・願書情報を見る ↗</a>`:''}${row.official_url?`<a href="${safe(row.official_url)}" target="_blank" rel="noopener">大学公式サイト ↗</a>`:''}<a href="${mapsUrl(row)}" target="_blank" rel="noopener">Google Maps ↗</a></div><p class="detail-note">掲載内容は大学公式・公的資料など一次情報を優先して確認しています。未確認項目は推測で補完しません。</p></div></div>`;dialog.querySelector('.detail-close').onclick=()=>closeDetail(dialog);dialog.showModal();requestAnimationFrame(()=>dialog.querySelector('.detail-close')?.focus());}
function enhance(){document.querySelectorAll('.tokyo-card').forEach(card=>{if(card.querySelector('.card-detail-open'))return;const actions=card.querySelector('.card-actions');if(!actions)return;const b=document.createElement('button');b.type='button';b.className='btn card-detail-open';b.dataset.detail=card.dataset.id;b.textContent='詳しく見る';b.setAttribute('aria-label',`${card.querySelector('h3')?.textContent||'大学'}の詳細を見る`);actions.prepend(b);});}
const grid=document.querySelector('#tokyo-grid');new MutationObserver(enhance).observe(grid,{childList:true,subtree:true});enhance();grid.addEventListener('click',e=>{const b=e.target.closest('[data-detail]');if(!b)return;e.preventDefault();openDetail(b.dataset.detail,b);});
applyCanonicalAdmissions();
})();
