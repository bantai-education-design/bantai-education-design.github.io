import test from 'node:test';
import assert from 'node:assert/strict';
import {GitHub,allowedPath} from '../src/github.js';
const id='11111111-1111-4111-8111-111111111111';
const article={id,revision:2,title:'新規記事',excerpt:'概要',doc:{type:'doc',content:[{type:'paragraph',content:[{type:'text',text:'本文'}]}]}};
function fake(changed=false){
 const calls=[];let refs=0;
 const gh=new GitHub('test-token',async(url,opt)=>{
  const p=new URL(url).pathname.split('/bantai-education-design.github.io/')[1];
  const b=opt.body?JSON.parse(opt.body):undefined;calls.push({path:p,method:opt.method,body:b});
  let v;
  if(p==='git/ref/heads/main'){refs++;v={object:{sha:changed && refs>1?'base2':'base'}};}
  else if(p==='git/commits/base')v={tree:{sha:'tree-base'}};
  else if(p==='contents/data/columns.json')v={content:Buffer.from(JSON.stringify([{id:'old',url:'/columns/old/',title:'既存記事',content:'原文'}])).toString('base64')};
  else if(p==='git/blobs')v={sha:'blob-'+calls.length};
  else if(p==='git/trees')v={sha:'new-tree'};
  else if(p==='git/commits')v={sha:'new-commit'};
  else if(p==='git/refs')v={};
  else if(p==='pulls')v={html_url:'https://github.com/example/repo/pull/1',number:1};
  else if(p==='pulls/1')v={state:'closed',merged_at:'2026-11-11'};
  else throw Error('unexpected '+p);
  return {ok:true,json:async()=>v};
 });return {gh,calls};
}
const store=()=>({requests:()=>[],event(){},db:{prepare(){return {run(){}};}}});
test('publication appends catalog without touching old entries, only creates branch and PR',async()=>{
 const {gh,calls}=fake();await gh.publish(store(),article,'publish',()=>Buffer.alloc(0));
 const cat=JSON.parse(calls.find(c=>c.path==='git/blobs' && c.body.content.includes('column-managed-')).body.content);assert.equal(cat.length,2);assert.deepEqual(cat[1],{id:'old',url:'/columns/old/',title:'既存記事',content:'原文'});
 const tree=calls.find(c=>c.path==='git/trees').body;assert.equal(tree.base_tree,'tree-base');assert.equal(tree.tree.length,2);assert.ok(tree.tree.every(x=>x.sha));
 const branch=calls.find(c=>c.path==='git/refs').body.ref;assert.ok(branch.startsWith('refs/heads/admin-center/'));assert.equal(calls.find(c=>c.path==='pulls').body.base,'main');
 assert.ok(!calls.some(c=>['PATCH','DELETE','PUT'].includes(c.method)));
});
test('unpublish replaces page, no deletion, original catalog entries preserved',async()=>{
 const {gh,calls}=fake();await gh.publish(store(),article,'unpublish',()=>Buffer.alloc(0));
 assert.equal(JSON.parse(calls.find(c=>c.path==='git/blobs').body.content).length,1);assert.ok(calls.some(c=>c.body?.content?.includes('この記事は非公開です')));assert.ok(!calls.some(c=>c.body?.content===null));
});
test('concurrent main update and pending PR block publication',async()=>{
 const {gh,calls}=fake(true);await assert.rejects(gh.publish(store(),article,'publish',()=>{}),/mainが更新/);assert.ok(!calls.some(c=>c.method==='POST'));
 const s=store();s.requests=()=>[{state:'open',number:1}];const f=fake();f.gh.sync=async()=>{};await assert.rejects(f.gh.publish(s,article,'publish',()=>{}),/未完了/);
});
test('write allowlist rejects source, secrets, other articles and null blob',async()=>{
 const {gh}=fake();for(const path of ['index.html','columns/old/index.html','.env','tools/university-database/tokyo/data/university-images.json','../main']){assert.equal(allowedPath(path),false);await assert.rejects(gh.createPR([{path,content:'x'}],'x','y'),/パス/);}
 await assert.rejects(gh.createPR([{path:'data/columns.json',content:null}],'x','y'),/パス/);
});
test('publication state becomes merged only after GitHub confirms it',async()=>{
 const {gh}=fake();const updates=[],events=[];const s={requests:()=>[{id:'r',state:'open',number:1,url:'https://github.com/example/repo/pull/1',action:'publish',article_id:id,revision:2}],db:{prepare:()=>({run:(...args)=>updates.push(args)})},event:(...args)=>events.push(args)};
 await gh.sync(s);assert.deepEqual(updates,[['merged','r']]);assert.equal(events[0][0],'publication.merged');
});
