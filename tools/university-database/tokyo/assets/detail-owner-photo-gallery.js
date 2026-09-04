(()=>{
'use strict';
const params=new URLSearchParams(location.search);
if(params.get('photo_preview_token'))return;
const universityId=params.get('id');
if(!universityId)return;

const MAX_PHOTOS=9;
const displayUrl=url=>/^(?:https?:|data:|blob:|\/)/i.test(String(url||''))?url:String(url||'');
const validVerified=record=>record?.rights_status==='verified'&&record.image_url&&record.source_url&&record.rights_note;

function collectPhotos(record){
  if(!record?.image_url)return [];
  const raw=[
    {image_url:record.image_url,alt:record.alt||`${record.university_name||'大学'}の実景写真`,role:'main'},
    ...(Array.isArray(record.gallery)?record.gallery:[]),
    ...(Array.isArray(record.images)?record.images:[])
  ].map(item=>({...item}));
  const seen=new Set();
  return raw.filter(item=>{
    const url=item?.image_url||item?.source_url||'';
    if(!url||seen.has(url))return false;
    seen.add(url);
    item.image_url=url;
    return true;
  }).slice(0,MAX_PHOTOS);
}

function ensureSourceStyle(){
  if(document.querySelector('#detail-photo-source-style'))return;
  const style=document.createElement('style');
  style.id='detail-photo-source-style';
  style.textContent='.detail-photo-source-link{position:absolute;right:12px;bottom:12px;z-index:4;display:inline-flex;align-items:center;gap:.25rem;padding:.42rem .65rem;border-radius:999px;background:rgba(12,12,12,.78);color:#fff!important;text-decoration:none;font-size:.76rem;font-weight:700;backdrop-filter:blur(3px)}.detail-photo-source-link:hover{text-decoration:underline}.detail-owner-photo-gallery{position:relative}';
  document.head.appendChild(style);
}

function installPhoto(record,photos){
  const hero=document.querySelector('.detail-hero');
  if(!hero||!photos.length)return false;
  if(hero.querySelector('.detail-owner-photo-gallery'))return true;

  ensureSourceStyle();
  hero.classList.add('photo-preview-active','owner-photo-gallery-active');
  const universityName=hero.querySelector('h1')?.textContent?.trim()||record.university_name||'大学';

  const gallery=document.createElement('div');
  gallery.className='detail-photo-preview-gallery detail-owner-photo-gallery';
  gallery.setAttribute('aria-label',`${universityName}の大学写真`);
  const main=document.createElement('img');
  main.className='detail-photo-preview-main detail-owner-photo-main';
  main.src=displayUrl(photos[0].image_url);
  main.alt=photos[0].alt||`${universityName}の実景写真`;
  const shade=document.createElement('div');
  shade.className='detail-photo-preview-shade';
  gallery.append(main,shade);

  if(record.source_url){
    const source=document.createElement('a');
    source.className='detail-photo-source-link';
    source.href=record.source_url;
    source.target='_blank';
    source.rel='noopener';
    source.textContent=`${record.source_label||'写真・ライセンス'} ↗`;
    source.title=[record.creator,record.license].filter(Boolean).join(' / ');
    gallery.appendChild(source);
  }

  hero.prepend(gallery);

  if(photos.length>1){
    const thumbs=document.createElement('div');
    thumbs.className='detail-photo-preview-thumbs detail-owner-photo-thumbs';
    thumbs.setAttribute('aria-label','大学写真を切り替える');
    photos.forEach((photo,index)=>{
      const button=document.createElement('button');
      button.type='button';
      button.className='detail-photo-preview-thumb detail-owner-photo-thumb'+(index===0?' active':'');
      button.setAttribute('aria-label',index===0?'メイン写真を表示':`写真${index+1}を表示`);
      const thumb=document.createElement('img');
      thumb.src=displayUrl(photo.image_url);
      thumb.alt='';
      button.appendChild(thumb);
      button.addEventListener('click',()=>{
        main.src=displayUrl(photo.image_url);
        main.alt=photo.alt||`${universityName}の実景写真`;
        thumbs.querySelectorAll('.detail-owner-photo-thumb').forEach(x=>x.classList.toggle('active',x===button));
      });
      thumbs.appendChild(button);
    });
    hero.appendChild(thumbs);
  }

  document.documentElement.dataset.ownerPhotoGallery=String(photos.length);
  document.documentElement.dataset.detailPhotoSource=record.rights_basis==='photographer_permission'?'owner':'registry';
  return true;
}

async function load(){
  try{
    const [ownerResponse,baseResponse]=await Promise.all([
      fetch('data/user-photo-overrides.json',{cache:'no-store'}).catch(()=>null),
      fetch('data/university-images.json',{cache:'no-store'}).catch(()=>null)
    ]);
    const ownerRegistry=ownerResponse?.ok?await ownerResponse.json():{records:{}};
    const baseRegistry=baseResponse?.ok?await baseResponse.json():{images:{}};
    const ownerRecord=ownerRegistry?.records?.[universityId];
    const baseRecord=baseRegistry?.images?.[universityId];
    const record=validVerified(ownerRecord)?ownerRecord:(validVerified(baseRecord)?baseRecord:null);
    if(!record)return;
    const photos=collectPhotos(record);
    if(!photos.length)return;
    const tryInstall=()=>{
      if(installPhoto(record,photos))return;
      setTimeout(tryInstall,80);
    };
    tryInstall();
  }catch(err){
    console.error('University detail photo load failed',err);
    document.documentElement.dataset.ownerPhotoGallery='error';
  }
}
load();
})();
