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

  // 駅伝ドラマ可視化スタイル：各大学のたすき色（スクールカラー）定義
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
    '東京農業大学': { bg: '#15803d', stripe: '#ffffff', label: '松葉緑（大根グリーン）' },
    '東京国際大学': { bg: '#0f172a', stripe: '#d4a72c', label: 'ネイビー・ゴールド' },
    '中央学院大学': { bg: '#7e22ce', stripe: '#eab308', label: 'パープル・イエロー' },
    '国士舘大学':   { bg: '#1d4ed8', stripe: '#dc2626', label: '青・赤' },
    '専修大学':     { bg: '#14532d', stripe: '#b91c1c', label: '深緑・エンジ' },
    '拓殖大学':     { bg: '#f97316', stripe: '#ffffff', label: 'オレンジ' },
    '亜細亜大学':   { bg: '#0284c7', stripe: '#fde047', label: 'マリンブルー' },
    '駿河台大学':   { bg: '#0369a1', stripe: '#facc15', label: 'ブルー・イエロー' },
    '上武大学':     { bg: '#111827', stripe: '#dc2626', label: '黒・赤' },
    '筑波大学':     { bg: '#7c3aed', stripe: '#ffffff', label: '桐の紫（筑波パープル）' },
    '慶應義塾大学': { bg: '#1e3a8a', stripe: '#dc2626', label: '三色旗（紺・赤）' },
    '東京大学':     { bg: '#38bdf8', stripe: '#ffffff', label: '淡青（ライトブルー）' },
    '京都大学':     { bg: '#1e3a8a', stripe: '#ffffff', label: '濃青（ダークブルー）' },
    '名城大学':     { bg: '#dc2626', stripe: '#1d4ed8', label: '真紅・ブルー' },
    '立命館大学':   { bg: '#7f1d1d', stripe: '#ffffff', label: 'エンジ（立命館レッド）' },
    '佛教大学':     { bg: '#7e22ce', stripe: '#ffffff', label: '紫' },
    '京都産業大学': { bg: '#1e3a8a', stripe: '#ffffff', label: '神山ブルー' },
    '大阪学院大学': { bg: '#1d4ed8', stripe: '#dc2626', label: 'ブルー・レッド' },
    '東北福祉大学': { bg: '#b91c1c', stripe: '#ffffff', label: 'エンジ' },
    '関西大学':     { bg: '#4c1d95', stripe: '#ffffff', label: '紫紺' },
    '関西学院大学': { bg: '#1e3a8a', stripe: '#fbbf24', label: '新月ブルー' },
    '松山大学':     { bg: '#1e40af', stripe: '#ffffff', label: 'コバルトブルー' },
    '福岡大学':     { bg: '#7f1d1d', stripe: '#ffffff', label: 'エンジ' },
    '玉川大学':     { bg: '#1e3a8a', stripe: '#ffffff', label: 'ネイビー' },
    '白鷗大学':     { bg: '#0284c7', stripe: '#ffffff', label: 'スカイブルー' }
  };
  const FALLBACK_COLORS = ['#0f766e', '#1d4ed8', '#b45309', '#6d28d9', '#be185d', '#15803d', '#334155', '#9333ea'];
  function getTasuki(name) {
    const clean = String(name || '').trim();
    if (TASUKI_MAP[clean]) return TASUKI_MAP[clean];
    for (const [k, v] of Object.entries(TASUKI_MAP)) {
      if (clean.includes(k) || k.includes(clean)) return v;
    }
    let h = 0;
    for (let i = 0; i < clean.length; i++) h = (h * 31 + clean.charCodeAt(i)) >>> 0;
    return { bg: FALLBACK_COLORS[h % FALLBACK_COLORS.length], stripe: '#ffffff', label: 'チームカラー' };
  }
  function tasukiSwatch(name, sizeClass = '') {
    const t = getTasuki(name);
    return `<span class="tasuki-swatch ${sizeClass}" style="--t-bg:${t.bg};--t-stripe:${t.stripe}" title="${esc(name)}（${esc(t.label)}）" aria-hidden="true"></span>`;
  }
  function rankBadgeHtml(r) {
    if (!r) return '<span class="dim">—</span>';
    if (r.overall_rank === 1) return '<span class="rank-medal medal-1" title="優勝（1位）">1位 👑</span>';
    if (r.overall_rank === 2) return '<span class="rank-medal medal-2" title="準優勝（2位）">2位</span>';
    if (r.overall_rank === 3) return '<span class="rank-medal medal-3" title="3位">3位</span>';
    if (r.overall_rank) return `<span class="rank-num">${r.overall_rank}位</span>`;
    return `<span class="status">${esc(STATUS_NAME[r.result_status] || r.result_status)}</span>`;
  }
  const SEED_RANK = { hakone: 10, zennihon: 8, wzennihon: 8 };
  const SEED_NOTE = {
    hakone: '11位以下は10月の箱根駅伝予選会から本戦出場を目指します',
    zennihon: '9位以下は各地区の選考会から次回出場を目指します',
    wzennihon: '9位以下は各地区代表選考・5000m記録選考から次回出場を目指します'
  };

  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const newState = () => ({ taikai: [], teams: [], summary: new Map(), results: {}, byTaikai: new Map(), byTeam: new Map(), taikaiById: new Map(), teamById: new Map() });
  const DATA = { men: newState(), women: null };
  let S = DATA.men;
  // 基本情報は男女で共用し、切り替え時に選択した側を必ず再描画する
  let BASICS = null;
  // Leaflet地図の再描画時に、既存インスタンスを安全に破棄するため保持する
  let activeCourseMap = null;
  let activeSectionMap = null;

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
    const requestedTab = p.get('tab');
    selectTab(['univ', 'race', 'record'].includes(requestedTab) ? requestedTab : 'univ', false);
    loadBasics();
    if (requestedTab === 'basics' && !location.hash) {
      requestAnimationFrame(() => $('#basics-guide').scrollIntoView({ block: 'start' }));
    }
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
      return `<li><button type="button" data-team="${t.id}" ${S.current === t.id ? 'aria-current="true"' : ''}><strong class="team-list-title">${tasukiSwatch(t.display_name, 'sm')}<span>${esc(t.display_name)}</span></strong><small>${esc(sub)}</small><span class="badges">${badges}</span></button></li>`;
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
        <dt>最高</dt><dd>${x.best_rank ? (x.best_rank === 1 ? '<span class="best-rank-win">1位 👑</span>' : x.best_rank + '位') : '—'}</dd>
        <dt>優勝</dt><dd>${x.wins ? `${x.wins}回（${x.win_years.join('、')}年）` : 'なし'}</dd></dl></section>`;
    }).join('');
    const ck = GENDER[G].crownKey;
    const crownSeasons = sm[ck] || [];
    const crown = crownSeasons.length ? `<p class="crown"><span class="crown-icon" aria-hidden="true">👑</span>${GENDER[G].crownLong}: ${crownSeasons.map(seasonLabel).join('、')}</p>` : '';

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
    const crownSet = new Set(crownSeasons.map(String));
    const table = `<div class="table-scroll"><table class="race-table compact"><thead><tr><th>年度</th>${SERIES.map((s) => `<th>${SERIES_SHORT[s]}</th>`).join('')}${hasQ ? '<th>予選会</th>' : ''}</tr></thead><tbody>${
      seasons.map((y) => `<tr class="${crownSet.has(String(y)) ? 'win' : ''}"><td>${seasonLabel(y)}${crownSet.has(String(y)) ? ` <span class="leg-mark award">👑${GENDER[G].crownName}</span>` : ''}</td>${SERIES.map((s) => {
        const r = (bySeason.get(y) || {})[s];
        if (!r) return '<td>—</td>';
        const tk = S.taikaiById.get(r.taikai_id);
        const aw = r.leg_awards ? `<small class="leg-count" title="区間賞（区間1位）の数">区間賞${r.leg_awards}</small>` : '';
        return `<td><button type="button" class="link" data-race="${tk.series}|${edOf(tk)}|${r.id}" title="${raceTitle(tk)}（${tk.year}年）の順位表を見る">${rankCell(r)}</button>${aw}</td>`;
      }).join('')}${hasQ ? `<td>${qCell(y)}</td>` : ''}</tr>`).join('')}</tbody></table></div>`;

    const tasuki = getTasuki(t.display_name);
    const detailEl = $('#team-detail');
    detailEl.style.setProperty('--team-bg', tasuki.bg);
    detailEl.style.setProperty('--team-stripe', tasuki.stripe);
    detailEl.innerHTML = `<div class="team-tasuki-banner" aria-hidden="true"></div>
      <div class="team-header-row">
        <div class="team-title-wrap">
          ${tasukiSwatch(t.display_name, 'lg')}
          <div>
            <div class="team-heading-line">
              <h2>${esc(t.display_name)}</h2>
              <span class="tasuki-color-pill">たすき色：${esc(tasuki.label)}</span>
            </div>
            <p class="team-sub">${esc(subParts.join('　'))}</p>
          </div>
        </div>
        ${link}
      </div>
      ${crown}
      <div class="series-cards">${cards}</div>
      <div class="chart-wrap">${rankChart(bySeason, chartSeasons, crownSeasons)}<div class="chart-legend">${SERIES.map((s) => `<span data-series="${s}">${SERIES_SHORT[s]}</span>`).join('')}<b class="chart-legend-note">★＝優勝（1位）　破線＝シード権目安（10位）</b></div></div>
      ${table}`;
    $('#team-detail').querySelectorAll('[data-race]').forEach((b) => b.addEventListener('click', () => {
      const [s, ed, rid] = b.dataset.race.split('|');
      $('#r-series').value = s; fillEditions(); $('#r-edition').value = ed; selectTab('race', true); renderRace(rid);
      $('#finder').scrollIntoView({ behavior: 'smooth' });
    }));
    if (push) setParams({ tab: 'univ', team: teamId });
    if (push && matchMedia('(max-width:900px)').matches) $('#team-detail').scrollIntoView({ behavior: 'smooth' });
  }

  // 順位の推移（上ほど上位）。年度を横軸に3大会を重ね、優勝（★）と三冠／二冠帯・シード権ラインを表示する
  function rankChart(bySeason, seasonsDesc, crownSeasons = []) {
    const seasons = [...seasonsDesc].reverse().map(Number);
    if (!seasons.length) return '';
    const W = 660, H = 228, L = 42, R = 18, T = 24, B = 30;
    const minY = seasons[0], maxY = seasons[seasons.length - 1];
    let maxRank = 10;
    bySeason.forEach((v) => Object.values(v).forEach((r) => { if (r.overall_rank) maxRank = Math.max(maxRank, r.overall_rank); }));
    maxRank = Math.max(15, Math.ceil(maxRank / 5) * 5);
    const x = (y) => L + (maxY === minY ? (W - L - R) / 2 : (y - minY) / (maxY - minY) * (W - L - R));
    const yy = (rank) => T + (rank - 1) / (maxRank - 1) * (H - T - B);
    const color = { izumo: 'var(--izumo)', zennihon: 'var(--zennihon)', hakone: 'var(--hakone)', wzennihon: 'var(--wzennihon)', wfujisan: 'var(--wfujisan)' };
    let g = '';
    for (let rk = 1; rk <= maxRank; rk += (maxRank > 15 ? 5 : 2)) {
      const isTop = rk === 1;
      g += `<line x1="${L}" x2="${W - R}" y1="${yy(rk)}" y2="${yy(rk)}" stroke="${isTop ? '#f59e0b' : '#ebe8de'}" stroke-opacity="${isTop ? '0.55' : '1'}"/><text x="${L - 7}" y="${yy(rk) + 4}" font-size="11" font-weight="${isTop ? '700' : '400'}" text-anchor="end" fill="${isTop ? '#b45309' : '#6b7280'}">${rk}位</text>`;
    }
    // 10位シード権目安ライン（破線）
    if (maxRank >= 10) {
      const sy = yy(10);
      g += `<line x1="${L}" x2="${W - R}" y1="${sy}" y2="${sy}" stroke="#0f766e" stroke-width="1.5" stroke-dasharray="5 3" stroke-opacity="0.55"/>`;
      g += `<text x="${W - R - 4}" y="${sy - 4}" font-size="10" font-weight="700" text-anchor="end" fill="#0f766e" opacity="0.85">シード権目安（10位）</text>`;
    }
    // 三冠・二冠達成年度のゴールドハイライト縦帯
    const crownName = GENDER[G].crownName;
    (crownSeasons || []).map(Number).filter((cy) => cy >= minY && cy <= maxY).forEach((cy) => {
      const cx = x(cy);
      const bw = Math.min(34, Math.max(20, (W - L - R) / Math.max(4, maxY - minY + 1)));
      g += `<rect x="${(cx - bw / 2).toFixed(1)}" y="${T - 14}" width="${bw.toFixed(1)}" height="${H - T - B + 18}" rx="6" fill="#f59e0b" fill-opacity="0.16" stroke="#d97706" stroke-opacity="0.45" stroke-dasharray="2 2"/>`;
      g += `<text x="${cx.toFixed(1)}" y="${T - 4}" font-size="10" font-weight="800" text-anchor="middle" fill="#b45309">👑${cy}${crownName}</text>`;
    });

    const step = Math.max(1, Math.ceil((maxY - minY) / 8));
    for (let y = minY; y <= maxY; y += step) g += `<text x="${x(y)}" y="${H - 8}" font-size="11" text-anchor="middle" fill="#6b7280">${y}</text>`;
    SERIES.forEach((s) => {
      const pts = seasons.map((y) => [y, bySeason.get(String(y))?.[s]]).filter(([, r]) => r && r.overall_rank);
      if (!pts.length) return;
      // 出場しなかった年度で線を切る
      let path = '';
      pts.forEach(([y, r], i) => { path += `${i && pts[i - 1][0] === y - 1 ? 'L' : 'M'}${x(y).toFixed(1)},${yy(r.overall_rank).toFixed(1)}`; });
      g += `<path d="${path}" fill="none" stroke="${color[s]}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;
      g += pts.map(([y, r]) => {
        const cx = x(y).toFixed(1), cy = yy(r.overall_rank).toFixed(1);
        if (r.overall_rank === 1) {
          return `<g><circle cx="${cx}" cy="${cy}" r="6.8" fill="#fbbf24" stroke="${color[s]}" stroke-width="2"/><text x="${cx}" y="${(Number(cy) + 3.4).toFixed(1)}" font-size="9" font-weight="800" text-anchor="middle" fill="#78350f">★</text><title>${seasonLabel(y)} ${SERIES_NAME[s]} 1位（優勝）</title></g>`;
        }
        return `<circle cx="${cx}" cy="${cy}" r="3.6" fill="${color[s]}" stroke="#fff" stroke-width="1.2"><title>${seasonLabel(y)} ${SERIES_NAME[s]} ${r.overall_rank}位</title></circle>`;
      }).join('');
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
    const seedRank = SEED_RANK[s] || 0;
    const seedNote = SEED_NOTE[s] || '';
    $('#race-table').innerHTML = `<thead><tr><th class="num">順位</th><th>チーム</th><th class="num">総合記録</th>${hk ? '<th class="num">往路</th><th class="num">復路</th>' : ''}</tr></thead><tbody>${
      rows.map((r) => {
        const team = S.teamById.get(r.team_id);
        const cls = r.overall_rank === 1 ? 'win' : (seedRank && r.overall_rank && r.overall_rank <= seedRank ? 'seed-zone' : (r.overall_rank ? '' : 'open'));
        const outBadge = r.outbound_rank === 1 ? '<span class="sub-win-badge">往路1位</span> ' : (r.outbound_rank ? r.outbound_rank + '位 ' : '');
        const retBadge = r.return_rank === 1 ? '<span class="sub-win-badge">復路1位</span> ' : (r.return_rank ? r.return_rank + '位 ' : '');
        const legs = hk ? `<td class="num">${outBadge}${esc(r.outbound_time || '—')}</td><td class="num">${retBadge}${esc(r.return_time || '—')}</td>` : '';
        const name = r.name_at_entry !== team.display_name && !team.display_name.startsWith(r.name_at_entry) ? `${esc(r.name_at_entry)}<small class="dim">（今の${esc(team.display_name)}）</small>` : esc(r.name_at_entry);
        const seedTag = (seedRank && r.overall_rank === seedRank) ? '<span class="seed-cutoff-tag">シード権</span>' : '';
        const rowHtml = `<tr class="${cls}" data-result="${r.id}"><td class="num">${rankBadgeHtml(r)}</td><td><div class="team-cell-inner">${tasukiSwatch(team.display_name)}<button type="button" class="link" data-team="${team.id}">${name}</button>${seedTag}${legMarks(r)}<button type="button" class="leg-toggle" data-legs="${r.id}" aria-expanded="false" aria-controls="legs-${r.id}" hidden>区間成績</button></div>${r.note ? `<small class="dim team-row-note">${esc(r.note)}</small>` : ''}</td><td class="num">${esc(r.overall_time || '—')}</td>${legs}</tr>`;
        if (seedRank && r.overall_rank === seedRank) {
          return rowHtml + `<tr class="seed-divider-row" data-series="${s}"><td colspan="${ncol}"><div class="seed-divider-bar"><span class="seed-divider-pill">▲ ここまで次回大会シード権（上位${seedRank}校）</span><span class="seed-divider-note">${esc(seedNote)}</span></div></td></tr>`;
        }
        return rowHtml;
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
  const MAP_COLOR = { izumo: '#c2410c', zennihon: '#1d4ed8', hakone: '#0f766e', wzennihon: '#be185d', wfujisan: '#6d28d9' };
  let ELEV_DATA = null;
  function loadBasics() {
    Promise.all([
      getJson('basics.json?v=20261108-3'),
      getJson('elevation_profiles.json?v=20261122-1').catch(() => null)
    ]).then(([b, elev]) => {
      BASICS = b;
      ELEV_DATA = elev;
      S.basics = BASICS;
      renderBasics();
    }).catch(() => { $('#basics-guide').hidden = true; });
  }

  // 国土地理院 数値標高モデル（DEM）を輪切りにした実地形断面SVGを描画する
  function renderDemCrossSectionSvg(legData, seriesKey, opts = {}) {
    if (!legData || !legData.samples || !legData.samples.length) return '';
    const W = opts.w || 340, H = opts.h || 175;
    const padL = 38, padR = 14, padT = 24, padB = 26;
    const plotW = W - padL - padR, plotH = H - padT - padB;
    const pts = legData.samples;
    const totalKm = legData.km || pts[pts.length - 1][2] || 1;
    const rawMax = Math.max(...pts.map((p) => p[3]));
    // 標高スケール：平地区間でも輪切りの地層と微地形（橋・坂）が読み取れるよう最小上限を40mとし、山岳区間は実標高に合わせる
    const ceilM = rawMax > 400 ? 900 : rawMax > 150 ? 200 : rawMax > 60 ? 80 : 40;
    const xAt = (km) => padL + (km / totalKm) * plotW;
    const yAt = (m) => padT + plotH - Math.min(1, Math.max(0, m / ceilM)) * plotH;
    const baseLineY = padT + plotH;

    const polyPts = pts.map((p) => `${xAt(p[2]).toFixed(1)},${yAt(p[3]).toFixed(1)}`).join(' ');
    const areaPath = `M${xAt(pts[0][2]).toFixed(1)},${baseLineY} L` + pts.map((p) => `${xAt(p[2]).toFixed(1)},${yAt(p[3]).toFixed(1)}`).join(' L') + ` L${xAt(pts[pts.length - 1][2]).toFixed(1)},${baseLineY} Z`;
    const subSoilPath = `M${xAt(pts[0][2]).toFixed(1)},${baseLineY} L` + pts.map((p) => `${xAt(p[2]).toFixed(1)},${Math.min(baseLineY, yAt(p[3]) + 9).toFixed(1)}`).join(' L') + ` L${xAt(pts[pts.length - 1][2]).toFixed(1)},${baseLineY} Z`;

    const c = MAP_COLOR[seriesKey] || '#0f766e';
    const uid = `dem-${seriesKey}-${legData.no}`;
    // 標高メモリ線（3段階）
    const steps = ceilM === 900 ? [0, 400, 800] : ceilM === 200 ? [0, 100, 200] : ceilM === 80 ? [0, 40, 80] : [0, 20, 40];
    const gridHtml = steps.map((m) => {
      const y = yAt(m).toFixed(1);
      return `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="${m === 0 ? '' : '3 2'}"/>
              <text x="${padL - 5}" y="${(Number(y) + 3.5).toFixed(1)}" font-size="9.5" font-weight="700" text-anchor="end" fill="#64748b">${m}m</text>`;
    }).join('');

    // 距離メモリ（垂線＝地形の輪切りスリット）
    let slitsHtml = '';
    for (let i = 4; i < pts.length - 1; i += 4) {
      const sx = xAt(pts[i][2]).toFixed(1);
      const sy = yAt(pts[i][3]).toFixed(1);
      slitsHtml += `<line x1="${sx}" y1="${sy}" x2="${sx}" y2="${baseLineY}" stroke="${c}" stroke-opacity="0.16" stroke-width="1"/>`;
    }

    // 最高標高地点マーカー
    let maxIdx = 0;
    pts.forEach((p, i) => { if (p[3] > pts[maxIdx][3]) maxIdx = i; });
    const mx = xAt(pts[maxIdx][2]), my = yAt(pts[maxIdx][3]);
    const peakAnchor = mx > W - 95 ? 'end' : mx < 95 ? 'start' : 'middle';
    const peakBadge = `<circle cx="${mx.toFixed(1)}" cy="${my.toFixed(1)}" r="4" fill="#fbbf24" stroke="${c}" stroke-width="2"/>
      <text x="${mx.toFixed(1)}" y="${Math.max(13, my - 6).toFixed(1)}" font-size="9.5" font-weight="800" text-anchor="${peakAnchor}" fill="#92400e">最高 ${pts[maxIdx][3].toFixed(0)}m（${pts[maxIdx][2].toFixed(1)}km）</text>`;

    return `<div class="dem-cross-wrap">
      <div class="dem-metrics-bar">
        <span>スタート <b>${pts[0][3].toFixed(0)}m</b></span>
        <span>最高 <b>${legData.max_m.toFixed(0)}m</b></span>
        <span>累積上り <b>+${legData.gain_m}m</b> ／ 下り <b>-${legData.drop_m}m</b></span>
        <span>ゴール <b>${pts[pts.length - 1][3].toFixed(0)}m</b></span>
      </div>
      <svg class="section-profile-svg dem-profile-svg" viewBox="0 0 ${W} ${H}" data-series="${seriesKey}" data-leg="${legData.no}" role="img" aria-label="${esc(legData.no)}区の実地形断面図（最高標高${legData.max_m}m）">
        <defs>
          <linearGradient id="${uid}-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${c}" stop-opacity="0.52"/>
            <stop offset="65%" stop-color="#b45309" stop-opacity="0.24"/>
            <stop offset="100%" stop-color="#78350f" stop-opacity="0.12"/>
          </linearGradient>
          <pattern id="${uid}-hatch" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="6" stroke="#78350f" stroke-opacity="0.14" stroke-width="1.5"/>
          </pattern>
        </defs>
        ${gridHtml}
        <!-- 地層断面（輪切りハッチング＋グラデーション） -->
        <path d="${areaPath}" fill="url(#${uid}-fill)"/>
        <path d="${subSoilPath}" fill="url(#${uid}-hatch)"/>
        ${slitsHtml}
        <!-- 地表面ライン -->
        <polyline fill="none" stroke="${c}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" points="${polyPts}"/>
        <!-- 基底岩盤ライン -->
        <line x1="${padL}" y1="${baseLineY}" x2="${W - padR}" y2="${baseLineY}" stroke="#475569" stroke-width="2"/>
        ${peakBadge}
        <!-- ホバー連動カーソル -->
        <line class="dem-hover-line" x1="0" y1="${padT}" x2="0" y2="${baseLineY}" stroke="#d97706" stroke-width="1.5" stroke-dasharray="3 2" visibility="hidden"/>
        <circle class="dem-hover-dot" cx="0" cy="0" r="4.5" fill="#fbbf24" stroke="#111827" stroke-width="1.8" visibility="hidden"/>
        <text x="${padL}" y="${H - 7}" font-size="10" font-weight="700" fill="#475569">0km（${esc(legData.from)}）</text>
        <text x="${(padL + plotW / 2).toFixed(1)}" y="${H - 7}" font-size="9.5" text-anchor="middle" fill="#64748b">${(totalKm / 2).toFixed(1)}km</text>
        <text x="${W - padR}" y="${H - 7}" font-size="10" font-weight="700" text-anchor="end" fill="#475569">${totalKm.toFixed(1)}km（${esc(legData.to)}）</text>
      </svg>
      <div class="dem-hover-readout" aria-live="polite">断面図にマウスを重ねると、その地点の距離・実測標高・地図上の位置を表示します</div>
    </div>`;
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
    let fig = courseOverview(r);
    if (series === 'hakone') {
      fig += courseStrip(r, r.legs.slice(0, 5), r.points.slice(0, 6), '往路（1月2日）大手町 → 芦ノ湖', true)
          + courseStrip(r, r.legs.slice(5), r.points.slice(5), '復路（1月3日）芦ノ湖 → 大手町', false);
    } else {
      fig += courseStrip(r, r.legs, r.points, `${r.points[0]} → ${r.points[r.points.length - 1]}`, false);
    }
    $('#basics-course').innerHTML = fig + (r.course_note ? `<p class="basics-note">${esc(r.course_note)}</p>` : '');
    requestAnimationFrame(() => {
      if (['izumo', 'zennihon', 'hakone'].includes(series)) renderCourseMap(r);
      if (series === 'hakone') initHakoneSectionGuide(r);
      if (series === 'izumo') initIzumoSectionGuide(r);
      if (series === 'zennihon') initZennihonSectionGuide(r);
      if (series === 'wzennihon' || series === 'wfujisan') initWomenSectionGuide(r);
    });
    const hasNote = r.legs.some((l) => l.note);
    const hasDay = r.legs.some((l) => l.day);
    const LEG_TAGS = {
      hakone: { 1: '開幕区間', 2: '花の2区', 3: '湘南の海風', 4: '山へのつなぎ', 5: '天下の険・山上り', 6: '急勾配・山下り', 7: '寒暖差の7区', 8: '遊行寺の坂', 9: '復路のエース区間', 10: '大手町フィニッシュ' },
      izumo: { 1: '出雲大社スタート', 2: '最短スピード区間', 3: '斐伊川・エース区間', 4: '北山山系を望む', 5: 'ぶどう畑の起伏', 6: '最長アンカー決戦' },
      zennihon: { 1: '熱田神宮スタート', 2: '序盤のスピード戦', 3: '伊勢湾岸の駆け引き', 4: '前半の起伏区間', 5: '中盤の要所', 6: '伊勢路のつなぎ', 7: '準アンカー長距離', 8: '伊勢神宮フィニッシュ' },
      wzennihon: { 1: '杜の都スタート', 2: '最短スピード区間', 3: '広瀬川を渡る', 4: '中盤の起伏と風', 5: '最長・仙台城跡の上り', 6: '競技場フィニッシュ' },
      wfujisan: { 1: '浅間大社周回', 2: '高低差98mの下り', 3: '最短スピード区間', 4: '富士川の冬風', 5: '最長・田子の浦港', 6: '富士山を望む直線', 7: '169m上る最大の難関' }
    };
    const tagMap = LEG_TAGS[r.series] || {};
    $('#basics-legs').innerHTML = `<thead><tr><th>区間</th>${hasDay ? '<th>日</th>' : ''}<th>スタート</th><th>たすきを渡す場所</th><th class="num">距離</th>${hasNote ? '<th>見どころ</th>' : ''}</tr></thead><tbody>${
      r.legs.map((l) => {
        const tag = tagMap[l.no] ? `<span class="leg-drama-tag ${l.no === 5 && r.series === 'hakone' || l.no === 7 && r.series === 'wfujisan' ? 'is-peak' : ''}">${esc(tagMap[l.no])}</span> ` : '';
        return `<tr><th scope="row">${l.no}区</th>${hasDay ? `<td>${esc(l.day)}</td>` : ''}<td class="wrap">${esc(l.from)}</td><td class="wrap">${esc(l.to)}</td><td class="num">${l.km.toFixed(1)}km</td>${hasNote ? `<td class="wrap">${tag}${esc(l.note || '')}</td>` : ''}</tr>`;
      }).join('')
    }<tr class="total"><th scope="row">合計</th>${hasDay ? '<td></td>' : ''}<td></td><td></td><td class="num">${r.distance_km.toFixed(1)}km</td>${hasNote ? '<td></td>' : ''}</tr></tbody>`;
    $('#basics-course-src').innerHTML = '出典: ' + r.sources.map((s) => srcLink(s)).join('、');
  }

  // 地点間の線は位置関係を示すもので、実際の道路形状とは区別して表示する。
  function courseOverview(r) {
    if (r.series === 'wzennihon' || r.series === 'wfujisan') return womenCourseOverview(r);
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
        <p class="course-map-note">地図: <a href="https://maps.gsi.go.jp/" target="_blank" rel="noopener">国土地理院</a>。コース経路に沿ったポリラインと各中継所を表示しています。</p>
      </section>
      <section class="course-elevation-card" aria-label="${esc(r.name)}の高低差の特徴">
        <div class="course-elevation-head"><h3>高低差の特徴</h3><span>地点と区間で読む</span></div>
        ${elevationFeatureGraphic(r)}
      </section>
    </div>${r.series === 'hakone' ? hakoneSectionGuide(r) : r.series === 'izumo' ? izumoSectionGuide(r) : r.series === 'zennihon' ? zennihonSectionGuide(r) : ''}`;
  }


  function womenCourseOverview(r) {
    const mapLabel = r.series === 'wzennihon' ? '公式コース・交通規制図' : '公式コースマップ';
    const mapAsset = r.series === 'wzennihon' ? 'assets/wzennihon-course-map.webp' : 'assets/wfujisan-course-map.webp';
    return `<div class="course-overview-grid">
      <section class="course-map-card" aria-label="${esc(r.name)}の公式コース地図">
        <div class="course-map-head"><h3>コース地図</h3><span>公式資料で確認</span></div>
        <div class="official-map-wrap">
          <a class="official-map-link" href="${esc(r.map_url)}" target="_blank" rel="noopener" aria-label="${esc(r.name)}の公式地図を大きく開く">
            <img class="official-map-image" src="${mapAsset}" alt="${esc(r.name)}の公式コース地図" decoding="async">
          </a>
          <div class="official-map-fallback"><b>${esc(mapLabel)}</b><p>地図を選ぶと、大会公式PDFを大きく開けます。</p><a class="button" href="${esc(r.map_url)}" target="_blank" rel="noopener">公式PDFを開く ↗</a></div>
        </div>
        <p class="course-map-note">大会公式PDFの地図を画像化して表示しています。出典・詳細は公式PDFで確認できます。</p>
      </section>
      <section class="course-elevation-card" aria-label="${esc(r.name)}の高低差の特徴">
        <div class="course-elevation-head"><h3>高低差の特徴</h3><span>公式発表だけで読む</span></div>
        ${elevationFeatureGraphic(r)}
      </section>
    </div>${womenSectionGuide(r)}`;
  }

  function womenSectionGuide(r) {
    return `<section class="hakone-section-guide women-section-guide" aria-labelledby="women-section-title">
      <div class="hakone-section-head">
        <div><p class="section-kicker">走者の目線で見る区間ガイド</p><h3 id="women-section-title">1区ずつ、走る場所と特徴を見る</h3></div>
        <div class="hakone-section-switch" role="group" aria-label="${esc(r.name)}の区間を選ぶ">${r.legs.map((leg) => `<button type="button" data-women-section="${leg.no}" aria-pressed="${leg.no === 1}">${leg.no}区</button>`).join('')}</div>
      </div>
      <div id="women-section-summary" class="hakone-section-summary" aria-live="polite"></div>
      <div id="women-section-profile" class="hakone-section-profile" style="max-width:760px;margin:1rem auto 0"></div>
    </section>`;
  }

  function initWomenSectionGuide(r) {
    document.querySelectorAll('[data-women-section]').forEach((button) => button.addEventListener('click', () => renderWomenSection(r, Number(button.dataset.womenSection))));
    renderWomenSection(r, 1);
  }

  let activeHoverMarker = null;
  function bindDemCrossSectionHover(containerEl, seriesKey, legNo) {
    if (!containerEl || !ELEV_DATA || !ELEV_DATA.series[seriesKey]) return;
    const legData = ELEV_DATA.series[seriesKey].legs.find((l) => l.no === legNo);
    if (!legData || !legData.samples || !legData.samples.length) return;
    const svg = containerEl.querySelector('.dem-profile-svg');
    const hLine = containerEl.querySelector('.dem-hover-line');
    const hDot = containerEl.querySelector('.dem-hover-dot');
    const readout = containerEl.querySelector('.dem-hover-readout');
    if (!svg || !hLine || !hDot) return;

    const W = 340, H = 175, padL = 38, padR = 14, padT = 24, padB = 26;
    const plotW = W - padL - padR, plotH = H - padT - padB;
    const pts = legData.samples;
    const totalKm = legData.km || pts[pts.length - 1][2] || 1;
    const rawMax = Math.max(...pts.map((p) => p[3]));
    const ceilM = rawMax > 400 ? 900 : rawMax > 150 ? 200 : rawMax > 60 ? 80 : 40;
    const xAt = (km) => padL + (km / totalKm) * plotW;
    const yAt = (m) => padT + plotH - Math.min(1, Math.max(0, m / ceilM)) * plotH;

    function onMove(clientX) {
      const rect = svg.getBoundingClientRect();
      if (!rect.width) return;
      const relX = ((clientX - rect.left) / rect.width) * W;
      const frac = Math.min(1, Math.max(0, (relX - padL) / plotW));
      const targetKm = frac * totalKm;
      let best = pts[0], minDiff = Infinity;
      for (const p of pts) {
        const d = Math.abs(p[2] - targetKm);
        if (d < minDiff) { minDiff = d; best = p; }
      }
      const cx = xAt(best[2]).toFixed(1), cy = yAt(best[3]).toFixed(1);
      hLine.setAttribute('x1', cx); hLine.setAttribute('x2', cx);
      hLine.setAttribute('visibility', 'visible');
      hDot.setAttribute('cx', cx); hDot.setAttribute('cy', cy);
      hDot.setAttribute('visibility', 'visible');
      if (readout) {
        readout.innerHTML = `地点：スタートから <b>${best[2].toFixed(1)}km</b> ／ 実測標高 <b>${best[3].toFixed(1)}m</b> <span class="dim">（北緯${best[0].toFixed(3)}° 東経${best[1].toFixed(3)}°）</span>`;
      }
      if (activeSectionMap && typeof L !== 'undefined') {
        const latlng = [best[0], best[1]];
        if (!activeHoverMarker) {
          const icon = L.divIcon({ className: '', html: '<span class="dem-map-cursor"></span>', iconSize: [18, 18], iconAnchor: [9, 9] });
          activeHoverMarker = L.marker(latlng, { icon, interactive: false }).addTo(activeSectionMap);
        } else {
          activeHoverMarker.setLatLng(latlng);
          if (!activeSectionMap.hasLayer(activeHoverMarker)) activeHoverMarker.addTo(activeSectionMap);
        }
      }
    }

    svg.addEventListener('mousemove', (e) => onMove(e.clientX));
    svg.addEventListener('touchmove', (e) => { if (e.touches[0]) onMove(e.touches[0].clientX); }, { passive: true });
    svg.addEventListener('mouseleave', () => {
      hLine.setAttribute('visibility', 'hidden');
      hDot.setAttribute('visibility', 'hidden');
      if (activeHoverMarker && activeSectionMap) {
        activeSectionMap.removeLayer(activeHoverMarker);
        activeHoverMarker = null;
      }
    });
  }

  function renderWomenSection(r, no) {
    const leg = r.legs.find((item) => item.no === no);
    if (!leg) return;
    document.querySelectorAll('[data-women-section]').forEach((button) => button.setAttribute('aria-pressed', String(Number(button.dataset.womenSection) === no)));
    $('#women-section-summary').innerHTML = `<div><b>${leg.no}区</b><span>${esc(leg.from)} → ${esc(leg.to)}</span></div><strong>${leg.km.toFixed(1)}km</strong><p>${esc(leg.note)}</p>`;
    const profileEl = $('#women-section-profile');
    profileEl.innerHTML = womenSectionProfile(r, leg);
    bindDemCrossSectionHover(profileEl, r.series, leg.no);
  }

  function womenSectionProfile(r, leg) {
    const demLeg = ELEV_DATA && ELEV_DATA.series[r.series] ? ELEV_DATA.series[r.series].legs.find((l) => l.no === leg.no) : null;
    const graphic = demLeg
      ? renderDemCrossSectionSvg(demLeg, r.series)
      : `<div class="section-no-elevation"><b>標高データを読み込み中</b></div>`;
    return `<h4>${leg.no}区の実地形断面（国土地理院DEM）と走りどころ</h4>${graphic}<ol class="izumo-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(leg.from)}</b></div></li><li><span>→</span><div><small>公式の見どころ</small><b>${esc(leg.note)}</b></div></li><li><span>F</span><div><small>${leg.km.toFixed(1)}km</small><b>${esc(leg.to)}</b></div></li></ol><p class="section-source-note">標高断面は国土地理院の数値標高モデル（DEM）をコース経路に沿って輪切り抽出した実測地形データに基づきます。</p>`;
  }

  function zennihonSectionGuide(r) {
    return `<section class="hakone-section-guide zennihon-section-guide" aria-labelledby="zennihon-section-title">
      <div class="hakone-section-head">
        <div><p class="section-kicker">走者の目線で見る区間ガイド</p><h3 id="zennihon-section-title">1区ずつ、走る場所を見る</h3></div>
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
    const profileEl = $('#zennihon-section-profile');
    profileEl.innerHTML = zennihonSectionProfile(leg);
    const demLeg = ELEV_DATA && ELEV_DATA.series.zennihon ? ELEV_DATA.series.zennihon.legs.find((l) => l.no === leg.no) : null;
    const poly = demLeg && demLeg.samples ? demLeg.samples.map((p) => [p[0], p[1]]) : [start, finish];
    renderSimpleSectionMap({ elementId: 'zennihon-section-map', start, finish, poly, from: leg.from, to: leg.to, color: MAP_COLOR.zennihon });
    bindDemCrossSectionHover(profileEl, 'zennihon', leg.no);
  }

  function zennihonSectionProfile(leg) {
    const demLeg = ELEV_DATA && ELEV_DATA.series.zennihon ? ELEV_DATA.series.zennihon.legs.find((l) => l.no === leg.no) : null;
    const graphic = demLeg
      ? renderDemCrossSectionSvg(demLeg, 'zennihon')
      : '';
    return `<h4>${leg.no}区の実地形断面（国土地理院DEM）</h4>${graphic}<ol class="izumo-route-order zennihon-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(leg.from)}</b></div></li><li><span>F</span><div><small>${leg.km.toFixed(1)}km</small><b>${esc(leg.to)}</b></div></li></ol><p class="section-source-note">標高断面は国土地理院の数値標高モデル（DEM）をコース経路に沿って輪切り抽出した実測地形データに基づきます。</p>`;
  }

  function izumoSectionGuide(r) {
    return `<section class="hakone-section-guide izumo-section-guide" aria-labelledby="izumo-section-title">
      <div class="hakone-section-head">
        <div><p class="section-kicker">走者の目線で見る区間ガイド</p><h3 id="izumo-section-title">1区ずつ、走る場所を見る</h3></div>
        <div class="hakone-section-switch izumo-section-switch" role="group" aria-label="出雲駅伝の区間を選ぶ">${r.legs.map((leg) => `<button type="button" data-izumo-section="${leg.no}" aria-pressed="${leg.no === 1}">${leg.no}区</button>`).join('')}</div>
      </div>
      <div id="izumo-section-summary" class="hakone-section-summary" aria-live="polite"></div>
      <div class="hakone-section-grid">
        <div><div id="izumo-section-map" class="hakone-section-map" role="application" aria-label="出雲駅伝の区間別コース地図"></div><p class="course-map-note">地図: 国土地理院。断面図にマウスを重ねると、地図上にも対応する地点が表示されます。</p></div>
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
    const profileEl = $('#izumo-section-profile');
    profileEl.innerHTML = izumoSectionProfile(leg);
    const demLeg = ELEV_DATA && ELEV_DATA.series.izumo ? ELEV_DATA.series.izumo.legs.find((l) => l.no === leg.no) : null;
    const poly = demLeg && demLeg.samples ? demLeg.samples.map((p) => [p[0], p[1]]) : [start, finish];
    renderSimpleSectionMap({ elementId: 'izumo-section-map', start, finish, poly, from: leg.from, to: leg.to, color: MAP_COLOR.izumo });
    bindDemCrossSectionHover(profileEl, 'izumo', leg.no);
  }

  function izumoSectionProfile(leg) {
    const demLeg = ELEV_DATA && ELEV_DATA.series.izumo ? ELEV_DATA.series.izumo.legs.find((l) => l.no === leg.no) : null;
    const graphic = demLeg
      ? renderDemCrossSectionSvg(demLeg, 'izumo')
      : '';
    return `<h4>${leg.no}区の実地形断面（国土地理院DEM）と走りどころ</h4>${graphic}<ol class="izumo-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(leg.from)}</b></div></li><li><span>→</span><div><small>公式の見どころ</small><b>${esc(leg.note || '区間情報を確認中')}</b></div></li><li><span>F</span><div><small>${leg.km.toFixed(1)}km</small><b>${esc(leg.to)}</b></div></li></ol><p class="section-source-note">標高断面は国土地理院の数値標高モデル（DEM）をコース経路に沿って輪切り抽出した実測地形データに基づきます。</p>`;
  }

  function renderSimpleSectionMap(d) {
    const el = $('#' + d.elementId);
    if (!el || typeof L === 'undefined') return;
    if (activeSectionMap) activeSectionMap.remove();
    activeHoverMarker = null;
    activeSectionMap = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', { attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>', maxZoom: 18 }).addTo(activeSectionMap);
    const routeCoords = d.poly && d.poly.length > 2 ? d.poly : [d.start, d.finish];
    const line = L.polyline(routeCoords, { color: d.color, weight: 6, opacity: .88 }).addTo(activeSectionMap);
    [[d.start, 'S', d.from], [d.finish, 'F', d.to]].forEach(([pos, label, name]) => {
      const icon = L.divIcon({ className: '', html: `<span class="course-pin is-end" style="--pin:${d.color}">${label}</span>`, iconSize: [31,31], iconAnchor: [15.5,15.5] });
      L.marker(pos, { icon }).addTo(activeSectionMap).bindPopup(`<b>${label === 'S' ? 'スタート' : '中継所'}</b>${esc(name)}`);
    });
    activeSectionMap.fitBounds(line.getBounds(), { padding: [36, 36] });
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
        <div><p class="section-kicker">走者の目線で見る区間ガイド</p><h3 id="hakone-section-title">区間ごとに、どこを走るか見る</h3></div>
        <div class="hakone-section-switch hakone-all-section-switch" role="group" aria-label="箱根駅伝の区間を選ぶ">${r.legs.map((leg) => `<button type="button" data-hakone-section="${leg.no}" aria-pressed="${leg.no === 1}">${leg.no}区</button>`).join('')}</div>
      </div>
      <div id="hakone-section-summary" class="hakone-section-summary" aria-live="polite"></div>
      <div class="hakone-section-grid">
        <div><div id="hakone-section-map" class="hakone-section-map" role="application" aria-label="箱根駅伝の区間別コース地図"></div><p class="course-map-note">地図: 国土地理院。右の実地形断面図にマウスを重ねると、地図上にも対応する地点が表示されます。</p></div>
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
    const profileEl = $('#hakone-section-profile');
    profileEl.innerHTML = d.points.length > 2 ? hakoneSectionProfile(d) : hakoneSimpleSectionProfile(d);
    const demLeg = ELEV_DATA && ELEV_DATA.series.hakone ? ELEV_DATA.series.hakone.legs.find((l) => l.no === d.no) : null;
    if (demLeg && demLeg.samples && demLeg.samples.length > 2) {
      d.poly = demLeg.samples.map((p) => [p[0], p[1]]);
    }
    renderHakoneSectionMap(d);
    bindDemCrossSectionHover(profileEl, 'hakone', d.no);
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
    const demLeg = ELEV_DATA && ELEV_DATA.series.hakone ? ELEV_DATA.series.hakone.legs.find((l) => l.no === d.no) : null;
    const graphic = demLeg ? renderDemCrossSectionSvg(demLeg, 'hakone') : '';
    return `<h4>${d.no}区の実地形断面（国土地理院DEM）と走りどころ</h4>${graphic}<ol class="izumo-route-order hakone-route-order"><li><span>S</span><div><small>スタート</small><b>${esc(d.points[0].name)}</b></div></li><li><span>→</span><div><small>公式の見どころ</small><b>${esc(d.summary)}</b></div></li><li><span>F</span><div><small>${d.distance}</small><b>${esc(d.points[1].name)}</b></div></li></ol><p class="section-source-note">標高断面は国土地理院の数値標高モデル（DEM）をコース経路に沿って輪切り抽出した実測地形データに基づきます。</p>`;
  }

  function hakoneSectionProfile(d) {
    const stops = d.points.map((p, i) => `<li class="${i === 0 ? 'is-start' : i === d.points.length - 1 ? 'is-finish' : ''}"><span class="section-km">${p.km}</span><i aria-hidden="true"></i><span><b>${p.name}</b><small>${p.note}</small></span></li>`).join('');
    const demLeg = ELEV_DATA && ELEV_DATA.series.hakone ? ELEV_DATA.series.hakone.legs.find((l) => l.no === d.no) : null;
    const profile = demLeg ? renderDemCrossSectionSvg(demLeg, 'hakone') : '';
    return `<h4>${d.no}区の実地形断面（国土地理院DEM）と走る順番</h4>${profile}<ol class="section-timeline section-${d.no}">${stops}</ol><p class="section-source-note">標高断面は国土地理院の数値標高モデル（DEM）をコース経路に沿って輪切り抽出した実測地形データに基づきます。</p>`;
  }

  function renderHakoneSectionMap(d) {
    const el = $('#hakone-section-map');
    if (!el || typeof L === 'undefined') return;
    if (activeSectionMap) activeSectionMap.remove();
    activeHoverMarker = null;
    activeSectionMap = L.map(el, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png', { attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">国土地理院</a>', maxZoom: 18 }).addTo(activeSectionMap);
    const routeCoords = d.poly && d.poly.length > 2 ? d.poly : d.route;
    const line = L.polyline(routeCoords, { color: MAP_COLOR.hakone, weight: 6, opacity: .88 }).addTo(activeSectionMap);
    d.points.forEach((p, i) => {
      const end = i === 0 || i === d.points.length - 1;
      const icon = L.divIcon({ className: '', html: `<span class="course-pin${end ? ' is-end' : ''}" style="--pin:${MAP_COLOR.hakone}">${i === 0 ? 'S' : i === d.points.length - 1 ? 'F' : i}</span>`, iconSize: [end ? 31 : 26, end ? 31 : 26], iconAnchor: [end ? 15.5 : 13, end ? 15.5 : 13] });
      L.marker(p.pos, { icon }).addTo(activeSectionMap).bindPopup(`<b>${p.km}　${p.name}</b>${p.note}`);
    });
    activeSectionMap.fitBounds(line.getBounds(), { padding: [26, 26] });
  }

  // 国土地理院 数値標高モデル（DEM）を輪切りにしたコース全体の実地形断面図と、地図連携を描画する
  function elevationFeatureGraphic(r) {
    const demSeries = ELEV_DATA && ELEV_DATA.series[r.series];
    if (!demSeries) {
      return '<p class="course-elevation-note">国土地理院の数値標高モデル（DEM）から実地形断面を読み込んでいます…</p>';
    }

    // 区間リストを連結して、コース全体（または往路・復路ごと）の連続した地形断面ポリゴンを生成するヘルパー
    function buildFullCrossSection(legsSubset, boxX, boxY, boxW, boxH, ceilM, uid, color) {
      const totalKm = legsSubset.reduce((a, l) => a + l.km, 0);
      const xAt = (km) => boxX + (km / totalKm) * boxW;
      const baseY = boxY + boxH;
      const yAt = (m) => {
        if (ceilM >= 800) {
          if (m <= 100) return baseY - (Math.max(0, m) / 100) * (boxH * 0.36);
          return baseY - (boxH * 0.36) - Math.min(1, (m - 100) / 800) * (boxH * 0.64);
        }
        return baseY - Math.min(1, Math.max(0, m / ceilM)) * boxH;
      };

      let cumKm = 0;
      const allPts = [];
      const relayLines = [];
      legsSubset.forEach((leg, idx) => {
        if (idx > 0) relayLines.push({ km: cumKm, no: leg.no, from: leg.from });
        leg.samples.forEach((s, sIdx) => {
          if (idx > 0 && sIdx === 0) return;
          allPts.push([cumKm + s[2], s[3], leg.no]);
        });
        cumKm += leg.km;
      });

      const poly = allPts.map((p) => `${xAt(p[0]).toFixed(1)},${yAt(p[1]).toFixed(1)}`).join(' ');
      const area = `M${xAt(0).toFixed(1)},${baseY} L` + allPts.map((p) => `${xAt(p[0]).toFixed(1)},${yAt(p[1]).toFixed(1)}`).join(' L') + ` L${xAt(totalKm).toFixed(1)},${baseY} Z`;
      const soil = `M${xAt(0).toFixed(1)},${baseY} L` + allPts.map((p) => `${xAt(p[0]).toFixed(1)},${Math.min(baseY, yAt(p[1]) + 10).toFixed(1)}`).join(' L') + ` L${xAt(totalKm).toFixed(1)},${baseY} Z`;

      // 標高グリッド
      const steps = ceilM >= 800 ? [0, 400, 800] : ceilM >= 150 ? [0, 100, 180] : ceilM >= 70 ? [0, 35, 70] : [0, 20, 40];
      const grid = steps.map((m) => {
        const y = yAt(m).toFixed(1);
        return `<line x1="${boxX}" y1="${y}" x2="${boxX + boxW}" y2="${y}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="${m === 0 ? '' : '3 2'}"/>
                <text x="${boxX - 5}" y="${(Number(y) + 3.5).toFixed(1)}" font-size="9.5" font-weight="700" text-anchor="end" fill="#64748b">${m}m</text>`;
      }).join('');

      // 中継所ごとの垂直輪切りスリット線と区間番号
      let relays = '';
      let prevKm = 0;
      legsSubset.forEach((leg, idx) => {
        const midKm = prevKm + leg.km / 2;
        relays += `<text x="${xAt(midKm).toFixed(1)}" y="${baseY - 4}" font-size="9.5" font-weight="800" text-anchor="middle" fill="${color}" opacity="0.85">${leg.no}区</text>`;
        if (idx > 0) {
          const rx = xAt(prevKm).toFixed(1);
          relays += `<line x1="${rx}" y1="${boxY + 4}" x2="${rx}" y2="${baseY}" stroke="#475569" stroke-width="1" stroke-dasharray="2 2" stroke-opacity="0.55"/>`;
        }
        prevKm += leg.km;
      });

      // 最高地点
      let maxP = allPts[0];
      allPts.forEach((p) => { if (p[1] > maxP[1]) maxP = p; });
      const mx = xAt(maxP[0]), my = yAt(maxP[1]);
      const anchor = mx > boxX + boxW - 85 ? 'end' : mx < boxX + 85 ? 'start' : 'middle';

      return `
        <defs>
          <linearGradient id="${uid}-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${color}" stop-opacity="0.55"/>
            <stop offset="65%" stop-color="#b45309" stop-opacity="0.24"/>
            <stop offset="100%" stop-color="#78350f" stop-opacity="0.12"/>
          </linearGradient>
          <pattern id="${uid}-hatch" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="6" stroke="#78350f" stroke-opacity="0.15" stroke-width="1.5"/>
          </pattern>
        </defs>
        ${grid}
        <path d="${area}" fill="url(#${uid}-fill)"/>
        <path d="${soil}" fill="url(#${uid}-hatch)"/>
        ${relays}
        <polyline fill="none" stroke="${color}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" points="${poly}"/>
        <line x1="${boxX}" y1="${baseY}" x2="${boxX + boxW}" y2="${baseY}" stroke="#334155" stroke-width="2"/>
        <circle cx="${mx.toFixed(1)}" cy="${my.toFixed(1)}" r="4.5" fill="#fbbf24" stroke="${color}" stroke-width="2"/>
        <text x="${mx.toFixed(1)}" y="${Math.max(boxY + 10, my - 6).toFixed(1)}" font-size="10" font-weight="800" text-anchor="${anchor}" fill="#92400e">▲ 最高 ${maxP[1].toFixed(0)}m（${maxP[2]}区）</text>
      `;
    }

    const c = MAP_COLOR[r.series] || '#0f766e';
    if (r.series === 'hakone') {
      const outLegs = demSeries.legs.slice(0, 5);
      const retLegs = demSeries.legs.slice(5, 10);
      return `<svg class="course-elevation" viewBox="0 0 420 340" role="img" aria-label="国土地理院の標高データに基づく箱根駅伝の往路・復路実地形断面図">
        <text x="38" y="22" class="elev-kicker">往路（1〜5区 107.5km）実地形断面</text>
        ${buildFullCrossSection(outLegs, 40, 32, 362, 96, 900, 'hk-out-dem', '#0f766e')}
        <g class="elev-place"><text x="40" y="145">大手町(6m)</text><text x="172" y="145" text-anchor="middle">権太坂・戸塚(70m)</text><text x="292" y="145" text-anchor="middle">小田原(35m)</text><text x="402" y="145" text-anchor="end">芦ノ湖(743m)</text></g>
        <text x="38" y="184" class="elev-kicker">復路（6〜10区 109.6km）実地形断面</text>
        ${buildFullCrossSection(retLegs, 40, 194, 362, 96, 900, 'hk-ret-dem', '#0f766e')}
        <g class="elev-place"><text x="40" y="308">芦ノ湖(743m)</text><text x="148" y="308" text-anchor="middle">小田原(35m)</text><text x="268" y="308" text-anchor="middle">遊行寺坂(69m)</text><text x="402" y="308" text-anchor="end">大手町(6m)</text></g>
      </svg><p class="course-elevation-note"><b>実地形の輪切り（国土地理院DEM）:</b> 2区権太坂・戸塚の壁（約70m）から4区小田原（35m）、5区の最高点（約874m）・芦ノ湖（743m）まで、実際の道路座標の標高を断面表示しています。</p>`;
    }

    const maxAll = Math.max(...demSeries.legs.map((l) => l.max_m));
    const ceil = maxAll > 150 ? 200 : maxAll > 60 ? 80 : 40;
    const startName = demSeries.legs[0].from;
    const endName = demSeries.legs[demSeries.legs.length - 1].to;
    const startElev = demSeries.legs[0].samples[0][3].toFixed(0);
    const endSamples = demSeries.legs[demSeries.legs.length - 1].samples;
    const endElev = endSamples[endSamples.length - 1][3].toFixed(0);
    const notes = {
      izumo: '1区浜山公園付近（約20m）と、5区鳶巣〜島根ワイナリー間の丘陵（最高約69m）の実地形起伏がはっきり表れます。',
      zennihon: '1〜2区の木曽三川河口域（海抜0〜4m）、3〜4区の四日市・鈴鹿の段丘（最高28m）、8区伊勢神宮内宮へ向かう緩やかな上り（約26m）を実測標高で断面化しています。',
      wzennihon: '仙台市内の海岸平野側（2区・標高5m）から、広瀬川を越え5区の仙台城跡・東北大川内周辺（最高約54m）へ上る実地形断面です。',
      wfujisan: '富士山本宮浅間大社（標高119m）から2区で富士市街（18m）へ一気に100m以上下り、最終7区で富士総合運動公園（約173m）へ駆け上がる劇的な断面です。'
    };

    return `<svg class="course-elevation" viewBox="0 0 420 270" role="img" aria-label="国土地理院の標高データに基づく${esc(r.name)}の実地形断面図">
      <text x="38" y="24" class="elev-kicker">${esc(r.name)}（全${demSeries.legs.length}区間 ${r.distance_km}km）実地形断面</text>
      ${buildFullCrossSection(demSeries.legs, 40, 38, 362, 165, ceil, `ov-${r.series}-dem`, c)}
      <g class="elev-place">
        <text x="40" y="224">${esc(startName)}(${startElev}m)</text>
        <text x="402" y="224" text-anchor="end">${esc(endName)}(${endElev}m)</text>
      </g>
    </svg><p class="course-elevation-note"><b>実地形の輪切り（国土地理院DEM）:</b> ${esc(notes[r.series] || '')}</p>`;
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
    // 実道路ポリライン（ELEV_DATA）があれば実際の走行ルートに沿って描画する
    const demSeries = ELEV_DATA && ELEV_DATA.series[r.series];
    let polyCoords = d.coords;
    if (demSeries) {
      const legsToDraw = r.series === 'hakone' ? demSeries.legs.slice(0, 5) : demSeries.legs;
      polyCoords = [];
      legsToDraw.forEach((leg) => leg.samples.forEach((s) => polyCoords.push([s[0], s[1]])));
    }
    const line = L.polyline(polyCoords, { color: MAP_COLOR[r.series], weight: 5, opacity: .85 }).addTo(activeCourseMap);
    d.coords.forEach((latlng, i) => {
      const end = i === 0 || i === d.coords.length - 1;
      const icon = L.divIcon({ className: '', html: `<span class="course-pin${end ? ' is-end' : ''}" style="--pin:${MAP_COLOR[r.series]}">${i === 0 ? 'S' : i === d.coords.length - 1 ? 'F' : i}</span>`, iconSize: [end ? 31 : 26, end ? 31 : 26], iconAnchor: [end ? 15.5 : 13, end ? 15.5 : 13] });
      const role = i === 0 ? 'スタート' : i === d.coords.length - 1 ? (r.series === 'hakone' ? '往路ゴール・復路スタート' : 'フィニッシュ') : `第${i}中継所`;
      L.marker(latlng, { icon }).addTo(activeCourseMap).bindPopup(`<b>${esc(role)}</b>${esc(d.short[i])}`);
    });
    activeCourseMap.fitBounds(line.getBounds(), { padding: [28, 28] });
  }

  // 区間の長さに合わせた帯＋国土地理院DEMの実地形輪切り断面を重ねた図
  function courseStrip(r, legs, points, title, mountain) {
    const W = 760, L = 34, R = 30, y = 128, topY = 38, profH = 74, H = y + 90;
    const total = legs.reduce((a, l) => a + l.km, 0);
    const scale = (W - L - R) / total;
    const c = MAP_COLOR[r.series] || '#0f766e';
    let x = L;
    let g = `<text x="${L}" y="22" font-size="14" font-weight="800" fill="var(--ink)">${esc(title)}</text><text x="${W - R}" y="22" font-size="12" font-weight="700" text-anchor="end" fill="var(--muted)">実地形断面（国土地理院DEM） ／ 総距離 ${Math.round(total * 10) / 10}km</text>`;

    // 実地形断面（ELEV_DATA）から連続断面ポリゴンを構築
    const demSeries = ELEV_DATA && ELEV_DATA.series[r.series];
    if (demSeries) {
      const demLegs = legs.map((l) => demSeries.legs.find((dl) => dl.no === l.no)).filter(Boolean);
      if (demLegs.length === legs.length) {
        // 箱根駅伝の1〜4区・7〜10区（最高70m）と5・6区（最高874m）の両方が一つの断面図で鮮明に見えるよう、
        // 100m以下を45%の高さで描き、100m〜900mを上部55%で描く「二段地形断面スケール（実測値目盛り付き）」を採用
        const isHakone = r.series === 'hakone';
        const maxM = Math.max(...demLegs.map((dl) => dl.max_m));
        const ceilM = maxM > 150 ? 200 : maxM > 60 ? 80 : 40;
        const baseY = y - 8;
        const elevToY = (m) => {
          if (isHakone) {
            if (m <= 100) return baseY - (m / 100) * (profH * 0.42);
            return baseY - (profH * 0.42) - Math.min(1, (m - 100) / 800) * (profH * 0.58);
          }
          return baseY - Math.min(1, Math.max(0, m / ceilM)) * profH;
        };

        const uid = `strip-dem-${r.series}-${legs[0].no}`;
        g += `<defs>
          <linearGradient id="${uid}-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${c}" stop-opacity="0.50"/>
            <stop offset="65%" stop-color="#b45309" stop-opacity="0.24"/>
            <stop offset="100%" stop-color="#78350f" stop-opacity="0.10"/>
          </linearGradient>
          <pattern id="${uid}-hatch" width="6" height="6" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="6" stroke="#78350f" stroke-opacity="0.16" stroke-width="1.5"/>
          </pattern>
        </defs>`;

        // 標高基準破線
        const refLevels = isHakone ? [50, 400, 800] : (ceilM === 200 ? [50, 150] : ceilM === 80 ? [30, 60] : [15, 30]);
        refLevels.forEach((rm) => {
          const ry = elevToY(rm).toFixed(1);
          g += `<line x1="${L}" y1="${ry}" x2="${W - R}" y2="${ry}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="3 3"/>`;
          g += `<text x="${L - 4}" y="${(Number(ry) + 3).toFixed(1)}" font-size="9" font-weight="700" text-anchor="end" fill="#64748b">${rm}m</text>`;
        });

        let cumKm = 0;
        const allPts = [];
        demLegs.forEach((dl, idx) => {
          dl.samples.forEach((s, sIdx) => {
            if (idx > 0 && sIdx === 0) return;
            const px = L + (cumKm + s[2]) * scale;
            const py = elevToY(s[3]);
            allPts.push({ x: px, y: py, km: cumKm + s[2], m: s[3], no: dl.no });
          });
          cumKm += dl.km;
        });

        const polyStr = allPts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
        const areaStr = `M${L},${baseY} L` + allPts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L') + ` L${(L + total * scale).toFixed(1)},${baseY} Z`;
        const soilStr = `M${L},${baseY} L` + allPts.map((p) => `${p.x.toFixed(1)},${Math.min(baseY, p.y + 10).toFixed(1)}`).join(' L') + ` L${(L + total * scale).toFixed(1)},${baseY} Z`;

        g += `<path d="${areaStr}" fill="url(#${uid}-fill)"/>`;
        g += `<path d="${soilStr}" fill="url(#${uid}-hatch)"/>`;
        // 地形輪切りスリット線
        for (let i = 6; i < allPts.length - 1; i += 6) {
          g += `<line x1="${allPts[i].x.toFixed(1)}" y1="${allPts[i].y.toFixed(1)}" x2="${allPts[i].x.toFixed(1)}" y2="${baseY}" stroke="${c}" stroke-opacity="0.16" stroke-width="1"/>`;
        }
        g += `<polyline fill="none" stroke="${c}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" points="${polyStr}"/>`;

        // 箱根2区・8区（権太坂・戸塚の壁 約70m）や5区・6区（最高点 約874m）などの実測ピーク注記
        if (isHakone && mountain) {
          // 2区の最高点（戸塚・権太坂付近）
          const leg2Pts = allPts.filter((p) => p.no === 2);
          const p2Max = leg2Pts.reduce((a, b) => (b.m > a.m ? b : a), leg2Pts[0]);
          if (p2Max) {
            g += `<circle cx="${p2Max.x.toFixed(1)}" cy="${p2Max.y.toFixed(1)}" r="3.2" fill="#fff" stroke="${c}" stroke-width="2"/>`;
            g += `<text x="${(p2Max.x - 10).toFixed(1)}" y="${(p2Max.y - 6).toFixed(1)}" font-size="10" font-weight="800" text-anchor="middle" fill="#0f766e">権太坂・戸塚の壁 ${p2Max.m.toFixed(0)}m</text>`;
          }
          // 5区の最高点（874m）
          const leg5Pts = allPts.filter((p) => p.no === 5);
          const p5Max = leg5Pts.reduce((a, b) => (b.m > a.m ? b : a), leg5Pts[0]);
          if (p5Max) {
            g += `<circle cx="${p5Max.x.toFixed(1)}" cy="${p5Max.y.toFixed(1)}" r="4.5" fill="#fbbf24" stroke="#b45309" stroke-width="2"/>`;
            g += `<text x="${(p5Max.x - 6).toFixed(1)}" y="${(p5Max.y - 7).toFixed(1)}" font-size="11" font-weight="800" text-anchor="end" fill="#92400e">▲ 国道1号最高点 標高約874m</text>`;
          }
        } else if (isHakone && !mountain) {
          // 6区の最高点（874m）と8区遊行寺坂（69m）
          const leg6Pts = allPts.filter((p) => p.no === 6);
          const p6Max = leg6Pts.reduce((a, b) => (b.m > a.m ? b : a), leg6Pts[0]);
          if (p6Max) {
            g += `<circle cx="${p6Max.x.toFixed(1)}" cy="${p6Max.y.toFixed(1)}" r="4.5" fill="#fbbf24" stroke="#b45309" stroke-width="2"/>`;
            g += `<text x="${(p6Max.x + 8).toFixed(1)}" y="${(p6Max.y - 5).toFixed(1)}" font-size="11" font-weight="800" text-anchor="start" fill="#92400e">▲ 最高点 約874mから山下り（-949m）</text>`;
          }
          const leg8Pts = allPts.filter((p) => p.no === 8);
          const p8Max = leg8Pts.reduce((a, b) => (b.m > a.m ? b : a), leg8Pts[0]);
          if (p8Max) {
            g += `<circle cx="${p8Max.x.toFixed(1)}" cy="${p8Max.y.toFixed(1)}" r="3.2" fill="#fff" stroke="${c}" stroke-width="2"/>`;
            g += `<text x="${p8Max.x.toFixed(1)}" y="${(p8Max.y - 6).toFixed(1)}" font-size="10" font-weight="800" text-anchor="middle" fill="#0f766e">遊行寺坂 ${p8Max.m.toFixed(0)}m</text>`;
          }
        }
      }
    }

    const xs = [x];
    const SUB_TAG = { 1: '開幕区間', 2: '花の2区', 3: '湘南・富士', 4: '山へのつなぎ', 5: '山上り', 6: '山下り', 7: '寒暖差', 8: '遊行寺坂', 9: '復路エース', 10: '日本橋・大手町' };
    legs.forEach((l, i) => {
      const w = l.km * scale;
      const isPeakLeg = (r.series === 'hakone' && (l.no === 5 || l.no === 6)) || (r.series === 'wfujisan' && l.no === 7);
      const wx = x;
      if (i > 0) {
        g += `<line x1="${wx.toFixed(1)}" y1="${topY}" x2="${wx.toFixed(1)}" y2="${y - 7}" stroke="#475569" stroke-width="1" stroke-dasharray="2 2" stroke-opacity="0.5"/>`;
      }
      g += `<rect x="${x.toFixed(1)}" y="${y - 7}" width="${(w - 3).toFixed(1)}" height="14" rx="7" fill="${isPeakLeg ? '#d97706' : COLOR[r.series]}" fill-opacity="${i % 2 ? 0.68 : 0.95}"/>`;
      const cx = (x + w / 2).toFixed(1);
      g += `<text x="${cx}" y="${y + 20}" text-anchor="middle" font-size="11.5" font-weight="800" fill="${isPeakLeg ? '#92400e' : 'var(--ink)'}">${l.no}区 <tspan font-weight="700">${l.km.toFixed(1)}km</tspan></text>`;
      if (r.series === 'hakone' && SUB_TAG[l.no]) {
        g += `<text x="${cx}" y="${y + 33}" text-anchor="middle" font-size="9.5" font-weight="700" fill="${isPeakLeg ? '#b45309' : 'var(--ink-soft)'}">（${SUB_TAG[l.no]}）</text>`;
      }
      x += w;
      xs.push(x);
    });
    points.forEach((p, i) => {
      const px = Math.min(xs[i], W - R);
      const end = i === 0 || i === points.length - 1;
      g += `<circle cx="${px.toFixed(1)}" cy="${y}" r="${end ? 7 : 5}" fill="#fff" stroke="var(--ink)" stroke-width="2.2"/>`;
      const anchor = i === 0 ? 'start' : i === points.length - 1 ? 'end' : 'middle';
      if (i % 2 && !end) g += `<line x1="${px.toFixed(1)}" y1="${y + 36}" x2="${px.toFixed(1)}" y2="${y + 56}" stroke="var(--line)" stroke-width="1.5"/>`;
      g += `<text x="${(i === 0 ? px - 4 : i === points.length - 1 ? px + 4 : px).toFixed(1)}" y="${y + (i % 2 && !end ? 70 : 50)}" text-anchor="${anchor}" font-size="12" font-weight="${end ? 800 : 600}" fill="var(--ink)">${esc(p)}</text>`;
    });
    return `<svg class="fig course" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(r.name)} ${esc(title)} の実地形断面・区間図">${g}</svg>`;
  }

  // 人物は生成済みのアニメ風イラストを使い、線や距離表示だけをSVGで重ねる。
  function relayFigure() {
    const W = 720, H = 250, x0 = 250, zone = 360;
    const art = G === 'women' ? 'assets/relay-women.svg' : 'assets/relay-men.svg';
    return `<svg class="fig" viewBox="0 0 ${W} ${H}" role="img" aria-label="たすきの受け渡しは中継線から前方20mの中継ゾーンで行う">
      <rect x="18" y="165" width="${W - 36}" height="14" rx="4" fill="#e9e5d8"/>
      <rect x="${x0}" y="36" width="${zone}" height="150" rx="14" fill="var(--gold-soft)" fill-opacity=".62"/>
      <line x1="${x0}" y1="30" x2="${x0}" y2="186" stroke="var(--ink)" stroke-width="3"/>
      <text x="${x0}" y="24" text-anchor="middle" font-size="13" font-weight="700" fill="var(--ink)">中継線</text>
      <image href="${art}" x="265" y="42" width="320" height="164" preserveAspectRatio="xMidYMid meet"/>
      <path d="M${x0 + 4} 214 H${x0 + zone - 4}" stroke="var(--ink)" stroke-width="1.5" marker-end="url(#arr)" marker-start="url(#arr)"/>
      <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="var(--ink)"/></marker></defs>
      <text x="${x0 + zone / 2}" y="239" text-anchor="middle" font-size="13" font-weight="700" fill="var(--ink)">中継ゾーン（中継線から前方20m）</text>
      <text x="38" y="90" font-size="13" fill="var(--ink-soft)">前の区間の選手が</text><text x="38" y="112" font-size="13" fill="var(--ink-soft)">たすきをつなぐ</text>
      <text x="${W - 28}" y="146" text-anchor="end" font-size="13" fill="var(--ink-soft)">進む向き →</text>
    </svg>`;
  }

  /* ---------- 記録から探す ---------- */
  function renderRecord() {
    const crowns = [];
    S.summary.forEach((sm) => (sm[GENDER[G].crownKey] || []).forEach((y) => crowns.push([y, sm.team_id])));
    crowns.sort((a, b) => a[0] - b[0]);
    $('#triple-list').innerHTML = crowns.map(([y, tid]) => {
      const tm = S.teamById.get(tid);
      return `<li class="crown-list-item"><span class="crown-year-badge">👑 ${seasonLabel(y)}</span> ${tasukiSwatch(tm.display_name, 'sm')}<button type="button" class="link" data-team="${tid}">${esc(tm.display_name)}</button></li>`;
    }).join('') || '<li>収録範囲ではなし</li>';
    const wins = [...S.summary.values()].map((sm) => ({ tid: sm.team_id, w: SERIES.map((s) => sm.series[s]?.wins || 0) }))
      .filter((x) => x.w.some(Boolean)).sort((a, b) => b.w.reduce((p, q) => p + q) - a.w.reduce((p, q) => p + q));
    $('#wins-table').innerHTML = `<thead><tr><th>チーム</th>${SERIES.map((s) => `<th class="num">${SERIES_SHORT[s]}</th>`).join('')}<th class="num">計</th></tr></thead><tbody>${
      wins.map((x) => {
        const tm = S.teamById.get(x.tid);
        return `<tr><td><div class="team-cell-inner">${tasukiSwatch(tm.display_name, 'sm')}<button type="button" class="link" data-team="${x.tid}">${esc(tm.display_name)}</button></div></td>${x.w.map((n) => `<td class="num">${n || ''}</td>`).join('')}<td class="num"><strong>${x.w.reduce((p, q) => p + q)}</strong></td></tr>`;
      }).join('')}</tbody>`;
    document.querySelectorAll('#panel-record [data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
    renderWinners();
  }
  function renderWinners() {
    const s = $('#w-series').value;
    const list = S.taikai.filter((t) => t.series === s).sort((a, b) => edOf(b) - edOf(a));
    $('#winners-table').innerHTML = `<thead><tr><th class="num">回</th><th>年</th><th>優勝</th><th class="num">記録</th></tr></thead><tbody>${
      list.map((t) => {
        const team = t.winner_team_id && S.teamById.get(t.winner_team_id);
        const name = t.status === 'cancelled' ? '<span class="status">中止</span>' : team ? `<div class="team-cell-inner">${tasukiSwatch(team.display_name, 'sm')}<button type="button" class="link" data-team="${team.id}">${esc(t.winner_name)}</button></div>` : `<div class="team-cell-inner">${tasukiSwatch(t.winner_name, 'sm')}<span>${esc(t.winner_name || '')}</span></div>`;
        return `<tr><td class="num">${t.series === 'wfujisan' ? '' : t.edition}</td><td>${t.year}</td><td>${name}</td><td class="num">${esc(t.winning_time || '')}</td></tr>`;
      }).join('')}</tbody>`;
    $('#winners-table').querySelectorAll('[data-team]').forEach((b) => b.addEventListener('click', () => { selectTab('univ', false); showTeam(b.dataset.team, true); }));
  }
})();
