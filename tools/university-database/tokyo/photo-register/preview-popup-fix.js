(()=>{
'use strict';
const button=document.querySelector('#open-real-preview');
const list=document.querySelector('#batch-list');
const firstSelect=document.querySelector('#university-first-select');
const status=document.querySelector('#real-preview-status');
if(!button||!list||!firstSelect||!status||typeof BroadcastChannel==='undefined')return;
let channel=null;
const rowBlob=async row=>{
  const img=row.querySelector('.thumb img');
  if(!img?.src)throw new Error('写真を取得できません');
  const res=await fetch(img.src);
  if(!res.ok)throw new Error('写真を取得できません');
  return res.blob();
};
const urlBlob=async url=>{
  const res=await fetch(url,{cache:'no-store'});
  if(!res.ok)throw new Error('現在の登録写真を取得できません');
  return res.blob();
};
button.addEventListener('click',async e=>{
  e.preventDefault();
  e.stopImmediatePropagation();
  const allRows=[...list.querySelectorAll('.batch-row')];
  const universityId=firstSelect.value;
  const helper=window.__universityPhotoMainChoice;
  const existingPhotos=helper?.getExistingPhotos?.()||[];
  if((!allRows.length&&!existingPhotos.length)||!universityId)return;

  const previewWindow=window.open('about:blank','_blank');
  if(!previewWindow){
    status.textContent='プレビュー画面を開けませんでした。ブラウザのポップアップ許可をご確認ください。';
    return;
  }
  previewWindow.document.title='大学ページの実画面プレビューを準備中';
  previewWindow.document.body.innerHTML='<p style="font-family:sans-serif;padding:24px">実画面プレビューを準備しています…</p>';
  button.disabled=true;
  status.textContent='実画面プレビューを準備しています…';

  try{
    const mainChoice=helper?.getChoice?.()||{type:'new',key:''};
    const photos=[];

    for(const photo of existingPhotos.slice(0,5)){
      photos.push({
        blob:await urlBlob(`../${photo.image_url}`),
        main:mainChoice.type==='existing'&&mainChoice.key===photo.image_url,
        source:'existing'
      });
    }

    const remaining=Math.max(0,5-photos.length);
    for(const row of allRows.slice(0,remaining)){
      photos.push({
        blob:await rowBlob(row),
        main:mainChoice.type==='new'&&mainChoice.key===(row.dataset.key||''),
        source:'new'
      });
    }
    if(!photos.some(x=>x.main)&&photos.length)photos[0].main=true;

    const token=(crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`).replace(/[^a-zA-Z0-9-]/g,'');
    channel?.close();
    channel=new BroadcastChannel(`university-photo-preview-${token}`);
    const target=`../detail.html?id=${encodeURIComponent(universityId)}&photo_preview_token=${encodeURIComponent(token)}`;
    let sent=0;
    const send=()=>{
      if(sent++>15)return;
      channel.postMessage({universityId,photos});
      setTimeout(send,400);
    };
    channel.onmessage=event=>{
      if(event.data?.type==='receiver-ready'||event.data?.type==='ready'){
        channel.postMessage({universityId,photos});
        if(event.data?.type==='ready'){
          status.textContent='実詳細ページでプレビューを開きました。本番登録はまだ行っていません。';
          button.disabled=false;
        }
      }
    };
    previewWindow.location.href=target;
    send();
  }catch(err){
    console.error(err);
    try{previewWindow.close();}catch(_e){}
    status.textContent=err.message||'プレビュー準備に失敗しました。';
    button.disabled=false;
  }
},true);
})();
