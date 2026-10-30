// キャンパス所在地での絞り込み。都道府県を選んだとき「その県にキャンパスがある大学も含める」を切り替え、
// 本部が他県の大学には、その県のキャンパス名と所在地をカードに表示する。
(()=>{
if(typeof state==='undefined')return;
const INDEX_URL='../campuses/campus_index.json';
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const hqPref=row=>row.prefecture||row.headquarters?.prefecture||'東京都';
const extraCount=()=>state.pref==='all'?0:state.rows.filter(r=>hqPref(r)!==state.pref&&(state.campusIdx.get(r.id)?.prefectures||[]).includes(state.pref)).length;

function makeToggle(cls){
  const label=document.createElement('label');
  label.className=`campus-toggle ${cls}`;
  label.innerHTML='<input type="checkbox"><span class="campus-toggle-text">キャンパスがある大学も含める</span><small class="campus-toggle-count"></small>';
  const box=label.querySelector('input');
  box.checked=state.withCampus;
  box.addEventListener('change',()=>{state.withCampus=box.checked;if(typeof render==='function')render();sync();});
  return label;
}
const toggles=[];
function place(){
  const listGroup=document.querySelector('#pref-filters')?.closest('.filter-group');
  if(listGroup&&!listGroup.querySelector('.campus-toggle')){const t=makeToggle('campus-toggle-list');listGroup.appendChild(t);toggles.push(t);}
  const quick=document.querySelector('.ref-pref-filter');
  if(quick&&!quick.querySelector('.campus-toggle')){const t=makeToggle('campus-toggle-quick');quick.appendChild(t);toggles.push(t);}
}
function sync(){
  const n=extraCount();
  for(const t of toggles){
    t.querySelector('input').checked=state.withCampus;
    t.hidden=state.pref==='all';
    const label=state.pref==='all'?'':`${state.pref}にキャンパスがある大学も含める`;
    t.querySelector('.campus-toggle-text').textContent=label;
    t.querySelector('.campus-toggle-count').textContent=n?`（本部が他県の大学 ＋${n}校）`:'';
  }
}
function decorate(){
  for(const card of document.querySelectorAll('.tokyo-card[data-id]')){
    card.querySelector('.campus-badge')?.remove();
    if(state.pref==='all')continue;
    const row=state.rows.find(r=>r.id===card.dataset.id);
    if(!row||hqPref(row)===state.pref)continue;
    const cs=(state.campusIdx.get(row.id)?.campuses||[]).filter(c=>c.prefecture===state.pref);
    if(!cs.length)continue;
    const text=cs.map(c=>`${c.name||'キャンパス'}（${c.municipality||''}）`).join('・');
    const badge=document.createElement('div');
    badge.className='campus-badge';
    badge.innerHTML=`<span>📍 ${esc(state.pref)}で学べる</span>${esc(text)}<small>本部：${esc(hqPref(row))}</small>`;
    (card.querySelector('h3')||card.firstElementChild)?.insertAdjacentElement('afterend',badge);
  }
}
fetch(INDEX_URL).then(r=>r.ok?r.json():null).then(doc=>{
  if(!doc)return;
  state.campusIdx=new Map(Object.entries(doc.universities||{}));
  const wait=()=>{if(!state.rows.length||!document.querySelector('.ref-pref-filter')){setTimeout(wait,100);return;}place();sync();if(typeof render==='function')render();};
  wait();
}).catch(err=>console.error('campus index load failed',err));
document.addEventListener('click',e=>{if(e.target.closest('[data-pref],[data-ref-pref],#clear-filters'))setTimeout(()=>{if(e.target.closest('#clear-filters')){state.withCampus=false;if(typeof render==='function')render();}sync();decorate();},0)});
const grid=document.querySelector('#tokyo-grid');
if(grid)new MutationObserver(()=>decorate()).observe(grid,{childList:true});
})();
