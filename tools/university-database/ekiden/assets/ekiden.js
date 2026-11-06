/* 三大駅伝 出場校検索（大学DBの付録）
 * データ: data/（daigaku_DB の scripts/ekiden/export_public.py で書き出し、そのまま写したもの）
 * URL: ?tab=univ&team=t00001 / ?tab=race&series=hakone&ed=102 / ?tab=record
 */
(() => {
  'use strict';
  const BASE = 'data/';
  const SERIES = ['izumo', 'zennihon', 'hakone'];
  const SERIES_NAME = { izumo: '出雲駅伝', zennihon: '全日本大学駅伝', hakone: '箱根駅伝' };
  const SERIES_SHORT = { izumo: '出雲', zennihon: '全日本', hakone: '箱根' };
  const TYPE_NAME = { national: '国立', public: '公立', private: '私立' };
  const STATUS_NAME = { open: '参考', dnf: '途中棄権', disqualified: '失格', dns: '出走せず' };
  // 公式HPの大学紹介ページ。東京都・埼玉県・神奈川県の大学は同じ詳細ページで大学IDから開ける
  const UNIV_DETAIL = '../tokyo/detail.html?id=';

  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const S = { taikai: [], teams: [], summary: new Map(), results: {}, byTaikai: new Map(), byTeam: new Map(), taikaiById: new Map(), teamById: new Map() };

  const getJson = (f) => fetch(BASE + f).then((r) => { if (!r.ok) throw new Error(f); return r.json(); });

  Promise.all(['manifest.json', 'taikai.json', 'teams.json', 'team_summary.json', ...SERIES.map((s) => `results_${s}.json`)].map(getJson))
    .then(([manifest, taikai, teams, summary, ...results]) => {
      S.manifest = manifest;
      S.taikai = taikai.taikai;
      S.teams = teams.teams;
      summary.summary.forEach((x) => S.summary.set(x.team_id, x));
      S.taikai.forEach((t) => S.taikaiById.set(t.id, t));
      S.teams.forEach((t) => S.teamById.set(t.id, t));
      SERIES.forEach((s, i) => {
        S.results[s] = results[i];
        results[i].results.forEach((r) => {
          if (!S.byTaikai.has(r.taikai_id)) S.byTaikai.set(r.taikai_id, []);
          S.byTaikai.get(r.taikai_id).push(r);
          if (!S.byTeam.has(r.team_id)) S.byTeam.set(r.team_id, []);
          S.byTeam.get(r.team_id).push(r);
        });
      });
      init();
    })
    .catch(() => {
      $('#univ-count').textContent = '読み込みエラー';
      $('#univ-list').innerHTML = '<li class="team-empty">駅伝データを読み込めませんでした。時間をおいて開き直してください。</li>';
    });

  /* ---------- 共通 ---------- */
  function seasonLabel(season) { return `${season}年度`; }
  function appearancesOf(teamId) { return (S.byTeam.get(teamId) || []).filter((r) => r.result_status !== 'dns'); }
  function totalApps(teamId) {
    const sm = S.summary.get(teamId);
    return sm ? Object.values(sm.series).reduce((a, b) => a + b.appearances, 0) : 0;
  }
  function univHref(team) {
    if (!team.university_id) return null;
    return UNIV_DETAIL + encodeURIComponent(team.university_id);
  }
  function rankCell(r) {
    if (!r) return '<span class="dim">—</span>';
    if (r.overall_rank) return `${r.overall_rank}位`;
    return `<span class="status">${esc(STATUS_NAME[r.result_status] || r.result_status)}</span>`;
  }
  function setParams(obj) {
    const p = new URLSearchParams();
    Object.entries(obj).forEach(([k, v]) => { if (v) p.set(k, v); });
    history.replaceState(null, '', `${location.pathname}?${p.toString()}${location.hash}`);
  }

  function init() {
    const m = S.manifest;
    const editions = Object.values(m.coverage).reduce((a, c) => a + c.editions, 0);
    $('#stat-editions').textContent = `${editions}回`;
    $('#stat-teams').textContent = `${m.counts.teams}`;
    $('#stat-linked').textContent = `${m.counts.teams_linked_to_university_db}校`;
    $('#coverage-note').textContent = '総合成績の収録範囲: ' + SERIES.map((s) => {
      const c = m.coverage[s];
      return `${SERIES_NAME[s]} 第${c.from_edition}回（${c.from_year}年）〜第${c.to_edition}回（${c.to_year}年）`;
    }).join('、') + '。大会ごとの優勝校は全回を収録しています。古い回の総合成績は順次追加します。';

    // 年代の選択肢（収録範囲の年から）
    const years = S.taikai.filter((t) => S.byTaikai.has(t.id)).map((t) => t.year);
    for (let d = Math.floor(Math.min(...years) / 10) * 10; d <= Math.max(...years); d += 10) {
      $('#f-decade').insertAdjacentHTML('beforeend', `<option value="${d}">${d}年代</option>`);
    }
    ['北海道', '東北', '関東', '北信越', '東海', '関西', '中国四国', '九州'].filter((r) => S.teams.some((t) => t.region === r)).forEach((r) => {
      $('#f-region').insertAdjacentHTML('beforeend', `<option value="${esc(r)}">${esc(r)}</option>`);
    });
    [...new Set(S.teams.map((t) => t.prefecture).filter(Boolean))].sort().forEach((p) => {
      $('#f-pref').insertAdjacentHTML('beforeend', `<option value="${esc(p)}">${esc(p)}</option>`);
    });

    bindTabs();
    ['#f-series', '#f-decade', '#f-region', '#f-pref', '#f-type', '#f-win', '#f-univonly'].forEach((id) => $(id).addEventListener('change', renderList));
    $('#univ-q').addEventListener('input', renderList);
    $('#univ-search').addEventListener('submit', (e) => { e.preventDefault(); renderList(); const b = $('#univ-list button'); if (b) b.click(); });
    $('#r-series').addEventListener('change', () => { fillEditions(); renderRace(); });
    $('#r-edition').addEventListener('change', renderRace);
    $('#w-series').addEventListener('change', renderWinners);

    fillEditions();
    renderList();
    renderRecord();

    const p = new URLSearchParams(location.search);
    if (p.get('series') && SERIES.includes(p.get('series'))) { $('#r-series').value = p.get('series'); fillEditions(); }
    if (p.get('ed')) $('#r-edition').value = p.get('ed');
    renderRace();
    if (p.get('team') && S.teamById.has(p.get('team'))) showTeam(p.get('team'), false);
    selectTab(['univ', 'race', 'record'].includes(p.get('tab')) ? p.get('tab') : 'univ', false);
  }

  /* ---------- タブ ---------- */
  function bindTabs() {
    const tabs = [...document.querySelectorAll('.ekiden-tabs [role="tab"]')];
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => selectTab(tab.dataset.tab, true));
      tab.addEventListener('keydown', (e) => {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        const next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
        next.focus(); selectTab(next.dataset.tab, true);
      });
    });
  }
  function selectTab(name, push) {
    document.querySelectorAll('.ekiden-tabs [role="tab"]').forEach((t) => {
      const on = t.dataset.tab === name;
      t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1;
      $(`#panel-${t.dataset.tab}`).hidden = !on;
    });
    if (push) {
      if (name === 'race') setParams({ tab: 'race', series: $('#r-series').value, ed: $('#r-edition').value });
      else if (name === 'univ') setParams({ tab: 'univ', team: S.current });
      else setParams({ tab: name });
    }
  }

  /* ---------- 大学から探す ---------- */
  function matches(team, q) {
    if (!q) return true;
    const hay = [team.display_name, ...(team.names_used || []).map((n) => n.name), ...(team.search_aliases || [])].join(' ');
    return hay.includes(q);
  }
  function renderList() {
    const q = $('#univ-q').value.trim();
    const series = $('#f-series').value;
    const decade = $('#f-decade').value ? Number($('#f-decade').value) : null;
    const region = $('#f-region').value;
    const pref = $('#f-pref').value;
    const type = $('#f-type').value;
    const win = $('#f-win').checked;
    const univOnly = $('#f-univonly').checked;
    const rows = S.teams.filter((t) => {
      if (univOnly && t.team_type !== 'university') return false;
      if (region && t.region !== region) return false;
      if (pref && t.prefecture !== pref) return false;
      if (type && t.establishment_type !== type) return false;
      if (!matches(t, q)) return false;
      const apps = appearancesOf(t.id).filter((r) => {
        const tk = S.taikaiById.get(r.taikai_id);
        if (series && tk.series !== series) return false;
        if (decade !== null && (tk.year < decade || tk.year >= decade + 10)) return false;
        return true;
      });
      if (!apps.length) return false;
      if (win && !apps.some((r) => r.overall_rank === 1)) return false;
      return true;
    }).sort((a, b) => totalApps(b.id) - totalApps(a.id) || a.display_name.localeCompare(b.display_name, 'ja'));

    $('#univ-count').textContent = `${rows.length}チーム`;
    const list = $('#univ-list');
    list.setAttribute('aria-busy', 'false');
    list.innerHTML = rows.map((t) => {
      const sm = S.summary.get(t.id);
      const badges = SERIES.filter((s) => sm && sm.series[s]).map((s) =>
        `<span class="badge" data-series="${s}">${SERIES_SHORT[s]} ${sm.series[s].appearances}回</span>`).join('');
      const sub = [t.region && `${t.region}地区`, t.prefecture, TYPE_NAME[t.establishment_type]].filter(Boolean).join('・') || (t.team_type === 'university' ? '大学紹介 準備中' : '選抜・連合チーム');
      return `<li><button type="button" data-team="${t.id}" ${S.current === t.id ? 'aria-current="true"' : ''}><strong>${esc(t.display_name)}</strong><small>${esc(sub)}</small><span class="badges">${badges}</span></button></li>`;
    }).join('') || '<li class="team-empty">条件に合うチームがありません。</li>';
    list.querySelectorAll('button[data-team]').forEach((b) => b.addEventListener('click', () => showTeam(b.dataset.team, true)));
  }

  function showTeam(teamId, push) {
    S.current = teamId;
    const t = S.teamById.get(teamId);
    const sm = S.summary.get(teamId) || { series: {} };
    document.querySelectorAll('#univ-list button').forEach((b) => b.toggleAttribute('aria-current', b.dataset.team === teamId));

    const older = (t.names_used || []).filter((n) => n.name !== t.display_name && !t.display_name.startsWith(n.name));
    const subParts = [t.region && `${t.region}地区`, t.prefecture, TYPE_NAME[t.establishment_type]].filter(Boolean);
    if (older.length) subParts.push('記録上の名前: ' + older.map((n) => `${n.name}（${n.from_year}〜${n.to_year}年）`).join('、'));
    const href = univHref(t);
    let link = '';
    if (href) link = `<a class="univ-link" href="${esc(href)}">${esc(t.display_name)}の大学紹介を見る →</a>`;
    else if (t.team_type === 'university') link = `<span class="univ-link pending">大学紹介 準備中${t.university_id ? '（この都道府県の版を公開したらつながります）' : ''}</span>`;

    const cards = SERIES.map((s) => {
      const x = sm.series[s];
      if (!x) return `<section class="series-card none" data-series="${s}"><h3>${SERIES_NAME[s]}</h3><p class="team-sub">収録範囲では出場なし</p></section>`;
      return `<section class="series-card" data-series="${s}"><h3>${SERIES_NAME[s]}</h3><dl>
        <dt>出場</dt><dd>${x.appearances}回</dd>
        <dt>期間</dt><dd>${x.first_year}〜${x.last_year}年</dd>
        <dt>最高</dt><dd>${x.best_rank ? x.best_rank + '位' : '—'}</dd>
        <dt>優勝</dt><dd>${x.wins ? `${x.wins}回（${x.win_years.join('、')}年）` : 'なし'}</dd></dl></section>`;
    }).join('');
    const crown = sm.triple_crown_seasons ? `<p class="crown">三冠（出雲・全日本・箱根を同じ年度に優勝）: ${sm.triple_crown_seasons.map(seasonLabel).join('、')}</p>` : '';

    // 年度ごとの年表
    const rows = appearancesOf(teamId).concat((S.byTeam.get(teamId) || []).filter((r) => r.result_status === 'dns'));
    const bySeason = new Map();
    rows.forEach((r) => {
      const tk = S.taikaiById.get(r.taikai_id);
      if (!bySeason.has(tk.season)) bySeason.set(tk.season, {});
      bySeason.get(tk.season)[tk.series] = r;
    });
    const seasons = [...bySeason.keys()].sort().reverse();
    const table = `<div class="table-scroll"><table class="race-table compact"><thead><tr><th>年度</th>${SERIES.map((s) => `<th>${SERIES_SHORT[s]}</th>`).join('')}</tr></thead><tbody>${
      seasons.map((y) => `<tr><td>${seasonLabel(y)}</td>${SERIES.map((s) => {
        const r = bySeason.get(y)[s];
        if (!r) return '<td>—</td>';
        const tk = S.taikaiById.get(r.taikai_id);
        return `<td><button type="button" class="link" data-race="${tk.series}|${tk.edition}" title="${SERIES_NAME[s]} 第${tk.edition}回（${tk.year}年）の順位表を見る">${rankCell(r)}</button></td>`;
      }).join('')}</tr>`).join('')}</tbody></table></div>`;

    $('#team-detail').innerHTML = `<h2>${esc(t.display_name)}</h2><p class="team-sub">${esc(subParts.join('　'))}</p>${link}${crown}
      <div class="series-cards">${cards}</div>
      <div class="chart-wrap">${rankChart(bySeason, seasons)}<div class="chart-legend">${SERIES.map((s) => `<span data-series="${s}">${SERIES_SHORT[s]}</span>`).join('')}</div></div>
      ${table}`;
    $('#team-detail').querySelectorAll('[data-race]').forEach((b) => b.addEventListener('click', () => {
      const [s, ed] = b.dataset.race.split('|');
      $('#r-series').value = s; fillEditions(); $('#r-edition').value = ed; renderRace(); selectTab('race', true);
      $('#finder').scrollIntoView({ behavior: 'smooth' });
    }));
    if (push) setParams({ tab: 'univ', team: teamId });
    if (push && matchMedia('(max-width:900px)').matches) $('#team-detail').scrollIntoView({ behavior: 'smooth' });
  }

  // 順位の推移（上ほど上位）。年度を横軸に3大会を重ねる
  function rankChart(bySeason, seasonsDesc) {
    const seasons = [...seasonsDesc].reverse().map(Number);
    if (!seasons.length) return '';
    const W = 640, H = 210, L = 36, R = 12, T = 14, B = 28;
    const minY = seasons[0], maxY = seasons[seasons.length - 1];
    let maxRank = 10;
    bySeason.forEach((v) => Object.values(v).forEach((r) => { if (r.overall_rank) maxRank = Math.max(maxRank, r.overall_rank); }));
    maxRank = Math.ceil(maxRank / 5) * 5;
    const x = (y) => L + (maxY === minY ? (W - L - R) / 2 : (y - minY) / (maxY - minY) * (W - L - R));
    const yy = (rank) => T + (rank - 1) / (maxRank - 1) * (H - T - B);
    const color = { izumo: 'var(--izumo)', zennihon: 'var(--zennihon)', hakone: 'var(--hakone)' };
    let g = '';
    for (let rk = 1; rk <= maxRank; rk += (maxRank > 15 ? 5 : 2)) {
      g += `<line x1="${L}" x2="${W - R}" y1="${yy(rk)}" y2="${yy(rk)}" stroke="#ebe8de"/><text x="${L - 6}" y="${yy(rk) + 4}" font-size="11" text-anchor="end" fill="#6b7280">${rk}位</text>`;
    }
    const step = Math.max(1, Math.ceil((maxY - minY) / 8));
    for (let y = minY; y <= maxY; y += step) g += `<text x="${x(y)}" y="${H - 8}" font-size="11" text-anchor="middle" fill="#6b7280">${y}</text>`;
    SERIES.forEach((s) => {
      const pts = seasons.map((y) => [y, bySeason.get(String(y))?.[s]]).filter(([, r]) => r && r.overall_rank);
      if (!pts.length) return;
      // 出場しなかった年度で線を切る
      let path = '';
      pts.forEach(([y, r], i) => { path += `${i && pts[i - 1][0] === y - 1 ? 'L' : 'M'}${x(y).toFixed(1)},${yy(r.overall_rank).toFixed(1)}`; });
      g += `<path d="${path}" fill="none" stroke="${color[s]}" stroke-width="2.2"/>`;
      g += pts.map(([y, r]) => `<circle cx="${x(y).toFixed(1)}" cy="${yy(r.overall_rank).toFixed(1)}" r="3.4" fill="${color[s]}"><title>${seasonLabel(y)} ${SERIES_NAME[s]} ${r.overall_rank}位</title></circle>`).join('');
    });
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="年度ごとの総合順位の推移">${g}</svg>`;
  }

  /* ---------- 大会と年から探す ---------- */
  function fillEditions() {
    const s = $('#r-series').value;
    const list = S.taikai.filter((t) => t.series === s).sort((a, b) => b.edition - a.edition);
    $('#r-edition').innerHTML = list.map((t) =>
      `<option value="${t.edition}">第${t.edition}回（${t.year}年）${t.status === 'cancelled' ? ' 中止' : S.byTaikai.has(t.id) ? '' : ' 優勝のみ'}</option>`).join('');
  }
  function renderRace() {
    const s = $('#r-series').value;
    const ed = Number($('#r-edition').value);
    const tk = S.taikaiById.get(`${s}-${ed}`);
    if (!tk) return;
    const rows = (S.byTaikai.get(tk.id) || []).slice().sort((a, b) => (a.overall_rank || 999) - (b.overall_rank || 999));
    const facts = [tk.date ? tk.date.replace(/-/g, '/').replace('/', '年').replace('/', '月') + '日' : `${tk.year}年`,
      tk.legs && tk.distance_km ? `${tk.legs}区間 ${tk.distance_km}km` : '', tk.teams_count ? `${tk.teams_count}チーム` : ''].filter(Boolean).join('　');
    const winTeam = tk.winner_team_id && S.teamById.get(tk.winner_team_id);
    $('#race-head').innerHTML = `<h2>${SERIES_NAME[s]} 第${tk.edition}回</h2><p>${esc(facts)}</p>${
      tk.status === 'cancelled' ? '<p>この回は中止されました。</p>' :
      `<p>優勝: ${esc(winTeam ? winTeam.display_name : tk.winner_name)}（${esc(tk.winning_time || '')}）</p>`}
      <p>出典: <a href="${esc(tk.source_url)}" target="_blank" rel="noopener">${SERIES_NAME[s]}公式サイト ↗</a>${tk.note ? '　' + esc(tk.note) : ''}</p>`;
    const hk = s === 'hakone';
    if (!rows.length) {
      $('#race-table').innerHTML = tk.status === 'cancelled' ? '' : '<tbody><tr><td>この回の総合成績は、まだ収録していません（優勝校のみ）。</td></tr></tbody>';
      return;
    }
    $('#race-table').innerHTML = `<thead><tr><th class="num">順位</th><th>チーム</th><th class="num">総合記録</th>${hk ? '<th class="num">往路</th><th class="num">復路</th>' : ''}</tr></thead><tbody>${
      rows.map((r) => {
        const team = S.teamById.get(r.team_id);
        const cls = r.overall_rank === 1 ? 'win' : r.overall_rank ? '' : 'open';
        const legs = hk ? `<td class="num">${r.outbound_rank ? r.outbound_rank + '位 ' : ''}${esc(r.outbound_time || '—')}</td><td class="num">${r.return_rank ? r.return_rank + '位 ' : ''}${esc(r.return_time || '—')}</td>` : '';
        const name = r.name_at_entry !== team.display_name && !team.display_name.startsWith(r.name_at_entry) ? `${esc(r.name_at_entry)}<small class="dim">（今の${esc(team.display_name)}）</small>` : esc(r.name_at_entry);
        return `<tr class="${cls}"><td class="num">${rankCell(r)}</td><td><button type="button" class="link" data-team="${team.id}">${name}</button>${r.note ? `<br><small class="dim">${esc(r.note)}</small>` : ''}</td><td class="num">${esc(r.overall_time || '—')}</td>${legs}</tr>`;
      }).join('')}</tbody>`;
    $('#race-table').querySelectorAll('[data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
    if (!$('#panel-race').hidden) setParams({ tab: 'race', series: s, ed });
  }

  /* ---------- 記録から探す ---------- */
  function renderRecord() {
    const crowns = [];
    S.summary.forEach((sm) => (sm.triple_crown_seasons || []).forEach((y) => crowns.push([y, sm.team_id])));
    crowns.sort((a, b) => a[0] - b[0]);
    $('#triple-list').innerHTML = crowns.map(([y, tid]) => `<li>${seasonLabel(y)} <button type="button" class="link" data-team="${tid}">${esc(S.teamById.get(tid).display_name)}</button></li>`).join('') || '<li>収録範囲ではなし</li>';
    const wins = [...S.summary.values()].map((sm) => ({ tid: sm.team_id, w: SERIES.map((s) => sm.series[s]?.wins || 0) }))
      .filter((x) => x.w.some(Boolean)).sort((a, b) => b.w.reduce((p, q) => p + q) - a.w.reduce((p, q) => p + q));
    $('#wins-table').innerHTML = `<thead><tr><th>チーム</th>${SERIES.map((s) => `<th class="num">${SERIES_SHORT[s]}</th>`).join('')}<th class="num">計</th></tr></thead><tbody>${
      wins.map((x) => `<tr><td><button type="button" class="link" data-team="${x.tid}">${esc(S.teamById.get(x.tid).display_name)}</button></td>${x.w.map((n) => `<td class="num">${n || ''}</td>`).join('')}<td class="num">${x.w.reduce((p, q) => p + q)}</td></tr>`).join('')}</tbody>`;
    document.querySelectorAll('#panel-record [data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
    renderWinners();
  }
  function renderWinners() {
    const s = $('#w-series').value;
    const list = S.taikai.filter((t) => t.series === s).sort((a, b) => b.edition - a.edition);
    $('#winners-table').innerHTML = `<thead><tr><th class="num">回</th><th>年</th><th>優勝</th><th class="num">記録</th></tr></thead><tbody>${
      list.map((t) => {
        const team = t.winner_team_id && S.teamById.get(t.winner_team_id);
        const name = t.status === 'cancelled' ? '<span class="status">中止</span>' : team ? `<button type="button" class="link" data-team="${team.id}">${esc(t.winner_name)}</button>` : esc(t.winner_name || '');
        return `<tr><td class="num">${t.edition}</td><td>${t.year}</td><td>${name}</td><td class="num">${esc(t.winning_time || '')}</td></tr>`;
      }).join('')}</tbody>`;
    $('#winners-table').querySelectorAll('[data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
  }
})();
