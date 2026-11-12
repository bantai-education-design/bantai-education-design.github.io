import {parse,parseFragment} from 'parse5';
import MarkdownIt from 'markdown-it';
import {createHash} from 'node:crypto';
import {renderDoc,escape,safeURL} from './content.js';
export const digest=value=>createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');
const children=n=>n.childNodes || [];
const find=(n,tag)=>n.tagName===tag?n:children(n).map(x=>find(x,tag)).find(Boolean);
const text=n=>n.nodeName==='#text'?n.value:children(n).map(text).join('');
const attr=(n,key)=>n.attrs?.find(a=>a.name===key)?.value;
export function legacyPath(entry) {
  if(!entry.url)return null;
  if(!/^\/columns\/[a-z0-9][a-z0-9-]*\/$/.test(entry.url))throw Error('既存記事のURL形式が未対応です');
  return entry.url.slice(1)+'index.html';
}
export function legacyCandidatePath(entry) {
  if(entry.url)return legacyPath(entry);
  return /^[a-z0-9][a-z0-9-]*$/.test(entry.slug || '')?`columns/${entry.slug}/index.html`:null;
}
export function importLegacy(entry,sourceHtml=null,sourcePath=legacyPath(entry)) {
  if(sourcePath && !/^columns\/[a-z0-9][a-z0-9-]*\/index\.html$/.test(sourcePath))throw Error('原本のパスが不正です');
  if(sourceHtml!==null && sourceHtml.length>2000000)throw Error('記事が大きすぎます');
  const origin={entry,expectedEntryHash:digest(entry),sourceHtml,path:sourcePath,expectedSourceHash:sourceHtml===null?null:digest(sourceHtml),blocks:[]};
  let source,container;
  if(sourceHtml!==null) {
    source=sourceHtml;const dom=parse(source,{sourceCodeLocationInfo:true});container=find(dom,'article') || find(dom,'main');
    if(!container?.sourceCodeLocation?.startTag || !container.sourceCodeLocation.endTag)throw Error('本文範囲を安全に特定できません');
    origin.range=[container.sourceCodeLocation.startTag.endOffset,container.sourceCodeLocation.endTag.startOffset];
    origin.metadata=[];
    function metadata(n){
      const loc=n.sourceCodeLocation;
      if(n.tagName==='title' && loc?.startTag && loc.endTag)origin.metadata.push({start:loc.startTag.endOffset,end:loc.endTag.startOffset,type:'title'});
      if(n.tagName==='meta' && ['description','og:title','og:description'].includes(attr(n,'name') || attr(n,'property'))){const key=attr(n,'name')?'name':'property';origin.metadata.push({start:loc.startOffset,end:loc.endOffset,type:attr(n,key),key});}
      for(const c of children(n))metadata(c);
    }
    metadata(dom);
  } else {
    if(typeof entry.content!=='string')throw Error('本文がありません');
    source=new MarkdownIt({html:false,linkify:false}).render(entry.content);container=parseFragment(source,{sourceCodeLocationInfo:true});
  }
  function preserve(n){
    const loc=n.sourceCodeLocation;if(!loc)throw Error('本文の原本位置が不明です');
    const index=origin.blocks.length;origin.blocks.push({html:source.slice(loc.startOffset,loc.endOffset),label:text(n).trim().slice(0,180) || (n.tagName==='img'?'元の画像':'元のレイアウト'),isTitle:n.tagName==='h1',openHtml:loc.startTag?source.slice(loc.startTag.startOffset,loc.startTag.endOffset):'',closeHtml:loc.endTag?source.slice(loc.endTag.startOffset,loc.endTag.endOffset):''});
    return {type:'preserved',attrs:{index}};
  }
  function inline(n,marks=[]) {
    if(n.nodeName==='#text')return n.value?[{type:'text',text:n.value,...(marks.length?{marks}: {})}]:[];
    if(n.tagName==='br')return [{type:'hardBreak'}];
    let mark;
    if(['strong','b','em','i','s','strike','code','u','a'].includes(n.tagName)) {
      const names={strong:'bold',b:'bold',em:'italic',i:'italic',s:'strike',strike:'strike',code:'code',u:'underline'};
      mark=n.tagName==='a'?{type:'link',attrs:{href:safeURL(attr(n,'href'))}}:{type:names[n.tagName]};
    } else throw Error('preserve');
    return children(n).flatMap(c=>inline(c,[...marks,mark]));
  }
  function block(n) {
    if(n.nodeName==='#text')return n.value.trim()?{type:'paragraph',content:[{type:'text',text:n.value}]}:null;
    if(n.nodeName==='#comment')return preserve(n);
    try {
      if(n.tagName==='p'){
        const content=children(n).flatMap(c=>inline(c)),saved=preserve(n);origin.blocks[saved.attrs.index].kind='paragraph';
        return {type:'legacyParagraph',attrs:{index:saved.attrs.index},content};
      }
      if(['div','section','header','footer','aside'].includes(n.tagName)){
        const saved=preserve(n);origin.blocks[saved.attrs.index].kind='container';
        return {type:'legacyContainer',attrs:{index:saved.attrs.index},content:children(n).map(block).filter(Boolean)};
      }
      if(['h2','h3'].includes(n.tagName))return {type:'heading',attrs:{level:Number(n.tagName[1])},content:children(n).flatMap(c=>inline(c))};
      if(n.tagName==='hr')return {type:'horizontalRule'};
      // Layouts, images, tables and scripts remain exact immutable source blocks.
      return preserve(n);
    }catch{return preserve(n);}
  }
  const doc={type:'doc',content:children(container).map(block).filter(Boolean)};
  if(!doc.content.length)doc.content=[{type:'paragraph'}];
  origin.originalDoc=doc;return {origin,body:{title:entry.title,excerpt:entry.excerpt || '',doc}};
}
export function legacyPage(article,origin) {
  const options={preserved:origin.blocks,title:article.title,originalTitle:origin.entry.title};
  const body=renderDoc(article.doc,s=>s,options);
  if(!origin.sourceHtml)return null;
  if(article.title===origin.entry.title && article.excerpt===(origin.entry.excerpt || '') && JSON.stringify(article.doc)===JSON.stringify(origin.originalDoc))return origin.sourceHtml;
  if(origin.metadata){
    const replacements=[[origin.range[0],origin.range[1],body],...origin.metadata.map(m=>[m.start,m.end,m.type==='title'?escape(article.title)+' | Ban.Tai':`<meta ${m.key}="${m.type}" content="${escape(m.type==='og:title'?article.title:article.excerpt)}">`])];
    let html=origin.sourceHtml;for(const [start,end,value] of replacements.sort((a,b)=>b[0]-a[0]))html=html.slice(0,start)+value+html.slice(end);return html;
  }
  // Compatibility for snapshots made before metadata offsets were recorded.
  let html=origin.sourceHtml.slice(0,origin.range[0])+body+origin.sourceHtml.slice(origin.range[1]);
  const dom=parse(html,{sourceCodeLocationInfo:true}),replacements=[];
  function visit(n){
    if(n.tagName==='title')replacements.push([n.sourceCodeLocation.startTag.endOffset,n.sourceCodeLocation.endTag.startOffset,escape(article.title)+' | Ban.Tai']);
    if(n.tagName==='meta' && ['description','og:title','og:description'].includes(attr(n,'name') || attr(n,'property'))) {
      const key=attr(n,'name')?'name':'property',name=attr(n,key),value=name==='og:title'?article.title:article.excerpt;
      replacements.push([n.sourceCodeLocation.startOffset,n.sourceCodeLocation.endOffset,`<meta ${key}="${name}" content="${escape(value)}">`]);
    }
    for(const c of children(n))visit(c);
  }
  visit(dom);for(const [start,end,value] of replacements.sort((a,b)=>b[0]-a[0]))html=html.slice(0,start)+value+html.slice(end);
  return html;
}
export function validateLegacyIdentity(entry) {
  if(!entry || typeof entry.id!=='string' || !/^[a-z0-9-]{1,150}$/.test(entry.id))throw Error('記事IDが不正です');
  legacyPath(entry);
}
