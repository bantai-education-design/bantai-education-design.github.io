(()=>{
'use strict';
const params=new URLSearchParams(location.search);
const token=params.get('photo_preview_token');
const universityId=params.get('id');
if(!token||!universityId||typeof BroadcastChannel==='undefined')return;

document.documentElement.dataset.photoPreview='waiting';
const channel=new BroadcastChannel(`university-photo-preview-${token}`);
let objectUrls=[];

function cleanup(){for(const url of objectUrls)URL.revokeObjectURL(url);objectUrls=[];}
window.addEventListener('pagehide',cleanup,{once:true});

function installGallery(photos){
  const hero=document.querySelector('.detail-hero');
  if(!hero)return false;
  cleanup();
  const ordered=[...photos].slice(0,5).sort((a,b)=>(b.main?1:0)-(a.main?1:0));
  if(!ordered.length)return false;
  const prepared=ordered.map(photo=>{
    const url=URL.createObjectURL(photo.blob);
    objectUrls.push(url);
    return {...photo,url};
  });
  hero.querySelector('.detail-photo-preview-gallery')?.remove();
  hero.classList.add('photo-preview-active');
  const gallery=document.createElement('div');
  gallery.className='detail-photo-preview-gallery';
  gallery.setAttribute('aria-label','大学写真の実画面プレビュー');
  gallery.innerHTML=`<img class="detail-photo-preview-main" src="${prepared[0].url}" alt="${document.querySelector('.detail-hero h1')?.textContent?.trim()||'大学'}の実景写真"><div class="detail-photo-preview-shade"></div><span class="detail-photo-preview-badge">実画面プレビュー</span><div class="detail-photo-preview-thumbs"></div>`;
  const thumbWrap=gallery.querySelector('.detail-photo-preview-thumbs');
  prepared.forEach((photo,index)=>{
    const btn=document.createElement('button');
    btn.type='button';
    btn.className='detail-photo-preview-thumb'+(index===0?' active':'');
    btn.setAttribute('aria-label',index===0?'メイン写真を表示':`写真${index+1}を表示`);
    btn.innerHTML=`<img src="${photo.url}" alt="">`;
    btn.addEventListener('click',()=>{
      gallery.querySelector('.detail-photo-preview-main').src=photo.url;
      gallery.querySelectorAll('.detail-photo-preview-thumb').forEach(x=>x.classList.toggle('active',x===btn));
    });
    thumbWrap.appendChild(btn);
  });
  hero.prepend(gallery);
  document.documentElement.dataset.photoPreview='ready';
  channel.postMessage({type:'ready'});
  return true;
}

let pending=null;
function tryInstall(){
  if(!pending)return;
  if(installGallery(pending))pending=null;
}
const observer=new MutationObserver(tryInstall);
observer.observe(document.querySelector('#detail-root'),{childList:true});
channel.onmessage=e=>{
  const data=e.data;
  if(!data||data.universityId!==universityId||!Array.isArray(data.photos))return;
  pending=data.photos;
  tryInstall();
};
channel.postMessage({type:'receiver-ready'});
})();
