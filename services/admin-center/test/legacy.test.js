import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {importLegacy,legacyPage,legacyPath,legacyCandidatePath,validateLegacyIdentity,digest} from '../src/legacy.js';
import {renderDoc,validateArticle} from '../src/content.js';
import {applyProfileProposal,profilePath} from '../src/university.js';
const root=new URL('../../../',import.meta.url);
test('all existing articles import without changing source or losing unsupported blocks',()=>{
 const rows=JSON.parse(readFileSync(new URL('data/columns.json',root)));let pages=0,modal=0;
 for(const entry of rows){
  validateLegacyIdentity(entry);const candidate=legacyCandidatePath(entry),path=candidate && existsSync(new URL(candidate,root))?candidate:null,source=path?readFileSync(new URL(path,root),'utf8'):null;
  const {origin,body}=importLegacy(entry,source,path);validateArticle(body,{preserved:origin.blocks,title:body.title});
  assert.ok(body.doc.content.length,entry.id);assert.equal(origin.expectedEntryHash,digest(entry));
  if(source!==null){pages++;assert.equal(legacyPage(body,origin),source,entry.id);assert.equal(origin.expectedSourceHash,digest(source));}
  else{modal++;assert.equal(legacyPage(body,origin),null);assert.ok(renderDoc(body.doc,s=>s,{preserved:origin.blocks,title:body.title}).length);}
  // Arbitrary HTML provided by a client cannot be used as a preserved block.
  assert.throws(()=>renderDoc({type:'doc',content:[{type:'preserved',attrs:{index:999999,html:'<script>bad()</script>'}}]},s=>s,{preserved:origin.blocks}),/原本保持/);
 }
 assert.ok(rows.length>=60);assert.equal(pages+modal,rows.length);
});
test('editing a legacy article preserves its document shell, images and unknown layouts',()=>{
 const source='<!doctype html><html><head><title>元</title><meta name="description" content="概要"></head><body><nav>メニュー</nav><article><h1>元</h1><p>元の本文</p><figure class="custom"><img src="/assets/images/x.png"><figcaption>写真</figcaption></figure></article><footer>フッター</footer></body></html>';
 const entry={id:'column-example',url:'/columns/example/',title:'元',excerpt:'概要'};const {origin,body}=importLegacy(entry,source);
 const changed={...body,title:'新しい題名',excerpt:'新しい概要',doc:structuredClone(body.doc)};
 changed.doc.content.find(x=>x.type==='paragraph' || x.type==='legacyParagraph').content=[{type:'text',text:'変更後<script>'}];
 const html=legacyPage(changed,origin);assert.match(html,/<h1>新しい題名<\/h1>/);assert.match(html,/変更後&lt;script&gt;/);assert.match(html,/<nav>メニュー<\/nav>/);assert.match(html,/<footer>フッター<\/footer>/);assert.match(html,/<figure class="custom"><img src="\/assets\/images\/x.png"><figcaption>写真<\/figcaption><\/figure>/);assert.match(html,/content="新しい概要"/);
 assert.equal(origin.sourceHtml,source);
});
test('university field application preserves unrelated structure, compares old value, records source',()=>{
 const p=JSON.parse(readFileSync(new URL('tools/university-database/tokyo/data/complete/u000001.json',root)));
 const proposal={region:'tokyo',universityId:p.university_id,field:'feature_summary',before:p.feature_summary,after:'テスト用の説明',reason:'公式情報確認',source:p.official_url,sourceConfirmed:true};
 const changed=applyProfileProposal(p,proposal);assert.equal(changed.feature_summary,proposal.after);assert.deepEqual(changed.campuses,p.campuses);assert.deepEqual(changed.academics,p.academics);assert.deepEqual(changed.sources,p.sources);assert.equal(changed.verification.verification_status,'needs_review');assert.match(changed.verification.notes,/出典 https:/);
 assert.throws(()=>applyProfileProposal(p,{...proposal,before:'古い内容'}),e=>e.status===409);assert.throws(()=>applyProfileProposal(p,{...proposal,field:'academics'}),/パイプライン/);assert.throws(()=>applyProfileProposal(p,{...proposal,sourceConfirmed:false}),/確認/);assert.throws(()=>applyProfileProposal(p,{...proposal,field:'admissions_url',before:p.admissions_url,after:'javascript:alert(1)'}));
 assert.throws(()=>profilePath('tokyo','../../main'));assert.equal(profilePath('tokyo','u000001'),'tools/university-database/tokyo/data/complete/u000001.json');
});
