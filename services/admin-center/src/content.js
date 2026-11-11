export const escape = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function safeURL(value) {
  if (typeof value !== 'string' || value.length > 2000) throw Error('URLが不正です');
  const u = new URL(value);
  if (!['https:', 'http:'].includes(u.protocol) || u.username || u.password) throw Error('http/httpsのURLを指定してください');
  return u.href;
}
export function validateArticle(a) {
  if (!a || typeof a.title !== 'string' || !a.title.trim() || a.title.length > 200) throw Error('タイトルは1〜200文字です');
  if (typeof a.excerpt !== 'string' || a.excerpt.length > 500) throw Error('概要は500文字以内です');
  if (!a.doc || a.doc.type !== 'doc' || JSON.stringify(a.doc).length > 500000) throw Error('本文が不正です');
  renderDoc(a.doc);
  return {title:a.title.trim(), excerpt:a.excerpt, doc:a.doc};
}
export function renderDoc(doc, imageURL = s => s) {
  let count = 0;
  function node(n, depth = 0) {
    if (++count > 10000 || depth > 25 || !n || typeof n !== 'object') throw Error('本文が複雑すぎます');
    const children = () => (n.content || []).map(c => node(c, depth + 1)).join('');
    const attrs = n.attrs || {};
    switch (n.type) {
      case 'doc': return children();
      case 'text': {
        if (typeof n.text !== 'string') throw Error('文章が不正です');
        let s = escape(n.text);
        for (const m of n.marks || []) {
          if (m.type === 'link') s = `<a href="${escape(safeURL(m.attrs?.href))}" rel="noopener noreferrer">${s}</a>`;
          else if (['bold','italic','strike','code','underline'].includes(m.type)) {
            const t = {bold:'strong',italic:'em',strike:'s',code:'code',underline:'u'}[m.type]; s = `<${t}>${s}</${t}>`;
          } else throw Error('未対応の文字装飾です');
        }
        return s;
      }
      case 'heading': {const l = Number(attrs.level); if (![2,3].includes(l)) throw Error('見出しは2または3です'); return `<h${l}>${children()}</h${l}>`;}
      case 'paragraph': return `<p>${children()}</p>`;
      case 'hardBreak': return '<br>';
      case 'horizontalRule': return '<hr>';
      case 'blockquote': return `<blockquote>${children()}</blockquote>`;
      case 'bulletList': return `<ul>${children()}</ul>`;
      case 'orderedList': return `<ol>${children()}</ol>`;
      case 'listItem': return `<li>${children()}</li>`;
      case 'codeBlock': return `<pre><code>${children()}</code></pre>`;
      case 'table': return `<div class="table-scroll"><table>${children()}</table></div>`;
      case 'tableRow': return `<tr>${children()}</tr>`;
      case 'tableCell': case 'tableHeader': {
        if (Number(attrs.colspan || 1) !== 1 || Number(attrs.rowspan || 1) !== 1) throw Error('結合セルは未対応です');
        const t = n.type === 'tableCell' ? 'td' : 'th'; return `<${t}>${children()}</${t}>`;
      }
      case 'image': {
        if (!/^\/assets\/images\/admin\/[a-f0-9]{64}\.(png|jpg|webp)$/.test(attrs.src)) throw Error('管理画面から画像をアップロードしてください');
        return `<figure><img src="${escape(imageURL(attrs.src))}" alt="${escape(attrs.alt || '')}"><figcaption>${escape(attrs.title || '')}</figcaption></figure>`;
      }
      case 'chart': {
        const rows = attrs.rows;
        if (!Array.isArray(rows) || !rows.length || rows.length > 30 || rows.some(r => typeof r.label !== 'string' || r.label.length > 100 || typeof r.value !== 'number' || !Number.isFinite(r.value) || r.value < 0)) throw Error('グラフは30件以内の非負数で指定してください');
        const max = Math.max(1, ...rows.map(r => r.value));
        return `<figure class="chart"><figcaption>${escape(attrs.title || '棒グラフ')}</figcaption>${rows.map(r => `<div class="bar-row"><span>${escape(r.label)}</span><meter min="0" max="${max}" value="${r.value}">${r.value}</meter><b>${r.value}</b></div>`).join('')}</figure>`;
      }
      default: throw Error(`未対応の本文形式: ${String(n.type).slice(0,40)}`);
    }
  }
  return node(doc);
}
export function articlePage(a, imageURL) {
  return `<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(a.title)} | Ban.Tai</title><meta name="description" content="${escape(a.excerpt)}"><link rel="stylesheet" href="/admin/center/content.css"><main class="article"><a href="/columns/">コラム一覧へ</a><h1>${escape(a.title)}</h1>${renderDoc(a.doc, imageURL)}</main></html>`;
}
export function imagePaths(doc) {
  const out = new Set();
  function walk(n) {if(n.type==='image') out.add(n.attrs.src); for(const c of n.content || []) walk(c);}
  walk(doc); return [...out];
}
