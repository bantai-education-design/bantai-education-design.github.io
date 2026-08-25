(()=>{
'use strict';
const params=new URLSearchParams(location.search);
if(params.get('photo_preview_token'))return;
const universityId=params.get('id');
if(!universityId)return;

const MAX_PHOTOS=9;
const displayUrl=url=>/^(?:https?:|data:|blob:|\/)/i.test(String(url||''))?url:String(url||'');

function collectPhotos(record){
  if(!record?.image_url)return [];
  const raw=[
    {image_url:record.image_url,alt:record.alt||`${record.university_name||'大学'}の実景写真`,role:'main'},
    ...(Array.isArray(record.gallery)?record.gallery:[]),
    ...(Array.isArray(record.images)?record.images:[])
  ];
  const seen=new Set();
  return raw.filter(item=>{
    const url=item?.image_url||item?.source_url||'';
    if(!url||seen.has(url))return false;
    seen.add(url);
    item.image_url=url;
    return true;
  }).slice(0,MAX_PHOTOS);
}

function installGallery(record,photos){
  const hero=document.querySelector('.detail-hero');
  if(!hero||photos.length<2)return false;
  if(hero.querySelector('.detail-owner-photo-gallery'))return true;

  hero.classList.add('photo-preview-active','owner-photo-gallery-active');
  const universityName=hero.querySelector('h1')?.textContent?.trim()||record.university_name||'大学';

  const gallery=document.createElement('div');
  gallery.className='detail-photo-preview-gallery detail-owner-photo-gallery';
  gallery.setAttribute('aria-label',`${universityName}の写真ギャラリー`);
  gallery.innerHTML=`<img class="detail-photo-preview-main detail-owner-photo-main" src="${displayUrl(photos[0].image_url)}" alt="${photos[0].alt||`${universityName}の実景写真`}"><div class="detail-photo-preview-shade"></div>`;

  const thumbs=document.createElement('div');
  thumbs.className='detail-photo-preview-thumbs detail-owner-photo-thumbs';
  thumbs.setAttribute('aria-label','大学写真を切り替える');

  photos.forEach((photo,index)=>{
    const button=document.createElement('button');
    button.type='button';
    button.className='detail-photo-preview-thumb detail-owner-photo-thumb'+(index===0?' active':'');
    button.setAttribute('aria-label',index===0?'メイン写真を表示':`写真${index+1}を表示`);
    button.innerHTML=`<img src="${displayUrl(photo.image_url)}" alt="">`;
    button.addEventListener('click',()=>{
      const main=gallery.querySelector('.detail-owner-photo-main');
      if(main){
        main.src=displayUrl(photo.image_url);
        main.alt=photo.alt||`${universityName}の実景写真`;
      }
      thumbs.querySelectorAll('.detail-owner-photo-thumb').forEach(x=>x.classList.toggle('active',x===button));
    });
    thumbs.appendChild(button);
  });

  hero.prepend(gallery);
  hero.appendChild(thumbs);
  document.documentElement.dataset.ownerPhotoGallery=String(photos.length);
  return true;
}

async function load(){
  try{
    const response=await fetch('data/user-photo-overrides.json',{cache:'no-store'});
    if(!response.ok)return;
    const registry=await response.json();
    const record=registry?.records?.[universityId];
    if(!record||record.rights_status!=='verified')return;
    const photos=collectPhotos(record);
    if(photos.length<2)return;
    const tryInstall=()=>{
      if(installGallery(record,photos))return;
      setTimeout(tryInstall,80);
    };
    tryInstall();
  }catch(err){
    console.error('University owner photo gallery failed',err);
    document.documentElement.dataset.ownerPhotoGallery='error';
  }
}
load();
})();
