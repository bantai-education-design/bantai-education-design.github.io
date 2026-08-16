(()=>{
const KEY='bantai:university-db:tokyo:favorites:v1';
let favorites=new Set();
try{favorites=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'));}catch{}
const save=()=>localStorage.setItem(KEY,JSON.stringify([...favorites]));
const label=(name,on)=>`${name}を${on?'お気に入りから外す':'お気に入りに追加'}`;
function syncHeader(){const b=document.querySelector('.header-fav');if(!b)return;b.innerHTML=`♥ お気に入り <span class="fav-count">${favorites.size}</span>`;b.setAttribute('aria-label',`お気に入り大学 ${favorites.size}校`);b.onclick=()=>{document.querySelector('#search')?.scrollIntoView({behavior:'smooth'});document.body.classList.toggle('show-favorites-only');decorate();};}
function decorate(){document.querySelectorAll('.tokyo-card[data-id]').forEach(card=>{const id=card.dataset.id;const name=card.querySelector('h3')?.textContent?.trim()||'大学';const on=favorites.has(id);let b=card.querySelector('.favorite-toggle');if(!b){b=document.createElement('button');b.type='button';b.className='favorite-toggle';b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();favorites.has(id)?favorites.delete(id):favorites.add(id);save();syncHeader();decorate();});card.querySelector('.card-visual')?.appendChild(b);}b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.setAttribute('aria-label',label(name,on));b.title=label(name,on);b.textContent=on?'♥':'♡';card.classList.toggle('is-favorite',on);card.hidden=document.body.classList.contains('show-favorites-only')&&!on;});}
const grid=document.querySelector('#tokyo-grid');if(grid)new MutationObserver(decorate).observe(grid,{childList:true});syncHeader();decorate();
})();