// 検索欄の絞り込み（都道府県・設置区分）。一覧の #pref-filters / #type-filters と常に同じ状態を保つ。
(()=>{
const GROUPS=[
  {key:'pref',label:'都道府県',list:'#pref-filters',options:[['all','すべて'],['東京都','東京都'],['埼玉県','埼玉県'],['神奈川県','神奈川県']]},
  {key:'type',label:'設置区分',list:'#type-filters',options:[['all','すべて'],['national','国立'],['public','公立'],['private','私立']]},
];
const form=document.querySelector('.ref-quick-form');
if(!form||typeof state==='undefined')return;

let anchor=form;
const groups=[];
for(const g of GROUPS){
  const listFilters=document.querySelector(g.list);
  if(!listFilters)continue;
  const el=document.createElement('div');
  el.className=`ref-type-filter ref-${g.key}-filter`;
  el.setAttribute('role','group');
  el.setAttribute('aria-label',`${g.label}で絞り込む`);
  el.innerHTML=`<span class="ref-type-label">${g.label}</span>`+g.options.map(([value,label])=>`<button type="button" class="ref-type-chip" data-ref-${g.key}="${value}" aria-pressed="false">${label}</button>`).join('');
  anchor.insertAdjacentElement('afterend',el);
  anchor=el;
  groups.push({...g,el,listFilters});
}
const attr=key=>`ref${key[0].toUpperCase()}${key.slice(1)}`;
const sync=()=>{for(const g of groups)for(const b of g.el.querySelectorAll(`[data-ref-${g.key}]`)){const on=b.dataset[attr(g.key)]===(state[g.key]||'all');b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));}};
for(const g of groups){
  g.el.addEventListener('click',e=>{
    const b=e.target.closest(`[data-ref-${g.key}]`);if(!b)return;
    state[g.key]=b.dataset[attr(g.key)];
    if(typeof activate==='function')activate(g.listFilters,g.key,state[g.key]);
    if(typeof render==='function')render();
    sync();
  });
  g.listFilters.addEventListener('click',()=>setTimeout(sync,0));
}
document.querySelector('#clear-filters')?.addEventListener('click',()=>setTimeout(sync,0));

// 検索ボタンを押したときも、選んだ条件のまま一覧へ移動する
form.onsubmit=null;
form.removeAttribute('onsubmit');
form.addEventListener('submit',e=>{
  e.preventDefault();
  const q=form.elements.q.value;
  const input=document.querySelector('#tokyo-search-input');
  if(input)input.value=q;
  state.q=q;
  if(typeof render==='function')render();
  document.querySelector('#search')?.scrollIntoView({behavior:'smooth'});
});
sync();
})();
