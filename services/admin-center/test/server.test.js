import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createApp,passwordHash} from '../src/server.js';
const doc=text=>({type:'doc',content:[{type:'paragraph',content:[{type:'text',text}]}]});
const article={title:'テスト記事',excerpt:'概要',doc:doc('文章')};
async function fixture(t){
  const dataDir=mkdtempSync(join(tmpdir(),'bantai-test-'));
  const {server,store}=createApp({origin:'http://localhost',development:true,dataDir,password:passwordHash('test-password')});
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
