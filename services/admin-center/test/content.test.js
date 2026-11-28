import test from 'node:test';
import assert from 'node:assert/strict';
import {renderDoc,validateArticle} from '../src/content.js';
test('all insertion types render, HTML is escaped, unsafe nodes/URLs rejected',()=>{
 const d={type:'doc',content:[{type:'heading',attrs:{level:2},content:[{type:'text',text:'<script>alert(1)</script>'}]},{type:'paragraph',content:[{type:'text',text:'公式',marks:[{type:'link',attrs:{href:'https://example.org/?q="'}}]}]},{type:'table',content:[{type:'tableRow',content:[{type:'tableHeader',content:[{type:'paragraph',content:[{type:'text',text:'値'}]}]},{type:'tableCell',content:[{type:'paragraph'}]}]}]},{type:'chart',attrs:{title:'比較',rows:[{label:'<img>',value:12}]}}]};
 const html=renderDoc(d);assert.match(html,/<table>/);assert.match(html,/<meter/);assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img>'));
 assert.throws(()=>renderDoc({type:'iframe'}));assert.throws(()=>renderDoc({type:'chart',attrs:{rows:[{label:'a',value:-1}]}}));
 assert.throws(()=>validateArticle({title:'',excerpt:'',doc:d}));
});
