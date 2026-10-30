// 検索欄の設置区分（国立・公立・私立）選択。一覧の #type-filters と常に同じ状態を保つ。
(()=>{
const TYPES=[['all','すべて'],['national','国立'],['public','公立'],['private','私立']];
const form=document.querySelector('.ref-quick-form');
const listFilters=document.querySelector('#type-filters');
if(!form||!listFilters||typeof state==='undefined')return;

const group=document.createElement('div');
group.className='ref-type-filter';
group.setAttribute('role','group');
group.setAttribute('aria-label','設置区分で絞り込む');
group.innerHTML='<span class="ref-type-label">設置区分</span>'+TYPES.map(([value,label])=>`<button type="button" class="ref-type-chip" data-ref-type="${value}" aria-pressed="false">${label}</button>`).join('');
form.insertAdjacentElement('afterend',group);

const sync=()=>{for(const b of group.querySelectorAll('[data-ref-type]')){const on=b.dataset.refType===state.type;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));}};
const applyType=value=>{state.type=value;if(typeof activate==='function')activate(listFilters,'type',value);if(typeof render==='function')render();sync();};

group.addEventListener('click',e=>{const b=e.target.closest('[data-ref-type]');if(b)applyType(b.dataset.refType);});
listFilters.addEventListener('click',()=>setTimeout(sync,0));
document.querySelector('#clear-filters')?.addEventListener('click',()=>setTimeout(sync,0));

// 検索ボタンを押したときも、選んだ区分のまま一覧へ移動する
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
