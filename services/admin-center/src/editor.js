import {Editor, Node, mergeAttributes} from '@tiptap/core';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import {Table,TableRow,TableHeader,TableCell} from '@tiptap/extension-table';
import {renderDoc} from './content.js';
const $=s=>document.querySelector(s), publicSite='https://bantai-education-design.github.io';
let profiles=[];
let csrf='',article=null,editor=null,timer=null,dirty=false,saving=null,generation=0,conflict=false;
const notice=s=>{$('#notice').textContent=s;};
const run=fn=>async(...args)=>{try{await fn(...args);}catch(e){notice(e.message);}};
async function api(path,method='GET',body) {
  const r=await fetch('/api/'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:body===undefined?undefined:JSON.stringify(body),credentials:'same-origin',cache:'no-store'});
  const d=await r.json();
  if(!r.ok) {const e=Error(d.message || '接続に失敗しました');e.status=r.status;throw e;}
  return d;
}
const chart=Node.create({
  name:'chart',group:'block',atom:true,
  addAttributes(){return {title:{default:'棒グラフ'},rows:{default:[]}};},
  parseHTML(){return [{tag:'div[data-chart]'}];},
  renderHTML({HTMLAttributes}){return ['div',mergeAttributes(HTMLAttributes,{'data-chart':'true'}),'棒グラフ'];},
  addNodeView(){return ({node})=>{const dom=document.createElement('div');dom.innerHTML=renderDoc({type:'doc',content:[node.toJSON()]});return {dom};};}
});
const preserved=Node.create({
  name:'preserved',group:'block',atom:true,selectable:true,
  addAttributes(){return {index:{default:null}};},
  parseHTML(){return [{tag:'div[data-preserved]'}];},
  renderHTML(){return ['div',{'data-preserved':'true'},'原本保持ブロック'];},
  addNodeView(){return ({node})=>{const dom=document.createElement('div');dom.className='preserved-block';const title=document.createElement('strong');title.textContent='原本のレイアウトを保持';const p=document.createElement('p');p.textContent=article?.legacy?.labels[node.attrs.index] || '画像・表・独自レイアウト';dom.append(title,p);return {dom};};}
});
const legacyParagraph=Node.create({
  name:'legacyParagraph',group:'block',content:'inline*',
  addAttributes(){return {index:{default:null}};},
  parseHTML(){return [{tag:'p[data-legacy-paragraph]'}];},
  renderHTML(){return ['p',{'data-legacy-paragraph':'true'},0];}
});
const legacyContainer=Node.create({
  name:'legacyContainer',group:'block',content:'block*',defining:true,
  addAttributes(){return {index:{default:null}};},
  parseHTML(){return [{tag:'div[data-legacy-container]'}];},
  renderHTML(){return ['div',{'data-legacy-container':'true',class:'legacy-container'},0];}
});
function changed(){if(!article)return;dirty=true;generation++;$('#save-status').textContent='未保存…';clearTimeout(timer);timer=setTimeout(()=>run(save)(),1000);}
function setupEditor(){
  editor=new Editor({element:$('#editor'),extensions:[StarterKit.configure({heading:{levels:[2,3]},link:{openOnClick:false,protocols:['https','http']}}),Image.configure({allowBase64:false}),Table,TableRow,TableHeader,TableCell,chart,preserved,legacyParagraph,legacyContainer],content:{type:'doc',content:[{type:'paragraph'}]},onUpdate:changed,editorProps:{handlePaste:(_v,event)=>{
    // External rich HTML can introduce unknown or tracking image URLs. Paste prose only.
    const text=event.clipboardData?.getData('text/plain');if(text){event.preventDefault();editor.commands.insertContent(text.split('\n').map(text=>({type:'paragraph',content:text?[{type:'text',text}]:[]})));return true;}return false;
  },handleDrop:(_v,e)=>{e.preventDefault();notice('画像は「画像」ボタンからアップロードしてください。');return true;}}});
}
async function listDrafts(){
  const list=await api('articles');$('#draft-list').replaceChildren();
  for(const a of list){const b=document.createElement('button');b.className='draft'+(a.id===article?.id?' active':'');b.textContent=a.title;b.onclick=run(async()=>{await save();await openArticle(await api('articles/'+a.id));});$('#draft-list').append(b);}
  if(!list.length)$('#draft-list').textContent='下書きはまだありません。';
}
async function versions(){
  const id=article?.id;if(!id)return;const versions=await api(`articles/${id}/versions`);if(article?.id!==id)return;$('#versions').replaceChildren();
  for(const v of versions){const row=document.createElement('div');row.className='history-row';row.textContent=`第${v.revision}版 · ${new Date(v.created).toLocaleString('ja-JP')}`;const b=document.createElement('button');b.textContent='この版を復元';b.onclick=run(async()=>{
    if(!confirm('この版を新しい下書きとして復元しますか？'))return;
    await save();if(article?.id!==id)throw Error('編集中の記事が変わりました。履歴を開き直してください。');await openArticle(await api(`articles/${id}/restore`,'POST',{revision:article.revision,target:v.revision}));notice('下書きを復元しました。公開ページは変更していません。');
  });row.append(b);$('#versions').append(row);}
}
async function openArticle(a){
  if(dirty || saving)await save();
  clearTimeout(timer);article=a;dirty=false;conflict=false;$('#title').value=a.title;$('#excerpt').value=a.excerpt;
  editor.commands.setContent(a.doc,{emitUpdate:false});$('#writing').hidden=false;$('#empty-editor').hidden=true;$('#save-status').textContent=`第${a.revision}版 保存済み`;
  await Promise.all([listDrafts(),versions()]);
}
async function save(){
  if(!article || !dirty)return;
  if(conflict)throw Error('編集競合があります。本文をコピーしてから画面を再読込してください。');
  if(saving){await saving;if(dirty)return save();return;}
  const sentGeneration=generation,id=article.id;
  const snapshot={title:$('#title').value,excerpt:$('#excerpt').value,doc:editor.getJSON(),revision:article.revision};
  $('#save-status').textContent='保存中…';
  saving=(async()=>{
    try {
      const result=await api('articles/'+id,'PUT',snapshot);article=result;dirty=generation!==sentGeneration;
      $('#save-status').textContent=dirty?'未保存…':`第${result.revision}版 保存済み`;
    }catch(e){conflict=e.status===409;$('#save-status').textContent=conflict?'競合・未保存（本文をコピーして保護）':'保存失敗・未保存';throw e;}
    finally{saving=null;}
  })();
  await saving;
  if(dirty)return save();
  await Promise.all([listDrafts(),versions()]);
}
async function loadLegacy(){
  const rows=await api('legacy');const render=()=>{
    $('#legacy-list').replaceChildren();const query=$('#legacy-search').value.trim().toLowerCase();
    for(const r of rows.filter(x=>!query || x.title.toLowerCase().includes(query))){
      const p=document.createElement('div');p.className='legacy-row';const a=document.createElement('a');a.textContent=r.title;a.href=publicSite+(r.url || '/columns/');a.target='_blank';a.rel='noopener';p.append(a);
      for(const fresh of [false,true]){const b=document.createElement('button');b.textContent=fresh?'最新版を再取込':'編集する';b.onclick=run(async()=>{
        await save();if(fresh && !confirm('現在の下書きを残し、最新版を別の下書きとして取り込みます。続けますか？'))return;
        b.disabled=true;try{await openArticle(await api('legacy/import','POST',{catalogId:r.id,fresh}));notice('既存記事を下書きに取り込みました。元の記事は公開申請・承認まで変わりません。');}finally{b.disabled=false;}
      });p.append(b);}
      $('#legacy-list').append(p);
    }
  };$('#legacy-search').oninput=render;render();
}
async function loadProfiles(){
  profiles=await api('universities');const select=$('#profile-select');
  for(const p of profiles){const o=document.createElement('option');o.value=p.region+'/'+p.id;o.textContent=`${p.name}（${{tokyo:'東京',kanagawa:'神奈川',saitama:'埼玉'}[p.region]} / ${p.id}）`;select.append(o);}
  select.onchange=()=>{const p=profiles.find(x=>x.region+'/'+x.id===select.value);if(!p)return;
    const f=$('#proposal-form');f.elements.region.value=p.region;f.elements.universityId.value=p.id;f.elements.source.value=p.source;
    $('#profile-field').replaceChildren();for(const [key,label] of Object.entries(p.fieldLabels)){const o=document.createElement('option');o.value=key;o.textContent=label;$('#profile-field').append(o);}
    const fill=()=>{const key=$('#profile-field').value;f.elements.field.value=key;f.elements.before.value=p.fields[key];f.elements.after.value=p.fields[key];};$('#profile-field').onchange=fill;fill();
  };
}
async function history(){
  const h=await api('history');$('#requests').replaceChildren();$('#events').replaceChildren();
  if(!h.requests.length)$('#requests').textContent='公開申請はまだありません。';
  for(const r of h.requests){const p=document.createElement('p');p.className='history-row';p.textContent=`${{'publish':'公開','unpublish':'非公開','university-proposal':'大学DB修正提案'}[r.action]} / ${{open:'申請中',merged:'マージ済み（配信は要確認）',closed:'取り下げ'}[r.state] || r.state} `;const a=document.createElement('a');a.href=r.url;a.textContent=`PR #${r.number}`;a.target='_blank';a.rel='noopener';p.append(a);$('#requests').append(p);}
  const labels={'draft.saved':'下書きを保存','draft.restored':'下書きを復元','legacy.imported':'既存記事を取り込み','publication.requested':'公開・非公開を申請','publication.merged':'マージを確認','publication.closed':'申請の取り下げを確認','image.uploaded':'画像をアップロード','university.proposed':'大学情報の修正提案を保存','university.requested':'大学情報の申請を作成','session.login':'ログイン'};
  for(const e of h.events){const p=document.createElement('p');p.className='history-row';p.textContent=`${new Date(e.created).toLocaleString('ja-JP',{timeZone:'Asia/Tokyo'})} · ${labels[e.kind] || '操作を記録'}${e.detail.revision?' · 第'+e.detail.revision+'版':''}`;$('#events').append(p);}
}
async function proposals(){
  const rows=await api('proposals');$('#proposals').replaceChildren();
  for(const p of rows){const el=document.createElement('div');el.className='history-row';const text=document.createElement('p');text.textContent=`${{tokyo:'東京',kanagawa:'神奈川',saitama:'埼玉'}[p.region]} · ${p.universityId} · ${profiles.find(x=>x.id===p.universityId && x.region===p.region)?.fieldLabels[p.field] || p.field}: ${p.before || '（未登録）'} → ${p.after}`;el.append(text);
    for(const apply of [false,true]){const b=document.createElement('button');b.textContent=apply?'DB反映を申請（PR）':'提案だけをPRにする';if(apply && (!p.sourceConfirmed || !profiles.some(x=>x.id===p.universityId && x.region===p.region && Object.hasOwn(x.fieldLabels,p.field)))){b.disabled=true;b.title='対応プロフィールの大学・項目を選び、公式出典を確認して保存してください';}b.onclick=run(async()=>{
      if(!confirm(apply?'公式出典と変更前後を確認しましたか？対象プロフィールを変更する公開PRを作成します。':'修正提案を公開リポジトリのPRに載せます。続けますか？'))return;
      b.disabled=true;try{const r=await api(`proposals/${p.id}/submit`,'POST',{apply});notice(`PR #${r.number}を作成しました。反映はレビュー・承認後です。`);await history();}finally{b.disabled=false;}
    });el.append(b);}
    $('#proposals').append(el);
  }
}
async function enter(session){csrf=session.csrf;$('#login').hidden=true;$('#workspace').hidden=false;$('#logout').hidden=false;if(!editor)setupEditor();notice(session.publicationConfigured===false?'下書き編集を利用できます。公開用のGitHub接続は未設定です。':'');await Promise.all([listDrafts(),loadLegacy(),loadProfiles(),proposals(),history()]);const tab=document.querySelector('[data-tab="'+location.hash.slice(1).replace(/[^a-z]/g,'')+'"]');if(tab)tab.click();}
$('#login-form').onsubmit=run(async e=>{e.preventDefault();const s=await api('login','POST',{password:$('#password').value});$('#password').value='';await enter({...s,...await api('session')});});
$('#logout').onclick=run(async()=>{await save();await api('logout','POST',{});location.reload();});
$('#new').onclick=run(async()=>{await save();const a=await api('articles','POST',{title:'新しいコラム',excerpt:'',doc:{type:'doc',content:[{type:'paragraph'}]}});await openArticle(a);$('#title').focus();});
$('#title').oninput=changed;$('#excerpt').oninput=changed;$('#save').onclick=run(save);
$('#preview').onclick=run(async()=>{await save();if(!article)return;const a=document.createElement('a');a.href=`/api/articles/${article.id}/preview`;a.target='_blank';a.rel='noopener';a.click();});
$('#toolbar').onmousedown=e=>{if(e.target.closest('button'))e.preventDefault();};
function insertBlock(node){const selection=editor.state.selection;const chain=editor.chain().focus();if(selection.node)chain.insertContentAt(selection.to,node).run();else chain.insertContent(node).run();}
$('#toolbar').onclick=run(async e=>{
  const cmd=e.target.dataset.command;if(!cmd)return;
  if(cmd==='paragraph')editor.chain().focus().setParagraph().run();
  if(cmd==='heading')editor.chain().focus().toggleHeading({level:2}).run();
  if(cmd==='heading3')editor.chain().focus().toggleHeading({level:3}).run();
  if(cmd==='bold')editor.chain().focus().toggleBold().run();
  if(cmd==='undo')editor.chain().focus().undo().run();if(cmd==='redo')editor.chain().focus().redo().run();
  if(cmd==='link'){const url=prompt('リンク先のURL（http/https）。空欄でリンクを解除。',editor.getAttributes('link').href || 'https://');if(url===null)return;if(!url)editor.chain().focus().extendMarkRange('link').unsetLink().run();else{const parsed=new URL(url);if(!['https:','http:'].includes(parsed.protocol))throw Error('http/httpsを指定してください');editor.chain().focus().extendMarkRange('link').setLink({href:parsed.href}).run();}}
  if(cmd==='table')editor.chain().focus().insertTable({rows:3,cols:3,withHeaderRow:true}).run();
  if(cmd==='row')editor.chain().focus().addRowAfter().run();if(cmd==='column')editor.chain().focus().addColumnAfter().run();if(cmd==='deleteTable')editor.chain().focus().deleteTable().run();
  if(cmd==='image')$('#image-input').click();
  if(cmd==='chart'){const title=prompt('グラフの見出し','棒グラフ');if(title===null)return;const text=prompt('1行に「項目,数値」を入力（30件以内、非負数）','項目A,10\n項目B,20');if(text===null)return;const rows=text.split('\n').filter(x=>x.trim()).map(line=>{const i=line.lastIndexOf(',');if(i<1 || !line.slice(i+1).trim())throw Error('項目,数値 の形式で入力してください');return {label:line.slice(0,i).trim(),value:Number(line.slice(i+1))};});const node={type:'chart',attrs:{title,rows}};renderDoc({type:'doc',content:[node]});insertBlock(node);}
});
$('#image-input').onchange=run(async e=>{
  const file=e.target.files[0];e.target.value='';if(!file)return;
  if(file.size>5*1024*1024)throw Error('画像は5MB以内で選択してください');
  const alt=prompt('画像の説明（読み上げにも使用）',file.name);if(alt===null)return;
  notice('画像をアップロード中…');const bytes=new Uint8Array(await file.arrayBuffer());let raw='';for(let i=0;i<bytes.length;i+=8192)raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
  const img=await api('images','POST',{base64:btoa(raw)});insertBlock({type:'image',attrs:{src:img.src,alt,title:alt}});notice('画像を挿入しました。下書きを保存中です。');await save();notice('画像を挿入して下書きを保存しました。');
});
for(const action of ['publish','unpublish'])$('#'+action).onclick=run(async()=>{
  await save();if(!article)return;
  if(!confirm(action==='publish'?'記事と画像を公開PRに載せます。権利・内容を確認しましたか？':'非公開化のPRを作成します。反映は承認・マージ後です。続けますか？'))return;
  $('#publish').disabled=true;$('#unpublish').disabled=true;
  try{const r=await api(`articles/${article.id}/${action}`,'POST',{revision:article.revision});notice(`PR #${r.number}を作成しました。公開履歴から確認してください。`);await history();}
  finally{$('#publish').disabled=false;$('#unpublish').disabled=false;}
});
for(const b of document.querySelectorAll('[data-tab]'))b.onclick=run(async()=>{await save();for(const p of document.querySelectorAll('.panel'))p.hidden=p.id!==b.dataset.tab;for(const tab of document.querySelectorAll('[data-tab]'))tab.removeAttribute('aria-current');b.setAttribute('aria-current','page');if(b.dataset.tab==='history')await history();});
$('#sync').onclick=run(async()=>{await api('sync','POST',{});await history();notice('GitHubの状態を更新しました。');});
$('#proposal-form').onsubmit=run(async e=>{e.preventDefault();await api('proposals','POST',{...Object.fromEntries(new FormData(e.target)),sourceConfirmed:e.target.elements.sourceConfirmed.checked});e.target.reset();$('#profile-select').value='';$('#profile-field').replaceChildren(new Option('大学を選択してください',''));await proposals();notice('修正提案を保存しました。公開DBはまだ変更していません。');});
window.addEventListener('beforeunload',e=>{if(dirty||saving){e.preventDefault();e.returnValue='';}});
api('session').then(enter).catch(e=>{if(e.status!==401)notice('管理サーバーに接続できません。公式サイトの管理入口から開いてください。');});
