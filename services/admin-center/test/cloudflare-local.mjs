import {execFileSync,spawn} from 'node:child_process';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID,createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const cwd=fileURLToPath(new URL('../',import.meta.url)),cli=resolve(cwd,'node_modules/wrangler/bin/wrangler.js'),state=mkdtempSync(join(tmpdir(),'bantai-cf-local-'));
const common=['--config','cloudflare/wrangler.jsonc','--persist-to',state],env={...process.env,WRANGLER_SEND_METRICS:'false'};
const raw=randomUUID(),hash=createHash('sha256').update(raw).digest('hex'),csrf='local-csrf-fixture';let child;
function wrangler(args){return execFileSync(process.execPath,[cli,...args],{cwd,env,encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout:90000});}
try{
 wrangler(['d1','migrations','apply','bantai-admin-center','--local',...common]);
 wrangler(['d1','execute','bantai-admin-center','--local',...common,'--command',`INSERT INTO sessions VALUES('${hash}','${csrf}',${Date.now()+3600000})`]);
 child=spawn(process.execPath,[cli,'dev','--local',...common,'--ip','127.0.0.1','--port','8791','--var','SESSION_SECRET:local-fixture-secret-with-more-than-32-characters','--var','GITHUB_OAUTH_CLIENT_ID:local-oauth-fixture','--var','GITHUB_OAUTH_CLIENT_SECRET:local-oauth-secret-fixture'],{cwd,env,stdio:['ignore','pipe','pipe']});
 let logs='';child.stdout.on('data',d=>logs+=d);child.stderr.on('data',d=>logs+=d);
 const base='http://127.0.0.1:8791';async function request(path,method='GET',body,authenticated=true){return fetch(base+path,{method,headers:{Origin:base,'Content-Type':'application/json',...(authenticated?{Cookie:'__Host-bantai='+raw,'x-csrf-token':csrf}:{})},body:body===undefined?undefined:JSON.stringify(body),redirect:'manual'});}
 let ready=false;for(let i=0;i<150;i++){try{const r=await request('/healthz');if(r.status===200){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}
 assert.ok(ready,'Local Workers runtime failed: '+logs.slice(-2500));
 const config=await (await request('/api/auth-config')).json();assert.equal(config.provider,'github');assert.equal(config.ready,true);assert.equal((await request('/api/articles','GET',undefined,false)).status,401);
 const signIn=await request('/auth/login','GET',undefined,false);assert.equal(signIn.status,302);assert.ok(signIn.headers.get('location').startsWith('https://github.com/login/oauth/authorize?'));assert.match(signIn.headers.get('set-cookie'),/HttpOnly/);
 let r=await request('/api/articles','POST',{title:'D1 local persistence',excerpt:'fixture',doc:{type:'doc',content:[{type:'paragraph'}]}});assert.equal(r.status,201,await r.clone().text());const a=await r.json();
 r=await request('/api/articles/'+a.id,'PUT',{...a,revision:1,title:'D1 changed'});assert.equal(r.status,200,await r.clone().text());assert.equal((await r.json()).revision,2);
 assert.equal((await request('/api/articles/'+a.id,'PUT',{...a,revision:1})).status,409);
 r=await request(`/api/articles/${a.id}/restore`,'POST',{revision:2,target:1});assert.equal(r.status,200);assert.equal((await r.json()).title,a.title);
 const image=await (await request('/api/images','POST',{base64:'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR42mP8z8AARMAgYKSAAAMAAgAB9HFkzgAAAABJRU5ErkJggg=='})).json();assert.ok(image.src,JSON.stringify(image));assert.equal((await request(image.src)).status,200);assert.equal((await request(image.src,'GET',undefined,false)).status,401);
 assert.equal((await request('/')).status,200);assert.equal((await request('/data/columns.json','GET',undefined,false)).status,404);const universities=await (await request('/api/universities')).json();assert.ok(universities.length>=66);
 assert.equal((await request(`/api/articles/${a.id}/publish`,'POST',{revision:3})).status,503,'unconfigured GitHub publishing must fail closed');
 console.log('Local Workers + real D1 passed: OAuth redirect, auth/CSRF, atomic revisions, restore, private image upload, static app and unconfigured publishing. No cloud resources created.');
}finally{if(child){child.kill('SIGTERM');await new Promise(r=>{if(child.exitCode!==null)return r();child.once('exit',r);setTimeout(r,5000).unref();});}rmSync(state,{recursive:true,force:true});}
