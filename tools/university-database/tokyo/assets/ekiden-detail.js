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
  const W_SERIES = [['wzennihon', '全日本大学女子駅伝'], ['wfujisan', '富士山女子駅伝']];
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const TASUKI_MAP = {
    '青山学院大学': { bg: '#006948', stripe: '#ffffff', label: 'フレッシュグリーン' },
    '駒澤大学':     { bg: '#5b2c83', stripe: '#ffffff', label: '藤色（紫）' },
    '早稲田大学':   { bg: '#8e1728', stripe: '#ffffff', label: '臙脂（えんじ）' },
    '中央大学':     { bg: '#c8102e', stripe: '#ffffff', label: '真紅（白C）' },
    '國學院大學':   { bg: '#6d28d9', stripe: '#f59e0b', label: '江戸紫' },
    '順天堂大学':   { bg: '#1e3a8a', stripe: '#dc2626', label: '紺青・赤' },
    '東洋大学':     { bg: '#1e293b', stripe: '#ffffff', label: '鉄紺（てつこん）' },
    '東海大学':     { bg: '#1d4ed8', stripe: '#ffffff', label: '東海ブルー' },
    '城西大学':     { bg: '#eab308', stripe: '#1e3a8a', label: 'イエロー・紺' },
    '創価大学':     { bg: '#dc2626', stripe: '#2563eb', label: '赤・青ストライプ' },
    '帝京大学':     { bg: '#e11d48', stripe: '#ffffff', label: 'ファイヤーレッド' },
    '日本大学':     { bg: '#ec4899', stripe: '#ffffff', label: '桜色（ピンク）' },
    '法政大学':     { bg: '#ea580c', stripe: '#1e3a8a', label: 'オレンジ・紺' },
    '明治大学':     { bg: '#4c1d95', stripe: '#fbbf24', label: '紫紺（しこん）' },
    '立教大学':     { bg: '#6b21a8', stripe: '#ffffff', label: '江戸紫' },
    '大東文化大学': { bg: '#65a30d', stripe: '#ffffff', label: 'ライトグリーン' },
    '日本体育大学': { bg: '#0369a1', stripe: '#ffffff', label: 'コバルトブルー' },
    '山梨学院大学': { bg: '#0284c7', stripe: '#ffffff', label: 'プルシアンブルー' },
    '神奈川大学':   { bg: '#312e81', stripe: '#ffffff', label: 'プラウドブルー' },
    '東京農業大学': { bg: '#15803d', stripe: '#ffffff', label: '松葉緑' },
    '東京国際大学': { bg: '#0f172a', stripe: '#d4a72c', label: 'ネイビー・ゴールド' },
    '中央学院大学': { bg: '#7e22ce', stripe: '#eab308', label: 'パープル・イエロー' },
    '国士舘大学':   { bg: '#1d4ed8', stripe: '#dc2626', label: '青・赤' },
    '専修大学':     { bg: '#14532d', stripe: '#b91c1c', label: '深緑・エンジ' },
    '拓殖大学':     { bg: '#f97316', stripe: '#ffffff', label: 'オレンジ' },
    '亜細亜大学':   { bg: '#0284c7', stripe: '#fde047', label: 'マリンブルー' },
    '駿河台大学':   { bg: '#0369a1', stripe: '#facc15', label: 'ブルー・イエロー' },
    '筑波大学':     { bg: '#7c3aed', stripe: '#ffffff', label: '桐の紫' }
  };
  function getTasuki(name) {
    const clean = String(name || '').trim();
    if (TASUKI_MAP[clean]) return TASUKI_MAP[clean];
    for (const [k, v] of Object.entries(TASUKI_MAP)) {
      if (clean.includes(k) || k.includes(clean)) return v;
    }
    return { bg: '#0f766e', stripe: '#ffffff', label: 'チームカラー' };
  }

  const data = Promise.all(['teams.json', 'team_summary.json', 'women.json'].map((f) =>
    fetch(BASE + 'data/' + f).then((r) => (r.ok ? r.json() : null)).catch(() => null)));

  function buildRows(seriesList, s) {
    return seriesList.map(([k, name]) => {
      const x = s.series[k];
      const bestStr = x && x.best_rank ? (x.best_rank === 1 ? '1位 👑' : x.best_rank + '位') : '—';
      const value = x
        ? `${x.appearances}回出場（${x.first_year}〜${x.last_year}年）／最高 ${bestStr}${x.wins ? `／優勝 ${x.wins}回` : ''}`
        : '収録範囲では出場なし';
      return `<div class="ekiden-detail-row" data-series="${k}"><dt>${name}</dt><dd>${esc(value)}</dd></div>`;
    }).join('');
  }

  function build(team, s, wTeam, wS) {
    const schoolName = (team && team.display_name) || (wTeam && wTeam.display_name) || '';
    const tasuki = getTasuki(schoolName);
    let inner = '';
    if (team && s) {
      const rows = buildRows(SERIES, s);
      const crown = s.triple_crown_seasons
        ? `<p class="ekiden-detail-crown">👑 三冠（出雲・全日本・箱根を同じ年度に優勝）: ${s.triple_crown_seasons.map((y) => `${y}年度`).join('、')}</p>` : '';
      inner += `<dl class="ekiden-detail-list">${rows}</dl>${crown}`;
    }
    if (wTeam && wS) {
      const wRows = buildRows(W_SERIES, wS);
      const wCrown = wS.double_crown_seasons
        ? `<p class="ekiden-detail-crown">👑 二冠（全日本大学女子・富士山女子を同じ年度に優勝）: ${wS.double_crown_seasons.map((y) => `${y}年度`).join('、')}</p>` : '';
      inner += `${team && s ? '<h3 class="ekiden-detail-subhead">女子大学駅伝</h3>' : ''}<dl class="ekiden-detail-list">${wRows}</dl>${wCrown}`;
    }
    const primaryLink = team
      ? `<a class="ekiden-detail-link" href="${BASE}?tab=univ&amp;team=${esc(team.id)}">駅伝の年表と順位を見る →</a>`
      : `<a class="ekiden-detail-link" href="${BASE}?g=women&amp;tab=univ&amp;team=${esc(wTeam.id)}">女子駅伝の年表と順位を見る →</a>`;
    const womenExtraLink = (team && wTeam)
      ? ` <a class="ekiden-detail-link is-women" href="${BASE}?g=women&amp;tab=univ&amp;team=${esc(wTeam.id)}">女子駅伝の年表を見る →</a>` : '';

    const sec = document.createElement('section');
    sec.className = 'detail-section ekiden-detail';
    sec.style.setProperty('--team-bg', tasuki.bg);
    sec.style.setProperty('--team-stripe', tasuki.stripe);
    sec.innerHTML = `<div class="ekiden-detail-head">
        <span class="ekiden-detail-tasuki" aria-hidden="true"></span>
        <h2>駅伝の成績</h2>
        <span class="ekiden-detail-color-pill">たすき色：${esc(tasuki.label)}</span>
      </div>
      ${inner}
      <p class="ekiden-detail-note">三大駅伝・女子大学駅伝の総合成績を収録した範囲（2006年ごろから最新大会まで）で数えています。出典は各大会の公式記録です。</p>
      <div class="ekiden-detail-actions">${primaryLink}${womenExtraLink}</div>`;
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
    const team = d[0] && d[0].teams ? d[0].teams.find((t) => t.university_id === id) : null;
    const s = (team && d[1] && d[1].summary) ? d[1].summary.find((x) => x.team_id === team.id) : null;
    const wTeam = d[2] && d[2].teams ? d[2].teams.find((t) => t.university_id === id) : null;
    const wS = (wTeam && d[2] && d[2].summary) ? d[2].summary.find((x) => x.team_id === wTeam.id) : null;
    if ((!team || !s) && (!wTeam || !wS)) return;
    const sec = build(team, s, wTeam, wS);
    if (place(sec)) return;
    const mo = new MutationObserver(() => { if (place(sec)) mo.disconnect(); });
    mo.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => mo.disconnect(), 15000);
  });
})();
