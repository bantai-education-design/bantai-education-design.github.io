// 収録件数・品質表示を、読み込んだ全地域（東京都・埼玉県・神奈川県の先行掲載分）の実データから表示する。
(()=>{
if(typeof state==='undefined')return;
const PREFS=['東京都','埼玉県','神奈川県'];
const NOTES={'神奈川県':'神奈川県版は準備中（本部が神奈川県の大学を先行掲載）'};
const byPref=p=>state.rows.filter(r=>(r.prefecture||r.headquarters?.prefecture||'東京都')===p);
const count=(rows,t)=>rows.filter(r=>r.establishment_type===t).length;
const label=()=>PREFS.filter(p=>byPref(p).length&&!NOTES[p]).join('・');
function apply(){
  const rows=state.rows;if(!rows.length)return false;
  const total=rows.length;const areas=label();
  const h3=[...document.querySelectorAll('.ref-panel h3')].find(h=>h.textContent.startsWith('収録エリア'));
  if(h3)h3.textContent=`収録エリア：${areas}`;
  const list=document.querySelector('.ref-area-list');
  if(list)list.innerHTML=PREFS.map(p=>{const r=byPref(p);return r.length?`<span>📍 ${p} <b>${r.length}</b><small>${NOTES[p]||`国立${count(r,'national')}・公立${count(r,'public')}・私立${count(r,'private')}`}</small></span>`:''}).join('');
  const tot=document.querySelector('.ref-area-total strong');if(tot)tot.textContent=String(total);
  const set=(sel,v)=>{const el=document.querySelector(sel);if(el)el.textContent=v};
  set('#quality-official',`${rows.filter(r=>r.official_url).length}/${total}`);
  set('#quality-location',`${rows.filter(r=>r.municipality||r.headquarters?.municipality).length}/${total}`);
  set('#quality-address',`本部所在地を確認 ${rows.filter(r=>r.headquarters?.address).length}/${total}校。`);
  set('#quality-admissions',`${rows.filter(r=>r.admissions_url||r.admissions_status==='stopped').length}/${total}`);
  const fourth=[...document.querySelectorAll('.trust-item strong')].find(s=>/公開完成|学部・学科/.test(s.textContent));
  if(fourth){const b=fourth.querySelector('b');if(b)b.textContent=`${total}/${total}`}
  const extra=PREFS.some(p=>NOTES[p]&&byPref(p).length);const lead=extra?`${areas}を中心に${total}大学`:`${areas}の${total}大学`;
  const hero=document.querySelector('.hero-copy p');if(hero)hero.innerHTML=`${lead}を、学びたいこと・地域・設置区分・大学の特色から探せるデータベースです。<br>大学公式情報や公的資料を優先し、比較しやすい形に整理しています。`;
  const notice=document.querySelector('.ref-notice');if(notice&&/公開中/.test(notice.textContent))notice.innerHTML=`ⓘ ${lead}を公開中です。大学情報は更新される場合があります。出願・入試の最新情報は各大学の公式情報もご確認ください。`;
  const foot=document.querySelector('.footer-inner span');if(foot)foot.textContent=`${lead} · 全国大学データベース`;
  document.title=`${lead} | Ban.Tai 全国大学データベース`;
  return true;
}
let tries=0;const t=setInterval(()=>{if(apply()||++tries>200)clearInterval(t)},150);
// 後から読み込まれる補正レイヤーで数値が上書きされても、最新の行数で表示し直す
const grid=document.querySelector('#tokyo-grid');
if(grid)new MutationObserver(()=>apply()).observe(grid,{childList:true});
})();
