(()=>{
'use strict';
const status=document.querySelector('#center-connection');
const open=document.querySelector('#center-open');
fetch('center-config.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(c=>{
  if(!c.enabled || !c.url){status.textContent='コラム編集・大学DB修正提案・公開履歴は、管理サーバーの接続設定後に利用できます。写真の審査・補正は下のメニューから利用できます。';return;}
  const url=new URL(c.url);if(url.protocol!=='https:' || url.username || url.password || url.search || url.hash || url.pathname!=='/')throw Error();
  status.textContent='編集には管理サーバーでのログインが必要です。';open.href=url.href;open.hidden=false;
  for(const link of document.querySelectorAll('[data-center-tab]'))link.href=url.href+'#'+link.dataset.centerTab;
}).catch(()=>{status.textContent='編集サーバーの設定を確認できません。下の写真管理機能は引き続き利用できます。';});
})();
