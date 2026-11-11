import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {GitHub} from '../src/github.js';
import {createApp,passwordHash} from '../src/server.js';

// In-memory Git objects exercise the actual branch/tree/commit/PR code without remote writes.
class MemoryGitHub extends GitHub {
  constructor(entry,html){
    super('fixture');this.main='base';this.blobs=new Map();this.refs=new Map();this.commits=new Map([['base',{tree:{sha:'base-tree'}}]]);this.trees=new Map([['base-tree',new Map([['data/columns.json',JSON.stringify([{id:'other',title:'無関係の記事',url:'/columns/other/'},entry])],...(entry.url?[[entry.url.slice(1)+'index.html',html]]:[])])]]);this.prs=[];this.writes=[];
  }
  async request(path,method='GET',body){
    if(method!=='GET')this.writes.push({path,method,body});
    if(path==='git/ref/heads/main')return {object:{sha:this.main}};
    if(path.startsWith('contents/')){
      const pathname=path.slice('contents/'.length).split('?')[0],ref=new URL('https://fixture/'+path).searchParams.get('ref');
      const commit=this.commits.get(ref==='main'?this.main:ref);assert.ok(commit,'read ref must exist');const value=this.trees.get(commit.tree.sha).get(pathname);assert.notEqual(value,undefined,'file must exist: '+pathname);
      return {content:Buffer.from(value).toString('base64')};
    }
    if(path.startsWith('git/commits/') && method==='GET')return this.commits.get(path.slice('git/commits/'.length));
    if(path==='git/blobs' && method==='POST'){const sha='blob-'+this.blobs.size;this.blobs.set(sha,body.encoding==='base64'?Buffer.from(body.content,'base64').toString():body.content);return {sha};}
    if(path==='git/trees' && method==='POST'){const tree=new Map(this.trees.get(body.base_tree));for(const f of body.tree){assert.notEqual(f.sha,null);tree.set(f.path,this.blobs.get(f.sha));}const sha='tree-'+this.trees.size;this.trees.set(sha,tree);return {sha};}
    if(path==='git/commits' && method==='POST'){const sha='commit-'+this.commits.size;this.commits.set(sha,{tree:{sha:body.tree}});return {sha};}
    if(path==='git/refs' && method==='POST'){assert.match(body.ref,/^refs\/heads\/admin-center\//);this.refs.set(body.ref,body.sha);return {};}
    if(path==='pulls' && method==='POST'){assert.equal(body.base,'main');const pr={number:this.prs.length+1,html_url:'https://github.com/example/repo/pull/'+(this.prs.length+1),state:'open',merged_at:null,head:body.head};this.prs.push(pr);return pr;}
    if(/^pulls\/\d+$/.test(path))return this.prs[Number(path.split('/')[1])-1];
    throw Error('Unexpected GitHub operation '+method+' '+path);
  }
  merge(number){const pr=this.prs[number-1];this.main=this.refs.get('refs/heads/'+pr.head);pr.state='closed';pr.merged_at='2026-11-11T00:00:00Z';}
  files(){return this.trees.get(this.commits.get(this.main).tree.sha);}
}
async function fixture(t,entry,html){
 const gh=new MemoryGitHub(entry,html),dataDir=mkdtempSync(join(tmpdir(),'bantai-publication-'));
 const {server,store}=createApp({origin:'http://localhost',development:true,dataDir,password:passwordHash('publication-test'),github:gh});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 t.after(async()=>{await new Promise(r=>server.close(r));store.db.close();rmSync(dataDir,{recursive:true,force:true});});
 const base=`http://127.0.0.1:${server.address().port}`;let cookie='',csrf='';
 async function api(path,method='GET',body){const r=await fetch(base+'/api/'+path,{method,headers:{Origin:'http://localhost','Content-Type':'application/json',Cookie:cookie,'X-CSRF-Token':csrf},body:body===undefined?undefined:JSON.stringify(body)});const data=await r.json();return {status:r.status,data,headers:r.headers};}
 const login=await api('login','POST',{password:'publication-test'});cookie=login.headers.get('set-cookie').split(';')[0];csrf=login.data.csrf;
 return {gh,store,api};
}
const html='<!doctype html><html><head><title>原本</title></head><body><nav>既存ナビ</nav><article><h1>原本</h1><p>元の文章</p><figure><img src="/assets/images/original.png"></figure></article><footer>既存フッター</footer></body></html>';
const entry={id:'column-original',title:'原本',excerpt:'概要',url:'/columns/original/',thumbnail:'/assets/images/original.png',tags:['残す'],content:'モーダル内原文'};
test('legacy article update, merge sync, unpublish, restore and republish preserve originals end to end',async t=>{
 const {gh,store,api}=await fixture(t,entry,html);
 const imported=await api('legacy/import','POST',{catalogId:entry.id});assert.equal(imported.status,201);let a=imported.data;
 a=(await api('articles/'+a.id,'PUT',{...a,title:'更新した題名'})).data;
 const first=await api(`articles/${a.id}/publish`,'POST',{revision:a.revision});assert.equal(first.status,201,JSON.stringify(first.data));assert.equal(store.requests()[0].state,'open');
 assert.equal(gh.files().get('columns/original/index.html'),html,'pending PR must not alter main');
 const duplicate=await api(`articles/${a.id}/publish`,'POST',{revision:a.revision});assert.equal(duplicate.status,409);
 gh.merge(first.data.number);assert.equal((await api('sync','POST',{})).status,200);assert.equal(store.requests()[0].state,'merged');
 const files=gh.files(),published=JSON.parse(files.get('data/columns.json'));assert.equal(published[0].id,'other');assert.equal(published[1].id,entry.id);assert.deepEqual(published[1].tags,entry.tags);assert.equal(published[1].content,undefined);assert.equal(published[1].title,'更新した題名');assert.match(files.get('columns/original/index.html'),/<figure><img src="\/assets\/images\/original.png"><\/figure>/);
 assert.equal(store.origin(a.id).sourceHtml,html);assert.deepEqual(store.origin(a.id).entry,entry);assert.ok(![...files.keys()].some(p=>p.includes('archive')),'originals must not be newly exposed as public backup files');
 const hidden=await api(`articles/${a.id}/unpublish`,'POST',{revision:a.revision});assert.equal(hidden.status,201,JSON.stringify(hidden.data));gh.merge(hidden.data.number);await api('sync','POST',{});
 assert.equal(JSON.parse(gh.files().get('data/columns.json')).length,1);assert.match(gh.files().get('columns/original/index.html'),/非公開/);
 a=(await api(`articles/${a.id}/restore`,'POST',{revision:a.revision,target:1})).data;assert.equal(a.title,'原本');const restored=await api(`articles/${a.id}/publish`,'POST',{revision:a.revision});assert.equal(restored.status,201,JSON.stringify(restored.data));gh.merge(restored.data.number);await api('sync','POST',{});
 assert.equal(gh.files().get('columns/original/index.html'),html);assert.equal(store.origin(a.id).sourceHtml,html);
 assert.ok(gh.writes.every(w=>w.method==='POST'));assert.ok(!gh.writes.some(w=>w.path.includes('/merge')));
});
test('external changes to a legacy source stop publication without any write',async t=>{
 const {gh,api}=await fixture(t,entry,html);const a=(await api('legacy/import','POST',{catalogId:entry.id})).data;
 gh.files().set('columns/original/index.html',html+'<!--外部更新-->');const response=await api(`articles/${a.id}/publish`,'POST',{revision:a.revision});assert.equal(response.status,409);assert.equal(gh.writes.length,0);
});
test('modal-only article gains a rich URL and can be published repeatedly after merge',async t=>{
 const modal={id:'column-modal',title:'本文型',excerpt:'概要',content:'## 見出し\n\n本文\n\n|A|B|\n|--|--|\n|1|2|'};
 const {gh,api}=await fixture(t,modal,null);let a=(await api('legacy/import','POST',{catalogId:modal.id})).data;
 let r=await api(`articles/${a.id}/publish`,'POST',{revision:a.revision});assert.equal(r.status,201);gh.merge(r.data.number);await api('sync','POST',{});
 const published=JSON.parse(gh.files().get('data/columns.json'))[1];assert.equal(published.id,modal.id);assert.match(published.url,/^\/columns\/managed-/);assert.match(gh.files().get(published.url.slice(1)+'index.html'),/<table>/);
 a=(await api('articles/'+a.id,'PUT',{...a,title:'二回目'})).data;r=await api(`articles/${a.id}/publish`,'POST',{revision:a.revision});assert.equal(r.status,201,JSON.stringify(r.data));
});
