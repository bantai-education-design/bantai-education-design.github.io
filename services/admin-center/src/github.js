import {randomUUID} from 'node:crypto';
import {articlePage,imagePaths,escape} from './content.js';
import {digest,legacyPage} from './legacy.js';
export const REPO = 'bantai-education-design/bantai-education-design.github.io';
export class GitHub {
  constructor(token, api = fetch) {this.token=token;this.fetch=api;}
  async request(path, method='GET', body) {
    if(!this.token) throw Object.assign(Error('公開用GitHub接続が未設定です'),{status:503});
    const r = await this.fetch(`https://api.github.com/repos/${REPO}/${path}`,{method,headers:{Authorization:`Bearer ${this.token}`,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(30000),redirect:'error'});
    if(!r.ok) throw Object.assign(Error(`GitHub接続エラー (${r.status})`),{upstreamStatus:r.status});
    return r.json();
  }
  async read(path, ref='main') {
    const r = await this.request(`contents/${path}?ref=${encodeURIComponent(ref)}`);
    return Buffer.from(r.content.replace(/\n/g,''),'base64').toString('utf8');
  }
  async sync(store) {
    for(const r of store.requests().filter(r=>r.state==='open')) {
      const pr = await this.request(`pulls/${r.number}`);
      const state = pr.merged_at ? 'merged' : pr.state;
      if(state !== r.state)store.updateRequestState(r,state);
    }
  }
  async createPR(files,title,body,expectedBase,context={}) {
    // No write endpoint for main, merge, or deletion. Every change is one atomic tree.
    if(files.some(f => f.content === null || !allowedPath(f.path,context))) throw Error('公開対象パスが許可されていません');
    const base = await this.request('git/ref/heads/main');
    if(expectedBase && base.object.sha !== expectedBase) throw Object.assign(Error('mainが更新されました。もう一度申請してください'),{status:409});
    const commit = await this.request(`git/commits/${base.object.sha}`);
    const tree=[];
    for(const f of files) {
      const blob=await this.request('git/blobs','POST',{content:f.content,encoding:f.encoding || 'utf-8'});
      tree.push({path:f.path,mode:'100644',type:'blob',sha:blob.sha});
    }
    const t=await this.request('git/trees','POST',{base_tree:commit.tree.sha,tree});
    const c=await this.request('git/commits','POST',{message:title,tree:t.sha,parents:[base.object.sha]});
    const branch=`admin-center/${randomUUID()}`;
    await this.request('git/refs','POST',{ref:`refs/heads/${branch}`,sha:c.sha});
    return this.request('pulls','POST',{base:'main',head:branch,title,body});
  }
  async publish(store,a,action,loadImage) {
    await this.sync(store);
    if(store.requests().some(r=>r.state==='open')) throw Object.assign(Error('未完了の公開申請があります。先にPRをマージまたは閉じて状態を更新してください'),{status:409});
    // Use the exact same base for the catalog and the commit to avoid a lost update.
    const base=await this.request('git/ref/heads/main');
    const catalog=JSON.parse(await this.read('data/columns.json',base.object.sha));
    if(!Array.isArray(catalog)) throw Error('コラム一覧の形式が不正です');
    const origin=store.origin?.(a.id);
    if(origin) return this.publishLegacy(store,a,action,loadImage,origin,catalog,base.object.sha);
    const slug=`managed-${a.id}`, url=`/columns/${slug}/`, key=`column-${slug}`;
    const next=catalog.filter(x=>x.id!==key);
    if(next.length!==catalog.length && catalog.filter(x=>x.id===key).some(x=>x.url!==url)) throw Error('既存記事との衝突を検出しました');
    if(action==='publish') next.unshift({id:key,slug,title:a.title,category:'日常の気づき',categorySlug:'thoughts',date:new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'}).replaceAll('-','.'),excerpt:a.excerpt,thumbnail:imagePaths(a.doc)[0] || '/assets/images/brand-logo.png',readTime:'',tags:[],url});
    const files=[{path:'data/columns.json',content:JSON.stringify(next,null,2)+'\n'},{path:`columns/${slug}/index.html`,content:action==='publish'?articlePage(a):`<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="robots" content="noindex"><title>非公開 | Ban.Tai</title><h1>この記事は非公開です</h1><a href="/columns/">コラム一覧へ</a></html>`}];
    if(action==='publish') for(const path of imagePaths(a.doc)) files.push({path:path.slice(1),content:loadImage(path).toString('base64'),encoding:'base64'});
    // Recheck main immediately before creating a PR; the base cannot silently change.
    return await this.createPR(files,`コラム${action==='publish'?'公開':'非公開'}申請: ${a.title}`,`管理センターからの申請。記事 ${escape(a.id)} / 下書き第${a.revision}版。\n\nCIと内容・画像権利を確認し、人間の承認後にマージしてください。自動マージは禁止。下書きの他の版は含みません。`,base.object.sha);
  }
  async publishLegacy(store,a,action,loadImage,origin,catalog,base) {
    const current=catalog.find(x=>x.id===origin.entry.id);
    if((current?digest(current):null)!==origin.expectedEntryHash)throw Object.assign(Error('元の記事情報が更新されています。差分を確認して最新版を別の下書きへ再取り込みしてください'),{status:409});
    const path=origin.path || `columns/managed-${a.id}/index.html`;
    if(origin.expectedSourceHash){const currentSource=await this.read(path,base);if(digest(currentSource)!==origin.expectedSourceHash)throw Object.assign(Error('元の記事HTMLが更新されています。上書きを停止しました'),{status:409});}
    const next=catalog.filter(x=>x.id!==origin.entry.id);
    let entry=null;
    if(action==='publish') {
      entry={...(current || origin.entry),title:a.title,excerpt:a.excerpt,url:'/'+path.replace(/index\.html$/,'')};
      delete entry.content;
      // Existing metadata and ordering are retained. Modal-only articles gain a rich article URL.
      const index=current?catalog.findIndex(x=>x.id===current.id):0;next.splice(index,0,entry);
    }
    const html=action==='publish'?(legacyPage(a,origin) || articlePage(a,undefined,{preserved:origin.blocks,title:a.title})):'<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="robots" content="noindex"><title>非公開 | Ban.Tai</title><h1>この記事は非公開です</h1><a href="/columns/">コラム一覧へ</a></html>';
    const files=[{path:'data/columns.json',content:JSON.stringify(next,null,2)+'\n'},{path,content:html}];
    if(action==='publish')for(const image of imagePaths(a.doc))files.push({path:image.slice(1),content:loadImage(image).toString('base64'),encoding:'base64'});
    const pr=await this.createPR(files,`既存コラム${action==='publish'?'更新':'非公開'}申請: ${a.title}`,`既存記事 ${origin.entry.id} / 下書き第${a.revision}版。原本は管理サーバーの非公開履歴に保持し、Git履歴でも確認できます。変換できないレイアウトは原本保持ブロックです。差分・表示・画像権利を確認し、人間の承認後にマージしてください。`,base,{legacyPath:path});
    pr.baseline={expectedEntryHash:entry?digest(entry):null,expectedSourceHash:digest(html)};
    return pr;
  }
}
export function allowedPath(p,context={}) {
  return (p===context.legacyPath && /^columns\/[a-z0-9][a-z0-9-]*\/index\.html$/.test(p)) || /^tools\/university-database\/(tokyo|kanagawa|saitama)\/data\/complete\/u[0-9]{6}\.json$/.test(p) || p==='data/columns.json' || /^columns\/managed-[a-f0-9-]{36}\/index\.html$/.test(p) || /^assets\/images\/admin\/[a-f0-9]{64}\.(png|jpg|webp)$/.test(p) || /^data-source\/admin-proposals\/[a-f0-9-]{36}\.json$/.test(p);
}
