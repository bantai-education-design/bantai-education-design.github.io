(() => {
  'use strict';

  const DATA_URL = '/data/school-database/national-awards-index.json';
  const PAGE_SIZE = 48;

  const kpiAll = document.getElementById('kpi-all');
  const kpiSports = document.getElementById('kpi-sports');
  const kpiCulture = document.getElementById('kpi-culture');
  const kpiMusic = document.getElementById('kpi-music');
  const kpiBtns = Array.from(document.querySelectorAll('.nat-kpi'));

  const quickChipsEl = document.getElementById('nat-quick-chips');
  const keywordInput = document.getElementById('nat-keyword');
  const prefSelect = document.getElementById('nat-pref');
  const catSelect = document.getElementById('nat-category');
  const resetBtn = document.getElementById('nat-reset');

  const regionBarsEl = document.getElementById('nat-region-bars');
  const topPrefsEl = document.getElementById('nat-top-prefs');

  const countEl = document.getElementById('nat-count');
  const activeFiltersEl = document.getElementById('nat-active-filters');
  const resultsEl = document.getElementById('nat-results');
  const moreWrap = document.getElementById('nat-more-wrap');
  const moreBtn = document.getElementById('nat-more-btn');

  let allSchools = [];
  let filteredSchools = [];
  let visibleCount = PAGE_SIZE;
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
      { value: '野球（甲子園）', label: '野球（甲子園）', icon: '⚾' },
      { value: 'サッカー', label: 'サッカー', icon: '⚽' },
      { value: '駅伝（都大路）', label: '駅伝（都大路）', icon: '🏃' },
      { value: 'バレーボール（春高）', label: '春高バレー', icon: '🏐' },
      { value: 'バスケットボール（ウインターカップ）', label: 'バスケ（WC）', icon: '🏀' },
      { value: 'ラグビー（花園）', label: 'ラグビー（花園）', icon: '🏉' },
      { value: '武道（柔道・剣道・相撲・空手）', label: '武道4競技', icon: '🥋' },
      { value: 'フェンシング（インターハイ）', label: 'フェンシング', icon: '🤺' },
      { value: '夏期競技（水泳・水球・陸上）', label: '夏期競技', icon: '🏊' },
      { value: '冬期競技（スキー・スケート・アイスホッケー）', label: '冬期競技', icon: '⛷️' },
      { value: '中学校全国大会（全中・駅伝）', label: '中学校（全中）', icon: '🎽' },
    ],
    culture: [
      { value: '演劇', label: '演劇', icon: '🎭' },
      { value: '書道', label: '書道', icon: '🖌️' },
      { value: '将棋', label: '将棋', icon: '♟️' },
      { value: '囲碁', label: '囲碁', icon: '⚫' },
      { value: '箏曲・日本音楽', label: '箏曲・日本音楽', icon: '🪕' },
      { value: '華道', label: '華道', icon: '💐' },
      { value: '絵画・漫画', label: '絵画・漫画', icon: '🎨' },
      { value: 'ロボット', label: 'ロボット', icon: '🤖' },
      { value: '漢検（準会場・団体表彰）', label: '漢検 団体賞', icon: '📝' },
    ],
    music: [
      { value: '全日本吹奏楽コンクール', label: '全日本吹奏楽', icon: '🎺' },
      { value: 'NHK全国学校音楽コンクール（Nコン）', label: 'Nコン', icon: '🎼' },
      { value: '全日本合唱コンクール', label: '全日本合唱', icon: '🎤' },
      { value: '全日本マーチングコンテスト', label: 'マーチング', icon: '🥁' },
      { value: 'こども音楽コンクール', label: 'こども音楽', icon: '🎻' },
      { value: '日本学校合奏コンクール（全国学校合奏コンクール）', label: '日本学校合奏', icon: '🎻' },
      { value: '全国高等学校軽音楽コンテスト', label: '高校軽音楽', icon: '🎸' },
    ],
  };

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function getRegionBySlug(slug) {
    return REGIONS.find(r => r.slugs.includes(slug));
  }

  function schoolMatchesTab(sc, tab) {
    if (tab === 'sports') return sc.sports_awards.length > 0;
    if (tab === 'culture') return sc.culture_awards.length > 0;
    if (tab === 'music') return sc.music_awards.length > 0;
    return true;
  }

  function schoolMatchesCategory(sc, cat) {
    if (!cat) return true;
    return (
      sc.sports_awards.some(x => x.sport === cat) ||
      sc.culture_awards.some(x => x.category === cat) ||
      sc.music_awards.some(x => x.contest === cat)
    );
  }

  function populateCategories() {
    const prev = catSelect.value;
    const opts = ['<option value="">すべての競技・分野</option>'];
    const addGroup = (label, items) => {
      opts.push(`<optgroup label="${escapeHtml(label)}">`);
      items.forEach(item => {
        opts.push(`<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`);
      });
      opts.push('</optgroup>');
    };
    if (activeTab === 'all' || activeTab === 'sports') addGroup('スポーツ・武道', CATEGORY_GROUPS.sports);
    if (activeTab === 'all' || activeTab === 'culture') addGroup('文化部・漢検', CATEGORY_GROUPS.culture);
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
    const basePool = allSchools.filter(sc => {
      if (pref && sc.pref_slug !== pref) return false;
      if (activeRegion) {
        const reg = REGIONS.find(r => r.id === activeRegion);
        if (reg && !reg.slugs.includes(sc.pref_slug)) return false;
      }
      return schoolMatchesTab(sc, activeTab);
    });

    const items = [];
    if (activeTab === 'all') {
      items.push(
        ...CATEGORY_GROUPS.sports.slice(0, 7).map(x => ({ ...x, domain: 'sports' })),
        ...CATEGORY_GROUPS.culture.slice(0, 5).map(x => ({ ...x, domain: 'culture' })),
        { value: '漢検（準会場・団体表彰）', label: '漢検 団体賞', icon: '📝', domain: 'culture' },
        ...CATEGORY_GROUPS.music.slice(0, 3).map(x => ({ ...x, domain: 'music' }))
      );
    } else {
      items.push(...CATEGORY_GROUPS[activeTab].map(x => ({ ...x, domain: activeTab })));
    }

    const currentCat = catSelect.value;
    const chipHtml = [
      `<button type="button" class="nat-qchip ${!currentCat ? 'is-active' : ''}" data-cat="">すべて <span class="nat-qchip-cnt">${basePool.length}</span></button>`,
      ...items.map(it => {
        const cnt = basePool.filter(sc => schoolMatchesCategory(sc, it.value)).length;
        const activeCls = currentCat === it.value ? 'is-active' : '';
        return `<button type="button" class="nat-qchip nat-qchip--${it.domain} ${activeCls}" data-cat="${escapeHtml(it.value)}">${it.icon} ${escapeHtml(it.label)} <span class="nat-qchip-cnt">${cnt}</span></button>`;
      })
    ].join('');

    quickChipsEl.innerHTML = chipHtml;
    quickChipsEl.querySelectorAll('.nat-qchip').forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.dataset.cat || '';
        catSelect.value = (catSelect.value === val && val !== '') ? '' : val;
        applyFilter();
      });
    });
  }

  function classifyMedal(awardText) {
    const a = String(awardText || '');
    if (/優勝|金賞|最優秀|グランプリ|日本一|1位|文部科学大臣賞|最優秀団体賞/.test(a)) {
      return { cls: 'nat-medal--gold', icon: '🥇' };
    }
    if (/準優勝|銀賞|優秀賞|2位|優秀団体賞/.test(a)) {
      return { cls: 'nat-medal--silver', icon: '🥈' };
    }
    if (/3位|ベスト4|銅賞|優良賞|奨励賞/.test(a)) {
      return { cls: 'nat-medal--bronze', icon: '🥉' };
    }
    return { cls: 'nat-medal--other', icon: '🏅' };
  }

  function collectSchoolAwards(sc) {
    const list = [];
    if (activeTab === 'all' || activeTab === 'sports') {
      sc.sports_awards.forEach(x => list.push({
        domain: 'sports',
        award: x.award || '入賞',
        title: x.contest || x.sport || 'スポーツ大会',
        meta: [x.sport, x.year, x.division].filter(Boolean).join(' / '),
      }));
    }
    if (activeTab === 'all' || activeTab === 'culture') {
      sc.culture_awards.forEach(x => list.push({
        domain: 'culture',
        award: x.award || '入賞',
        title: x.contest || x.category || '文化部・検定',
        meta: [x.category, x.year, x.division].filter(Boolean).join(' / '),
      }));
    }
    if (activeTab === 'all' || activeTab === 'music') {
      sc.music_awards.forEach(x => list.push({
        domain: 'music',
        award: x.award || '入賞',
        title: x.contest || '音楽コンクール',
        meta: [x.year, x.division, x.detail].filter(Boolean).join(' / '),
      }));
    }
    return list;
  }

  function renderAwardRow(aw) {
    const m = classifyMedal(aw.award);
    return `
      <div class="nat-aw-row">
        <span class="nat-medal ${m.cls}">${m.icon} ${escapeHtml(aw.award)}</span>
        <div class="nat-aw-body">
          <div class="nat-aw-title">${escapeHtml(aw.title)}</div>
          ${aw.meta ? `<span class="nat-aw-meta">${escapeHtml(aw.meta)}</span>` : ''}
        </div>
      </div>
    `;
  }

  function renderCharts(scopePool) {
    const fillClass = activeTab === 'all' ? '' : `nat-bar-fill--${activeTab}`;

    // Regional distribution
    const regCounts = REGIONS.map(r => ({
      id: r.id,
      label: r.label,
      count: scopePool.filter(sc => r.slugs.includes(sc.pref_slug)).length,
    }));
    const maxReg = Math.max(1, ...regCounts.map(r => r.count));
    regionBarsEl.innerHTML = regCounts.map(r => {
      const pct = Math.round((r.count / maxReg) * 100);
      const isAct = activeRegion === r.id ? 'is-active' : '';
      return `
        <button type="button" class="nat-bar-row ${isAct}" data-region="${r.id}">
          <span class="nat-bar-label">${escapeHtml(r.label)}</span>
          <span class="nat-bar-track"><span class="nat-bar-fill ${fillClass}" style="width:${pct}%"></span></span>
          <span class="nat-bar-val">${r.count}校</span>
        </button>
      `;
    }).join('');

    regionBarsEl.querySelectorAll('.nat-bar-row').forEach(btn => {
      btn.addEventListener('click', () => {
        const rid = btn.dataset.region || '';
        activeRegion = (activeRegion === rid) ? '' : rid;
        if (activeRegion) prefSelect.value = '';
        applyFilter();
      });
    });

    // Top 6 Prefectures
    const prefMap = new Map();
    scopePool.forEach(sc => {
      const cur = prefMap.get(sc.pref_slug) || { slug: sc.pref_slug, name: sc.pref, count: 0 };
      cur.count += 1;
      prefMap.set(sc.pref_slug, cur);
    });
    const topPrefs = Array.from(prefMap.values())
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
    const maxPref = Math.max(1, ...topPrefs.map(p => p.count));
    const currentPref = prefSelect.value;

    topPrefsEl.innerHTML = topPrefs.length ? topPrefs.map(p => {
      const pct = Math.round((p.count / maxPref) * 100);
      const isAct = currentPref === p.slug ? 'is-active' : '';
      return `
        <button type="button" class="nat-bar-row ${isAct}" data-pref="${escapeHtml(p.slug)}">
          <span class="nat-bar-label">${escapeHtml(p.name)}</span>
          <span class="nat-bar-track"><span class="nat-bar-fill ${fillClass}" style="width:${pct}%"></span></span>
          <span class="nat-bar-val">${p.count}校</span>
        </button>
      `;
    }).join('') : '<p style="font-size:.82rem;color:#64748b;margin:8px 0;">該当する都道府県データがありません。</p>';

    topPrefsEl.querySelectorAll('.nat-bar-row').forEach(btn => {
      btn.addEventListener('click', () => {
        const ps = btn.dataset.pref || '';
        prefSelect.value = (prefSelect.value === ps) ? '' : ps;
        if (prefSelect.value) activeRegion = '';
        applyFilter();
      });
    });
  }

  function renderCards() {
    const slice = filteredSchools.slice(0, visibleCount);
    if (slice.length === 0) {
      resultsEl.innerHTML = '<p style="grid-column:1/-1;color:#64748b;padding:28px 0;text-align:center;background:#fff;border-radius:14px;border:1px solid #e2e8f0;">該当する学校が見つかりませんでした。条件をクリアするか、別の競技・地域をお試しください。</p>';
      moreWrap.style.display = 'none';
      return;
    }

    resultsEl.innerHTML = slice.map(sc => {
      const domainCount = (sc.sports_awards.length > 0 ? 1 : 0) +
                          (sc.culture_awards.length > 0 ? 1 : 0) +
                          (sc.music_awards.length > 0 ? 1 : 0);
      let cardMod = 'nat-card--multi';
      if (domainCount === 1) {
        if (sc.sports_awards.length) cardMod = 'nat-card--sports';
        else if (sc.culture_awards.length) cardMod = 'nat-card--culture';
        else if (sc.music_awards.length) cardMod = 'nat-card--music';
      }

      const badges = [
        `<span class="nat-pref-badge">${escapeHtml(sc.pref)}</span>`,
        sc.establishment ? `<span class="nat-type-badge">${escapeHtml(sc.establishment)}</span>` : '',
        sc.type ? `<span class="nat-type-badge">${escapeHtml(sc.type)}</span>` : '',
        sc.sports_awards.length ? '<span class="nat-domain-pill nat-domain-pill--sports">🏆 スポーツ</span>' : '',
        sc.culture_awards.length ? '<span class="nat-domain-pill nat-domain-pill--culture">🎨 文化・漢検</span>' : '',
        sc.music_awards.length ? '<span class="nat-domain-pill nat-domain-pill--music">🎵 音楽</span>' : '',
      ].filter(Boolean).join('');

      const awards = collectSchoolAwards(sc);
      const topAwards = awards.slice(0, 2);
      const restAwards = awards.slice(2);

      const restHtml = restAwards.length ? `
        <details class="nat-more-awards">
          <summary>他 ${restAwards.length} 件の実績をひらく</summary>
          <div class="nat-more-awards-list">${restAwards.map(renderAwardRow).join('')}</div>
        </details>
      ` : '';

      return `
        <article class="nat-card ${cardMod}">
          <div class="nat-card-head">${badges}</div>
          <h3>${escapeHtml(sc.name)}</h3>
          <p class="nat-addr">${escapeHtml(sc.address || sc.city || sc.pref)}</p>
          <div class="nat-highlights">${topAwards.map(renderAwardRow).join('')}</div>
          ${restHtml}
          <div class="nat-card-foot">
            <span class="nat-aw-total">掲載実績 ${awards.length} 件</span>
            <a href="/tools/school-database/${encodeURIComponent(sc.pref_slug)}/">${escapeHtml(sc.pref)}の学校DB →</a>
          </div>
        </article>
      `;
    }).join('');

    if (visibleCount < filteredSchools.length) {
      moreWrap.style.display = 'block';
      moreBtn.textContent = `さらに表示する（残り ${filteredSchools.length - visibleCount} 校）`;
    } else {
      moreWrap.style.display = 'none';
    }
  }

  function applyFilter() {
    const kw = (keywordInput.value || '').trim().toLowerCase();
    const pref = prefSelect.value;
    const cat = catSelect.value;

    // Pool before pref/region filter for the nationwide distribution charts
    const chartPool = allSchools.filter(sc => {
      if (!schoolMatchesTab(sc, activeTab)) return false;
      if (!schoolMatchesCategory(sc, cat)) return false;
      if (kw) {
        const hay = [
          sc.pref, sc.name, sc.city, sc.address, sc.type,
          ...sc.sports_awards.flatMap(x => [x.sport, x.contest, x.year, x.division, x.award]),
          ...sc.culture_awards.flatMap(x => [x.category, x.contest, x.year, x.division, x.award]),
          ...sc.music_awards.flatMap(x => [x.contest, x.year, x.division, x.award, x.detail]),
        ].filter(Boolean).join(' ').toLowerCase();
        if (!hay.includes(kw)) return false;
      }
      return true;
    });

    filteredSchools = chartPool.filter(sc => {
      if (pref && sc.pref_slug !== pref) return false;
      if (activeRegion) {
        const reg = REGIONS.find(r => r.id === activeRegion);
        if (reg && !reg.slugs.includes(sc.pref_slug)) return false;
      }
      return true;
    });

    visibleCount = PAGE_SIZE;

    const regObj = activeRegion ? REGIONS.find(r => r.id === activeRegion) : null;
    const scopeLabel = pref
      ? prefSelect.options[prefSelect.selectedIndex].text
      : (regObj ? regObj.label : '全国');
    countEl.textContent = `${scopeLabel}：${filteredSchools.length} 校が該当（全 ${allSchools.length} 校中）`;

    const af = [];
    if (activeTab !== 'all') {
      const tabNames = { sports: 'スポーツ・武道', culture: '文化部・漢検', music: '音楽コンクール' };
      af.push(`<span class="nat-af-pill">分野: ${tabNames[activeTab]}</span>`);
    }
    if (regObj) af.push(`<span class="nat-af-pill">エリア: ${escapeHtml(regObj.label)}</span>`);
    if (pref) af.push(`<span class="nat-af-pill">都道府県: ${escapeHtml(prefSelect.options[prefSelect.selectedIndex].text)}</span>`);
    if (cat) af.push(`<span class="nat-af-pill">競技・大会: ${escapeHtml(cat)}</span>`);
    if (kw) af.push(`<span class="nat-af-pill">キーワード: ${escapeHtml(kw)}</span>`);
    activeFiltersEl.innerHTML = af.join('');

    renderQuickChips();
    renderCharts(chartPool);
    renderCards();
  }

  async function init() {
    const params = new URLSearchParams(window.location.search);
    const initialTab = params.get('tab');
    if (initialTab && ['all', 'sports', 'culture', 'music'].includes(initialTab)) {
      activeTab = initialTab;
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
      allSchools = data.schools || [];

      const st = data.stats || {};
      kpiAll.textContent = st.total_schools || allSchools.length;
      kpiSports.textContent = st.sports_entries || 0;
      kpiCulture.textContent = st.culture_entries || 0;
      kpiMusic.textContent = st.music_entries || 0;

      (data.prefectures || []).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.slug;
        opt.textContent = p.name;
        prefSelect.appendChild(opt);
      });

      const initialPref = params.get('pref');
      if (initialPref && Array.from(prefSelect.options).some(o => o.value === initialPref)) {
        prefSelect.value = initialPref;
      }
      const initialCat = params.get('category');
      if (initialCat && Array.from(catSelect.options).some(o => o.value === initialCat)) {
        catSelect.value = initialCat;
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

  moreBtn.addEventListener('click', () => {
    visibleCount += PAGE_SIZE;
    renderCards();
  });

  init();
})();
