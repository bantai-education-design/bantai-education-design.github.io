// 最寄り駅。公式アクセスページで確認した駅（access.json）をカードに表示し、駅名でも検索できるようにする。
(()=>{
if(typeof state==='undefined')return;
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
function decorate(){
  for(const card of document.querySelectorAll('.tokyo-card[data-id]')){
    if(card.querySelector('.access-line'))continue;
    const a=state.accessIdx.get(card.dataset.id);
    if(!a||!a.stations?.length)continue;
    const s=a.stations.slice(0,2);
    const box=document.createElement('div');
    box.className='access-line';
    box.innerHTML=`<span class="access-label">最寄り駅</span>${s.map(x=>`<span class="access-station" title="${esc(x.line||'')}"><b>${esc(x.station)}</b>${x.access?` ${esc(x.access)}`:''}</span>`).join('')}${a.school_bus?'<span class="access-bus">スクールバスあり</span>':''}`;
    const anchor=card.querySelector('.campus-badge')||card.querySelector('.finished-fields')||card.querySelector('h3');
    anchor?.insertAdjacentElement('afterend',box);
  }
}
fetch('../access/access.json').then(r=>r.ok?r.json():null).then(d=>{
  if(!d)return;
  state.accessIdx=new Map(Object.entries(d.universities||{}));
  const wait=()=>{if(!state.rows.length){setTimeout(wait,100);return;}if(typeof render==='function')render();decorate();};
  wait();
}).catch(err=>console.error('access index load failed',err));
const grid=document.querySelector('#tokyo-grid');
if(grid)new MutationObserver(()=>decorate()).observe(grid,{childList:true});
})();
