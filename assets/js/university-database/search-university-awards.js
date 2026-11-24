(() => {
  'use strict';

  const DATA_URL = '/tools/university-database/awards/data/university_awards.json';

  const kpiAll = document.getElementById('ua-kpi-all');
  const kpiSports = document.getElementById('ua-kpi-sports');
  const kpiCulture = document.getElementById('ua-kpi-culture');
  const kpiMusic = document.getElementById('ua-kpi-music');
  const kpiBtns = Array.from(document.querySelectorAll('.ua-kpi'));

  const quickChipsEl = document.getElementById('ua-quick-chips');
  const keywordInput = document.getElementById('ua-keyword');
  const prefSelect = document.getElementById('ua-pref');
  const catSelect = document.getElementById('ua-category');
  const resetBtn = document.getElementById('ua-reset');

  const regionBarsEl = document.getElementById('ua-region-bars');
  const topPrefsEl = document.getElementById('ua-top-prefs');
  const countEl = document.getElementById('ua-count');
  const activeFiltersEl = document.getElementById('ua-active-filters');
  const resultsEl = document.getElementById('ua-results');
  const sourcesEl = document.getElementById('ua-sources-list');

  let allUnivs = [];
  let activeTab = 'all';
  let activeRegion = '';

  const REGIONS = [
    { id: 'hokkaido-tohoku', label: '北海道・東北', slugs: ['hokkaido', 'aomori', 'iwate', 'miyagi', 'akita', 'yamagata', 'fukushima'] },
    { id: 'kanto', label: '関東', slugs: ['ibaraki', 'tochigi', 'gunma', 'saitama', 'chiba', 'tokyo', 'kanagawa'] },
    { id: 'chubu', label: '中部', slugs: ['niigata', 'toyama', 'ishikawa', 'fukui', 'yamanashi', 'nagano', 'gifu', 'shizuoka', 'aichi'] },
    { id: 'kinki', label: '近畿', slugs: ['mie', 'shiga', 'kyoto', 'osaka', 'hyogo', 'nara', 'wakayama'] },
    { id: 'chugoku-shikoku', label: '中国・四国', slugs: ['tottori', 'shimane', 'okayama', 'hiroshima', 'yamaguchi', 'tokushima', 'kagawa', 'ehime', 'kochi'] },
    { id: 'kyushu-okinawa', label: '九州・沖縄', slugs: ['fukuoka', 'saga', 'nagasaki', 'kumamoto', 'oita', 'miyazaki', 'kagoshima', 'okinawa'] },
  ];

  const CATEGORY_GROUPS = {
    sports: [
      { value: '野球', label: '野球', icon: '⚾' },
      { value: 'サッカー', label: 'サッカー', icon: '⚽' },
      { value: 'ラグビー', label: 'ラグビー', icon: '🏉' },
      { value: 'バレーボール', label: 'バレー', icon: '🏐' },
      { value: 'バスケットボール', label: 'バスケ', icon: '🏀' },
      { value: '柔道', label: '柔道', icon: '🥋' },
      { value: '剣道', label: '剣道', icon: '⚔️' },
      { value: '陸上競技', label: '陸上', icon: '🏃' },
      { value: '水泳', label: '水泳', icon: '🏊' },
      { value: 'テニス', label: 'テニス', icon: '🎾' },
      { value: '卓球', label: '卓球', icon: '🏓' },
      { value: 'バドミントン', label: 'バドミントン', icon: '🏸' },
      { value: 'アメリカンフットボール', label: 'アメフト', icon: '🏈' },
    ],
    culture: [
      { value: '将棋', label: '将棋', icon: '♟️' },
      { value: '囲碁', label: '囲碁', icon: '⚫' },
      { value: 'ロボコン', label: 'ロボコン', icon: '🤖' },
      { value: '競技かるた', label: '競技かるた', icon: '🎴' },
      { value: '競技プログラミング', label: 'ICPCプログラミング', icon: '💻' },
      { value: '書道', label: '書道', icon: '🖌️' },
      { value: '軽音楽・ジャズ', label: '軽音・ジャズ', icon: '🎷' },
      { value: 'ダンス・パフォーマンス', label: 'ダンス', icon: '💃' },
    ],
    music: [
      { value: '全日本吹奏楽コンクール', label: '全日本吹奏楽', icon: '🎺' },
      { value: '全日本合唱コンクール', label: '全日本合唱', icon: '🎤' },
    ],
  };

  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function matchesTab(u, tab) {
    if (tab === 'sports') return u.sports_awards.length > 0;
    if (tab === 'culture') return u.culture_awards.length > 0;
    if (tab === 'music') return u.music_awards.length > 0;
    return true;
  }

  function matchesCategory(u, cat) {
    if (!cat) return true;
    return (
      u.sports_awards.some(x => x.category === cat) ||
      u.culture_awards.some(x => x.category === cat) ||
      u.music_awards.some(x => x.category === cat || x.contest === cat)
    );
  }

  function populateCategories() {
    const prev = catSelect.value;
    const opts = ['<option value="">すべての競技・分野</option>'];
    const addGroup = (label, items) => {
      opts.push(`<optgroup label="${esc(label)}">`);
      items.forEach(it => opts.push(`<option value="${esc(it.value)}">${esc(it.label)}</option>`));
      opts.push('</optgroup>');
    };
    if (activeTab === 'all' || activeTab === 'sports') addGroup('運動・武道', CATEGORY_GROUPS.sports);
    if (activeTab === 'all' || activeTab === 'culture') addGroup('文化・学術', CATEGORY_GROUPS.culture);
    if (activeTab === 'all' || activeTab === 'music') addGroup('音楽コンクール', CATEGORY_GROUPS.music);
    catSelect.innerHTML = opts.join('');
    if (prev && Array.from(catSelect.options).some(o => o.value === prev)) {
      catSelect.value = prev;
    } else {
      catSelect.value = '';
    }
  }

  function renderQuickChips() {
    const pref = prefSelect.value;
    const pool = allUnivs.filter(u => {
      if (pref && u.pref_slug !== pref) return false;
      if (activeRegion) {
        const reg = REGIONS.find(r => r.id === activeRegion);
        if (reg && !reg.slugs.includes(u.pref_slug)) return false;
      }
      return matchesTab(u, activeTab);
    });

    const items = [];
    if (activeTab === 'all') {
      items.push(
        ...CATEGORY_GROUPS.sports.map(x => ({ ...x, domain: 'sports' })),
        ...CATEGORY_GROUPS.culture.map(x => ({ ...x, domain: 'culture' })),
        ...CATEGORY_GROUPS.music.map(x => ({ ...x, domain: 'music' }))
      );
    } else {
      items.push(...CATEGORY_GROUPS[activeTab].map(x => ({ ...x, domain: activeTab })));
    }

    const cur = catSelect.value;
    quickChipsEl.innerHTML = [
      `<button type="button" class="ua-qchip ${!cur ? 'is-active' : ''}" data-cat="">すべて <span class="ua-qchip-cnt">${pool.length}</span></button>`,
      ...items.map(it => {
        const cnt = pool.filter(u => matchesCategory(u, it.value)).length;
        return `<button type="button" class="ua-qchip ua-qchip--${it.domain} ${cur === it.value ? 'is-active' : ''}" data-cat="${esc(it.value)}">${it.icon} ${esc(it.label)} <span class="ua-qchip-cnt">${cnt}</span></button>`;
      })
    ].join('');

    quickChipsEl.querySelectorAll('.ua-qchip').forEach(btn => {
      btn.addEventListener('click', () => {
        const v = btn.dataset.cat || '';
        catSelect.value = (catSelect.value === v && v !== '') ? '' : v;
        applyFilter();
      });
    });
  }

  function classifyMedal(awardText) {
    const a = String(awardText || '');
    if (/優勝|金賞|最優秀|1位/.test(a)) return { cls: 'ua-medal--gold', icon: '🥇' };
    if (/準優勝|銀賞|決勝進出/.test(a)) return { cls: 'ua-medal--silver', icon: '🥈' };
    if (/3位|銅賞|優秀校/.test(a)) return { cls: 'ua-medal--bronze', icon: '🥉' };
    return { cls: 'ua-medal--other', icon: '🏅' };
  }

  function collectAwards(u) {
    const list = [];
    if (activeTab === 'all' || activeTab === 'sports') {
      u.sports_awards.forEach(x => list.push(x));
    }
    if (activeTab === 'all' || activeTab === 'culture') {
      u.culture_awards.forEach(x => list.push(x));
    }
    if (activeTab === 'all' || activeTab === 'music') {
      u.music_awards.forEach(x => list.push(x));
    }
    return list;
  }

  function renderAwardRow(aw) {
    const m = classifyMedal(aw.award);
    const meta = [aw.category, aw.year, aw.division, aw.detail].filter(Boolean).join(' / ');
    return `
      <div class="ua-aw-row">
        <span class="ua-medal ${m.cls}">${m.icon} ${esc(aw.award)}</span>
        <div class="ua-aw-body">
          <div class="ua-aw-title">${esc(aw.contest || aw.category)}</div>
          ${meta ? `<span class="ua-aw-meta">${esc(meta)}</span>` : ''}
        </div>
      </div>
    `;
  }

  function renderCharts(pool) {
    const fillCls = activeTab === 'all' ? '' : `ua-bar-fill--${activeTab}`;

    const regCounts = REGIONS.map(r => ({
      id: r.id,
      label: r.label,
      count: pool.filter(u => r.slugs.includes(u.pref_slug)).length,
    }));
    const maxReg = Math.max(1, ...regCounts.map(r => r.count));
    regionBarsEl.innerHTML = regCounts.map(r => {
      const pct = Math.round((r.count / maxReg) * 100);
      return `
        <button type="button" class="ua-bar-row ${activeRegion === r.id ? 'is-active' : ''}" data-region="${r.id}">
          <span class="ua-bar-label">${esc(r.label)}</span>
          <span class="ua-bar-track"><span class="ua-bar-fill ${fillCls}" style="width:${pct}%"></span></span>
          <span class="ua-bar-val">${r.count}校</span>
        </button>
      `;
    }).join('');

    regionBarsEl.querySelectorAll('.ua-bar-row').forEach(btn => {
      btn.addEventListener('click', () => {
        const rid = btn.dataset.region || '';
        activeRegion = (activeRegion === rid) ? '' : rid;
        if (activeRegion) prefSelect.value = '';
        applyFilter();
      });
    });

    const pMap = new Map();
    pool.forEach(u => {
      if (!u.pref_slug) return;
      const cur = pMap.get(u.pref_slug) || { slug: u.pref_slug, name: u.pref, count: 0 };
      cur.count += 1;
      pMap.set(u.pref_slug, cur);
    });
    const topPrefs = Array.from(pMap.values()).sort((a, b) => b.count - a.count).slice(0, 6);
    const maxP = Math.max(1, ...topPrefs.map(p => p.count));
    const curP = prefSelect.value;

    topPrefsEl.innerHTML = topPrefs.length ? topPrefs.map(p => {
      const pct = Math.round((p.count / maxP) * 100);
      return `
        <button type="button" class="ua-bar-row ${curP === p.slug ? 'is-active' : ''}" data-pref="${esc(p.slug)}">
          <span class="ua-bar-label">${esc(p.name)}</span>
          <span class="ua-bar-track"><span class="ua-bar-fill ${fillCls}" style="width:${pct}%"></span></span>
          <span class="ua-bar-val">${p.count}校</span>
        </button>
      `;
    }).join('') : '<p style="font-size:.82rem;color:#64748b;margin:8px 0;">該当する都道府県データがありません。</p>';

    topPrefsEl.querySelectorAll('.ua-bar-row').forEach(btn => {
      btn.addEventListener('click', () => {
        const ps = btn.dataset.pref || '';
        prefSelect.value = (prefSelect.value === ps) ? '' : ps;
        if (prefSelect.value) activeRegion = '';
        applyFilter();
      });
    });
  }

  function applyFilter() {
    const kw = (keywordInput.value || '').trim().toLowerCase();
    const pref = prefSelect.value;
    const cat = catSelect.value;

    const chartPool = allUnivs.filter(u => {
      if (!matchesTab(u, activeTab)) return false;
      if (!matchesCategory(u, cat)) return false;
      if (kw) {
        const hay = [
          u.university_name, u.pref, u.establishment,
          ...u.sports_awards.flatMap(x => [x.category, x.contest, x.year, x.division, x.award, x.detail]),
          ...u.culture_awards.flatMap(x => [x.category, x.contest, x.year, x.division, x.award, x.detail]),
          ...u.music_awards.flatMap(x => [x.category, x.contest, x.year, x.division, x.award, x.detail]),
        ].filter(Boolean).join(' ').toLowerCase();
        if (!hay.includes(kw)) return false;
      }
      return true;
    });

    const filtered = chartPool.filter(u => {
      if (pref && u.pref_slug !== pref) return false;
      if (activeRegion) {
        const reg = REGIONS.find(r => r.id === activeRegion);
        if (reg && !reg.slugs.includes(u.pref_slug)) return false;
      }
      return true;
    });

    const regObj = activeRegion ? REGIONS.find(r => r.id === activeRegion) : null;
    const scopeLabel = pref ? prefSelect.options[prefSelect.selectedIndex].text : (regObj ? regObj.label : '全国');
    countEl.textContent = `${scopeLabel}：${filtered.length} 大学が該当（全 ${allUnivs.length} 大学中）`;

    const af = [];
    if (activeTab !== 'all') {
      const names = { sports: '運動・武道', culture: '文化・学術', music: '音楽コンクール' };
      af.push(`<span class="ua-af-pill">分野: ${names[activeTab]}</span>`);
    }
    if (regObj) af.push(`<span class="ua-af-pill">エリア: ${esc(regObj.label)}</span>`);
    if (pref) af.push(`<span class="ua-af-pill">都道府県: ${esc(prefSelect.options[prefSelect.selectedIndex].text)}</span>`);
    if (cat) af.push(`<span class="ua-af-pill">競技・分野: ${esc(cat)}</span>`);
    if (kw) af.push(`<span class="ua-af-pill">キーワード: ${esc(kw)}</span>`);
    activeFiltersEl.innerHTML = af.join('');

    renderQuickChips();
    renderCharts(chartPool);

    if (!filtered.length) {
      resultsEl.innerHTML = '<p style="grid-column:1/-1;color:#64748b;padding:28px 0;text-align:center;background:#fff;border-radius:14px;border:1px solid #e2e8f0;">該当する大学が見つかりませんでした。条件を変えてお試しください。</p>';
      return;
    }

    resultsEl.innerHTML = filtered.map(u => {
      const dCount = (u.sports_awards.length ? 1 : 0) + (u.culture_awards.length ? 1 : 0) + (u.music_awards.length ? 1 : 0);
      let mod = 'ua-card--multi';
      if (dCount === 1) {
        if (u.sports_awards.length) mod = 'ua-card--sports';
        else if (u.culture_awards.length) mod = 'ua-card--culture';
        else if (u.music_awards.length) mod = 'ua-card--music';
      }

      const badges = [
        `<span class="ua-pref-badge">${esc(u.pref)}</span>`,
        u.establishment ? `<span class="ua-type-badge">${esc(u.establishment)}</span>` : '',
        u.sports_awards.length ? '<span class="ua-domain-pill ua-domain-pill--sports">🏆 運動・武道</span>' : '',
        u.culture_awards.length ? '<span class="ua-domain-pill ua-domain-pill--culture">🎨 文化・学術</span>' : '',
        u.music_awards.length ? '<span class="ua-domain-pill ua-domain-pill--music">🎵 音楽</span>' : '',
      ].filter(Boolean).join('');

      const awards = collectAwards(u);
      const top = awards.slice(0, 2);
      const rest = awards.slice(2);
      const restHtml = rest.length ? `
        <details class="ua-more-awards">
          <summary>他 ${rest.length} 件の実績をひらく</summary>
          <div class="ua-more-awards-list">${rest.map(renderAwardRow).join('')}</div>
        </details>
      ` : '';

      const dbLink = u.university_id
        ? `<a href="/tools/university-database/tokyo/?q=${encodeURIComponent(u.university_name)}">大学DBで詳細を見る →</a>`
        : `<span style="font-size:.76rem;color:#94a3b8;">首都圏外（順次拡張予定）</span>`;

      return `
        <article class="ua-card ${mod}">
          <div class="ua-card-head">${badges}</div>
          <h3>${esc(u.university_name)}</h3>
          <div class="ua-highlights">${top.map(renderAwardRow).join('')}</div>
          ${restHtml}
          <div class="ua-card-foot">
            <span class="ua-aw-total">掲載実績 ${awards.length} 件</span>
            ${dbLink}
          </div>
        </article>
      `;
    }).join('');
  }

  async function init() {
    const params = new URLSearchParams(window.location.search);
    const t = params.get('tab');
    if (t && ['all', 'sports', 'culture', 'music'].includes(t)) {
      activeTab = t;
      kpiBtns.forEach(b => {
        const act = b.dataset.tab === activeTab;
        b.classList.toggle('is-active', act);
        b.setAttribute('aria-selected', act ? 'true' : 'false');
      });
    }
    populateCategories();

    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      allUnivs = data.universities || [];

      const st = data.stats || {};
      kpiAll.textContent = st.total_universities || allUnivs.length;
      kpiSports.textContent = st.sports_entries || 0;
      kpiCulture.textContent = st.culture_entries || 0;
      kpiMusic.textContent = st.music_entries || 0;

      (data.prefectures || []).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.slug;
        opt.textContent = p.name;
        prefSelect.appendChild(opt);
      });

      sourcesEl.innerHTML = (data.sources || []).map(s => `<div>・${esc(s)}</div>`).join('');

      const initCat = params.get('category');
      if (initCat && Array.from(catSelect.options).some(o => o.value === initCat)) {
        catSelect.value = initCat;
      }
      applyFilter();
    } catch (err) {
      countEl.textContent = 'データの読み込みに失敗しました。';
      console.error(err);
    }
  }

  kpiBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab || 'all';
      kpiBtns.forEach(b => {
        const act = b === btn;
        b.classList.toggle('is-active', act);
        b.setAttribute('aria-selected', act ? 'true' : 'false');
      });
      populateCategories();
      applyFilter();
    });
  });

  prefSelect.addEventListener('change', () => {
    if (prefSelect.value) activeRegion = '';
    applyFilter();
  });
  catSelect.addEventListener('change', applyFilter);
  keywordInput.addEventListener('input', applyFilter);
  resetBtn.addEventListener('click', () => {
    activeTab = 'all';
    activeRegion = '';
    keywordInput.value = '';
    prefSelect.value = '';
    kpiBtns.forEach(b => {
      const act = b.dataset.tab === 'all';
      b.classList.toggle('is-active', act);
      b.setAttribute('aria-selected', act ? 'true' : 'false');
    });
    populateCategories();
    catSelect.value = '';
    applyFilter();
  });

  init();
})();
