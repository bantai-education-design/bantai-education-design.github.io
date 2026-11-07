/* 三大駅伝 出場校検索（大学DBの付録）
 * データ: data/public_export/ekiden/（scripts/ekiden/export_public.py で書き出したもの）
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
    selectTab(['univ', 'race', 'record', 'basics'].includes(p.get('tab')) ? p.get('tab') : 'univ', false);
    loadBasics();
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
      if (on && t.parentElement.scrollWidth > t.parentElement.clientWidth) {
        t.parentElement.scrollLeft = t.offsetLeft - (t.parentElement.clientWidth - t.offsetWidth) / 2;
      }
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

  /* ---------- 駅伝の基本 ---------- */
  const SVGNS = 'http://www.w3.org/2000/svg';
  const COLOR = { izumo: 'var(--izumo)', zennihon: 'var(--zennihon)', hakone: 'var(--hakone)' };
  function loadBasics() {
    getJson('basics.json').then((b) => { S.basics = b; renderBasics(); })
      .catch(() => { $('#tab-basics').hidden = true; $('#panel-basics').innerHTML = ''; });
  }
  function srcLink(src, role) {
    return `<a href="${esc(src.url)}" target="_blank" rel="noopener">${esc(src.name)} ↗</a>${role === 'secondary' ? '（報道による。公式の要項には記載なし）' : ''}`;
  }
  function renderBasics() {
    const B = S.basics;
    const races = B.races;
    const rows = [
      ['時期', (r) => r.month],
      ['スタート', (r) => r.start],
      ['ゴール', (r) => r.finish],
      ['区間数', (r) => `${r.legs_count}区間`],
      ['総距離', (r) => `${r.distance_km}km`],
      ['いちばん長い区間', (r) => { const l = r.legs.reduce((a, b) => (b.km > a.km ? b : a)); return `${l.no}区 ${l.km}km`; }],
      ['いちばん短い区間', (r) => { const l = r.legs.reduce((a, b) => (b.km < a.km ? b : a)); return `${l.no}区 ${l.km}km`; }],
      ['出場チーム', (r) => `${r.teams}チーム`],
      ['走る人数', (r) => r.runners],
      ['シード', (r) => r.seed],
    ];
    $('#basics-compare').innerHTML = `<thead><tr><th></th>${races.map((r) => `<th data-series="${r.series}" class="race-col">${esc(r.name)}</th>`).join('')}</tr></thead><tbody>${
      rows.map(([label, f]) => `<tr><th scope="row">${label}</th>${races.map((r) => `<td>${esc(f(r))}</td>`).join('')}</tr>`).join('')}</tbody>`;

    $('#basics-teams').innerHTML = teamsChart(races);

    document.querySelectorAll('[data-course]').forEach((b) => b.addEventListener('click', () => showCourse(b.dataset.course)));
    showCourse('hakone');

    $('#basics-relay').innerHTML = relayFigure() + `<p class="basics-src">出典: ${srcLink(B.relay_rules.zone.source, B.relay_rules.zone.role)}</p>`;
    $('#basics-kuriage').innerHTML = `<thead><tr><th>大会</th><th>決まり</th><th>出典</th></tr></thead><tbody>${
      SERIES.map((s) => B.relay_rules.kuriage.find((k) => k.series === s)).filter(Boolean).map((k) =>
        `<tr><th scope="row">${SERIES_NAME[k.series]}</th><td class="wrap">${esc(k.text)}</td><td class="wrap">${srcLink(k.source, k.role)}</td></tr>`).join('')}</tbody>`;
    $('#basics-terms').innerHTML = B.terms.map((t) => `<div><dt>${esc(t.term)}</dt><dd>${esc(t.text)}</dd></div>`).join('');
  }

  // 出場チームの内訳（1本の帯が全体）
  function teamsChart(races) {
    const W = 720, L = 130, R = 64, barH = 28, gap = 46, top = 12;
    const max = Math.max(...races.map((r) => r.teams));
    const unit = (W - L - R) / max;
    const shade = [1, 0.62, 0.32];
    let g = '';
    races.forEach((r, i) => {
      const y = top + i * gap;
      g += `<text x="${L - 12}" y="${y + barH / 2 + 5}" text-anchor="end" font-size="14" font-weight="700" fill="var(--ink)">${esc(r.name)}</text>`;
      let x = L;
      r.team_parts.forEach((p, j) => {
        const w = p.n * unit;
        g += `<rect x="${x.toFixed(1)}" y="${y}" width="${(w - 2).toFixed(1)}" height="${barH}" rx="5" fill="${COLOR[r.series]}" fill-opacity="${shade[j]}"><title>${esc(p.label)} ${p.n}</title></rect>`;
        if (w > 26) g += `<text x="${(x + w / 2 - 1).toFixed(1)}" y="${y + barH / 2 + 5}" text-anchor="middle" font-size="13" font-weight="700" fill="${j === 0 ? '#fff' : 'var(--ink)'}">${p.n}</text>`;
        x += w;
      });
      g += `<text x="${(x + 6).toFixed(1)}" y="${y + barH / 2 + 5}" font-size="12" fill="var(--muted)">計${r.teams}</text>`;
    });
    const H = top + races.length * gap - 6;
    const legend = races.map((r) => `<div class="team-legend" data-series="${r.series}"><b>${esc(r.name)}</b><ul>${
      r.team_parts.map((p, j) => `<li><i style="opacity:${shade[j]}"></i>${esc(p.label)} <b>${p.n}</b></li>`).join('')}</ul><p class="basics-note">${esc(r.team_note)}</p></div>`).join('');
    return `<svg class="fig" viewBox="0 0 ${W} ${H}" role="img" aria-label="三大駅伝の出場チームの内訳">${g}</svg><div class="team-legends">${legend}</div>`;
  }

  function showCourse(series) {
    document.querySelectorAll('[data-course]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.course === series));
    const r = S.basics.races.find((x) => x.series === series);
    let fig = courseOverview(r);
    if (series === 'hakone') {
      fig += courseStrip(r, r.legs.slice(0, 5), r.points.slice(0, 6), '往路（1月2日）大手町 → 芦ノ湖', true)
          + courseStrip(r, r.legs.slice(5), r.points.slice(5), '復路（1月3日）芦ノ湖 → 大手町', false);
    } else {
      fig += courseStrip(r, r.legs, r.points, `${r.points[0]} → ${r.points[r.points.length - 1]}`, false);
    }
    $('#basics-course').innerHTML = fig + (r.course_note ? `<p class="basics-note">${esc(r.course_note)}</p>` : '');
    const hasNote = r.legs.some((l) => l.note);
    const hasDay = r.legs.some((l) => l.day);
    $('#basics-legs').innerHTML = `<thead><tr><th>区間</th>${hasDay ? '<th>日</th>' : ''}<th>スタート</th><th>たすきを渡す場所</th><th class="num">距離</th>${hasNote ? '<th>見どころ</th>' : ''}</tr></thead><tbody>${
      r.legs.map((l) => `<tr><th scope="row">${l.no}区</th>${hasDay ? `<td>${esc(l.day)}</td>` : ''}<td class="wrap">${esc(l.from)}</td><td class="wrap">${esc(l.to)}</td><td class="num">${l.km.toFixed(1)}km</td>${hasNote ? `<td class="wrap">${esc(l.note || '')}</td>` : ''}</tr>`).join('')
    }<tr class="total"><th scope="row">合計</th>${hasDay ? '<td></td>' : ''}<td></td><td></td><td class="num">${r.distance_km.toFixed(1)}km</td>${hasNote ? '<td></td>' : ''}</tr></tbody>`;
    $('#basics-course-src').innerHTML = '出典: ' + r.sources.map((s) => srcLink(s)).join('、');
  }

  // 公式コース記載を基に、位置関係と起伏の特徴を簡略化したオリジナル模式図。
  // 道路形状や未公表の標高値を推測しないため、数値地図・標高グラフとは区別して表示する。
  function courseOverview(r) {
    const layouts = {
      izumo: {
        map: [[58,164],[138,139],[231,145],[318,92],[252,47],[151,61],[92,101]],
        short: ['出雲大社','市役所','斐川','平田','鳶巣','ワイナリー','出雲ドーム'],
        profile: 'M426 143 C448 139 461 113 478 124 S510 145 528 137 S560 132 576 128 S607 108 625 126 S656 141 685 132',
        notes: ['1区 浜山公園のアップダウン','5区 細かなアップダウン'],
      },
      zennihon: {
        map: [[83,42],[113,75],[142,108],[172,137],[207,162],[244,185],[281,207],[317,232],[354,254]],
        short: ['熱田神宮','1中継','2中継','3中継','4中継','5中継','6中継','7中継','伊勢神宮'],
        profile: 'M426 126 C442 104 456 147 472 118 S502 98 518 130 S548 146 566 124 S600 131 618 127 S653 129 685 126',
        notes: ['前半 小刻みなアップダウン','後半 比較的フラット'],
      },
      hakone: {
        map: [[54,83],[115,105],[176,126],[239,154],[299,176],[361,213]],
        short: ['大手町','鶴見','戸塚','平塚','小田原','芦ノ湖'],
        profile: 'M426 151 C458 148 485 143 512 139 S553 135 574 137 C590 132 606 72 628 43 C641 72 653 132 670 139 S681 147 688 147',
        notes: ['5区 山上り・最高点 約874m','6区 山下り'],
      },
    };
    const d = layouts[r.series];
    const mapPath = d.map.map((p, i) => `${i ? 'L' : 'M'}${p[0]} ${p[1]}`).join(' ');
    const points = d.map.map((p, i) => {
      const end = i === 0 || i === d.map.length - 1;
      const labelY = p[1] + (i % 2 ? 24 : -12);
      return `<circle cx="${p[0]}" cy="${p[1]}" r="${end ? 7 : 5}" fill="${end ? COLOR[r.series] : '#fff'}" stroke="${COLOR[r.series]}" stroke-width="2.5"/>
        <text x="${p[0]}" y="${labelY}" text-anchor="middle" font-size="10.5" font-weight="${end ? 800 : 600}" fill="var(--ink)">${esc(d.short[i])}</text>`;
    }).join('');
    const direction = r.series === 'hakone'
      ? '<text x="207" y="274" text-anchor="middle" font-size="11" fill="var(--muted)">往路・復路は同じ中継地点を逆向きに結ぶ</text>'
      : '<text x="207" y="274" text-anchor="middle" font-size="11" fill="var(--muted)">スタートからフィニッシュへの位置関係</text>';
    return `<svg class="fig course-overview" viewBox="0 0 760 300" role="img" aria-label="${esc(r.name)}のコース模式地図と高低差の特徴">
      <rect x="1" y="1" width="758" height="298" rx="18" fill="#faf9f5" stroke="var(--line)"/>
      <line x1="392" y1="20" x2="392" y2="280" stroke="var(--line)"/>
      <text x="28" y="31" font-size="14" font-weight="800" fill="var(--ink)">コース模式地図</text>
      <text x="420" y="31" font-size="14" font-weight="800" fill="var(--ink)">高低差の特徴</text>
      <text x="363" y="31" text-anchor="end" font-size="10.5" fill="var(--muted)">上が北</text>
      <path d="M362 51 V38 M357 45 L362 38 L367 45" fill="none" stroke="var(--ink-soft)" stroke-width="1.5"/>
      <path d="${mapPath}" fill="none" stroke="${COLOR[r.series]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity=".8"/>
      ${points}${direction}
      <line x1="426" y1="166" x2="688" y2="166" stroke="var(--line)" stroke-width="1.5"/>
      <path d="${d.profile}" fill="none" stroke="${COLOR[r.series]}" stroke-width="5" stroke-linecap="round"/>
      <text x="426" y="184" font-size="10.5" fill="var(--muted)">スタート</text>
      <text x="688" y="184" text-anchor="end" font-size="10.5" fill="var(--muted)">${r.series === 'hakone' ? '大手町へ' : 'フィニッシュ'}</text>
      ${d.notes.map((n, i) => `<rect x="420" y="${208 + i * 31}" width="280" height="24" rx="12" fill="#fff" stroke="var(--line)"/><text x="434" y="${224 + i * 31}" font-size="11.5" font-weight="700" fill="var(--ink-soft)">${esc(n)}</text>`).join('')}
      <text x="420" y="286" font-size="10.5" fill="var(--muted)">※高さは特徴を示す模式図。縦軸は実測値ではありません。</text>
    </svg>`;
  }

  // 区間の長さに合わせたコース図。mountain=true で5区の標高イメージを添える
  function courseStrip(r, legs, points, title, mountain) {
    const W = 760, L = 38, R = 38, y = mountain ? 118 : 88, H = y + 92;
    const total = legs.reduce((a, l) => a + l.km, 0);
    const scale = (W - L - R) / total;
    const totalLabel = `${Math.round(total * 10) / 10}km`;
    let x = L, g = `<rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="18" fill="#faf9f5" stroke="var(--line)"/>
      <text x="${L}" y="29" font-size="14" font-weight="800" fill="var(--ink)">${esc(title)}</text>
      <rect x="${W - R - 66}" y="13" width="66" height="25" rx="12.5" fill="${COLOR[r.series]}" fill-opacity=".11"/>
      <text x="${W - R - 33}" y="30" font-size="12" font-weight="700" text-anchor="middle" fill="${COLOR[r.series]}">${totalLabel}</text>
      <path d="M${L} ${y} H${W - R}" stroke="var(--line)" stroke-width="8" stroke-linecap="round"/>`;
    const xs = [x];
    legs.forEach((l, i) => {
      const w = l.km * scale;
      const mid = x + w / 2;
      g += `<path d="M${(x + 2).toFixed(1)} ${y} H${(x + w - 2).toFixed(1)}" stroke="${COLOR[r.series]}" stroke-width="8" stroke-linecap="round" opacity="${i % 2 ? .64 : 1}"/>`;
      g += `<circle cx="${mid.toFixed(1)}" cy="${y}" r="15" fill="#fff" stroke="${COLOR[r.series]}" stroke-width="2.5"/>
        <text x="${mid.toFixed(1)}" y="${y + 4.5}" text-anchor="middle" font-size="12" font-weight="800" fill="${COLOR[r.series]}">${l.no}</text>
        <text x="${mid.toFixed(1)}" y="${y - 24}" text-anchor="middle" font-size="12" font-weight="700" fill="var(--ink)">${l.no}区</text>
        <text x="${mid.toFixed(1)}" y="${y + 37}" text-anchor="middle" font-size="11.5" fill="var(--ink-soft)">${l.km.toFixed(1)}km</text>`;
      if (mountain && l.no === 5) {
        const mx = x + w * 0.56;
        g += `<path d="M${(x + 5).toFixed(1)} ${y - 39} Q${(x + w * .25).toFixed(1)} ${y - 47} ${mx.toFixed(1)} ${y - 72} T${(x + w - 4).toFixed(1)} ${y - 43}" fill="none" stroke="${COLOR[r.series]}" stroke-width="2" opacity=".38"/>
          <circle cx="${mx.toFixed(1)}" cy="${y - 72}" r="4" fill="${COLOR[r.series]}"/>
          <text x="${(mx - 7).toFixed(1)}" y="${y - 80}" text-anchor="end" font-size="11" font-weight="700" fill="var(--ink)">最高点 約874m</text>`;
      }
      x += w;
      xs.push(x);
    });
    points.forEach((p, i) => {
      const px = Math.min(xs[i], W - R);
      const end = i === 0 || i === points.length - 1;
      if (end) g += `<circle cx="${px.toFixed(1)}" cy="${y}" r="8" fill="${COLOR[r.series]}" stroke="#fff" stroke-width="3"/>`;
      const anchor = i === 0 ? 'start' : i === points.length - 1 ? 'end' : 'middle';
      if (!end) g += `<line x1="${px.toFixed(1)}" y1="${y + 17}" x2="${px.toFixed(1)}" y2="${y + 50 + (i % 2) * 17}" stroke="var(--line)" stroke-width="1.5"/>`;
      g += `<text x="${(i === 0 ? px - 2 : i === points.length - 1 ? px + 2 : px).toFixed(1)}" y="${y + (end ? 61 : 62 + (i % 2) * 17)}" text-anchor="${anchor}" font-size="11.5" font-weight="${end ? 800 : 500}" fill="var(--ink)">${esc(p)}</text>`;
    });
    return `<svg class="fig course" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(r.name)} ${esc(title)} の区間図">${g}</svg>`;
  }

  // たすきの受け渡しの図（中継線と前方20mの中継ゾーン）
  function relayFigure() {
    const runner = (cx, cy, flip, bib, sash) => `<g transform="translate(${cx},${cy}) scale(${flip ? -1 : 1},1)">
      <circle cx="2" cy="-48" r="12" fill="var(--ink)"/>
      <path d="M-5 -35 Q8 -38 16 -25 L21 1 Q12 13 -3 8 L-14 -18 Q-13 -30 -5 -35Z" fill="${bib}"/>
      <path d="M-10 -24 Q-28 -13 -36 4 M15 -23 Q29 -11 41 -4" fill="none" stroke="var(--ink)" stroke-width="8" stroke-linecap="round"/>
      <path d="M3 8 Q-5 29 -28 46 M12 7 Q26 23 39 44" fill="none" stroke="var(--ink)" stroke-width="9" stroke-linecap="round"/>
      <path d="M-37 4 L-45 9 M41 -4 L49 -1 M-29 46 L-39 49 M39 44 L49 46" stroke="var(--ink)" stroke-width="6" stroke-linecap="round"/>
      <rect x="-1" y="-24" width="13" height="15" rx="2" fill="#fff" opacity=".92"/>
      ${sash ? `<path d="M-10 -29 L17 5" stroke="#d4a719" stroke-width="6" stroke-linecap="round"/>` : ''}</g>`;
    const W = 760, H = 268, x0 = 240, zone = 360;
    return `<svg class="fig" viewBox="0 0 ${W} ${H}" role="img" aria-label="たすきの受け渡しは中継線から前方20mの中継ゾーンで行う">
      <defs><marker id="relay-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--ink)"/></marker></defs>
      <rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="18" fill="#faf9f5" stroke="var(--line)"/>
      <rect x="${x0}" y="45" width="${zone}" height="156" rx="14" fill="var(--gold-soft)"/>
      <text x="${x0 + 18}" y="68" font-size="12" font-weight="800" fill="#876c13">20m 中継ゾーン</text>
      <path d="M28 174 H732" stroke="#ded9ca" stroke-width="22" stroke-linecap="round"/>
      <path d="M28 174 H732" stroke="#fff" stroke-width="2" stroke-dasharray="18 12" opacity=".9"/>
      <line x1="${x0}" y1="35" x2="${x0}" y2="211" stroke="var(--ink)" stroke-width="4"/>
      <rect x="${x0 - 36}" y="14" width="72" height="25" rx="12.5" fill="var(--ink)"/>
      <text x="${x0}" y="31" text-anchor="middle" font-size="12" font-weight="800" fill="#fff">中継線</text>
      ${runner(342, 145, false, 'var(--hakone)', true)}${runner(487, 145, false, '#315c8a', false)}
      <path d="M386 117 Q421 92 452 111" stroke="#d4a719" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="7 7" marker-end="url(#relay-arrow)"/>
      <rect x="374" y="63" width="91" height="26" rx="13" fill="#fff" stroke="var(--line)"/>
      <text x="419.5" y="80" text-anchor="middle" font-size="12" font-weight="700" fill="var(--ink)">たすきを渡す</text>
      <path d="M${x0 + 8} 226 H${x0 + zone - 8}" stroke="var(--ink)" stroke-width="1.5" marker-end="url(#relay-arrow)" marker-start="url(#relay-arrow)"/>
      <text x="${x0 + zone / 2}" y="251" text-anchor="middle" font-size="13" font-weight="800" fill="var(--ink)">中継線から前方20m</text>
      <path d="M635 112 H710" stroke="var(--ink-soft)" stroke-width="2" marker-end="url(#relay-arrow)"/>
      <text x="672" y="101" text-anchor="middle" font-size="11.5" font-weight="700" fill="var(--ink-soft)">進む向き</text>
      <text x="55" y="94" font-size="12" font-weight="700" fill="var(--ink)">前の区間の選手</text>
      <text x="55" y="112" font-size="11.5" fill="var(--ink-soft)">中継線へ走ってくる</text>
    </svg>`;
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
