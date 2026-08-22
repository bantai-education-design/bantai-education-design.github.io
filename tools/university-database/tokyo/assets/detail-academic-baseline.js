(()=>{
const id=new URLSearchParams(location.search).get('id');
const root=document.querySelector('#detail-root');
if(!id||!root)return;
const esc=(v='')=>String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const summary=(items,label,max=8)=>{const names=(items||[]).map(x=>x.name).filter(Boolean);return names.length?`${label} ${names.length}：${names.slice(0,max).join('、')}${names.length>max?`、ほか${names.length-max}`:''}`:`${label}：該当なし`};
const listHtml=(items,empty)=>items.length?`<ul class="detail-list">${items.map(x=>`<li>${esc(x.name)}</li>`).join('')}</ul>`:`<p class="detail-empty">${esc(empty)}</p>`;
function setStat(label,value){for(const box of root.querySelectorAll('.detail-stat')){if(box.querySelector('small')?.textContent?.trim()===label){const strong=box.querySelector('strong');if(strong)strong.textContent=value;}}}
function setFact(label,value){for(const box of root.querySelectorAll('.detail-fact')){if(box.querySelector('dt')?.textContent?.trim()===label){const dd=box.querySelector('dd');if(dd)dd.textContent=value;return true;}}return false}
function setAcademicColumn(label,items,empty){for(const h3 of root.querySelectorAll('.detail-academic h3')){if(h3.textContent?.trim()!==label)continue;const wrap=h3.parentElement;if(!wrap)continue;[...wrap.children].filter(x=>x!==h3).forEach(x=>x.remove());wrap.insertAdjacentHTML('beforeend',listHtml(items,empty));return true;}return false}
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