(() => {
  'use strict';

  const DATA_URL = '/data/school-database/national-awards-index.json';
  const PAGE_SIZE = 60;

  const statsEl = document.getElementById('nat-stats');
  const keywordInput = document.getElementById('nat-keyword');
  const prefSelect = document.getElementById('nat-pref');
  const catSelect = document.getElementById('nat-category');
  const countEl = document.getElementById('nat-count');
  const resultsEl = document.getElementById('nat-results');
  const moreWrap = document.getElementById('nat-more-wrap');
  const moreBtn = document.getElementById('nat-more-btn');
  const tabBtns = Array.from(document.querySelectorAll('.nat-tab'));

  let allSchools = [];
  let filteredSchools = [];
  let visibleCount = PAGE_SIZE;
  let activeTab = 'all';

  const CATEGORY_GROUPS = {
    sports: [
      '野球（甲子園）',
      'サッカー',
      '駅伝（都大路）',
      'バレーボール（春高）',
      'バスケットボール（ウインターカップ）',
      'ラグビー（花園）',
      '武道（柔道・剣道・相撲・空手）',
      'フェンシング（インターハイ）',
      '夏期競技（水泳・水球・陸上）',
      '冬期競技（スキー・スケート・アイスホッケー）',
      '中学校全国大会（全中・駅伝）',
    ],
    culture: [
      '演劇',
      '書道',
      '将棋',
      '囲碁',
      '箏曲・日本音楽',
      '華道',
      '絵画・漫画',
      'ロボット',
      '漢検（準会場・団体表彰）',
    ],
    music: [
      'NHK全国学校音楽コンクール（Nコン）',
      '全日本合唱コンクール',
      '全日本吹奏楽コンクール',
      '全日本マーチングコンテスト',
      'こども音楽コンクール',
      '日本学校合奏コンクール（全国学校合奏コンクール）',
      '全国高等学校軽音楽コンテスト',
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

  function populateCategories() {
    const prev = catSelect.value;
    let opts = ['<option value="">すべての競技・分野</option>'];
    const addGroup = (label, items) => {
      opts.push(`<optgroup label="${escapeHtml(label)}">`);
      items.forEach(item => {
        opts.push(`<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`);
      });
      opts.push('</optgroup>');
    };

    if (activeTab === 'all' || activeTab === 'sports') {
      addGroup('スポーツ・武道', CATEGORY_GROUPS.sports);
    }
    if (activeTab === 'all' || activeTab === 'culture') {
      addGroup('文化部・漢検', CATEGORY_GROUPS.culture);
    }
    if (activeTab === 'all' || activeTab === 'music') {
      addGroup('音楽コンクール', CATEGORY_GROUPS.music);
    }

    catSelect.innerHTML = opts.join('');
    if (prev && Array.from(catSelect.options).some(o => o.value === prev)) {
      catSelect.value = prev;
    } else {
      catSelect.value = '';
    }
  }

  function renderDetailsBlock(title, items, detailsClass, summaryClass, listClass, itemClass, tagPrefix) {
    if (!items || items.length === 0) return '';
    const top = items[0];
    const headLabel = [top.sport || top.category || top.contest, top.award, top.year].filter(Boolean).join('・');
    const rows = items.map(it => {
      const aw = it.award || '';
      const meta = [it.year, it.division, it.detail].filter(Boolean).join(' / ');
      return `
        <div class="${itemClass}">
          <span class="${tagPrefix}">${escapeHtml(aw)}</span>
          <span class="sports-contest-name">${escapeHtml(it.contest || it.sport || it.category || '')}</span>
          ${meta ? `<span class="sports-meta">${escapeHtml(meta)}</span>` : ''}
        </div>
      `;
    }).join('');
    return `
      <details class="${detailsClass}">
        <summary class="${summaryClass}">${escapeHtml(title)}（${items.length}件） ${escapeHtml(headLabel)}</summary>
        <div class="${listClass}">${rows}</div>
      </details>
    `;
  }

  function renderCards() {
    const slice = filteredSchools.slice(0, visibleCount);
    if (slice.length === 0) {
      resultsEl.innerHTML = '<p style="grid-column:1/-1;color:#64748b;padding:24px 0;">該当する学校が見つかりませんでした。条件を変えてお試しください。</p>';
      moreWrap.style.display = 'none';
      return;
    }

    resultsEl.innerHTML = slice.map(sc => {
      const badges = [
        `<span class="nat-pref-badge">${escapeHtml(sc.pref)}</span>`,
        sc.type ? `<span class="nat-type-badge">${escapeHtml(sc.type)}</span>` : '',
        sc.sports_awards.length ? '<span class="school-badge-sports">スポーツ・武道</span>' : '',
        sc.culture_awards.length ? '<span class="school-badge-culture">文化部・漢検</span>' : '',
        sc.music_awards.length ? '<span class="school-badge-music">音楽</span>' : '',
      ].filter(Boolean).join('');

      const sportsHtml = renderDetailsBlock(
        'スポーツ・武道実績', sc.sports_awards,
        'school-sports-details', 'school-sports-summary', 'school-sports-list', 'school-sports-item',
        'sports-award-tag sports-award-tag--semi'
      );
      const cultureHtml = renderDetailsBlock(
        '文化部・検定実績', sc.culture_awards,
        'school-culture-details', 'school-culture-summary', 'school-culture-list', 'school-culture-item',
        'culture-award-tag culture-award-tag--second'
      );
      const musicHtml = renderDetailsBlock(
        '音楽コンクール実績', sc.music_awards,
        'school-sports-details', 'school-sports-summary', 'school-sports-list', 'school-sports-item',
        'music-award-tag music-award-tag--gold'
      );

      return `
        <article class="nat-card">
          <div class="nat-card-head">${badges}</div>
          <h2>${escapeHtml(sc.name)}</h2>
          <p class="nat-addr">${escapeHtml(sc.address || sc.city || sc.pref)}</p>
          ${sportsHtml}
          ${cultureHtml}
          ${musicHtml}
          <div class="nat-card-foot">
            <a href="/tools/school-database/${encodeURIComponent(sc.pref_slug)}/">${escapeHtml(sc.pref)}の学校DBで詳細を見る →</a>
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

    filteredSchools = allSchools.filter(sc => {
      if (pref && sc.pref_slug !== pref) return false;
      if (activeTab === 'sports' && sc.sports_awards.length === 0) return false;
      if (activeTab === 'culture' && sc.culture_awards.length === 0) return false;
      if (activeTab === 'music' && sc.music_awards.length === 0) return false;

      if (cat) {
        const hitSp = sc.sports_awards.some(x => x.sport === cat);
        const hitCu = sc.culture_awards.some(x => x.category === cat);
        const hitMu = sc.music_awards.some(x => x.contest === cat);
        if (!hitSp && !hitCu && !hitMu) return false;
      }

      if (kw) {
        const haystack = [
          sc.pref, sc.name, sc.city, sc.address, sc.type,
          ...sc.sports_awards.flatMap(x => [x.sport, x.contest, x.year, x.division, x.award]),
          ...sc.culture_awards.flatMap(x => [x.category, x.contest, x.year, x.division, x.award]),
          ...sc.music_awards.flatMap(x => [x.contest, x.year, x.division, x.award, x.detail]),
        ].filter(Boolean).join(' ').toLowerCase();
        if (!haystack.includes(kw)) return false;
      }
      return true;
    });

    visibleCount = PAGE_SIZE;
    const scopeLabel = pref ? prefSelect.options[prefSelect.selectedIndex].text : '全国';
    countEl.textContent = `${scopeLabel}：${filteredSchools.length} 校が該当（全 ${allSchools.length} 校中）`;
    renderCards();
  }

  async function init() {
    const params = new URLSearchParams(window.location.search);
    const initialTab = params.get('tab');
    if (initialTab && ['all', 'sports', 'culture', 'music'].includes(initialTab)) {
      activeTab = initialTab;
      tabBtns.forEach(b => b.classList.toggle('is-active', b.dataset.tab === activeTab));
    }

    populateCategories();

    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      allSchools = data.schools || [];

      const st = data.stats || {};
      statsEl.innerHTML = [
        `<span class="nat-stat-pill">全国実績校 ${st.total_schools || allSchools.length}校</span>`,
        `<span class="nat-stat-pill">スポーツ・武道 ${st.sports_entries || 0}件</span>`,
        `<span class="nat-stat-pill">文化部・漢検 ${st.culture_entries || 0}件</span>`,
        `<span class="nat-stat-pill">音楽コンクール ${st.music_entries || 0}件</span>`,
      ].join('');

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

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      activeTab = btn.dataset.tab || 'all';
      tabBtns.forEach(b => b.classList.toggle('is-active', b === btn));
      populateCategories();
      applyFilter();
    });
  });

  keywordInput.addEventListener('input', applyFilter);
  prefSelect.addEventListener('change', applyFilter);
  catSelect.addEventListener('change', applyFilter);
  moreBtn.addEventListener('click', () => {
    visibleCount += PAGE_SIZE;
    renderCards();
  });

  init();
})();
