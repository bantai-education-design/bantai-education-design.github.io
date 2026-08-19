(()=>{
const KEY='bantai:university-db:tokyo:favorites:v1';
let favorites=new Set();
try{favorites=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'));}catch{}
const save=()=>localStorage.setItem(KEY,JSON.stringify([...favorites]));
const label=(name,on)=>`${name}を${on?'お気に入りから外す':'お気に入りに追加'}`;
function syncHeader(){const b=document.querySelector('.header-fav');if(!b)return;b.innerHTML=`♥ お気に入り <span class="fav-count">${favorites.size}</span>`;b.setAttribute('aria-label',`お気に入り大学 ${favorites.size}校`);b.onclick=()=>{document.querySelector('#search')?.scrollIntoView({behavior:'smooth'});document.body.classList.toggle('show-favorites-only');decorate();};}
function decorate(){document.querySelectorAll('.tokyo-card[data-id]').forEach(card=>{const id=card.dataset.id;const name=card.querySelector('h3')?.textContent?.trim()||'大学';const on=favorites.has(id);let b=card.querySelector('.favorite-toggle');if(!b){b=document.createElement('button');b.type='button';b.className='favorite-toggle';b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();favorites.has(id)?favorites.delete(id):favorites.add(id);save();syncHeader();decorate();});card.querySelector('.card-visual')?.appendChild(b);}b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.setAttribute('aria-label',label(name,on));b.title=label(name,on);b.textContent=on?'♥':'♡';card.classList.toggle('is-favorite',on);card.hidden=document.body.classList.contains('show-favorites-only')&&!on;});}
const grid=document.querySelector('#tokyo-grid');if(grid)new MutationObserver(decorate).observe(grid,{childList:true});syncHeader();decorate();

const header=document.querySelector('.header-inner');
if(header&&!header.querySelector('.database-hub-back')){
  const back=document.createElement('a');
  back.className='database-hub-back';
  back.href='/databases/';
  back.textContent='← DB・情報検索へ戻る';
  back.setAttribute('aria-label','データベース・情報検索トップへ戻る');
  back.style.cssText='display:inline-flex;align-items:center;white-space:nowrap;padding:7px 12px;border:1px solid #c9d3dc;border-radius:999px;color:#082844;background:#fff;text-decoration:none;font-weight:800;font-size:.72rem;position:relative;z-index:5;margin-left:auto;margin-right:170px';
  const nav=header.querySelector('.nav-links');
  header.insertBefore(back,nav||header.firstChild);
  if(matchMedia('(max-width:620px)').matches)back.style.cssText+=';margin:0 8px 0 auto;padding:6px 9px;font-size:.66rem';
}

const heroLead=document.querySelector('.hero-copy p');
if(heroLead)heroLead.innerHTML='東京都144大学を、学びたいこと・地域・設置区分・大学の特色から探せるデータベースです。<br>大学公式情報や公的資料を優先し、比較しやすい形に整理しています。';
const notice=document.querySelector('.ref-notice');
if(notice)notice.textContent='ⓘ 東京都144大学を公開中です。大学情報は更新される場合があります。出願・入試の最新情報は各大学の公式情報もご確認ください。';
})();