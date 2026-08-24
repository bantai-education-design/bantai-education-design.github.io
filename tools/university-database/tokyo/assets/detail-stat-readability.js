(()=>{
'use strict';
const root=document.querySelector('#detail-root');
if(!root)return;
const defs=new Map([
  ['学部',{label:'学部数',unit:'学部'}],
  ['学部数',{label:'学部数',unit:'学部'}],
  ['学科等',{label:'学科等の数',unit:'学科等'}],
  ['学科等の数',{label:'学科等の数',unit:'学科等'}],
  ['学科・課程・類',{label:'学科・課程等の数',unit:'組織'}],
  ['学科・課程等の数',{label:'学科・課程等の数',unit:'組織'}],
  ['研究科',{label:'研究科数',unit:'研究科'}],
  ['研究科数',{label:'研究科数',unit:'研究科'}],
  ['専修・コース等',{label:'専修・コース等の数',unit:'件'}],
  ['専修・コース等の数',{label:'専修・コース等の数',unit:'件'}]
]);
function clarify(){
  const hero=root.querySelector('.detail-hero');
  if(!hero)return false;
  for(const stat of hero.querySelectorAll('.detail-stat')){
    const small=stat.querySelector('small');
    const strong=stat.querySelector('strong');
    if(!small||!strong)continue;
    const def=defs.get(small.textContent.trim());
    if(!def)continue;
    if(small.textContent.trim()!==def.label)small.textContent=def.label;
    const value=strong.textContent.trim();
    if(/^\d[\d,]*$/.test(value))strong.textContent=`${value}${def.unit}`;
  }
  document.documentElement.dataset.detailStatReadability='ready';
  return true;
}
let scheduled=false;
const schedule=()=>{
  if(scheduled)return;
  scheduled=true;
  queueMicrotask(()=>{scheduled=false;clarify();});
};
const observer=new MutationObserver(schedule);
observer.observe(root,{childList:true,subtree:true,characterData:true});
schedule();
setTimeout(()=>observer.disconnect(),15000);
})();
