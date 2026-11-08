/* 三大駅伝 出場校検索（大学DBの付録）
 * データ: data/public_export/ekiden/（scripts/ekiden/export_public.py で書き出したもの）
 * URL: ?tab=univ&team=t00001 / ?tab=race&series=hakone&ed=102 / ?tab=record
 *      女子は g=women を付ける（第2段階 工程20）: ?g=women&tab=race&series=wfujisan&ed=2025
 *      区間成績を開いた状態: &open=<成績ID>（第2段階 工程21）
 *      予選会: ?tab=race&series=q:hakone&ed=hakone-q-102（大会の値は q:<本大会>、回の値は予選会の大会ID。第2段階 工程22）
 * 選手名は区間成績の表の中だけで見せる。選手名で探す使い方はしない（DATA_POLICY 10-1）
 */
(() => {
  'use strict';
  const BASE = 'data/';
  // 男子（三大駅伝）と女子（2大会）。切り替えると下の SERIES などを差し替える
  const GENDER = {
    men: { series: ['izumo', 'zennihon', 'hakone'],
      name: { izumo: '出雲駅伝', zennihon: '全日本大学駅伝', hakone: '箱根駅伝' },
      short: { izumo: '出雲', zennihon: '全日本', hakone: '箱根' },
      all: '3大会すべて', crownKey: 'triple_crown_seasons', crownName: '三冠', crownHead: '三冠（同じ年度に3大会で優勝）',
      crownLong: '三冠（出雲・全日本・箱根を同じ年度に優勝）', strip: [['izumo', '10月', '6区間 45.1km'], ['zennihon', '11月', '8区間 106.8km'], ['hakone', '1月', '10区間 217.1km']] },
    women: { series: ['wzennihon', 'wfujisan'],
      name: { wzennihon: '全日本大学女子駅伝', wfujisan: '富士山女子駅伝' },
      short: { wzennihon: '全日本女子', wfujisan: '富士山' },
      all: '2大会すべて', crownKey: 'double_crown_seasons', crownName: '二冠', crownHead: '二冠（同じ年度に2大会で優勝）',
      crownLong: '二冠（全日本大学女子駅伝・富士山女子駅伝を同じ年度に優勝）', strip: [['wzennihon', '10月', '6区間 38.0km'], ['wfujisan', '12月', '7区間 43.4km']] },
  };
  // 予選会（第2段階 工程22）。男子・女子のどちらの画面でも使う
  const Q_NAME = { hakone: '箱根駅伝予選会', zennihon: '全日本大学駅伝 地区選考会', wzennihon: '全日本大学女子駅伝 地区代表・記録選考' };
  const Q_SERIES = { men: ['hakone', 'zennihon'], women: ['wzennihon'] };
  const Q = { taikai: new Map(), byTaikai: new Map(), byTeam: new Map(), runners: null };
  let G = 'men';
  let SERIES = GENDER.men.series;
  let SERIES_NAME = GENDER.men.name;
  let SERIES_SHORT = GENDER.men.short;
  const TYPE_NAME = { national: '国立', public: '公立', private: '私立' };
  const STATUS_NAME = { open: '参考', dnf: '途中棄権', disqualified: '失格', dns: '出走せず' };
  // 公式HPの大学紹介ページ。大学IDから詳細ページを開く
  const UNIV_DETAIL = '../tokyo/detail.html?id=';

  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const newState = () => ({ taikai: [], teams: [], summary: new Map(), results: {}, byTaikai: new Map(), byTeam: new Map(), taikaiById: new Map(), teamById: new Map() });
  const DATA = { men: newState(), women: null };
  let S = DATA.men;
  // 基本情報は男女で共用し、切り替え時に選択した側を必ず再描画する
  let BASICS = null;

  // 区間成績（大会ごとに、順位表で初めて開いたときに読む）
  const KUKAN = new Map();  // series -> Promise<{ editions:Set, byResult:Map }>
  const LEG_STATUS = { open: '参考', dnf: '途中棄権', disqualified: '失格' };
  function loadKukan(series) {
    if (!KUKAN.has(series)) {
      KUKAN.set(series, getJson(`kukan_${series}.json`).then((d) => {
        const col = Object.fromEntries(d.columns.map((c, i) => [c, i]));
        const byResult = new Map();
        d.rows.forEach((row) => {
          const o = Object.fromEntries(d.columns.map((c) => [c, row[col[c]]]));
          if (!byResult.has(o.result_id)) byResult.set(o.result_id, []);
          byResult.get(o.result_id).push(o);
        });
        return { editions: new Set(d.editions), byResult };
      }).catch(() => null));
    }
    return KUKAN.get(series);
  }
  function legMarks(r) {
    return [r.leg_awards ? `<span class="leg-mark award" title="区間1位の区間の数">区間賞${r.leg_awards}</span>` : '',
      r.leg_records ? `<span class="leg-mark record" title="区間新記録の区間の数">区間新${r.leg_records}</span>` : ''].join('');
  }
  function legTable(legs) {
    return `<table class="leg-table"><caption class="sr-only">区間成績</caption><thead><tr><th class="num">区間</th><th>選手</th><th class="num">区間順位</th><th class="num">区間記録</th><th>印</th></tr></thead><tbody>${
      legs.map((k) => {
        const rank = k.leg_status === 'ranked' ? `${k.leg_rank}位` : `<span class="status">${LEG_STATUS[k.leg_status] || ''}</span>`;
        const marks = [k.leg_status === 'ranked' && k.leg_rank === 1 ? '<span class="leg-mark award">区間賞</span>' : '',
          k.leg_record ? '<span class="leg-mark record">区間新</span>' : '', k.kuriage ? '<span class="leg-mark">繰り上げ</span>' : ''].join('');
        const name = k.runner_name ? esc(k.runner_name) : '<span class="dim">（名前は確認中）</span>';
        return `<tr><td class="num">${k.leg}区</td><td>${name}</td><td class="num">${rank}</td><td class="num">${esc(k.leg_time || '—')}</td><td>${marks}${k.note ? `<small class="dim">${esc(k.note)}</small>` : ''}</td></tr>`;
      }).join('')}</tbody></table>`;
  }

  const fmtDate = (d) => d.replace(/-/g, '/').replace('/', '年').replace('/', '月') + '日';
  const REGION_ORDER = ['関東', '北海道', '東北', '北信越', '東海', '関西', '中国四国', '九州', '記録'];
  const Q_SHORT = { hakone: '箱根予選会', zennihon: '全日本 選考', wzennihon: '全日本女子 選考' };
  function qLabel(t) {
    const where = t.region ? (t.gender === 'women' ? ` ${t.region}代表` : ` ${t.region}`) : (t.series === 'wzennihon' && t.id.endsWith('-record') ? ' 記録による選考' : '');
    return `第${t.edition}回（${t.year}年）${where}`;
  }
  function qResultText(r) {
    return r.qualified ? '<span class="q-pass">通過</span>' : (r.result_status === 'dns' ? '' : '<span class="q-fail">通過ならず</span>');
  }
  function loadQRunners() {
    if (!Q.runners) {
      Q.runners = getJson('qualifier_runners.json').then((d) => {
        const m = new Map();
        d.rows.forEach((row) => {
          const o = Object.fromEntries(d.columns.map((c, i) => [c, row[i]]));
          if (!m.has(o.result_id)) m.set(o.result_id, []);
          m.get(o.result_id).push(o);
        });
        return m;
      }).catch(() => null);
    }
    return Q.runners;
  }

  const getJson = (f) => fetch(BASE + f).then((r) => { if (!r.ok) throw new Error(f); return r.json(); });

  function fill(st, series, taikai, teams, summary, results) {
    st.taikai = taikai;
    st.teams = teams;
    summary.forEach((x) => st.summary.set(x.team_id, x));
    st.taikai.forEach((t) => st.taikaiById.set(t.id, t));
    st.teams.forEach((t) => st.teamById.set(t.id, t));
    series.forEach((s, i) => {
      st.results[s] = results[i];
      results[i].results.forEach((r) => {
        if (!st.byTaikai.has(r.taikai_id)) st.byTaikai.set(r.taikai_id, []);
        st.byTaikai.get(r.taikai_id).push(r);
        if (!st.byTeam.has(r.team_id)) st.byTeam.set(r.team_id, []);
        st.byTeam.get(r.team_id).push(r);
      });
    });
    return st;
  }
  // 女子のデータは、女子に切り替えたときに読む
  function loadWomen() {
    if (DATA.women) return Promise.resolve(DATA.women);
    return Promise.all(['women.json', ...GENDER.women.series.map((s) => `results_${s}.json`)].map(getJson)).then(([w, ...results]) => {
      const st = fill(newState(), GENDER.women.series, w.taikai, w.teams, w.summary, results);
      st.manifest = { coverage: w.coverage, counts: w.counts };
      DATA.women = st;
      return st;
    });
  }

  Promise.all(['manifest.json', 'taikai.json', 'teams.json', 'team_summary.json', 'qualifiers.json', ...SERIES.map((s) => `results_${s}.json`)].map(getJson))
    .then(([manifest, taikai, teams, summary, qual, ...results]) => {
      fill(S, SERIES, taikai.taikai, teams.teams, summary.summary, results);
      qual.taikai.forEach((t) => Q.taikai.set(t.id, t));
      qual.results.forEach((r) => {
        if (!Q.byTaikai.has(r.taikai_id)) Q.byTaikai.set(r.taikai_id, []);
        Q.byTaikai.get(r.taikai_id).push(r);
        if (!Q.byTeam.has(r.team_id)) Q.byTeam.set(r.team_id, []);
        Q.byTeam.get(r.team_id).push(r);
      });
      S.manifest = manifest;
      const g = new URLSearchParams(location.search).get('g') === 'women' ? 'women' : 'men';
      if (g === 'women') loadWomen().then(() => init('women')).catch(loadError);
      else init('men');
    })
    .catch(loadError);
  function loadError() {
    $('#univ-count').textContent = '読み込みエラー';
    $('#univ-list').innerHTML = '<li class="team-empty">駅伝データを読み込めませんでした。時間をおいて開き直してください。</li>';
  }

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
  // 富士山女子駅伝は回ではなく年で呼ぶ（大会IDも年）
  function edOf(tk) { return tk.edition ?? tk.year; }
  function raceTitle(tk) { return tk.series === 'wfujisan' ? `${SERIES_NAME[tk.series]} ${tk.year}年` : `${SERIES_NAME[tk.series]} 第${tk.edition}回`; }
  function edLabel(tk) { return tk.series === 'wfujisan' ? `${tk.year}年` : `第${tk.edition}回（${tk.year}年）`; }
  function setParams(obj) {
    const p = new URLSearchParams();
    if (G === 'women') p.set('g', 'women');
    Object.entries(obj).forEach(([k, v]) => { if (v) p.set(k, v); });
    history.replaceState(null, '', `${location.pathname}?${p.toString()}${location.hash}`);
  }

  // 男子・女子を切り替える。画面の選択肢・集計を選んだ側のデータで作り直す
  function applyGender(g) {
    G = g;
    S = DATA[g];
    const cfg = GENDER[g];
    ({ series: SERIES, name: SERIES_NAME, short: SERIES_SHORT } = cfg);
    S.current = S.current || null;
    document.querySelectorAll('.gender-switch [data-gender]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.gender === g));
    document.body.dataset.gender = g;
    $('#series-strip').innerHTML = cfg.strip.map(([s, m, d]) => `<li data-series="${s}"><span>${m}</span><strong>${SERIES_NAME[s]}</strong><small>${d}</small></li>`).join('');
    const m = S.manifest;
    const editions = Object.values(m.coverage).reduce((a, c) => a + c.editions, 0);
    $('#stat-editions').textContent = `${editions}回`;
    $('#stat-teams').textContent = `${m.counts.teams}`;
    $('#stat-linked').textContent = `${m.counts.teams_linked_to_university_db}校`;
    $('#coverage-note').textContent = '総合成績の収録範囲: ' + SERIES.map((s) => {
      const c = m.coverage[s];
      return s === 'wfujisan' ? `${SERIES_NAME[s]} ${c.from_year}年〜${c.to_year}年のうち${c.editions}回（結果の資料がある年）`
        : `${SERIES_NAME[s]} 第${c.from_edition}回（${c.from_year}年）〜第${c.to_edition}回（${c.to_year}年）`;
    }).join('、') + '。大会ごとの優勝校は全回を収録しています。古い回の総合成績は順次追加します。';

    const opts = (list) => list.map((s) => `<option value="${s}">${SERIES_NAME[s]}</option>`).join('');
    $('#f-series').innerHTML = `<option value="">${cfg.all}</option>` + opts(SERIES) + '<option value="q">予選会に出た</option>';
    const raceOrder = g === 'men' ? ['hakone', 'zennihon', 'izumo'] : SERIES;
    $('#r-series').innerHTML = opts(raceOrder) + `<optgroup label="予選会">${Q_SERIES[g].map((s) => `<option value="q:${s}">${Q_NAME[s]}</option>`).join('')}</optgroup>`;
    $('#w-series').innerHTML = opts(raceOrder);
    $('#crown-head').textContent = cfg.crownHead;
    // 年代の選択肢（収録範囲の年から）
    const years = S.taikai.filter((t) => S.byTaikai.has(t.id)).map((t) => t.year);
    $('#f-decade').innerHTML = '<option value="">すべての年</option>';
    for (let d = Math.floor(Math.min(...years) / 10) * 10; d <= Math.max(...years); d += 10) {
      $('#f-decade').insertAdjacentHTML('beforeend', `<option value="${d}">${d}年代</option>`);
    }
    $('#f-region').innerHTML = '<option value="">すべて</option>';
    ['北海道', '東北', '関東', '北信越', '東海', '関西', '中国四国', '九州'].filter((r) => S.teams.some((t) => t.region === r)).forEach((r) => {
      $('#f-region').insertAdjacentHTML('beforeend', `<option value="${esc(r)}">${esc(r)}</option>`);
    });
    $('#f-region').value = '';
    $('#f-region').closest('label').style.display = g === 'women' ? 'none' : '';  // 女子は地区の公式資料がまだない
    $('#f-pref').innerHTML = '<option value="">すべて</option>';
    [...new Set(S.teams.map((t) => t.prefecture).filter(Boolean))].sort().forEach((p) => {
      $('#f-pref').insertAdjacentHTML('beforeend', `<option value="${esc(p)}">${esc(p)}</option>`);
    });
    $('#basics-women').hidden = g !== 'women';
    if (BASICS) {
      S.basics = BASICS;
      renderBasics();
    }
    fillEditions();
    renderList();
    renderRecord();
    renderRace();
    if (S.current && S.teamById.has(S.current)) showTeam(S.current, false);
    else $('#team-detail').innerHTML = `<div class="team-empty">左の一覧から大学を選ぶと、${SERIES.length}大会の成績が年表で表示されます。</div>`;
  }

  function init(g) {
    bindTabs();
    document.querySelectorAll('.gender-switch [data-gender]').forEach((b) => b.addEventListener('click', () => {
      const want = b.dataset.gender;
      if (want === G) return;
      b.setAttribute('aria-busy', 'true');
      (want === 'women' ? loadWomen() : Promise.resolve(DATA.men)).then(() => {
        b.removeAttribute('aria-busy');
        applyGender(want);
        const tab = document.querySelector('.ekiden-tabs [aria-selected="true"]').dataset.tab;
        selectTab(tab, true);
      }).catch(() => { b.removeAttribute('aria-busy'); alert('女子のデータを読み込めませんでした。'); });
    }));
    ['#f-series', '#f-decade', '#f-region', '#f-pref', '#f-type', '#f-win', '#f-univonly'].forEach((id) => $(id).addEventListener('change', renderList));
    $('#univ-q').addEventListener('input', renderList);
    $('#univ-search').addEventListener('submit', (e) => { e.preventDefault(); renderList(); const b = $('#univ-list button'); if (b) b.click(); });
    $('#r-series').addEventListener('change', () => { fillEditions(); renderRace(); });
    $('#r-edition').addEventListener('change', renderRace);
    $('#w-series').addEventListener('change', renderWinners);

    applyGender(g);

    const p = new URLSearchParams(location.search);
    const okSeries = (v) => SERIES.includes(v) || (v.startsWith('q:') && Q_SERIES[G].includes(v.slice(2)));
    if (p.get('series') && okSeries(p.get('series'))) { $('#r-series').value = p.get('series'); fillEditions(); }
    if (p.get('ed')) $('#r-edition').value = p.get('ed');
    renderRace(p.get('open'));
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
      if (series === 'q') {
        const qa = (Q.byTeam.get(t.id) || []).filter((r) => {
          const tk = Q.taikai.get(r.taikai_id);
          return decade === null || (tk.year >= decade && tk.year < decade + 10);
        });
        return qa.length && (!win || qa.some((r) => r.qualified));
      }
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
      const qn = (Q.byTeam.get(t.id) || []).length;
      const badges = SERIES.filter((s) => sm && sm.series[s]).map((s) =>
        `<span class="badge" data-series="${s}">${SERIES_SHORT[s]} ${sm.series[s].appearances}回</span>`).join('') +
        (qn ? `<span class="badge badge-q">予選会 ${qn}回</span>` : '');
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
    const ck = GENDER[G].crownKey;
    const crown = sm[ck] ? `<p class="crown">${GENDER[G].crownLong}: ${sm[ck].map(seasonLabel).join('、')}</p>` : '';

    // 年度ごとの年表
    const rows = appearancesOf(teamId).concat((S.byTeam.get(teamId) || []).filter((r) => r.result_status === 'dns'));
    const bySeason = new Map();
    rows.forEach((r) => {
      const tk = S.taikaiById.get(r.taikai_id);
      if (!bySeason.has(tk.season)) bySeason.set(tk.season, {});
      bySeason.get(tk.season)[tk.series] = r;
    });
    // 予選会は、通過したら出る本大会の年度に並べる（箱根予選会は10月でも、その年度の箱根の欄の年度）
    const qBySeason = new Map();
    (Q.byTeam.get(teamId) || []).forEach((r) => {
      const qt = Q.taikai.get(r.taikai_id);
      const main = S.taikaiById.get(qt.qualifies_for);
      const y = main ? main.season : String(qt.year);
      if (!qBySeason.has(y)) qBySeason.set(y, []);
      qBySeason.get(y).push(r);
    });
    const hasQ = qBySeason.size > 0;
    const seasons = [...new Set([...bySeason.keys(), ...qBySeason.keys()])].sort().reverse();
    const chartSeasons = seasons.filter((y) => bySeason.has(y));
    const qCell = (y) => (qBySeason.get(y) || []).map((r) => {
      const qt = Q.taikai.get(r.taikai_id);
      const rank = r.overall_rank ? `${r.overall_rank}位` : (r.result_status === 'dnf' ? '記録なし' : '');
      return `<button type="button" class="link q-cell" data-race="q:${qt.series}|${qt.id}|${r.id}" title="${Q_NAME[qt.series]} ${qLabel(qt)}を見る">${Q_SHORT[qt.series]}${qt.region && qt.series === 'zennihon' ? `（${qt.region}）` : ''} ${rank} ${r.qualified ? '<span class="q-pass">通過</span>' : '<span class="q-fail">通過ならず</span>'}</button>`;
    }).join('') || '—';
    const table = `<div class="table-scroll"><table class="race-table compact"><thead><tr><th>年度</th>${SERIES.map((s) => `<th>${SERIES_SHORT[s]}</th>`).join('')}${hasQ ? '<th>予選会</th>' : ''}</tr></thead><tbody>${
      seasons.map((y) => `<tr><td>${seasonLabel(y)}</td>${SERIES.map((s) => {
        const r = (bySeason.get(y) || {})[s];
        if (!r) return '<td>—</td>';
        const tk = S.taikaiById.get(r.taikai_id);
        const aw = r.leg_awards ? `<small class="leg-count" title="区間賞（区間1位）の数">区間賞${r.leg_awards}</small>` : '';
        return `<td><button type="button" class="link" data-race="${tk.series}|${edOf(tk)}|${r.id}" title="${raceTitle(tk)}（${tk.year}年）の順位表を見る">${rankCell(r)}</button>${aw}</td>`;
      }).join('')}${hasQ ? `<td>${qCell(y)}</td>` : ''}</tr>`).join('')}</tbody></table></div>`;

    $('#team-detail').innerHTML = `<h2>${esc(t.display_name)}</h2><p class="team-sub">${esc(subParts.join('　'))}</p>${link}${crown}
      <div class="series-cards">${cards}</div>
      <div class="chart-wrap">${rankChart(bySeason, chartSeasons)}<div class="chart-legend">${SERIES.map((s) => `<span data-series="${s}">${SERIES_SHORT[s]}</span>`).join('')}</div></div>
      ${table}`;
    $('#team-detail').querySelectorAll('[data-race]').forEach((b) => b.addEventListener('click', () => {
      const [s, ed, rid] = b.dataset.race.split('|');
      $('#r-series').value = s; fillEditions(); $('#r-edition').value = ed; selectTab('race', true); renderRace(rid);
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
    const color = { izumo: 'var(--izumo)', zennihon: 'var(--zennihon)', hakone: 'var(--hakone)', wzennihon: 'var(--wzennihon)', wfujisan: 'var(--wfujisan)' };
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
    if (s.startsWith('q:')) {
      const qs = s.slice(2);
      const list = [...Q.taikai.values()].filter((t) => t.series === qs && (t.gender || 'men') === G)
        .sort((a, b) => b.edition - a.edition || REGION_ORDER.indexOf(a.region || '記録') - REGION_ORDER.indexOf(b.region || '記録'));
      $('#r-edition').innerHTML = list.map((t) => `<option value="${t.id}">${qLabel(t)}</option>`).join('');
      return;
    }
    const list = S.taikai.filter((t) => t.series === s).sort((a, b) => edOf(b) - edOf(a));
    $('#r-edition').innerHTML = list.map((t) =>
      `<option value="${edOf(t)}">${edLabel(t)}${t.status === 'cancelled' ? ' 中止' : S.byTaikai.has(t.id) ? '' : ' 優勝のみ'}</option>`).join('');
  }
  function renderRace(openId) {
    if (typeof openId !== 'string') openId = null;
    const s = $('#r-series').value;
    if (s.startsWith('q:')) { renderQualifier(openId); return; }
    const ed = Number($('#r-edition').value);
    const tk = S.taikaiById.get(`${s}-${ed}`);
    if (!tk) return;
    const rows = (S.byTaikai.get(tk.id) || []).slice().sort((a, b) => (a.overall_rank || 999) - (b.overall_rank || 999));
    const facts = [tk.date ? tk.date.replace(/-/g, '/').replace('/', '年').replace('/', '月') + '日' : `${tk.year}年`,
      tk.legs && tk.distance_km ? `${tk.legs}区間 ${tk.distance_km}km` : '', tk.teams_count ? `${tk.teams_count}チーム` : ''].filter(Boolean).join('　');
    const winTeam = tk.winner_team_id && S.teamById.get(tk.winner_team_id);
    $('#race-head').innerHTML = `<h2>${raceTitle(tk)}</h2><p>${esc(facts)}</p>${
      tk.status === 'cancelled' ? '<p>この回は中止されました。</p>' :
      `<p>優勝: ${esc(winTeam ? winTeam.display_name : tk.winner_name)}（${esc(tk.winning_time || '')}）</p>`}
      <p>出典: <a href="${esc(tk.source_url)}" target="_blank" rel="noopener">${G === 'women' ? '公式の記録 ↗' : SERIES_NAME[s] + '公式サイト ↗'}</a>${tk.note ? '　' + esc(tk.note) : ''}</p>`;
    const hk = s === 'hakone';
    if (!rows.length) {
      const why = s === 'wfujisan' ? 'この年は結果の資料が公開されていないか読み取れないため、優勝校のみです。' : 'この回の総合成績は、まだ収録していません（優勝校のみ）。';
      $('#race-table').innerHTML = tk.status === 'cancelled' ? '' : `<tbody><tr><td>${why}</td></tr></tbody>`;
      return;
    }
    const ncol = hk ? 5 : 3;
    $('#race-table').innerHTML = `<thead><tr><th class="num">順位</th><th>チーム</th><th class="num">総合記録</th>${hk ? '<th class="num">往路</th><th class="num">復路</th>' : ''}</tr></thead><tbody>${
      rows.map((r) => {
        const team = S.teamById.get(r.team_id);
        const cls = r.overall_rank === 1 ? 'win' : r.overall_rank ? '' : 'open';
        const legs = hk ? `<td class="num">${r.outbound_rank ? r.outbound_rank + '位 ' : ''}${esc(r.outbound_time || '—')}</td><td class="num">${r.return_rank ? r.return_rank + '位 ' : ''}${esc(r.return_time || '—')}</td>` : '';
        const name = r.name_at_entry !== team.display_name && !team.display_name.startsWith(r.name_at_entry) ? `${esc(r.name_at_entry)}<small class="dim">（今の${esc(team.display_name)}）</small>` : esc(r.name_at_entry);
        return `<tr class="${cls}" data-result="${r.id}"><td class="num">${rankCell(r)}</td><td><button type="button" class="link" data-team="${team.id}">${name}</button>${legMarks(r)}<button type="button" class="leg-toggle" data-legs="${r.id}" aria-expanded="false" aria-controls="legs-${r.id}" hidden>区間成績</button>${r.note ? `<br><small class="dim">${esc(r.note)}</small>` : ''}</td><td class="num">${esc(r.overall_time || '—')}</td>${legs}</tr>`;
      }).join('')}</tbody>`;
    $('#race-table').querySelectorAll('[data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
    if (!$('#panel-race').hidden) setParams({ tab: 'race', series: s, ed, open: openId });
    // 区間成績のある回は「区間成績」ボタンを出す
    const tableEl = $('#race-table');
    const token = (renderRace.token = (renderRace.token || 0) + 1);  // 描き直したら前の描画の処理は捨てる
    loadKukan(s).then((K) => {
      if (!K || !K.editions.has(edOf(tk)) || token !== renderRace.token) return;
      tableEl.querySelectorAll('.leg-toggle').forEach((b) => {
        if (!K.byResult.has(b.dataset.legs)) return;
        b.hidden = false;
        b.addEventListener('click', () => toggleLegs(b, K, ncol, s, ed));
        if (b.dataset.legs === openId) toggleLegs(b, K, ncol, s, ed, true);
      });
    });
  }

  // 予選会の成績表（第2段階 工程22）
  function renderQualifier(openId) {
    const s = $('#r-series').value;
    const tid = $('#r-edition').value;
    const t = Q.taikai.get(tid);
    renderRace.token = (renderRace.token || 0) + 1;
    if (!t) { $('#race-head').innerHTML = ''; $('#race-table').innerHTML = ''; return; }
    const rows = (Q.byTaikai.get(tid) || []).slice().sort((a, b) =>
      (b.qualified - a.qualified) * 0 || (a.overall_rank || 999) - (b.overall_rank || 999) || a.name_at_entry.localeCompare(b.name_at_entry, 'ja'));
    const passed = rows.filter((r) => r.qualified).length;
    const facts = [t.date ? fmtDate(t.date) : `${t.year}年`, `${rows.length}チーム`, `通過 ${passed}校`].join('　');
    const main = S.taikaiById.get(t.qualifies_for);
    $('#race-head').innerHTML = `<h2>${Q_NAME[t.series]} ${qLabel(t)}</h2><p>${esc(facts)}</p>
      ${main ? `<p>通過したチームが出る大会: <button type="button" class="link" data-main="${main.series}|${edOf(main)}">${raceTitle(main)}</button></p>` : ''}
      <p>出典: <a href="${esc(t.source_url)}" target="_blank" rel="noopener">${esc(t.source_name || '公式の記録')} ↗</a>${t.note ? '　' + esc(t.note) : ''}</p>`;
    const hasRunners = t.series === 'hakone';
    const timed = rows.some((r) => r.overall_time);
    $('#race-table').innerHTML = `<thead><tr><th class="num">順位</th><th>チーム</th>${timed ? '<th class="num">記録</th>' : ''}<th>結果</th></tr></thead><tbody>${
      rows.map((r) => {
        const team = S.teamById.get(r.team_id) || { id: r.team_id, display_name: r.name_at_entry };
        const name = esc(team.display_name) + (r.name_at_entry !== team.display_name ? `<small class="dim">（記録上の名前 ${esc(r.name_at_entry)}）</small>` : '');
        const btn = hasRunners && r.overall_time ? `<button type="button" class="leg-toggle" data-runners="${r.id}" aria-expanded="false" aria-controls="runners-${r.id}">10人の記録</button>` : '';
        const rank = r.overall_rank ? `${r.overall_rank}位` : (r.result_status === 'dnf' ? '<span class="status">記録なし</span>' : '—');
        return `<tr class="${r.qualified ? 'q-row-pass' : ''}" data-result="${r.id}"><td class="num">${rank}</td><td><button type="button" class="link" data-team="${team.id}">${name}</button>${btn}${r.note ? `<br><small class="dim">${esc(r.note)}</small>` : ''}</td>${timed ? `<td class="num">${esc(r.overall_time || '—')}</td>` : ''}<td>${qResultText(r)}</td></tr>`;
      }).join('')}</tbody>`;
    const ncol = timed ? 4 : 3;
    $('#race-table').querySelectorAll('[data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
    $('#race-head').querySelectorAll('[data-main]').forEach((b) => b.addEventListener('click', () => {
      const [ms, med] = b.dataset.main.split('|'); $('#r-series').value = ms; fillEditions(); $('#r-edition').value = med; renderRace();
    }));
    if (!$('#panel-race').hidden) setParams({ tab: 'race', series: s, ed: tid, open: openId });
    $('#race-table').querySelectorAll('[data-runners]').forEach((b) => {
      b.addEventListener('click', () => toggleRunners(b, ncol, s, tid));
      if (b.dataset.runners === openId) toggleRunners(b, ncol, s, tid, true);
    });
  }
  function toggleRunners(b, ncol, s, tid, scroll) {
    const tr = b.closest('tr');
    if (b.getAttribute('aria-expanded') === 'true') {
      const next = tr.nextElementSibling;
      if (next && next.classList.contains('legs-row')) next.remove();
      b.setAttribute('aria-expanded', 'false'); b.textContent = '10人の記録';
      setParams({ tab: 'race', series: s, ed: tid });
      return;
    }
    b.setAttribute('aria-expanded', 'true'); b.textContent = '10人の記録を閉じる';
    loadQRunners().then((m) => {
      const list = (m && m.get(b.dataset.runners)) || [];
      tr.insertAdjacentHTML('afterend', `<tr class="legs-row" id="runners-${b.dataset.runners}"><td colspan="${ncol}"><div class="table-scroll"><table class="leg-table"><caption class="sr-only">チームの合計に入った10人</caption><thead><tr><th class="num">チーム内</th><th class="num">個人順位</th><th>選手</th><th class="num">学年</th><th class="num">記録</th></tr></thead><tbody>${
        list.map((x) => `<tr><td class="num">${x.order_in_team}</td><td class="num">${x.place}位</td><td>${x.runner_name ? esc(x.runner_name) : '<span class="dim">（名前は伏せています）</span>'}</td><td class="num">${esc(x.runner_grade || '')}</td><td class="num">${esc(x.time)}</td></tr>`).join('')}</tbody></table></div></td></tr>`);
      setParams({ tab: 'race', series: s, ed: tid, open: b.dataset.runners });
      if (scroll) tr.scrollIntoView({ block: 'center' });
    });
  }

  function toggleLegs(b, K, ncol, s, ed, scroll) {
    const tr = b.closest('tr');
    const open = b.getAttribute('aria-expanded') === 'true';
    const next = tr.nextElementSibling;
    if (open) {
      if (next && next.classList.contains('legs-row')) next.remove();
      b.setAttribute('aria-expanded', 'false');
      b.textContent = '区間成績';
      setParams({ tab: 'race', series: s, ed });
      return;
    }
    const legs = K.byResult.get(b.dataset.legs).slice().sort((a, c) => a.leg - c.leg);
    tr.insertAdjacentHTML('afterend', `<tr class="legs-row" id="legs-${b.dataset.legs}"><td colspan="${ncol}"><div class="table-scroll">${legTable(legs)}</div></td></tr>`);
    b.setAttribute('aria-expanded', 'true');
    b.textContent = '区間成績を閉じる';
    setParams({ tab: 'race', series: s, ed, open: b.dataset.legs });
    if (scroll) tr.scrollIntoView({ block: 'center' });
  }

  /* ---------- 駅伝の基本 ---------- */
  const SVGNS = 'http://www.w3.org/2000/svg';
  const COLOR = { izumo: 'var(--izumo)', zennihon: 'var(--zennihon)', hakone: 'var(--hakone)', wzennihon: 'var(--wzennihon)', wfujisan: 'var(--wfujisan)' };
  function loadBasics() {
    getJson('basics.json?v=20261108-2').then((b) => {
      BASICS = b;
      S.basics = BASICS;
      renderBasics();
    }).catch(() => { $('#tab-basics').hidden = true; $('#panel-basics').innerHTML = ''; });
  }
  function srcLink(src, role) {
    return `<a href="${esc(src.url)}" target="_blank" rel="noopener">${esc(src.name)} ↗</a>${role === 'secondary' ? '（報道による。公式の要項には記載なし）' : ''}`;
  }
  function renderBasics() {
    const B = S.basics;
    const races = B.races.filter((r) => (r.gender || 'men') === G);
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

    const pills = document.querySelector('.basics-pills');
    pills.innerHTML = races.map((r) => `<button type="button" data-course="${r.series}">${esc(r.name)}</button>`).join('');
    document.querySelectorAll('[data-course]').forEach((b) => b.addEventListener('click', () => showCourse(b.dataset.course)));
    if (races[0]) showCourse(races[0].series);

    $('#basics-relay').innerHTML = relayFigure() + `<p class="basics-src">出典: ${srcLink(B.relay_rules.zone.source, B.relay_rules.zone.role)}</p>`;
    const kuriage = SERIES.map((s) => B.relay_rules.kuriage.find((k) => k.series === s)).filter(Boolean);
    $('#basics-kuriage').innerHTML = `<thead><tr><th>大会</th><th>決まり</th><th>出典</th></tr></thead><tbody>${
      kuriage.length ? kuriage.map((k) =>
        `<tr><th scope="row">${SERIES_NAME[k.series]}</th><td class="wrap">${esc(k.text)}</td><td class="wrap">${srcLink(k.source, k.role)}</td></tr>`).join('')
        : '<tr><td colspan="3" class="wrap">女子2大会の大会別の繰り上げ規定は、公式資料で確認できた内容を今後追加します。</td></tr>'
    }</tbody>`;
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
    return `<svg class="fig" viewBox="0 0 ${W} ${H}" role="img" aria-label="${G === 'women' ? '女子2大会' : '男子三大駅伝'}の出場チームの内訳">${g}</svg><div class="team-legends">${legend}</div>`;
  }

  function showCourse(series) {
    document.querySelectorAll('[data-course]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.course === series));
    const r = S.basics.races.find((x) => x.series === series);
    let fig = ['izumo', 'zennihon', 'hakone'].includes(series) ? courseOverview(r) : '';
    if (series === 'hakone') {
      fig += courseStrip(r, r.legs.slice(0, 5), r.points.slice(0, 6), '往路（1月2日）大手町 → 芦ノ湖', true)
          + courseStrip(r, r.legs.slice(5), r.points.slice(5), '復路（1月3日）芦ノ湖 → 大手町', false);
    } else {
      fig += courseStrip(r, r.legs, r.points, `${r.points[0]} → ${r.points[r.points.length - 1]}`, false);
    }
    $('#basics-course').innerHTML = fig + (r.course_note ? `<p class="basics-note">${esc(r.course_note)}</p>` : '');
    if (['izumo', 'zennihon', 'hakone'].includes(series)) requestAnimationFrame(() => {
      renderCourseMap(r);
      if (series === 'hakone') initHakoneSectionGuide(r);
      if (series === 'izumo') initIzumoSectionGuide(r);
      if (series === 'zennihon') initZennihonSectionGuide(r);
    });
    const hasNote = r.legs.some((l) => l.note);
    const hasDay = r.legs.some((l) => l.day);
    $('#basics-legs').innerHTML = `<thead><tr><th>区間</th>${hasDay ? '<th>日</th>' : ''}<th>スタート</th><th>たすきを渡す場所</th><th class="num">距離</th>${hasNote ? '<th>見どころ</th>' : ''}</tr></thead><tbody>${
      r.legs.map((l) => `<tr><th scope="row">${l.no}区</th>${hasDay ? `<td>${esc(l.day)}</td>` : ''}<td class="wrap">${esc(l.from)}</td><td class="wrap">${esc(l.to)}</td><td class="num">${l.km.toFixed(1)}km</td>${hasNote ? `<td class="wrap">${esc(l.note || '')}</td>` : ''}</tr>`).join('')
    }<tr class="total"><th scope="row">合計</th>${hasDay ? '<td></td>' : ''}<td></td><td></td><td class="num">${r.distance_km.toFixed(1)}km</td>${hasNote ? '<td></td>' : ''}</tr></tbody>`;
    $('#basics-course-src').innerHTML = '出典: ' + r.sources.map((s) => srcLink(s)).join('、');
  }

  // 地点間の線は位置関係を示すもので、実際の道路形状とは区別して表示する。
  function courseOverview(r) {
    const layouts = {
      izumo: {
        coords: [[35.392628,132.684174],[35.36705,132.754578],[35.387589,132.808548],[35.442329,132.825989],[35.403526,132.777512],[35.395527,132.711395],[35.382694,132.739319]],
        short: ['出雲大社正面鳥居前','出雲市役所前','ゆめタウン斐川前','JAラピタひらた店前','鳶巣CC前','島根ワイナリー前','出雲ドーム前'],
      },
      zennihon: {
        coords: [[35.125538,136.909073],[35.088169,136.83284],[35.056435,136.722656],[35.0042,136.630936],[34.884689,136.599258],[34.786518,136.546295],[34.685066,136.518753],[34.547501,136.579849],[34.439827,136.762283]],
        short: ['熱田神宮西門前','第1中継所','第2中継所','第3中継所','第4中継所','第5中継所','第6中継所','第7中継所','伊勢神宮内宮'],
      },
      hakone: {
        coords: [[35.687069,139.765045],[35.517773,139.687561],[35.389053,139.520615],[35.313683,139.33139],[35.245907,139.129822],[35.189735,139.037781]],
        short: ['大手町・読売新聞社前','鶴見中継所','戸塚中継所','平塚中継所','小田原中継所','芦ノ湖'],
      },
    };
    const d = layouts[r.series];
    r._mapOverview = d;
    return `<div class="course-overview-grid">
      <section class="course-map-card" aria-label="${esc(r.name)}のコース地図">
        <div class="course-map-head"><h3>コース地図</h3><span>拡大・移動できます</span></div>
        <div id="course-map" class="course-map" role="application" aria-label="${esc(r.name)}のスタート、中継所、フィニッシュの地図"></div>
        <p class="course-map-note">地図: <a href="https://maps.gsi.go.jp/" target="_blank" rel="noopener">国土地理院</a>。線は中継地点間の位置関係を示し、実際の道路形状は下の公式出典で確認できます。</p>
      </section>
      <section class="course-elevation-card" aria-label="${esc(r.name)}の高低差の特徴">
        <div class="course-elevation-head"><h3>高低差の特徴</h3><span>地点と区間で読む</span></div>
        ${elevationFeatureGraphic(r)}
      </section>
    </div>${r.series === 'hakone' ? hakoneSectionGuide(r) : r.series === 'izumo' ? izumoSectionGuide(r) : r.series === 'zennihon' ? zennihonSectionGuide(r) : ''}`;
  }

  function zennihonSectionGuide(r) {
    return `<section class="hakone-section-guide zennihon-section-guide" aria-labelledby="zennihon-section-title">
      <div class="hakone-section-head">
        <div><p class="section-kicker">RUNNER'S VIEW</p><h3 id="zennihon-section-title">1区ずつ、走る場所を見る</h3></div>
        <div class="hakone-section-switch zennihon-section-switch" role="group" aria-label="全日本大学駅伝の区間を選ぶ">${r.legs.map((leg) => `<button type="button" data-zennihon-section="${leg.no}" aria-pressed="${leg.no === 1}">${leg.no}区</button>`).join('')}</div>
      </div>
      <div id="zennihon-section-summary" class="hakone-section-summary" aria-live="polite"></div>
      <div class="hakone-section-grid">
        <div><div id="zennihon-section-map" class="hakone-section-map" role="application" aria-label="全日本大学駅伝の区間別コース地図"></div><p class="course-map-note">地図: 国土地理院。線は区間の始点と終点を結ぶ位置確認用の概略です。実際の道路形状は公式コースで確認できます。</p></div>
        <div id="zennihon-section-profile" class="hakone-section-profile"></div>
      </div>
    </section>`;
  }

  function initZennihonSectionGuide(r) {
    document.querySelectorAll('[data-zennihon-section]').forEach((button) => button.addEventListener('click', () => renderZennihonSection(r, Number(button.dataset.zennihonSection))));
    renderZennihonSection(r, 1);
  }

  function renderZennihonSection(r, no) {
    const leg = r.legs.find((item) => item.no === no);
    const start = r._mapOverview.coords[no - 1];
    const finish = r._mapOverview.coords[no];
    if (!leg || !start || !finish) return;
    const terrain = no <= 4 ? '前半区間：公式コース説明では、小刻みなアップダウンが多い区間です。' : '後半区間：公式コース説明では、前半に比べて比較的平らな区間です。';
    document.querySelectorAll('[data-zennihon-section]').forEach((button) => button.setAttribute('aria-pressed', String(Number(button.dataset.zennihonSection) === no)));
    $('#zennihon-section-summary').innerHTML = `<div><b>${leg.no}区</b><span>${esc(leg.from)} → ${esc(leg.to)}</span></div><strong>${leg.km.toFixed(1)}km</strong><p>${terrain}</p>`;
    $('#zennihon-section-profile').innerHTML = zennihonSectionProfile(leg);
    renderSimpleSectionMap({ elementId: 'zennihon-section-map', start, finish, from: leg.from, to: leg.to, color: MAP_COLOR.zennihon });
  }

  function zennihonSectionProfile(leg) {
    const front = leg.no <= 4;
    const path = front ? 'M18 87 C42 50 62 119 88 72 S132 52 157 91 S203 116 230 72 S271 58 302 84' : 'M18 86 C71 81 112 89 158 84 S245 87 302 83';
    const label = front ? '前半：小刻みなアップダウンが多い' : '後半：比較的平ら';
    return `<h4>${leg.no}区の高低差の特徴</h4><svg class="section-profile-svg zennihon-profile-svg" viewBox="0 0 320 145" role="img" aria-label="${label}"><path d="${path}" class="section-profile-area"/><path d="${path}" class="section-profile-line"/><text x="160" y="24" text-anchor="middle">${label}</text><text x="18" y="137">スタート</text><text x="302" y="137" text-anchor="end">中継所 ${leg.km.toFixed(1)}km</text></svg><div class="profile-caution"><b>標高の実測グラフではありません</b><span>公式説明の「前半」「後半」の特徴を区間に対応させた模式図です。</span></div><ol class="izumo-route-order zennihon-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(leg.from)}</b></div></li><li><span>F</span><div><small>${leg.km.toFixed(1)}km</small><b>${esc(leg.to)}</b></div></li></ol><p class="section-source-note">区間距離とコースの特徴は全日本大学駅伝公式の開催要項・コース紹介に基づきます。</p>`;
  }

  function izumoSectionGuide(r) {
    return `<section class="hakone-section-guide izumo-section-guide" aria-labelledby="izumo-section-title">
      <div class="hakone-section-head">
        <div><p class="section-kicker">RUNNER'S VIEW</p><h3 id="izumo-section-title">1区ずつ、走る場所を見る</h3></div>
        <div class="hakone-section-switch izumo-section-switch" role="group" aria-label="出雲駅伝の区間を選ぶ">${r.legs.map((leg) => `<button type="button" data-izumo-section="${leg.no}" aria-pressed="${leg.no === 1}">${leg.no}区</button>`).join('')}</div>
      </div>
      <div id="izumo-section-summary" class="hakone-section-summary" aria-live="polite"></div>
      <div class="hakone-section-grid">
        <div><div id="izumo-section-map" class="hakone-section-map" role="application" aria-label="出雲駅伝の区間別コース地図"></div><p class="course-map-note">地図: 国土地理院。線は区間の始点と終点を結ぶ位置確認用の概略です。実際の道路形状は公式コースで確認できます。</p></div>
        <div id="izumo-section-profile" class="hakone-section-profile"></div>
      </div>
    </section>`;
  }

  function initIzumoSectionGuide(r) {
    document.querySelectorAll('[data-izumo-section]').forEach((button) => button.addEventListener('click', () => renderIzumoSection(r, Number(button.dataset.izumoSection))));
    renderIzumoSection(r, 1);
  }

  function renderIzumoSection(r, no) {
    const leg = r.legs.find((item) => item.no === no);
    const start = r._mapOverview.coords[no - 1];
    const finish = r._mapOverview.coords[no];
    if (!leg || !start || !finish) return;
    document.querySelectorAll('[data-izumo-section]').forEach((button) => button.setAttribute('aria-pressed', String(Number(button.dataset.izumoSection) === no)));
    $('#izumo-section-summary').innerHTML = `<div><b>${leg.no}区</b><span>${esc(leg.from)} → ${esc(leg.to)}</span></div><strong>${leg.km.toFixed(1)}km</strong><p>${esc(leg.note || '公式資料に記載された区間情報を表示しています。')}</p>`;
    $('#izumo-section-profile').innerHTML = izumoSectionProfile(leg);
    renderSimpleSectionMap({ elementId: 'izumo-section-map', start, finish, from: leg.from, to: leg.to, color: MAP_COLOR.izumo });
  }

  function izumoSectionProfile(leg) {
    const profiles = {
      1: { path:'M18 105 C58 103 77 59 105 75 S153 119 181 86 S236 67 302 82', label:'浜山公園のアップダウン', aria:'1区は浜山公園にアップダウンがある' },
      5: { path:'M18 91 C50 72 76 110 105 82 S157 62 185 94 S235 108 302 84', label:'ぶどう畑の細かなアップダウン', aria:'5区はぶどう畑の中に細かなアップダウンがある' },
    };
    const p = profiles[leg.no];
    const graphic = p
      ? `<svg class="section-profile-svg izumo-profile-svg" viewBox="0 0 320 145" role="img" aria-label="${p.aria}"><path d="${p.path}" class="section-profile-area"/><path d="${p.path}" class="section-profile-line"/><text x="160" y="24" text-anchor="middle">${p.label}</text><text x="18" y="137">スタート</text><text x="302" y="137" text-anchor="end">中継所 ${leg.km.toFixed(1)}km</text></svg>`
      : `<div class="section-no-elevation"><b>高低差の数値は未掲載</b><p>公式の区間紹介に具体的な標高値がないため、推測の曲線は描いていません。</p></div>`;
    return `<h4>${leg.no}区の走りどころ</h4>${graphic}<ol class="izumo-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(leg.from)}</b></div></li><li><span>→</span><div><small>公式の見どころ</small><b>${esc(leg.note || '区間情報を確認中')}</b></div></li><li><span>F</span><div><small>${leg.km.toFixed(1)}km</small><b>${esc(leg.to)}</b></div></li></ol><p class="section-source-note">区間距離・見どころは出雲駅伝公式サイトと公式記録に基づきます。</p>`;
  }

  function renderSimpleSectionMap(d) {
    const el = $('#' + d.elementId);
    if (!el || typeof L === 'undefined') return;
    if (activeSectionMap) activeSectionMap.remove();
    activeSectionMap = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', { attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>', maxZoom: 18 }).addTo(activeSectionMap);
    const line = L.polyline([d.start, d.finish], { color: d.color, weight: 6, opacity: .86, dashArray: '12 7' }).addTo(activeSectionMap);
    [[d.start, 'S', d.from], [d.finish, 'F', d.to]].forEach(([pos, label, name]) => {
      const icon = L.divIcon({ className: '', html: `<span class="course-pin is-end" style="--pin:${d.color}">${label}</span>`, iconSize: [31,31], iconAnchor: [15.5,15.5] });
      L.marker(pos, { icon }).addTo(activeSectionMap).bindPopup(`<b>${label === 'S' ? 'スタート' : '中継所'}</b>${esc(name)}`);
    });
    activeSectionMap.fitBounds(line.getBounds(), { padding: [46, 46] });
  }

  const HAKONE_SECTIONS = {
    5: {
      no: 5, title: '5区　山上り', direction: '小田原中継所 → 芦ノ湖', distance: '20.8km',
      summary: '小田原から箱根の山へ。16.2km地点の国道1号最高点（約874m）まで上り、その後は芦ノ湖へ下ります。',
      route: [[35.245907,139.129822],[35.236652,139.104575],[35.239032,139.073894],[35.24186,139.062762],[35.2324,139.0517],[35.219776,139.043487],[35.2041,139.0310],[35.189735,139.037781]],
      points: [
        {km:'0.0km', name:'小田原中継所', note:'スタート', pos:[35.245907,139.129822]},
        {km:'—', name:'箱根湯本', note:'山上りへ', pos:[35.236652,139.104575]},
        {km:'—', name:'大平台・宮ノ下', note:'曲がりながら上る', pos:[35.2402,139.0678]},
        {km:'16.2km', name:'国道1号最高点', note:'約874m・ここから下り', pos:[35.2117,139.0368]},
        {km:'19km以降', name:'箱根神社大鳥居付近', note:'終盤', pos:[35.2037,139.0306]},
        {km:'20.8km', name:'芦ノ湖', note:'フィニッシュ', pos:[35.189735,139.037781]},
      ],
    },
    6: {
      no: 6, title: '6区　山下り', direction: '芦ノ湖 → 小田原中継所', distance: '20.8km',
      summary: '芦ノ湖を出て最初の約4kmは上り。その後は急な下りが続き、最後の約3kmは再び脚を使う区間です。',
      route: [[35.189735,139.037781],[35.2041,139.0310],[35.219776,139.043487],[35.2324,139.0517],[35.24186,139.062762],[35.239032,139.073894],[35.236652,139.104575],[35.245907,139.129822]],
      points: [
        {km:'0.0km', name:'芦ノ湖', note:'スタート', pos:[35.189735,139.037781]},
        {km:'約4km', name:'上りの終わり', note:'ここから山下り', pos:[35.2117,139.0368]},
        {km:'—', name:'芦之湯・小涌園', note:'急な下りとカーブ', pos:[35.2261,139.0476]},
        {km:'—', name:'宮ノ下・大平台', note:'下りが続く', pos:[35.2402,139.0678]},
        {km:'残り約3km', name:'箱根湯本付近', note:'終盤の走り直し', pos:[35.236652,139.104575]},
        {km:'20.8km', name:'小田原中継所', note:'たすき渡し', pos:[35.245907,139.129822]},
      ],
    },
  };

  function hakoneSectionGuide(r) {
    return `<section class="hakone-section-guide" aria-labelledby="hakone-section-title">
      <div class="hakone-section-head">
        <div><p class="section-kicker">RUNNER'S VIEW</p><h3 id="hakone-section-title">区間ごとに、どこを走るか見る</h3></div>
        <div class="hakone-section-switch hakone-all-section-switch" role="group" aria-label="箱根駅伝の区間を選ぶ">${r.legs.map((leg) => `<button type="button" data-hakone-section="${leg.no}" aria-pressed="${leg.no === 1}">${leg.no}区</button>`).join('')}</div>
      </div>
      <div id="hakone-section-summary" class="hakone-section-summary" aria-live="polite"></div>
      <div class="hakone-section-grid">
        <div><div id="hakone-section-map" class="hakone-section-map" role="application" aria-label="箱根駅伝の区間別コース地図"></div><p class="course-map-note">地図: 国土地理院。線は公式コース上の主要地点を結んだ位置確認用の概略です。</p></div>
        <div id="hakone-section-profile" class="hakone-section-profile"></div>
      </div>
    </section>`;
  }

  function initHakoneSectionGuide(r) {
    document.querySelectorAll('[data-hakone-section]').forEach((button) => button.addEventListener('click', () => renderHakoneSection(r, Number(button.dataset.hakoneSection))));
    renderHakoneSection(r, 1);
  }

  function renderHakoneSection(r, no) {
    const d = HAKONE_SECTIONS[no] || buildHakoneSection(r, no);
    if (!d) return;
    document.querySelectorAll('[data-hakone-section]').forEach((button) => button.setAttribute('aria-pressed', String(Number(button.dataset.hakoneSection) === no)));
    $('#hakone-section-summary').innerHTML = `<div><b>${d.title}</b><span>${d.direction}</span></div><strong>${d.distance}</strong><p>${d.summary}</p>`;
    $('#hakone-section-profile').innerHTML = d.points.length > 2 ? hakoneSectionProfile(d) : hakoneSimpleSectionProfile(d);
    renderHakoneSectionMap(d);
  }

  function buildHakoneSection(r, no) {
    const leg = r.legs.find((item) => item.no === no);
    if (!leg) return null;
    const outbound = [[35.687069,139.765045],[35.517773,139.687561],[35.389053,139.520615],[35.313683,139.33139],[35.245907,139.129822],[35.189735,139.037781]];
    const coords = outbound.concat(outbound.slice(0,5).reverse());
    const start = coords[no - 1], finish = coords[no];
    return {
      no, title:`${no}区　${leg.day}`, direction:`${leg.from} → ${leg.to}`, distance:`${leg.km.toFixed(1)}km`, summary:leg.note,
      route:[start, finish],
      points:[
        {km:'0.0km', name:leg.from, note:'スタート', pos:start},
        {km:`${leg.km.toFixed(1)}km`, name:leg.to, note:no === 10 ? 'フィニッシュ' : 'たすき渡し', pos:finish},
      ],
    };
  }

  function hakoneSimpleSectionProfile(d) {
    const profiles = {
      1:{path:'M18 91 C82 88 154 92 222 88 C247 83 269 58 286 72 S298 87 302 84',label:'17km過ぎ　六郷橋',aria:'1区は17キロ過ぎの六郷橋が勝負どころ'},
      2:{path:'M18 92 C53 61 75 112 107 75 S160 55 191 96 S246 110 302 72',label:'権太坂など起伏が多い',aria:'2区は権太坂など起伏が多い'},
      4:{path:'M18 90 C92 88 161 91 222 87 S274 68 302 55',label:'平地区間・終盤に緩やかな上り',aria:'4区は平地区間で終盤に緩やかな上りがある'},
      7:{path:'M18 87 C52 66 78 105 109 79 S161 64 192 94 S249 105 302 81',label:'小さなアップダウンが続く',aria:'7区は小さなアップダウンが続く'},
      8:{path:'M18 99 C92 96 155 92 205 83 S264 51 302 39',label:'湘南新道の上り坂',aria:'8区は湘南新道の上り坂がある'},
    };
    const p = profiles[d.no];
    const graphic = p ? `<svg class="section-profile-svg" viewBox="0 0 320 145" role="img" aria-label="${p.aria}"><path d="${p.path}" class="section-profile-area"/><path d="${p.path}" class="section-profile-line"/><text x="160" y="24" text-anchor="middle">${p.label}</text><text x="18" y="137">${esc(d.points[0].name)}</text><text x="302" y="137" text-anchor="end">${d.distance}</text></svg>` : `<div class="section-no-elevation hakone-no-elevation"><b>高低差は推測していません</b><p>公式紹介は景観・風・逆転・フィニッシュなどを説明していますが、具体的な起伏は示していないため曲線を描いていません。</p></div>`;
    return `<h4>${d.no}区の高低差と走りどころ</h4>${graphic}<ol class="izumo-route-order hakone-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(d.points[0].name)}</b></div></li><li><span>→</span><div><small>公式の見どころ</small><b>${esc(d.summary)}</b></div></li><li><span>F</span><div><small>${d.distance}</small><b>${esc(d.points[1].name)}</b></div></li></ol><p class="section-source-note">区間距離・特徴は箱根駅伝公式サイトに基づきます。図は標高の実測グラフではありません。</p>`;
  }

  function hakoneSectionProfile(d) {
    const stops = d.points.map((p, i) => `<li class="${i === 0 ? 'is-start' : i === d.points.length - 1 ? 'is-finish' : ''}"><span class="section-km">${p.km}</span><i aria-hidden="true"></i><span><b>${p.name}</b><small>${p.note}</small></span></li>`).join('');
    const profile = d.no === 5
      ? `<svg class="section-profile-svg" viewBox="0 0 320 150" role="img" aria-label="5区は小田原から16.2キロ地点の最高点まで上り、その後芦ノ湖へ下る"><path d="M18 126 C62 120 92 102 126 82 S190 42 238 24 C256 48 274 66 302 77" class="section-profile-area"/><path d="M18 126 C62 120 92 102 126 82 S190 42 238 24 C256 48 274 66 302 77" class="section-profile-line"/><circle cx="238" cy="24" r="5"/><text x="238" y="14" text-anchor="middle">16.2km・約874m</text><text x="18" y="145">小田原</text><text x="302" y="145" text-anchor="end">芦ノ湖 20.8km</text></svg>`
      : `<svg class="section-profile-svg" viewBox="0 0 320 150" role="img" aria-label="6区は芦ノ湖から最初の約4キロを上り、その後小田原へ急に下る"><path d="M18 72 C35 55 52 35 73 24 C102 58 126 86 166 106 S243 123 302 127" class="section-profile-area"/><path d="M18 72 C35 55 52 35 73 24 C102 58 126 86 166 106 S243 123 302 127" class="section-profile-line"/><circle cx="73" cy="24" r="5"/><text x="73" y="14" text-anchor="middle">約4km・上り終わり</text><text x="18" y="145">芦ノ湖</text><text x="302" y="145" text-anchor="end">小田原 20.8km</text></svg>`;
    return `<h4>高低差と走る順番</h4>${profile}<ol class="section-timeline section-${d.no}">${stops}</ol><p class="section-source-note">距離・高低差の説明は箱根駅伝公式サイトに基づきます。「—」は公式説明で通過距離を確認できないため、数値を付けていません。</p>`;
  }

  function renderHakoneSectionMap(d) {
    const el = $('#hakone-section-map');
    if (!el || typeof L === 'undefined') return;
    if (activeSectionMap) activeSectionMap.remove();
    activeSectionMap = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', { attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>', maxZoom: 18 }).addTo(activeSectionMap);
    const line = L.polyline(d.route, { color: MAP_COLOR.hakone, weight: 6, opacity: .86 }).addTo(activeSectionMap);
    d.points.forEach((p, i) => {
      const end = i === 0 || i === d.points.length - 1;
      const icon = L.divIcon({ className: '', html: `<span class="course-pin${end ? ' is-end' : ''}" style="--pin:${MAP_COLOR.hakone}">${i === 0 ? 'S' : i === d.points.length - 1 ? 'F' : i}</span>`, iconSize: [end ? 31 : 26, end ? 31 : 26], iconAnchor: [end ? 15.5 : 13, end ? 15.5 : 13] });
      L.marker(p.pos, { icon }).addTo(activeSectionMap).bindPopup(`<b>${p.km}　${p.name}</b>${p.note}`);
    });
    activeSectionMap.fitBounds(line.getBounds(), { padding: [26, 26] });
  }

  // 標高値が公表されていない地点を数値化せず、公式コース説明にある
  // 「アップダウン」「平ら」「山上り・山下り」を地点・区間と結び付けて示す。
  function elevationFeatureGraphic(r) {
    if (r.series === 'hakone') {
      return `<svg class="course-elevation" viewBox="0 0 420 340" role="img" aria-label="箱根駅伝は5区で国道1号の最高点約874メートルへ上り、復路6区で山を下る。2区・7区・8区にも起伏がある">
        <defs><linearGradient id="hakoneMountain" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#d9eee9"/><stop offset="1" stop-color="#75b7a7"/></linearGradient></defs>
        <text x="24" y="28" class="elev-kicker">往路　東京 → 箱根</text>
        <path d="M28 116 C80 112 126 105 178 108 S247 112 278 101 C302 90 323 43 347 25 C361 49 370 74 382 92 L382 126 L28 126 Z" fill="url(#hakoneMountain)"/>
        <path d="M28 116 C80 112 126 105 178 108 S247 112 278 101 C302 90 323 43 347 25 C361 49 370 74 382 92" fill="none" stroke="#0f766e" stroke-width="6" stroke-linecap="round"/>
        <line x1="28" y1="126" x2="382" y2="126" class="elev-base"/>
        <g class="elev-place"><text x="28" y="148">大手町</text><text x="278" y="148" text-anchor="middle">小田原</text><text x="382" y="148" text-anchor="end">芦ノ湖</text></g>
        <g class="elev-leg"><text x="154" y="72" text-anchor="middle">1〜4区</text><text x="154" y="89" text-anchor="middle">2区などに起伏</text><text x="325" y="117" text-anchor="middle">5区　山上り</text></g>
        <circle cx="347" cy="25" r="7" fill="#fff" stroke="#0f766e" stroke-width="4"/><text x="347" y="16" text-anchor="middle" class="elev-peak">国道1号最高点 約874m</text>
        <text x="24" y="190" class="elev-kicker">復路　箱根 → 東京</text>
        <path d="M28 213 C43 225 55 273 79 287 C111 300 146 292 184 286 S264 281 382 288" fill="none" stroke="#0f766e" stroke-width="6" stroke-linecap="round"/>
        <line x1="28" y1="298" x2="382" y2="298" class="elev-base"/>
        <g class="elev-place"><text x="28" y="320">芦ノ湖</text><text x="100" y="320" text-anchor="middle">小田原</text><text x="382" y="320" text-anchor="end">大手町</text></g>
        <g class="elev-leg"><text x="68" y="239" text-anchor="middle">6区</text><text x="68" y="256" text-anchor="middle">山下り</text><text x="244" y="272" text-anchor="middle">7・8区　小さな起伏や上りあり</text></g>
      </svg><p class="course-elevation-note"><b>読みどころ:</b> 大きな高低差が表れるのは、往路5区の山上りと復路6区の山下りです。</p>`;
    }
    if (r.series === 'zennihon') {
      return `<svg class="course-elevation" viewBox="0 0 420 290" role="img" aria-label="全日本大学駅伝は前半に小刻みなアップダウンが多く、後半は比較的平ら">
        <rect x="20" y="28" width="220" height="188" rx="16" fill="#eef3ff"/><rect x="240" y="28" width="160" height="188" rx="16" fill="#f2f7f6"/>
        <text x="38" y="55" class="elev-kicker">前半　1〜4区</text><text x="258" y="55" class="elev-kicker">後半　5〜8区</text>
        <path d="M38 151 C56 112 73 178 91 127 S126 92 145 145 S180 174 201 124 S224 102 238 142" fill="none" stroke="#1d4ed8" stroke-width="7" stroke-linecap="round"/>
        <path d="M250 146 C280 141 310 148 339 144 S372 146 389 143" fill="none" stroke="#1d4ed8" stroke-width="7" stroke-linecap="round"/>
        <g class="elev-feature"><text x="139" y="196" text-anchor="middle">小刻みなアップダウンが多い</text><text x="320" y="196" text-anchor="middle">比較的平ら</text></g>
        <g class="elev-place"><text x="24" y="243">熱田神宮</text><text x="210" y="243" text-anchor="middle">第4中継所</text><text x="396" y="243" text-anchor="end">伊勢神宮</text></g>
        <path d="M38 260 H382" stroke="#1d4ed8" stroke-width="3"/><path d="M382 260 l-10 -6 v12 z" fill="#1d4ed8"/>
      </svg><p class="course-elevation-note"><b>読みどころ:</b> 前半は起伏への対応、後半は長い平坦区間での持続力が鍵になります。</p>`;
    }
    return `<svg class="course-elevation" viewBox="0 0 420 290" role="img" aria-label="出雲駅伝は1区の浜山公園と5区のぶどう畑にアップダウンがある">
      <rect x="20" y="30" width="112" height="184" rx="16" fill="#fff1e8"/><rect x="254" y="30" width="78" height="184" rx="16" fill="#fff1e8"/>
      <path d="M28 151 C42 145 53 104 69 126 S98 173 118 137 C142 149 164 151 190 149 S229 148 258 146 C270 119 284 104 297 139 S318 160 330 146 C352 149 369 147 392 145" fill="none" stroke="#c2410c" stroke-width="7" stroke-linecap="round"/>
      <text x="76" y="57" text-anchor="middle" class="elev-kicker">1区</text><text x="76" y="77" text-anchor="middle" class="elev-feature">浜山公園</text><text x="76" y="96" text-anchor="middle" class="elev-feature">アップダウン</text>
      <text x="293" y="57" text-anchor="middle" class="elev-kicker">5区</text><text x="293" y="77" text-anchor="middle" class="elev-feature">ぶどう畑</text><text x="293" y="96" text-anchor="middle" class="elev-feature">細かな起伏</text>
      <g class="elev-place"><text x="24" y="241">出雲大社</text><text x="208" y="241" text-anchor="middle">第3中継所</text><text x="396" y="241" text-anchor="end">出雲ドーム</text></g>
      <path d="M38 260 H382" stroke="#c2410c" stroke-width="3"/><path d="M382 260 l-10 -6 v12 z" fill="#c2410c"/>
    </svg><p class="course-elevation-note"><b>読みどころ:</b> 起伏が明記されているのは1区の浜山公園と5区のぶどう畑です。</p>`;
  }

  function renderCourseMap(r) {
    const el = $('#course-map');
    if (!el || !r._mapOverview || typeof L === 'undefined') return;
    if (activeCourseMap) activeCourseMap.remove();
    const d = r._mapOverview;
    activeCourseMap = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', {
      attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>',
      maxZoom: 18,
    }).addTo(activeCourseMap);
    const line = L.polyline(d.coords, { color: MAP_COLOR[r.series], weight: 5, opacity: .72, dashArray: '10 7' }).addTo(activeCourseMap);
    d.coords.forEach((latlng, i) => {
      const end = i === 0 || i === d.coords.length - 1;
      const icon = L.divIcon({ className: '', html: `<span class="course-pin${end ? ' is-end' : ''}" style="--pin:${MAP_COLOR[r.series]}">${i === 0 ? 'S' : i === d.coords.length - 1 ? 'F' : i}</span>`, iconSize: [end ? 31 : 26, end ? 31 : 26], iconAnchor: [end ? 15.5 : 13, end ? 15.5 : 13] });
      const role = i === 0 ? 'スタート' : i === d.coords.length - 1 ? (r.series === 'hakone' ? '往路ゴール・復路スタート' : 'フィニッシュ') : `第${i}中継所`;
      L.marker(latlng, { icon }).addTo(activeCourseMap).bindPopup(`<b>${esc(role)}</b>${esc(d.short[i])}`);
    });
    activeCourseMap.fitBounds(line.getBounds(), { padding: [28, 28] });
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
    S.summary.forEach((sm) => (sm[GENDER[G].crownKey] || []).forEach((y) => crowns.push([y, sm.team_id])));
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
    const list = S.taikai.filter((t) => t.series === s).sort((a, b) => edOf(b) - edOf(a));
    $('#winners-table').innerHTML = `<thead><tr><th class="num">回</th><th>年</th><th>優勝</th><th class="num">記録</th></tr></thead><tbody>${
      list.map((t) => {
        const team = t.winner_team_id && S.teamById.get(t.winner_team_id);
        const name = t.status === 'cancelled' ? '<span class="status">中止</span>' : team ? `<button type="button" class="link" data-team="${team.id}">${esc(t.winner_name)}</button>` : esc(t.winner_name || '');
        return `<tr><td class="num">${t.series === 'wfujisan' ? '' : t.edition}</td><td>${t.year}</td><td>${name}</td><td class="num">${esc(t.winning_time || '')}</td></tr>`;
      }).join('')}</tbody>`;
    $('#winners-table').querySelectorAll('[data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
  }
})();
