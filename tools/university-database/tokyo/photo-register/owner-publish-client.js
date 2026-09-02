(()=>{
'use strict';
if(new URLSearchParams(location.search).get('mode')!=='owner')return;
const button=document.querySelector('#generate-batch');
const status=document.querySelector('#owner-publish-status');
if(!button)return;

let configPromise=null;
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function setStatus(text,state='working'){
  if(status)status.textContent=text;
  document.documentElement.dataset.ownerPublishStatus=state;
}
async function config(){
  if(!configPromise)configPromise=fetch('owner-publish-config.json',{cache:'no-store'}).then(async response=>{
    if(!response.ok)throw new Error('掲載API設定を読み込めません');
    return response.json();
  });
  return configPromise;
}
function expectedMatches(data,payload){
  const manifest=payload.manifest||{};
  const record=data?.records?.[payload.university_id];
  if(manifest.owner_record_removed)return !record;
  if(!record||record.image_url!==manifest.main_image_url)return false;
  const gallery=(Array.isArray(record.gallery)?record.gallery:[]).map(item=>item.image_url||item.source_url||'');
  return JSON.stringify(gallery)===JSON.stringify(manifest.gallery_image_urls||[]);
}
async function waitForPages(payload){
  const url='../data/user-photo-overrides.json';
  for(let attempt=0;attempt<60;attempt++){
    try{
      const response=await fetch(`${url}?published=${Date.now()}`,{cache:'no-store'});
      if(response.ok&&expectedMatches(await response.json(),payload))return true;
    }catch{}
    await sleep(2000);
  }
  return false;
}
function ownerKey(){
  let key=sessionStorage.getItem('bantai_owner_publish_key')||'';
  if(!key)key=window.prompt('初回のみ：本人写真の掲載キーを入力してください。')||'';
  key=key.trim();
  if(!key)throw new Error('掲載キーが入力されていません');
  sessionStorage.setItem('bantai_owner_publish_key',key);
  return key;
}
async function publish(payload){
  const cfg=await config();
  if(!cfg?.enabled||!cfg.endpoint)throw new Error('掲載APIは準備中です。公開DBは変更していません。');
  const key=ownerKey();
  button.disabled=true;
  button.textContent='掲載中…';
  setStatus('編集済み写真を大学DBへ掲載しています…','publishing');
  const response=await fetch(cfg.endpoint,{
    method:'POST',
    mode:'cors',
    headers:{'Content-Type':'application/json','X-Owner-Publish-Key':key},
    body:JSON.stringify(payload)
  });
  const result=await response.json().catch(()=>({}));
  if(response.status===401)sessionStorage.removeItem('bantai_owner_publish_key');
  if(!response.ok||result.ok!==true)throw new Error(result.message||`掲載APIエラー（${response.status}）`);
  setStatus('GitHubへの反映が完了しました。公開ページを更新しています…','deploying');
  const live=await waitForPages(payload);
  if(live){
    button.textContent='掲載完了';
    setStatus('掲載完了しました。公開大学DBにも反映されています。','complete');
    document.documentElement.dataset.ownerPhotoSetExport='published';
    return result;
  }
  button.textContent='掲載済み・公開反映待ち';
  setStatus('GitHubへの掲載は完了しました。GitHub Pagesの更新待ちです。数分後に公開DBをご確認ください。','waiting-pages');
  document.documentElement.dataset.ownerPhotoSetExport='published-waiting-pages';
  return result;
}
window.__ownerPublishClient={publish,config};
document.documentElement.dataset.ownerPublishClient='ready';
})();
