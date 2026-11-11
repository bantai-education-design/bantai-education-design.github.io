import {execFileSync,spawnSync} from 'node:child_process';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {passwordHash} from '../src/server.js';
const root=fileURLToPath(new URL('../../../',import.meta.url)),image=process.env.ADMIN_IMAGE || 'bantai-admin-center:local';
const prefix='bantai-admin-smoke-'+randomUUID().slice(0,12),temp=mkdtempSync(join(tmpdir(),prefix+'-'));
const env={...process.env,ADMIN_DOMAIN:'admin.example.invalid',ADMIN_SECRET_DIR:temp};for(const k of ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH'])delete env[k];
function docker(...args){return execFileSync('docker',['--host=unix:///var/run/docker.sock',...args],{env,encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout:180000}).trim();}
const password=join(temp,'password-hash'),token=join(temp,'github-token');writeFileSync(password,passwordHash('container-test-password'),{mode:0o444});writeFileSync(token,'',{mode:0o444});
const volumes=[prefix+'-data',prefix+'-backups'];let created=false;
try{
 for(const name of volumes)docker('volume','create','--label','bantai.test=true',name);
 docker('run','--detach','--name',prefix,'--label','bantai.test=true','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=16m','--publish','127.0.0.1::8787','--mount',`type=volume,src=${volumes[0]},dst=/var/lib/bantai-admin`,'--mount',`type=volume,src=${volumes[1]},dst=/var/backups/bantai-admin`,'--mount',`type=bind,src=${password},dst=/run/secrets/password_hash,readonly`,'--mount',`type=bind,src=${token},dst=/run/secrets/github_token,readonly`,'--env','ADMIN_ORIGIN=https://admin.example.invalid','--env','ADMIN_PASSWORD_HASH_FILE=/run/secrets/password_hash','--env','ADMIN_GITHUB_TOKEN_FILE=/run/secrets/github_token',image);created=true;
 const port=JSON.parse(docker('inspect',prefix))[0].NetworkSettings.Ports['8787/tcp'][0].HostPort;
 let base='http://127.0.0.1:'+port;let cookie='',csrf='';
 async function request(path,method='GET',body,headers={}){const r=await fetch(base+path,{method,headers:{Origin:'https://admin.example.invalid','Content-Type':'application/json',Cookie:cookie,'X-CSRF-Token':csrf,...headers},body:body===undefined?undefined:JSON.stringify(body)});return {status:r.status,headers:r.headers,data:await r.json()};}
 async function ready(){for(let i=0;i<100;i++){try{if((await request('/healthz')).status===200)return;}catch{}await new Promise(r=>setTimeout(r,100));}throw Error('Container did not become healthy');}
 await ready();assert.equal(docker('exec',prefix,'id','-u'),'1000');assert.equal((await request('/api/articles')).status,401);
 assert.equal((await request('/api/login','POST',{password:'container-test-password'},{Origin:'https://untrusted.invalid'})).status,403);
 const login=await request('/api/login','POST',{password:'container-test-password'});assert.equal(login.status,200);assert.match(login.headers.get('set-cookie'),/; Secure/);assert.match(login.headers.get('set-cookie'),/HttpOnly/);cookie=login.headers.get('set-cookie').split(';')[0];csrf=login.data.csrf;
 const saved=await request('/api/articles','POST',{title:'Container persistence fixture',excerpt:'fixture',doc:{type:'doc',content:[{type:'paragraph'}]}});assert.equal(saved.status,201);
 docker('restart','--time','120',prefix);base='http://127.0.0.1:'+JSON.parse(docker('inspect',prefix))[0].NetworkSettings.Ports['8787/tcp'][0].HostPort;await ready();const reloaded=await request('/api/articles');assert.equal(reloaded.data[0].id,saved.data.id);assert.equal(reloaded.data[0].title,'Container persistence fixture');
 docker('exec',prefix,'node','src/backup.js','create','/var/lib/bantai-admin','/var/backups/bantai-admin/snapshot');docker('exec',prefix,'node','src/backup.js','restore','/var/backups/bantai-admin/snapshot','/var/backups/bantai-admin/restored');
 const check="const{DatabaseSync}=require('node:sqlite');const db=new DatabaseSync('/var/backups/bantai-admin/restored/admin.sqlite',{readOnly:true});if(db.prepare('SELECT count(*) AS n FROM articles').get().n!==1||db.prepare('SELECT count(*) AS n FROM sessions').get().n!==0)process.exit(1);db.close();";
 docker('exec',prefix,'node','-e',check);
 docker('exec',prefix,'node','-e',"const fs=require('node:fs');for(const p of ['/app/.git','/app/.env','/run/secrets/proxy_ca'])if(fs.existsSync(p))process.exit(1);");
 docker('compose','--file',resolve(root,'services/admin-center/deploy/compose.yml'),'config','--quiet');
 docker('compose','--file',resolve(root,'services/admin-center/deploy/compose.yml'),'--file',resolve(root,'services/admin-center/deploy/compose.existing-proxy.yml'),'config','--quiet');
 docker('run','--rm','--network','none','--env','ADMIN_DOMAIN=admin.example.invalid','--mount',`type=bind,src=${resolve(root,'services/admin-center/deploy/Caddyfile')},dst=/etc/caddy/Caddyfile,readonly`,'caddy:2@sha256:ce773ec7a742ce15ee6bf2bb5f65882b9e2a4487b10733e6f1484f86e6b5d8bc','caddy','validate','--config','/etc/caddy/Caddyfile','--adapter','caddyfile');
 console.log('Container verification passed: non-root, read-only, auth, Secure cookie, restart persistence, backup/staged restore, Compose and HTTPS proxy configuration.');
}catch(e){if(created){try{const r=spawnSync('docker',['--host=unix:///var/run/docker.sock','logs','--tail','20',prefix],{env,encoding:'utf8'});console.error(r.stdout+r.stderr);console.error(docker('inspect','--format','{{json .State}}',prefix));}catch{}}throw e;
}finally{
 if(created){try{docker('rm','--force',prefix);}catch{}}
 for(const name of volumes){try{docker('volume','rm',name);}catch{}}
 rmSync(temp,{recursive:true,force:true});
}
