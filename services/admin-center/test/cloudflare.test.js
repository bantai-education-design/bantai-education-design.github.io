import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {D1Store} from '../cloudflare/store.js';
import {createWorker} from '../cloudflare/worker.js';
class Database {
 constructor(){this.db=new DatabaseSync(':memory:');this.db.exec(readFileSync(new URL('../cloudflare/migrations/0001_admin.sql',import.meta.url),'utf8'));}
 prepare(sql){const db=this.db;return {bind(...args){args=args.map(x=>x instanceof ArrayBuffer?new Uint8Array(x):x);return {first:async()=>db.prepare(sql).get(...args)||null,all:async()=>({results:db.prepare(sql).all(...args)}),run:async()=>{const r=db.prepare(sql).run(...args);return {meta:{changes:r.changes}};}};}};}
 async batch(statements){this.db.exec('BEGIN IMMEDIATE');try{const out=[];for(const s of statements)out.push(await s.run());this.db.exec('COMMIT');return out;}catch(e){this.db.exec('ROLLBACK');throw e;}}
}
const body={title:'無料構成の下書き',excerpt:'概要',doc:{type:'doc',content:[{type:'paragraph',content:[{type:'text',text:'本文'}]}]}};
async function fixture(t,{allowed=true}={}){
 const db=new Database();t.after(()=>db.db.close());const root=new URL('../../../',import.meta.url).pathname;
 const gh={request:async()=>({object:{sha:'fixture'}}),read:async path=>readFileSync(resolve(root,path),'utf8'),publish:async()=>({html_url:'https://github.com/example/repo/pull/1',number:1}),createPR:async()=>({html_url:'https://github.com/example/repo/pull/2',number:2}),sync:async()=>{}};
 const fetcher=async(url,options)=>{if(url==='https://github.com/login/oauth/access_token'){assert.ok(options.body.includes('oauth-secret-fixture'));return Response.json({access_token:'user-access-fixture'});}if(url==='https://api.github.com/user')return Response.json({login:allowed?'bantai-education-design':'not-admin'});throw Error('Unexpected fetch '+url);};
 const worker=createWorker({fetcher,githubFactory:()=>gh});
 const env={DB:db,GITHUB_OAUTH_CLIENT_ID:'oauth-client',GITHUB_OAUTH_CLIENT_SECRET:'oauth-secret-fixture',SESSION_SECRET:'fixture-session-secret-with-more-than-32-characters',ADMIN_GITHUB_LOGIN:'bantai-education-design',ADMIN_GITHUB_TOKEN:'publish-secret-fixture',ASSETS:{fetch:async request=>{const path=new URL(request.url).pathname,file=resolve(root,'.'+path);if(!file.startsWith(root)||!existsSync(file))return new Response('missing',{status:404});return new Response(readFileSync(file),{headers:{'content-type':path.endsWith('.json')?'application/json':'text/html'}});}}};
 let cookie='',csrf='';
 async function request(path,method='GET',data,headers={}){return worker.fetch(new Request('https://admin.example.invalid'+path,{method,headers:{Origin:'https://admin.example.invalid','Content-Type':'application/json',Cookie:cookie,'x-csrf-token':csrf,...headers},body:data===undefined?undefined:JSON.stringify(data)}),env);}
 async function login(){
  const start=await request('/auth/login');assert.equal(start.status,302);const state=new URL(start.headers.get('location')).searchParams.get('state');cookie=start.headers.getSetCookie()[0].split(';')[0];assert.match(start.headers.getSetCookie()[0],/SameSite=Lax/);
  const finish=await request('/auth/callback?state='+state+'&code=fixture-code');if(finish.status===303){const headers=finish.headers.getSetCookie();assert.ok(headers.every(h=>!h.includes('user-access-fixture')&&!h.includes('oauth-secret-fixture')));cookie=headers.find(h=>h.startsWith('__Host-bantai=')).split(';')[0];csrf=(await (await request('/api/session')).json()).csrf;}
  return finish;
 }
 return {db,env,request,login,store:new D1Store(db)};
}
test('D1 drafts use atomic revisions, preserve history, restore and prevent concurrent overwrites',async()=>{
 const db=new Database(),s=new D1Store(db);try{let a=await s.save(null,0,body);assert.equal(a.revision,1);a=await s.save(a.id,1,{...body,title:'変更後'});assert.equal(a.revision,2);await assert.rejects(s.save(a.id,1,body),e=>e.status===409);a=await s.restore(a.id,2,1);assert.equal(a.title,body.title);assert.equal(a.revision,3);assert.equal((await s.versions(a.id)).length,3);
 const results=await Promise.allSettled([s.save(a.id,3,{...body,title:'画面A'}),s.save(a.id,3,{...body,title:'画面B'})]);assert.equal(results.filter(r=>r.status==='fulfilled').length,1);assert.equal((await s.get(a.id)).revision,4);
 }finally{db.db.close();}
});
test('GitHub OAuth validates state and the exact administrator, keeps credentials server-side',async t=>{
 const f=await fixture(t);assert.equal((await f.request('/api/articles')).status,401);assert.equal((await f.request('/auth/callback?code=bad&state=bad')).status,403);
 const r=await f.login();assert.equal(r.status,303);assert.match(r.headers.getSetCookie()[0],/HttpOnly/);assert.match(r.headers.getSetCookie()[0],/Secure/);assert.match(r.headers.getSetCookie()[0],/SameSite=Strict/);
 const config=await (await f.request('/api/auth-config')).json();assert.equal(config.provider,'github');assert.equal(config.maxImageBytes,1000000);assert.ok(!JSON.stringify(config).includes('secret-fixture'));
 assert.equal((await f.request('/api/articles','POST',body,{'x-csrf-token':''})).status,403);assert.equal((await f.request('/api/articles','POST',body,{Origin:'https://evil.invalid'})).status,403);
 assert.equal((await f.request('/api/logout','POST',{})).status,200);assert.equal((await f.request('/api/articles')).status,401);
 const denied=await fixture(t,{allowed:false});assert.equal((await denied.login()).status,403);assert.equal(denied.db.db.prepare('SELECT count(*) AS n FROM sessions').get().n,0);
});
test('Workers API saves private drafts/images, publishes PR history and restores original articles',async t=>{
 const f=await fixture(t);await f.login();let r=await f.request('/api/articles','POST',body);assert.equal(r.status,201,await r.clone().text());let a=await r.json();
 r=await f.request(`/api/articles/${a.id}/publish`,'POST',{revision:1});assert.equal(r.status,201);assert.equal((await f.store.requests()).length,1);
 const png='iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR42mP8z8AARMAgYKSAAAMAAgAB9HFkzgAAAABJRU5ErkJggg==';
 const image=await (await f.request('/api/images','POST',{base64:png})).json();r=await f.request(image.src);assert.equal(r.status,200);assert.equal(Buffer.from(await r.arrayBuffer()).toString('base64'),png);
 const other=await fixture(t);assert.equal((await other.request(image.src)).status,401);
 r=await f.request('/api/legacy/import','POST',{catalogId:'column-waiting-with-children-2026'});assert.equal(r.status,201,await r.clone().text());a=await r.json();assert.ok(a.legacy.labels.length>0);
 a=await (await f.request('/api/articles/'+a.id,'PUT',{...a,title:'原本を保持した編集'})).json();assert.equal(a.revision,2);const preview=await f.request(`/api/articles/${a.id}/preview`);assert.match(await preview.text(),/原本を保持した編集/);
 const restored=await (await f.request(`/api/articles/${a.id}/restore`,'POST',{revision:2,target:1})).json();assert.equal(restored.revision,3);assert.ok(restored.title.includes('来られる'));
});
test('D1 lock is exclusive and free-quota errors never report a successful save',async t=>{
 const f=await fixture(t);await f.login();const release=await f.store.acquireLock();await assert.rejects(f.store.acquireLock(),e=>e.status===409);await release();await (await f.store.acquireLock())();
 const original=f.env.DB.batch.bind(f.env.DB);f.env.DB.batch=async()=>{throw Error('D1 quota exceeded');};const response=await f.request('/api/articles','POST',body);assert.equal(response.status,503);assert.equal((await f.store.list()).length,0);f.env.DB.batch=original;
});
