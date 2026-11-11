import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,mkdirSync,readFileSync,existsSync,rmSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {runtimeConfig} from '../src/runtime.js';
import {Store} from '../src/store.js';
import {createApp,passwordHash} from '../src/server.js';
import {createBackup,restoreBackup} from '../src/backup.js';
function directory(t){const path=mkdtempSync(join(tmpdir(),'bantai-deploy-'));t.after(()=>rmSync(path,{recursive:true,force:true}));return path;}
test('runtime reads external secret files and rejects ambiguous or unsafe deployment configuration',t=>{
 const root=directory(t),password=join(root,'password'),token=join(root,'token');writeFileSync(password,'fixture-hash\n',{mode:0o600});writeFileSync(token,'fixture-token\n',{mode:0o600});
 const env={ADMIN_ORIGIN:'https://example.invalid',ADMIN_DATA_DIR:root,ADMIN_PASSWORD_HASH_FILE:password,ADMIN_GITHUB_TOKEN_FILE:token,ADMIN_BIND_HOST:'0.0.0.0'};
 const config=runtimeConfig(env);assert.equal(runtimeConfig({...env,ADMIN_ORIGIN:undefined,RENDER_EXTERNAL_URL:'https://fixture.onrender.com/'}).origin,'https://fixture.onrender.com');assert.equal(config.password,'fixture-hash');assert.equal(config.githubToken,'fixture-token');assert.equal(config.host,'0.0.0.0');
 assert.throws(()=>runtimeConfig({...env,ADMIN_PASSWORD_HASH:'other'}),/同時/);assert.throws(()=>runtimeConfig({...env,ADMIN_DEV_HTTP:'1'}),/loopback/);assert.throws(()=>runtimeConfig({...env,PORT:'0'}),/PORT/);assert.throws(()=>runtimeConfig({...env,ADMIN_DATA_DIR:'relative'}),/絶対パス/);
 assert.throws(()=>runtimeConfig({...env,ADMIN_PASSWORD_HASH_FILE:new URL('../package.json',import.meta.url).pathname}),/公開リポジトリ外/);
 writeFileSync(token,'');assert.equal(runtimeConfig(env).githubToken,undefined);
});
test('online backup and staged restore preserve drafts/images and invalidate sessions without overwriting data',async t=>{
 const root=directory(t),live=join(root,'live');mkdirSync(live);mkdirSync(join(live,'images'));const store=new Store(join(live,'admin.sqlite'));t.after(()=>store.db.close());
 const a=store.save(null,0,{title:'大切な下書き',excerpt:'概要',doc:{type:'doc',content:[{type:'paragraph'}]}});store.db.prepare('INSERT INTO sessions VALUES(?,?,?)').run('hash','csrf',Date.now()+10000);
 const image=Buffer.from('immutable image fixture'),name=createHash('sha256').update(image).digest('hex')+'.png';writeFileSync(join(live,'images',name),image);
 const saved=await createBackup(live,join(root,'backup'));store.save(a.id,1,{...a,title:'バックアップ後の更新'});
 const restored=await restoreBackup(saved,join(root,'restored'));const recovered=new Store(join(restored,'admin.sqlite'));
 assert.equal(recovered.get(a.id).title,'大切な下書き');assert.equal(recovered.db.prepare('SELECT count(*) AS n FROM sessions').get().n,0);recovered.db.close();assert.deepEqual(readFileSync(join(restored,'images',name)),image);
 assert.equal(store.get(a.id).title,'バックアップ後の更新');assert.equal(store.db.prepare('SELECT count(*) AS n FROM sessions').get().n,1);
 await assert.rejects(restoreBackup(saved,live),e=>e.code==='EEXIST');await assert.rejects(createBackup(live,saved),e=>e.code==='EEXIST');
 writeFileSync(join(saved,'images',name),'tampered');await assert.rejects(restoreBackup(saved,join(root,'bad-restore')),/整合性/);assert.equal(existsSync(join(root,'bad-restore')),false);
});

test('private data cannot be redirected into the public repository through a symlink',t=>{
 const temp=directory(t),alias=join(temp,'public-alias');symlinkSync(new URL('../../../',import.meta.url).pathname,alias,'dir');
 assert.throws(()=>createApp({origin:'https://example.invalid',dataDir:alias,password:passwordHash('fixture-password')}),/公開リポジトリ外/);
});
