import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createApp,passwordHash} from '../src/server.js';
const doc=text=>({type:'doc',content:[{type:'paragraph',content:[{type:'text',text}]}]});
const article={title:'テスト記事',excerpt:'概要',doc:doc('文章')};
async function fixture(t,options={}){
  const dataDir=mkdtempSync(join(tmpdir(),'bantai-test-'));
  const {server,store}=createApp({origin:'http://localhost',development:true,dataDir,password:passwordHash('test-password'),...options});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  t.after(async()=>{await new Promise(r=>server.close(r));store.db.close();rmSync(dataDir,{recursive:true,force:true});});
  const base=`http://127.0.0.1:${server.address().port}`;let cookie='',csrf='';
  async function request(path,method='GET',body,headers={}){
    const r=await fetch(base+path,{method,headers:{Origin:'http://localhost','Content-Type':'application/json',Cookie:cookie,'X-CSRF-Token':csrf,...headers},body:body===undefined?undefined:JSON.stringify(body)});
    const type=r.headers.get('content-type');const data=type?.includes('application/json')?await r.json():await r.text();return {r,data};
  }
  async function login(){const {r,data}=await request('/api/login','POST',{password:'test-password'});cookie=r.headers.get('set-cookie').split(';')[0];csrf=data.csrf;return r;}
  return {request,login,store,base};
}
test('authentication, origin, CSRF, path protection and logout',async t=>{
  const f=await fixture(t);
  assert.equal((await f.request('/api/articles')).r.status,401);
  assert.equal((await f.request('/assets/images/admin/'+'a'.repeat(64)+'.png')).r.status,401);
  assert.equal((await f.request('/api/login','POST',{password:'wrong'})).r.status,401);
  assert.equal((await f.request('/api/login','POST',{password:'test-password'},{Origin:'https://evil.invalid'})).r.status,403);
  const login=await f.login();assert.match(login.headers.get('set-cookie'),/HttpOnly/);assert.match(login.headers.get('set-cookie'),/SameSite=Strict/);
  assert.equal((await f.request('/api/articles','POST',article,{'X-CSRF-Token':''})).r.status,403);
  assert.equal((await f.request('/services/admin-center/src/server.js')).r.status,404);
  assert.equal((await f.request('/admin/center/../../.git/config')).r.status,404);
  assert.equal((await f.request('/api/logout','POST',{})).r.status,200);
  assert.equal((await f.request('/api/articles')).r.status,401);
});
test('drafts persist, conflicts protect versions, restore makes a new version',async t=>{
  const f=await fixture(t);await f.login();
  const created=(await f.request('/api/articles','POST',article)).data;assert.equal(created.revision,1);
  const updated=(await f.request('/api/articles/'+created.id,'PUT',{...article,title:'変更後',revision:1})).data;assert.equal(updated.revision,2);
  assert.equal((await f.request('/api/articles/'+created.id,'PUT',{...article,revision:1})).r.status,409);
  const restored=(await f.request(`/api/articles/${created.id}/restore`,'POST',{revision:2,target:1})).data;assert.equal(restored.title,article.title);assert.equal(restored.revision,3);
  assert.equal((await f.request(`/api/articles/${created.id}/versions`)).data.length,3);
  assert.equal((await f.request(`/api/articles/${created.id}/restore`,'POST',{revision:2,target:1})).r.status,409);
  const preview=await f.request(`/api/articles/${created.id}/preview`);assert.match(preview.data,/テスト記事/);assert.match(preview.r.headers.get('content-security-policy'),/frame-ancestors 'none'/);
  assert.equal((await f.request(`/api/articles/${created.id}/publish`,'POST',{revision:2})).r.status,409);
  assert.equal((await f.request(`/api/articles/${created.id}/publish`,'POST',{revision:3})).r.status,503);
  assert.equal((await f.request('/api/history')).data.requests.length,0);
  const next=new (f.store.constructor)(f.store.db.location());assert.equal(next.get(created.id).revision,3);next.db.close();
});
test('private image upload signature/size checks and bad content rejection',async t=>{
  const f=await fixture(t);await f.login();
  assert.equal((await f.request('/api/images','POST',{base64:Buffer.from('<svg onload="alert(1)">').toString('base64')})).r.status,400);
  const png='iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR42mP8z8AARMAgYKSAAAMAAgAB9HFkzgAAAABJRU5ErkJggg==';
  const image=(await f.request('/api/images','POST',{base64:png})).data;assert.match(image.src,/\.png$/);assert.equal((await f.request(image.src)).r.status,200);
  assert.equal((await f.request('/api/articles','POST',{...article,doc:{type:'doc',content:[{type:'image',attrs:{src:'https://evil.invalid/a.png'}}]}})).r.status,400);
  const linked={...article,doc:{type:'doc',content:[{type:'paragraph',content:[{type:'text',text:'危険',marks:[{type:'link',attrs:{href:'javascript:alert(1)'}}]}]}]}};
  assert.equal((await f.request('/api/articles','POST',linked)).r.status,400);
  const good={...article,doc:{type:'doc',content:[{type:'image',attrs:{src:image.src,alt:'写真'}},{type:'chart',attrs:{title:'比較',rows:[{label:'A',value:10}]}}]}};
  assert.equal((await f.request('/api/articles','POST',good)).r.status,201);
});
test('login attempts limited and expired sessions rejected',async t=>{
  const f=await fixture(t);for(let i=0;i<5;i++)assert.equal((await f.request('/api/login','POST',{password:'bad'})).r.status,401);
  assert.equal((await f.request('/api/login','POST',{password:'test-password'})).r.status,429);
  f.store.db.exec('DELETE FROM attempts');await f.login();f.store.db.exec('UPDATE sessions SET expires=0');assert.equal((await f.request('/api/articles')).r.status,401);
});
test('university proposals require sources, do not overwrite DB',async t=>{
  const f=await fixture(t);await f.login();const p={region:'tokyo',universityId:'u-test',field:'name',before:'前',after:'後',reason:'公式更新',source:'https://example.org/'};
  assert.equal((await f.request('/api/proposals','POST',{...p,source:'javascript:alert(1)'})).r.status,400);
  assert.equal((await f.request('/api/proposals','POST',p)).r.status,201);
  assert.equal((await f.request('/api/proposals')).data[0].after,'後');
});
test('production requires HTTPS, secure cookies and external storage',()=>{
  assert.throws(()=>createApp({origin:'http://example.org',password:passwordHash('test')}),/HTTPS/);
  assert.throws(()=>createApp({origin:'https://example.org',password:'cleartext'}),/PASSWORD_HASH/);
  assert.throws(()=>createApp({origin:'https://example.org',password:passwordHash('test'),dataDir:process.cwd()}),/リポジトリ外/);
});
test('production login emits a Secure host cookie',async t=>{
 const dataDir=mkdtempSync(join(tmpdir(),'bantai-secure-'));
 const {server,store}=createApp({origin:'https://manage.example.org',dataDir,password:passwordHash('test-password')});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 t.after(async()=>{await new Promise(r=>server.close(r));store.db.close();rmSync(dataDir,{recursive:true,force:true});});
 const r=await fetch(`http://127.0.0.1:${server.address().port}/api/login`,{method:'POST',headers:{Origin:'https://manage.example.org','Content-Type':'application/json'},body:JSON.stringify({password:'test-password'})});
 assert.equal(r.status,200);const cookie=r.headers.get('set-cookie');assert.match(cookie,/^__Host-bantai=/);assert.match(cookie,/; Secure/);assert.ok(!cookie.includes('Domain='));assert.match(r.headers.get('strict-transport-security'),/31536000/);
 assert.throws(()=>createApp({origin:'http://example.org',development:true,dataDir,password:passwordHash('test')}),/loopback/);
});

test('existing article imports are authenticated, idempotent, refreshable and retain origin through restore',async t=>{
 const read=path=>readFileSync(new URL('../../../'+path,import.meta.url),'utf8');
 const gh={request:async()=>({object:{sha:'fixture'}}),read:async path=>read(path)};
 const f=await fixture(t,{github:gh});
 assert.equal((await f.request('/api/legacy/import','POST',{catalogId:'column-waiting-with-children-2026'})).r.status,401);await f.login();
 const a=(await f.request('/api/legacy/import','POST',{catalogId:'column-waiting-with-children-2026'})).data;
 assert.equal(a.legacy.catalogId,'column-waiting-with-children-2026');assert.ok(a.legacy.labels.length>0);
 const again=(await f.request('/api/legacy/import','POST',{catalogId:a.legacy.catalogId})).data;assert.equal(a.id,again.id);
 const edited=(await f.request('/api/articles/'+a.id,'PUT',{...a,title:'編集したタイトル'})).data;assert.equal(edited.legacy.catalogId,a.legacy.catalogId);assert.equal(edited.revision,2);
 const preview=await f.request(`/api/articles/${a.id}/preview`);assert.match(preview.data,/編集したタイトル/);assert.match(preview.data,/thumbnail.png/);
 const restored=(await f.request(`/api/articles/${a.id}/restore`,'POST',{revision:2,target:1})).data;assert.equal(restored.title,a.title);assert.equal(restored.legacy.catalogId,a.legacy.catalogId);
 const fresh=(await f.request('/api/legacy/import','POST',{catalogId:a.legacy.catalogId,fresh:true})).data;assert.notEqual(fresh.id,a.id);assert.ok(f.store.get(a.id));
 assert.equal((await f.request('/api/legacy/import','POST',{catalogId:'nonexistent'})).r.status,400);
});
test('profile apply request includes current validated profile and proposal in one PR',async t=>{
 const original=JSON.parse(readFileSync(new URL('../../../tools/university-database/tokyo/data/complete/u000001.json',import.meta.url)));
 let sent;
 const gh={request:async()=>({object:{sha:'current'}}),read:async()=>JSON.stringify(original),createPR:async(...args)=>{sent=args;return {html_url:'https://github.com/example/repo/pull/2',number:2};}};
 const f=await fixture(t,{github:gh});await f.login();
 const list=(await f.request('/api/universities')).data;assert.ok(list.some(p=>p.id==='u000001'));assert.ok(list.length>=66);
 const proposal=(await f.request('/api/proposals','POST',{region:'tokyo',universityId:'u000001',field:'feature_summary',before:original.feature_summary,after:'テスト説明',reason:'公式出典確認',source:original.official_url,sourceConfirmed:true})).data;
 const result=await f.request(`/api/proposals/${proposal.id}/submit`,'POST',{apply:true});assert.equal(result.r.status,201,JSON.stringify(result.data));assert.equal(sent[0].length,2);assert.equal(sent[3],'current');
 const changed=JSON.parse(sent[0][1].content);assert.equal(changed.feature_summary,'テスト説明');assert.deepEqual(changed.student_counts,original.student_counts);
});
test('successful publish records one request and supports baseline sync metadata',async t=>{
 const gh={publish:async()=>({html_url:'https://github.com/example/repo/pull/3',number:3,baseline:{expectedEntryHash:'entry',expectedSourceHash:'source'}})};
 const f=await fixture(t,{github:gh});await f.login();const a=(await f.request('/api/articles','POST',article)).data;
 const result=await f.request(`/api/articles/${a.id}/publish`,'POST',{revision:1});assert.equal(result.r.status,201,JSON.stringify(result.data));
 assert.equal(f.store.requests().length,1);assert.equal(f.store.requests()[0].number,3);assert.equal(JSON.parse(f.store.db.prepare('SELECT body FROM request_results').get().body).expectedEntryHash,'entry');
});
