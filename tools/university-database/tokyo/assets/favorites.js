(()=>{
const KEY='bantai:university-db:tokyo:favorites:v1';
let favorites=new Set();
try{favorites=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'));}catch{}
const save=()=>localStorage.setItem(KEY,JSON.stringify([...favorites]));
const label=(name,on)=>`${name}を${on?'お気に入りから外す':'お気に入りに追加'}`;
function syncHeader(){const b=document.querySelector('.header-fav');if(!b)return;const compact=matchMedia('(max-width:620px)').matches;b.innerHTML=compact?`♥ <span class="fav-count">${favorites.size}</span>`:`♥ お気に入り <span class="fav-count">${favorites.size}</span>`;b.setAttribute('aria-label',`お気に入り大学 ${favorites.size}校`);b.title=`お気に入り大学 ${favorites.size}校`;b.onclick=()=>{document.querySelector('#search')?.scrollIntoView({behavior:'smooth'});document.body.classList.toggle('show-favorites-only');decorate();};}
function decorate(){document.querySelectorAll('.tokyo-card[data-id]').forEach(card=>{const id=card.dataset.id;const name=card.querySelector('h3')?.textContent?.trim()||'大学';const on=favorites.has(id);let b=card.querySelector('.favorite-toggle');if(!b){b=document.createElement('button');b.type='button';b.className='favorite-toggle';b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();favorites.has(id)?favorites.delete(id):favorites.add(id);save();syncHeader();decorate();});card.querySelector('.card-visual')?.appendChild(b);}b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on));b.setAttribute('aria-label',label(name,on));b.title=label(name,on);b.textContent=on?'♥':'♡';card.classList.toggle('is-favorite',on);card.hidden=document.body.classList.contains('show-favorites-only')&&!on;});}
const grid=document.querySelector('#tokyo-grid');if(grid)new MutationObserver(decorate).observe(grid,{childList:true});syncHeader();decorate();

// Long-list navigation: show a floating control only after the user has scrolled.
const oldBack=document.querySelector('.database-hub-back');
if(oldBack)oldBack.remove();
let topButton=document.querySelector('.scroll-top-button');
if(!topButton){
  topButton=document.createElement('button');
  topButton.type='button';
  topButton.className='scroll-top-button';
  topButton.setAttribute('aria-label','ページ上部へ戻る');
  topButton.title='ページ上部へ戻る';
  topButton.innerHTML='<span aria-hidden="true">↑</span><small>上へ</small>';
  topButton.style.cssText='position:fixed;right:22px;bottom:22px;z-index:60;display:flex;align-items:center;gap:7px;padding:10px 14px;border:1px solid rgba(255,255,255,.7);border-radius:999px;background:#082844;color:#fff;font-weight:900;box-shadow:0 8px 24px rgba(6,27,46,.28);cursor:pointer;opacity:0;visibility:hidden;transform:translateY(8px);transition:opacity .18s ease,transform .18s ease,visibility .18s ease';
  topButton.querySelector('span').style.cssText='font-size:1.15rem;line-height:1';
  topButton.querySelector('small').style.cssText='font-size:.72rem';
  topButton.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
  document.body.appendChild(topButton);
}
const syncTopButton=()=>{
  const show=window.scrollY>520;
  topButton.style.opacity=show?'1':'0';
  topButton.style.visibility=show?'visible':'hidden';
  topButton.style.transform=show?'translateY(0)':'translateY(8px)';
};
window.addEventListener('scroll',syncTopButton,{passive:true});
syncTopButton();
if(matchMedia('(max-width:620px)').matches){topButton.style.right='12px';topButton.style.bottom='14px';topButton.style.padding='9px 11px';topButton.querySelector('small').style.display='none';}

const heroLead=document.querySelector('.hero-copy p');
if(heroLead)heroLead.innerHTML='東京都144大学を、学びたいこと・地域・設置区分・大学の特色から探せるデータベースです。<br>大学公式情報や公的資料を優先し、比較しやすい形に整理しています。';
const notice=document.querySelector('.ref-notice');
if(notice)notice.innerHTML='ⓘ <strong>現在開発・更新中です。</strong> 学部・学科・所在地・地図リンクを再確認しています。出願・入試の最新情報は各大学の公式情報もご確認ください。';

// Apply the authoritative compact academic baseline for the 66 universities
// that were under-covered in the public snapshot. This layer replaces, rather
// than appends to, the old per-university arrays so faculty/unit counts cannot
// be duplicated by legacy snapshots.
(async()=>{
  try{
    const manifestResponse=await fetch('data/public-academic-baseline/manifest.json');
    if(!manifestResponse.ok)return;
    const manifest=await manifestResponse.json();
    if(manifest.schema!=='tokyo-academic-public-baseline-v2'||!Array.isArray(manifest.shards))return;
    const docs=await Promise.all(manifest.shards.map(async file=>{
      const r=await fetch(`data/public-academic-baseline/${file}`);
      return r.ok?r.json():null;
    }));
    for(const doc of docs){
      if(!doc||doc.kind!=='academic_summary')continue;
      for(const u of doc.universities||[]){
        const uid=u.university_id;
        if(!uid)continue;
        const faculties=[];
        const departments=[];
        const graduateSchools=[];
        (u.faculties||[]).forEach((f,fi)=>{
          const fid=`baseline-${uid}-f${fi}`;
          faculties.push({id:fid,university_id:uid,name:f.name,organization_type:'faculty'});
          (f.units||[]).forEach((d,di)=>departments.push({id:`baseline-${uid}-d${fi}-${di}`,university_id:uid,faculty_id:fid,name:d.name,department_type:d.type||'department'}));
        });
        (u.graduate_schools||[]).forEach((g,gi)=>graduateSchools.push({id:`baseline-${uid}-g${gi}`,university_id:uid,name:g.name,organization_type:'graduate_school'}));
        state.faculties.set(uid,faculties);
        state.departments.set(uid,departments);
        state.graduateSchools.set(uid,graduateSchools);
      }
    }
    if(typeof render==='function')render();
    document.documentElement.dataset.academicBaseline='ready';
  }catch(err){
    console.error('Academic baseline overlay failed',err);
  }
})();

// Finished card layer: one common quality standard for all 144 universities.
const cardCss=document.createElement('link');cardCss.rel='stylesheet';cardCss.href='assets/card-finish.css';document.head.appendChild(cardCss);
const cardScript=document.createElement('script');cardScript.src='assets/card-finish.js';cardScript.defer=true;document.head.appendChild(cardScript);
})();