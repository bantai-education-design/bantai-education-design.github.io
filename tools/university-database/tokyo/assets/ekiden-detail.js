/* 大学紹介ページに「駅伝の成績」欄を足す（付録 三大駅伝 出場校検索との連携）
 * データ: ../ekiden/data/teams.json, team_summary.json（daigaku_DB から書き出したもの）
 * 三大駅伝の収録範囲に出場がない大学には何も表示しない。既存の表示処理には手を入れない。
 */
(() => {
  'use strict';
  const id = new URLSearchParams(location.search).get('id');
  if (!id || !/^u\d{6}$/.test(id)) return;
  const BASE = '../ekiden/';
  const SERIES = [['izumo', '出雲駅伝'], ['zennihon', '全日本大学駅伝'], ['hakone', '箱根駅伝']];
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const data = Promise.all(['teams.json', 'team_summary.json'].map((f) =>
    fetch(BASE + 'data/' + f).then((r) => (r.ok ? r.json() : Promise.reject(f))))).catch(() => null);

  function build(team, s) {
    const rows = SERIES.map(([k, name]) => {
      const x = s.series[k];
      const value = x
        ? `${x.appearances}回出場（${x.first_year}〜${x.last_year}年）／最高 ${x.best_rank ? x.best_rank + '位' : '—'}${x.wins ? `／優勝 ${x.wins}回` : ''}`
        : '収録範囲では出場なし';
      return `<div class="ekiden-detail-row"><dt>${name}</dt><dd>${esc(value)}</dd></div>`;
    }).join('');
    const crown = s.triple_crown_seasons
      ? `<p class="ekiden-detail-crown">三冠（出雲・全日本・箱根を同じ年度に優勝）: ${s.triple_crown_seasons.map((y) => `${y}年度`).join('、')}</p>` : '';
    const sec = document.createElement('section');
    sec.className = 'detail-section ekiden-detail';
    sec.innerHTML = `<h2>駅伝の成績</h2>
      <dl class="ekiden-detail-list">${rows}</dl>${crown}
      <p class="ekiden-detail-note">三大駅伝の総合成績を収録した範囲（2006年ごろから最新大会まで）で数えています。出典は各大会の公式記録です。</p>
      <a class="ekiden-detail-link" href="${BASE}?tab=univ&amp;team=${esc(team.id)}">駅伝の年表と順位を見る →</a>`;
    return sec;
  }

  function place(sec) {
    const root = document.querySelector('#detail-root');
    if (!root || root.querySelector('.ekiden-detail')) return true;
    const sections = [...root.querySelectorAll('section.detail-section')];
    if (!sections.length) return false;
    const sources = sections.find((x) => /出典/.test(x.querySelector('h2,h3')?.textContent || ''));
    if (sources) sources.before(sec);
    else sections[sections.length - 1].after(sec);
    return true;
  }

  data.then((d) => {
    if (!d) return;
    const team = d[0].teams.find((t) => t.university_id === id);
    if (!team) return;
    const s = d[1].summary.find((x) => x.team_id === team.id);
    if (!s) return;
    const sec = build(team, s);
    if (place(sec)) return;
    const mo = new MutationObserver(() => { if (place(sec)) mo.disconnect(); });
    mo.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => mo.disconnect(), 15000);
  });
})();
