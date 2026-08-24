(()=>{
'use strict';
const params=new URLSearchParams(location.search);
const token=params.get('photo_preview_token');
const universityId=params.get('id');
if(!token||!universityId||typeof BroadcastChannel==='undefined')return;

document.documentElement.dataset.photoPreview='waiting';
const channel=new BroadcastChannel(`university-photo-preview-${token}`);
let objectUrls=[];
let preparedPhotos=[];
let readySent=false;

function cleanup(){for(const url of objectUrls)URL.revokeObjectURL(url);objectUrls=[];preparedPhotos=[];}
window.addEventListener('pagehide',cleanup,{once:true});

function preparePhotos(photos){
  cleanup();
  const ordered=[...photos].slice(0,5).sort((a,b)=>(b.main?1:0)-(a.main?1:0));
  preparedPhotos=ordered.map(photo=>{
    const url=URL.createObjectURL(photo.blob);
    objectUrls.push(url);
    return {...photo,url};
  });
}

function installGallery(){
  if(!preparedPhotos.length)return false;
  const hero=document.querySelector('.detail-hero');
  if(!hero)return false;
  if(hero.querySelector('.detail-photo-preview-gallery')&&hero.querySelector('.detail-photo-preview-thumbs'))return true;
  hero.querySelector('.detail-photo-preview-gallery')?.remove();
  hero.querySelector('.detail-photo-preview-thumbs')?.remove();
  hero.classList.add('photo-preview-active');

  const gallery=document.createElement('div');
  gallery.className='detail-photo-preview-gallery';
  gallery.setAttribute('aria-label','大学写真の実画面プレビュー背景');
  const universityName=hero.querySelector('h1')?.textContent?.trim()||'大学';
  gallery.innerHTML=`<img class="detail-photo-preview-main" src="${preparedPhotos[0].url}" alt="${universityName}の実景写真"><div class="detail-photo-preview-shade"></div><span class="detail-photo-preview-badge">実画面プレビュー</span>`;

  const thumbWrap=document.createElement('div');
  thumbWrap.className='detail-photo-preview-thumbs';
  thumbWrap.setAttribute('aria-label','背景写真を切り替える');
  preparedPhotos.forEach((photo,index)=>{
    const btn=document.createElement('button');
    btn.type='button';
    btn.className='detail-photo-preview-thumb'+(index===0?' active':'');
    btn.setAttribute('aria-label',index===0?'メイン写真を表示':`写真${index+1}を表示`);
    btn.innerHTML=`<img src="${photo.url}" alt="">`;
    btn.addEventListener('click',()=>{
      const main=gallery.querySelector('.detail-photo-preview-main');
      if(main)main.src=photo.url;
      thumbWrap.querySelectorAll('.detail-photo-preview-thumb').forEach(x=>x.classList.toggle('active',x===btn));
    });
    thumbWrap.appendChild(btn);
  });

  hero.prepend(gallery);
  hero.appendChild(thumbWrap);
  document.documentElement.dataset.photoPreview='ready';
  if(!readySent){readySent=true;channel.postMessage({type:'ready'});}
  return true;
}

function ensureGallery(){
  if(!preparedPhotos.length)return;
  const hero=document.querySelector('.detail-hero');
  if(!hero)return;
  if(!hero.querySelector('.detail-photo-preview-gallery')||!hero.querySelector('.detail-photo-preview-thumbs'))installGallery();
}

const root=document.querySelector('#detail-root');
const observer=new MutationObserver(()=>queueMicrotask(ensureGallery));
if(root)observer.observe(root,{childList:true});

channel.onmessage=e=>{
  const data=e.data;
  if(!data||data.universityId!==universityId||!Array.isArray(data.photos)||!data.photos.length)return;
  readySent=false;
  preparePhotos(data.photos);
  ensureGallery();
};
channel.postMessage({type:'receiver-ready'});
})();
