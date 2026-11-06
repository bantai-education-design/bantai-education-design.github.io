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
    let fig = '';
    if (series === 'hakone') {
      fig = courseStrip(r, r.legs.slice(0, 5), r.points.slice(0, 6), '往路（1月2日）大手町 → 芦ノ湖', true)
          + courseStrip(r, r.legs.slice(5), r.points.slice(5), '復路（1月3日）芦ノ湖 → 大手町', false);
    } else {
      fig = courseStrip(r, r.legs, r.points, `${r.points[0]} → ${r.points[r.points.length - 1]}`, false);
    }
    $('#basics-course').innerHTML = fig + (r.course_note ? `<p class="basics-note">${esc(r.course_note)}</p>` : '');
    const hasNote = r.legs.some((l) => l.note);
    const hasDay = r.legs.some((l) => l.day);
    $('#basics-legs').innerHTML = `<thead><tr><th>区間</th>${hasDay ? '<th>日</th>' : ''}<th>スタート</th><th>たすきを渡す場所</th><th class="num">距離</th>${hasNote ? '<th>見どころ</th>' : ''}</tr></thead><tbody>${
      r.legs.map((l) => `<tr><th scope="row">${l.no}区</th>${hasDay ? `<td>${esc(l.day)}</td>` : ''}<td class="wrap">${esc(l.from)}</td><td class="wrap">${esc(l.to)}</td><td class="num">${l.km.toFixed(1)}km</td>${hasNote ? `<td class="wrap">${esc(l.note || '')}</td>` : ''}</tr>`).join('')
    }<tr class="total"><th scope="row">合計</th>${hasDay ? '<td></td>' : ''}<td></td><td></td><td class="num">${r.distance_km.toFixed(1)}km</td>${hasNote ? '<td></td>' : ''}</tr></tbody>`;
    $('#basics-course-src').innerHTML = '出典: ' + r.sources.map((s) => srcLink(s)).join('、');
  }

  // 区間の長さに合わせた帯の図。mountain=true で5区に最高点の印
  function courseStrip(r, legs, points, title, mountain) {
    const W = 760, L = 30, R = 30, y = mountain ? 92 : 62, H = y + 84;
    const total = legs.reduce((a, l) => a + l.km, 0);
    const scale = (W - L - R) / total;
    let x = L, g = `<text x="${L}" y="22" font-size="14" font-weight="700" fill="var(--ink)">${esc(title)}</text><text x="${W - R}" y="22" font-size="12" text-anchor="end" fill="var(--muted)">${Math.round(total * 10) / 10}km</text>`;
    const xs = [x];
    legs.forEach((l, i) => {
      const w = l.km * scale;
      g += `<rect x="${x.toFixed(1)}" y="${y - 7}" width="${(w - 3).toFixed(1)}" height="14" rx="7" fill="${COLOR[r.series]}" fill-opacity="${i % 2 ? 0.55 : 0.9}"/>`;
      g += `<text x="${(x + w / 2).toFixed(1)}" y="${y - 16}" text-anchor="middle" font-size="13" font-weight="700" fill="var(--ink)">${l.no}区</text>`;
      g += `<text x="${(x + w / 2).toFixed(1)}" y="${y + 24}" text-anchor="middle" font-size="12" fill="var(--ink-soft)">${l.km.toFixed(1)}km</text>`;
      if (mountain && l.no === 5) {
        const mx = x + w * 0.55;
        g += `<path d="M${(x + 6).toFixed(1)} ${y - 30} L${mx.toFixed(1)} ${y - 62} L${(x + w - 8).toFixed(1)} ${y - 34} Z" fill="#e9e5d8" stroke="var(--muted)" stroke-width="1.5" stroke-linejoin="round"/>`;
        g += `<circle cx="${mx.toFixed(1)}" cy="${y - 62}" r="3.5" fill="var(--ink)"/><text x="${(mx - 8).toFixed(1)}" y="${y - 70}" text-anchor="end" font-size="11.5" fill="var(--ink)">最高点 標高約874m</text>`;
      }
      x += w;
      xs.push(x);
    });
    points.forEach((p, i) => {
      const px = Math.min(xs[i], W - R);
      const end = i === 0 || i === points.length - 1;
      g += `<circle cx="${px.toFixed(1)}" cy="${y}" r="${end ? 7 : 5}" fill="#fff" stroke="var(--ink)" stroke-width="2"/>`;
      const anchor = i === 0 ? 'start' : i === points.length - 1 ? 'end' : 'middle';
      if (i % 2 && !end) g += `<line x1="${px.toFixed(1)}" y1="${y + 8}" x2="${px.toFixed(1)}" y2="${y + 50}" stroke="var(--line)" stroke-width="1.5"/>`;
      g += `<text x="${(i === 0 ? px - 6 : i === points.length - 1 ? px + 6 : px).toFixed(1)}" y="${y + (i % 2 && !end ? 62 : 44)}" text-anchor="${anchor}" font-size="12" font-weight="${end ? 700 : 400}" fill="var(--ink)">${esc(p)}</text>`;
    });
    return `<svg class="fig course" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(r.name)} ${esc(title)} の区間図">${g}</svg>`;
  }

  // たすきの受け渡しの図（中継線と前方20mの中継ゾーン）
  function relayFigure() {
    const runner = (cx, color, sash) => `<g transform="translate(${cx},0)">
      <circle cx="0" cy="62" r="11" fill="${color}"/>
      <path d="M0 74 L0 112 M0 84 L-16 100 M0 84 L18 94 M0 112 L-14 140 M0 112 L16 138" stroke="${color}" stroke-width="7" stroke-linecap="round" fill="none"/>
      ${sash ? `<path d="M-7 76 L9 108" stroke="#c9a227" stroke-width="6" stroke-linecap="round"/>` : ''}</g>`;
    const W = 720, H = 222, x0 = 270, zone = 260;
    return `<svg class="fig" viewBox="0 0 ${W} ${H}" role="img" aria-label="たすきの受け渡しは中継線から前方20mの中継ゾーンで行う">
      <rect x="20" y="146" width="${W - 40}" height="14" rx="4" fill="#e9e5d8"/>
      <rect x="${x0}" y="40" width="${zone}" height="126" rx="8" fill="var(--gold-soft)" fill-opacity=".75"/>
      <line x1="${x0}" y1="34" x2="${x0}" y2="166" stroke="var(--ink)" stroke-width="3"/>
      <text x="${x0}" y="28" text-anchor="middle" font-size="13" font-weight="700" fill="var(--ink)">中継線</text>
      <text x="${x0 + zone / 2}" y="208" text-anchor="middle" font-size="13" font-weight="700" fill="var(--ink)">中継ゾーン（中継線から前方20m）</text>
      <path d="M${x0 + 4} 182 H${x0 + zone - 4}" stroke="var(--ink)" stroke-width="1.5" marker-end="url(#arr)" marker-start="url(#arr)"/>
      <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--ink)"/></marker></defs>
      ${runner(330, 'var(--ink-soft)', true)}${runner(420, 'var(--ink-soft)', false)}
      <path d="M352 96 Q376 78 400 92" stroke="#c9a227" stroke-width="3" fill="none" stroke-dasharray="5 4" marker-end="url(#arr)"/>
      <text x="376" y="58" text-anchor="middle" font-size="12" fill="var(--ink-soft)">たすき</text>
      <text x="${W - 30}" y="120" text-anchor="end" font-size="13" fill="var(--ink-soft)">進む向き →</text>
      <text x="40" y="70" font-size="12.5" fill="var(--ink-soft)">前の区間の選手</text><text x="40" y="90" font-size="12.5" fill="var(--ink-soft)">が走ってくる</text>
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
