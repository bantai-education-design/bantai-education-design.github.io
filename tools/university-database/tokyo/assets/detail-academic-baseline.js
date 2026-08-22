(()=>{
const id=new URLSearchParams(location.search).get('id');
const root=document.querySelector('#detail-root');
if(!id||!root)return;
const LOCATION_SHARDS=Array.from({length:6},(_,i)=>`data/tokyo_locations_${String(i+1).padStart(2,'0')}.json`);
const ADMISSION_SHARDS=Array.from({length:6},(_,i)=>`data/tokyo_admissions_${String(i+1).padStart(2,'0')}.json`);
const esc=(v='')=>String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const summary=(items,label,max=8)=>{const names=(items||[]).map(x=>x.name).filter(Boolean);return names.length?`${label} ${names.length}：${names.slice(0,max).join('、')}${names.length>max?`、ほか${names.length-max}`:''}`:`${label}：該当なし`};
const listHtml=(items,empty)=>items.length?`<ul class="detail-list">${items.map(x=>`<li>${esc(x.name)}</li>`).join('')}</ul>`:`<p class="detail-empty">${esc(empty)}</p>`;
function setStat(label,value){for(const box of root.querySelectorAll('.detail-stat')){if(box.querySelector('small')?.textContent?.trim()===label){const strong=box.querySelector('strong');if(strong)strong.textContent=value;}}}
function setFact(label,value){for(const box of root.querySelectorAll('.detail-fact')){if(box.querySelector('dt')?.textContent?.trim()===label){const dd=box.querySelector('dd');if(dd)dd.textContent=value;return true;}}return false}
function setAcademicColumn(label,items,empty){for(const h3 of root.querySelectorAll('.detail-academic h3')){if(h3.textContent?.trim()!==label)continue;const wrap=h3.parentElement;if(!wrap)continue;[...wrap.children].filter(x=>x!==h3).forEach(x=>x.remove());wrap.insertAdjacentHTML('beforeend',listHtml(items,empty));return true;}return false}
async function loadLocations(){
  const shards=await Promise.all(LOCATION_SHARDS.map(async file=>{
    const response=await fetch(file);
    if(!response.ok)throw new Error(`location shard missing: ${file}`);
    const rows=await response.json();
    if(!Array.isArray(rows)||rows.length!==24)throw new Error(`location shard count invalid: ${file}`);
    return rows;
  }));
  const locations=shards.flat();
  if(locations.length!==144||new Set(locations.map(x=>x.id)).size!==144)throw new Error('location overlay count invalid');
  return locations;
}
async function loadAdmissions(){
  const shards=await Promise.all(ADMISSION_SHARDS.map(async file=>{
    const response=await fetch(file);
    if(!response.ok)throw new Error(`admissions shard missing: ${file}`);
    const rows=await response.json();
    if(!Array.isArray(rows)||rows.length!==24)throw new Error(`admissions shard count invalid: ${file}`);
    return rows;
  }));
  const admissions=shards.flat();
  if(admissions.length!==144||new Set(admissions.map(x=>x.id)).size!==144)throw new Error('admissions overlay count invalid');
  for(const row of admissions){
    if(!row?.id||!row?.name||row.verification_status!=='verified')throw new Error(`admissions record invalid: ${row?.id||'unknown'}`);
    if(row.admissions_status!=='stopped'&&!/^https:\/\//.test(row.admissions_url||''))throw new Error(`admissions URL missing: ${row.id}`);
  }
  return admissions;
}
function applyLocation(loc){
  if(!loc?.municipality||!loc?.headquarters?.address||!/^\d{3}-\d{4}$/.test(loc?.headquarters?.postal_code||'')||!root.querySelector('.detail-hero'))return false;
  const address=loc.headquarters.address;
  const postal=loc.headquarters.postal_code;
  const display=`〒${postal} ${address}`;
  if(!setFact('所在地',display)){
    const facts=root.querySelector('.detail-core .detail-facts');
    if(facts)facts.insertAdjacentHTML('afterbegin',`<div class="detail-fact"><dt>所在地</dt><dd>${esc(display)}</dd></div>`);
  }
  for(const pill of root.querySelectorAll('.detail-meta .detail-pill')){
    if(/^東京都(?:\s|$)/.test(pill.textContent?.trim()||'')){pill.textContent=`東京都 ${loc.municipality}`;break;}
  }
  const map=`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${loc.name} ${address}`)}`;
  for(const link of root.querySelectorAll('a[href*="google.com/maps/search"]')){
    if(link.closest('.complete-card'))continue;
    link.href=map;
  }
  root.dataset.locationOverlay='ready';
  return true;
}
function upsertLink(container,matchLabels,url,label,cls='secondary'){
  if(!container||!url)return;
  const existing=[...container.querySelectorAll('a')].find(a=>matchLabels.some(text=>(a.textContent||'').includes(text)));
  if(existing){existing.href=url;existing.target='_blank';existing.rel='noopener';return;}
  const a=document.createElement('a');a.className=cls;a.href=url;a.target='_blank';a.rel='noopener';a.textContent=`${label} ↗`;container.appendChild(a);
}
function applyAdmissions(adm){
  if(!root.querySelector('.detail-hero'))return false;
  const stopped=adm.admissions_status==='stopped';
  for(const pill of root.querySelectorAll('.detail-meta .detail-pill')){
    const text=pill.textContent?.trim()||'';
    if(text==='募集継続'||text==='募集停止'){pill.textContent=stopped?'募集停止':'募集継続';break;}
  }
  for(const container of root.querySelectorAll('.detail-actions,.detail-link-stack')){
    if(adm.admissions_url)upsertLink(container,['入試情報','入試・願書情報','入試公式'],adm.admissions_url,'入試情報');
    if(adm.application_guidelines_url)upsertLink(container,['募集要項','選抜要項'],adm.application_guidelines_url,'募集要項');
    if(adm.brochure_request_url)upsertLink(container,['資料請求'],adm.brochure_request_url,'資料請求');
    if(adm.open_campus_url)upsertLink(container,['オープンキャンパス'],adm.open_campus_url,'オープンキャンパス');
  }
  root.dataset.admissionsOverlay='ready';
  return true;
}
function apply(u){
  const faculties=u.faculties||[];
  const units=faculties.flatMap(f=>(f.units||[]).map(x=>({...x,faculty_name:f.name})));
  const grads=u.graduate_schools||[];
  const graduateOnly=!faculties.length&&grads.length>0;
  if(!root.querySelector('.detail-hero')||!root.querySelector('.detail-core'))return false;
  setStat('学部',graduateOnly?'該当なし':String(faculties.length));
  setStat('学科等',graduateOnly?'該当なし':String(units.length));
  setStat('研究科',grads.length?String(grads.length):'—');
  setFact('学部',graduateOnly?'学部を置かない大学院大学です。':summary(faculties,'学部'));
  setFact('学科・課程等',graduateOnly?'学部・学科は該当しません。':summary(units,'学科等'));
  setFact('研究科',grads.length?summary(grads,'研究科'):'研究科：該当なし／確認済み情報なし');
  setAcademicColumn('学部',faculties,graduateOnly?'学部を置かない大学院大学です。':'確認済み学部情報はありません。');
  setAcademicColumn('学科・課程等',units,graduateOnly?'学部・学科は該当しません。':'確認済み学科・課程情報はありません。');
  setAcademicColumn('研究科',grads,'確認済み研究科情報はありません。');
  root.dataset.academicBaseline='ready';
  return true;
}
(async()=>{
  try{
    const locations=await loadLocations();
    const target=locations.find(x=>x.id===id);
    if(!target)throw new Error(`location missing for ${id}`);
    if(applyLocation(target))return;
    const observer=new MutationObserver(()=>{if(applyLocation(target))observer.disconnect();});
    observer.observe(root,{childList:true,subtree:true});
    setTimeout(()=>observer.disconnect(),8000);
  }catch(err){console.error('Detail location overlay failed',err);root.dataset.locationOverlay='error';}
})();
(async()=>{
  try{
    const admissions=await loadAdmissions();
    const target=admissions.find(x=>x.id===id);
    if(!target)throw new Error(`admissions missing for ${id}`);
    const attempt=()=>applyAdmissions(target);
    if(attempt()){
      setTimeout(()=>attempt(),500);
      return;
    }
    const observer=new MutationObserver(()=>{if(attempt()){observer.disconnect();setTimeout(()=>attempt(),500);}});
    observer.observe(root,{childList:true,subtree:true});
    setTimeout(()=>observer.disconnect(),8000);
  }catch(err){console.error('Detail admissions overlay failed',err);root.dataset.admissionsOverlay='error';}
})();
(async()=>{
  try{
    const complete=await fetch(`data/complete/${encodeURIComponent(id)}.json`);
    if(complete.ok)return;
    const mr=await fetch('data/public-academic-baseline/manifest.json');
    if(!mr.ok)return;
    const manifest=await mr.json();
    const docs=await Promise.all((manifest.shards||[]).map(async file=>{const r=await fetch(`data/public-academic-baseline/${file}`);return r.ok?r.json():null;}));
    let target=null;
    for(const doc of docs){target=(doc?.universities||[]).find(x=>x.university_id===id);if(target)break;}
    if(!target)return;
    if(apply(target))return;
    const observer=new MutationObserver(()=>{if(apply(target))observer.disconnect();});
    observer.observe(root,{childList:true,subtree:true});
    setTimeout(()=>observer.disconnect(),8000);
  }catch(err){console.error('Detail academic baseline overlay failed',err);}
})();
})();
