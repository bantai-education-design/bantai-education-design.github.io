import {randomUUID} from 'node:crypto';
import {Buffer} from 'node:buffer';
import {D1Store} from './store.js';
import {login,callback,authReady,cookie,sessionCookie,hash} from './auth.js';
import {GitHub} from '../src/github.js';
import {validateArticle,articlePage,safeURL,imagePaths} from '../src/content.js';
import preparedImports from './generated-legacy.json' with {type:'json'};
import {digest,legacyCandidatePath,validateLegacyIdentity,legacyPage} from '../src/legacy.js';
import {profilePath,applyProfileProposal} from '../src/university.js';
const json=(value,status=200)=>Response.json(value,{status});
const bad=(message,status=400)=>Object.assign(Error(message),{status});
async function body(request,max=700000){
 if(!request.headers.get('content-type')?.startsWith('application/json'))throw bad('JSON形式が必要です',415);
 const reader=request.body?.getReader();if(!reader)throw bad('本文がありません');let length=0,parts=[];
 while(true){const {value,done}=await reader.read();if(done)break;length+=value.byteLength;if(length>max){await reader.cancel();throw bad('送信サイズが大きすぎます',413);}parts.push(value);}
 const data=new Uint8Array(length);let p=0;for(const part of parts){data.set(part,p);p+=part.byteLength;}try{return JSON.parse(new TextDecoder().decode(data));}catch{throw bad('JSONが不正です');}
}
async function asset(env,path){const r=await env.ASSETS.fetch(new Request('https://assets.invalid'+path));if(!r.ok)throw bad('公開データがありません',404);return r.json();}
async function decorate(store,a){const origin=await store.origin(a.id);return origin?{...a,legacy:{catalogId:origin.entry.id,labels:origin.blocks.map(b=>b.label)}}:a;}
export function createWorker({fetcher=fetch,githubFactory=env=>new GitHub(env.ADMIN_GITHUB_TOKEN,fetcher)}={}){
 return {async fetch(request,env){
  const url=new URL(request.url),path=url.pathname,store=new D1Store(env.DB),gh=githubFactory(env);
  let response;
  try{
   if(url.protocol!=='https:' && !['127.0.0.1','localhost','[::1]'].includes(url.hostname)){url.protocol='https:';return Response.redirect(url.href,308);}
   const mutate=!['GET','HEAD'].includes(request.method);
   if(mutate && request.headers.get('Origin')!==url.origin)throw bad('許可されていない送信元です',403);
   if(path==='/healthz'){await store.first('SELECT 1');response=json({ok:true});}
   else if(path==='/api/auth-config')response=json({provider:'github',ready:authReady(env),loginUrl:'/auth/login',maxImageBytes:1000000});
   else if(path==='/auth/login' && request.method==='GET')response=await login(request,env,store);
   else if(path==='/auth/callback' && request.method==='GET')response=await callback(request,env,store,fetcher);
   else if(path.startsWith('/data/'))throw bad('ページがありません',404);
   else if(path.startsWith('/api/') || path.startsWith('/assets/images/admin/')){
    const session=await store.first('SELECT * FROM sessions WHERE hash=? AND expires>?',hash(cookie(request,'__Host-bantai')),Date.now());
    if(!session)throw bad('ログインしてください',401);
    if(mutate && request.headers.get('x-csrf-token')!==session.csrf)throw bad('再ログインしてください',403);
    if(path==='/api/session')response=json({csrf:session.csrf,publicationConfigured:!!env.ADMIN_GITHUB_TOKEN});
    else if(path==='/api/logout' && request.method==='POST'){await store.run('DELETE FROM sessions WHERE hash=?',session.hash);response=json({ok:true});response.headers.append('Set-Cookie',sessionCookie('',0));}
    else if(path==='/api/articles' && request.method==='GET')response=json(await Promise.all((await store.list()).map(a=>decorate(store,a))));
    else if(path==='/api/articles' && request.method==='POST')response=json(await store.save(null,0,validateArticle(await body(request))),201);
    else if(/^\/api\/articles\/[a-f0-9-]{36}(\/\w+)?$/.test(path)){
     const [,id,action]=path.match(/^\/api\/articles\/([a-f0-9-]{36})(?:\/(\w+))?$/),a=await store.get(id);if(!a)throw bad('記事がありません',404);
     if(!action && request.method==='GET')response=json(await decorate(store,a));
     else if(!action && request.method==='PUT'){const b=await body(request),o=await store.origin(id);response=json(await decorate(store,await store.save(id,b.revision,validateArticle(b,{preserved:o?.blocks,title:b.title}))));}
     else if(action==='versions' && request.method==='GET')response=json(await store.versions(id));
     else if(action==='restore' && request.method==='POST'){const b=await body(request);response=json(await decorate(store,await store.restore(id,b.revision,b.target)));}
     else if(action==='preview' && request.method==='GET'){const o=await store.origin(id);response=new Response(o?(legacyPage(a,o)||articlePage(a,undefined,{preserved:o.blocks,title:a.title})):articlePage(a),{headers:{'Content-Type':'text/html; charset=utf-8'}});}
     else if(['publish','unpublish'].includes(action) && request.method==='POST'){
      const b=await body(request);if(b.revision!==a.revision)throw bad('最新版を保存してから申請してください',409);if(imagePaths(a.doc).length>9)throw bad('無料構成では1記事9画像以内で申請してください');const release=await store.acquireLock();
      try{const pr=await gh.publish(store,a,action,async path=>(await store.getImage(path)).data),r={id:randomUUID(),article_id:id,revision:a.revision,action,url:pr.html_url,number:pr.number,state:'open'};await store.recordRequest(r,pr.baseline);response=json(r,201);}finally{await release();}
     }
    }
    else if(path==='/api/history')response=json({events:await store.history(),requests:await store.requests()});
    else if(path==='/api/sync' && request.method==='POST'){await gh.sync(store);response=json({requests:await store.requests()});}
    else if(path==='/api/legacy' && request.method==='GET')response=json(env.ADMIN_GITHUB_TOKEN?JSON.parse(await gh.read('data/columns.json')):await asset(env,'/data/columns.json'));
    else if(path==='/api/legacy/import' && request.method==='POST'){
     const b=await body(request,4096),existing=!b.fresh?await store.first('SELECT article_id FROM origins WHERE catalog_id=? ORDER BY rowid DESC LIMIT 1',b.catalogId):null;
     if(existing)response=json(await decorate(store,await store.get(existing.article_id)),201);
     else {
       const base=await gh.request('git/ref/heads/main'),catalog=JSON.parse(await gh.read('data/columns.json',base.object.sha)),entry=catalog.find(x=>x.id===b.catalogId);validateLegacyIdentity(entry);
       const imported=preparedImports[entry.id];if(!imported || digest(entry)!==imported.origin.expectedEntryHash)throw bad('公開元が更新されています。管理センターを最新内容で再ビルドしてから取り込んでください',409);
       if(imported.origin.path && digest(await gh.read(imported.origin.path,base.object.sha))!==imported.origin.expectedSourceHash)throw bad('元のHTMLが更新されています。再ビルドが必要です',409);
       response=json(await decorate(store,await store.importLegacy(entry.id,imported.origin,imported.body,b.fresh===true)),201);
     }
    }
    else if(path==='/api/universities')response=json(await asset(env,'/data/admin-university-profiles.json'));
    else if(path==='/api/proposals' && request.method==='GET')response=json((await store.all('SELECT * FROM proposals ORDER BY rowid DESC')).map(r=>({id:r.id,...JSON.parse(r.body),created:r.created})));
    else if(path==='/api/proposals' && request.method==='POST'){
     const b=await body(request,40000);if(!['tokyo','kanagawa','saitama'].includes(b.region) || typeof b.before!=='string' || b.before.length>5000 || ![b.universityId,b.field,b.after,b.reason].every(v=>typeof v==='string'&&v.trim()&&v.length<=5000))throw bad('大学ID・項目・変更前後・理由を入力してください');
     const p={region:b.region,universityId:b.universityId,field:b.field,before:b.before,after:b.after,reason:b.reason,source:safeURL(b.source),sourceConfirmed:b.sourceConfirmed===true};if(!p.source.startsWith('https://'))throw bad('公式出典はHTTPSを指定してください');const id=randomUUID();await env.DB.batch([store.statement('INSERT INTO proposals VALUES(?,?,?)',id,JSON.stringify(p),new Date().toISOString()),store.eventStatement('university.proposed',{id})]);response=json({id,...p},201);
    }
    else if(/^\/api\/proposals\/[a-f0-9-]{36}\/submit$/.test(path) && request.method==='POST'){
     const id=path.split('/')[3],p=await store.first('SELECT * FROM proposals WHERE id=?',id);if(!p)throw bad('提案がありません',404);const b=await body(request,4096),data=JSON.parse(p.body),files=[{path:`data-source/admin-proposals/${id}.json`,content:JSON.stringify(data,null,2)+'\n'}],release=await store.acquireLock();
     try{let base;if(b.apply===true){const path=profilePath(data.region,data.universityId);base=(await gh.request('git/ref/heads/main')).object.sha;files.push({path,content:JSON.stringify(applyProfileProposal(JSON.parse(await gh.read(path,base)),data),null,2)+'\n'});}const pr=await gh.createPR(files,'大学DB修正申請','公式出典と変更差分を確認し、人間の承認後にマージしてください。',base),r={id:randomUUID(),article_id:null,revision:null,action:'university-proposal',url:pr.html_url,number:pr.number,state:'open'};await store.recordRequest(r,null,'university.requested');response=json(r,201);}finally{await release();}
    }
    else if(path==='/api/images' && request.method==='POST'){
     const b=await body(request,1500000),data=Buffer.from(String(b.base64||''),'base64');let ext;
     if(data.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))ext='png';else if(data[0]===255&&data[1]===216&&data[2]===255)ext='jpg';else if(data.toString('ascii',0,4)==='RIFF'&&data.toString('ascii',8,12)==='WEBP')ext='webp';
     if(!ext||data.byteLength>1000000)throw bad('無料構成では1MB以内のPNG/JPEG/WebPを選択してください');const src='/assets/images/admin/'+hash(data)+'.'+ext;await store.putImage(src,ext==='jpg'?'image/jpeg':'image/'+ext,data);response=json({src},201);
    }
    else if(/^\/assets\/images\/admin\/[a-f0-9]{64}\.(png|jpg|webp)$/.test(path) && request.method==='GET'){const image=await store.getImage(path);response=new Response(image.data,{headers:{'Content-Type':image.mime}});}
    if(!response)throw bad('APIがありません',404);
   }
   else if(['GET','HEAD'].includes(request.method)){if(path==='/')url.pathname='/admin/center/';response=await env.ASSETS.fetch(new Request(url,request));}
   else throw bad('この操作は利用できません',405);
  }catch(e){response=json({message:e.status?e.message:'保存または接続に失敗しました。無料枠の上限と設定を確認してください。'},e.status||503);}
  const headers=new Headers(response.headers);headers.set('Cache-Control','no-store');headers.set('X-Content-Type-Options','nosniff');headers.set('X-Frame-Options','DENY');headers.set('X-Robots-Tag','noindex, nofollow');headers.set('Referrer-Policy','no-referrer');headers.set('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'");headers.set('Strict-Transport-Security','max-age=31536000');return new Response(response.body,{status:response.status,headers});
 }};
}
const worker=createWorker();
export default {fetch(request,env,ctx){const pending=worker.fetch(request,env);ctx.waitUntil(pending.then(()=>{}));return pending;}};
