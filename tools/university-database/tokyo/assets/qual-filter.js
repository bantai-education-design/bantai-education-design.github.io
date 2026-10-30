// 取れる資格で探す。資格一覧（qualifications.json）を読み込み、絞り込みの選択欄とカードの「取れる資格」を表示する。
(()=>{
if(typeof state==='undefined')return;
const URL='../qualifications/qualifications.json';
const esc=v=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
let doc=null;
const short=n=>n.replace(/（.*?）/g,'').replace('一種免許状','').replace('二種免許状','（二種）');
function counts(){const c={};for(const r of state.rows)for(const g of new Set((state.qualIdx.get(r.id)||[]).map(x=>x.group).filter(Boolean)))c[g]=(c[g]||0)+1;return c;}
function makeSelect(id){
  const wrap=document.createElement('div');
  wrap.className='filter-group qual-filter-group';
  const c=counts();
  const opts=doc.groups.filter(g=>c[g]).map(g=>`<option value="${esc(g)}">${esc(g)}（${c[g]}校）</option>`).join('');
  wrap.innerHTML=`<label class="filter-label" for="${id}">取れる資格</label><select id="${id}" class="qual-select"><option value="">指定しない</option>${opts}</select>`;
  const sel=wrap.querySelector('select');
  sel.value=state.qual;
  sel.addEventListener('change',()=>{state.qual=sel.value;sync();if(typeof render==='function')render();});
  return wrap;
}
const selects=[];
function sync(){for(const s of selects)s.value=state.qual;}
function place(){
  const panel=document.querySelector('.filter-panel');
  const typeGroup=document.querySelector('#type-filters')?.closest('.filter-group');
  if(panel&&typeGroup&&!document.querySelector('#qual-select')){const w=makeSelect('qual-select');typeGroup.insertAdjacentElement('afterend',w);selects.push(w.querySelector('select'));}
  const quick=document.querySelector('.ref-type-filter.ref-type-filter:last-of-type')||document.querySelector('.ref-quick-form');
  if(quick&&!document.querySelector('#qual-select-quick')){const w=makeSelect('qual-select-quick');w.className='ref-type-filter qual-filter-quick';const lab=w.querySelector('label');lab.className='ref-type-label';quick.insertAdjacentElement('afterend',w);selects.push(w.querySelector('select'));}
}
function decorate(){
  for(const card of document.querySelectorAll('.tokyo-card[data-id]')){
    if(card.querySelector('.qual-chips'))continue;
    const items=state.qualIdx.get(card.dataset.id)||[];
    if(!items.length)continue;
    const sorted=[...items].sort((a,b)=>(b.group===state.qual)-(a.group===state.qual));
    const show=sorted.slice(0,4),rest=items.length-show.length;
    const box=document.createElement('div');
    box.className='qual-chips';
    box.innerHTML=`<span class="qual-chips-label">取れる資格</span>${show.map(x=>`<span class="qual-chip${x.group&&x.group===state.qual?' is-match':''}" title="${esc(x.name)}${x.department?`（${esc(x.department)}）`:''}">${esc(short(x.name))}</span>`).join('')}${rest>0?`<span class="qual-chip more">ほか${rest}</span>`:''}`;
    const anchor=card.querySelector('.finished-fields')||card.querySelector('.card-body h3')||card.querySelector('h3');
    anchor?.insertAdjacentElement('afterend',box);
  }
}
fetch(URL).then(r=>r.ok?r.json():null).then(d=>{
  if(!d)return;doc=d;
  state.qualIdx=new Map(Object.entries(d.universities||{}).map(([id,v])=>[id,v.qualifications||[]]));
  const wait=()=>{if(!state.rows.length||!document.querySelector('#type-filters')){setTimeout(wait,100);return;}place();sync();if(typeof render==='function')render();};
  wait();
}).catch(err=>console.error('qualification index load failed',err));
document.querySelector('#clear-filters')?.addEventListener('click',()=>setTimeout(()=>{state.qual='';sync();if(typeof render==='function')render();},0));
const grid=document.querySelector('#tokyo-grid');
if(grid)new MutationObserver(()=>decorate()).observe(grid,{childList:true});
})();
