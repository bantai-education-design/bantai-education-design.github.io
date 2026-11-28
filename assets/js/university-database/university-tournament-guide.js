(() => {
  'use strict';

  const DATA_URL = '/tools/university-database/guide/data/university_tournaments_guide.json';
  const calEl = document.getElementById('ug-calendar');
  const chipsEl = document.getElementById('ug-chips');
  const keywordEl = document.getElementById('ug-keyword');
  const countEl = document.getElementById('ug-count');
  const listEl = document.getElementById('ug-list');
  const domainBtns = Array.from(document.querySelectorAll('.ug-dtab'));

  let allItems = [];
  let activeDomain = 'all';
  let activeCategory = 'all';

  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function extractMonths(seasonStr) {
    const months = new Set();
    for (const m of String(seasonStr || '').matchAll(/(\d{1,2})月/g)) {
      const n = parseInt(m[1], 10);
      if (n >= 1 && n <= 12) months.add(n);
    }
    return months;
  }

  function seasonClass(m) {
    if (m >= 3 && m <= 5) return 'is-spring';
    if (m >= 6 && m <= 8) return 'is-summer';
    if (m >= 9 && m <= 11) return 'is-autumn';
    return 'is-winter';
  }

  function renderCalendar(items) {
    const header = `
      <div class="ug-cal-months">
        <span>大会名</span>
        ${Array.from({ length: 12 }, (_, i) => `<span>${i + 1}月</span>`).join('')}
      </div>
    `;
    const rows = items.map(it => {
      const months = extractMonths(it.season);
      const shortName = it.name.replace(/（.*?）/g, '').slice(0, 19);
      const cells = Array.from({ length: 12 }, (_, i) => {
        const m = i + 1;
        const on = months.has(m);
        return `<span class="ug-cal-cell ${on ? seasonClass(m) : ''}" title="${esc(it.name)}：${m}月${on ? '（開催期）' : ''}"></span>`;
      }).join('');
      return `
        <a class="ug-cal-row" href="#${esc(it.id)}">
          <span class="ug-cal-name" title="${esc(it.name)}">${esc(shortName)}</span>
          ${cells}
        </a>
      `;
    }).join('');
    calEl.innerHTML = header + rows;
  }

  function renderChips() {
    const pool = allItems.filter(it => activeDomain === 'all' || it.domain === activeDomain);
    const cats = Array.from(new Set(pool.map(x => x.category).filter(Boolean)));
    if (activeCategory !== 'all' && !cats.includes(activeCategory)) {
      activeCategory = 'all';
    }
    chipsEl.innerHTML = [
      `<button type="button" class="ug-chip ${activeCategory === 'all' ? 'is-active' : ''}" data-cat="all">すべて <span class="ug-chip-cnt">${pool.length}</span></button>`,
      ...cats.map(c => {
        const cnt = pool.filter(x => x.category === c).length;
        return `<button type="button" class="ug-chip ${activeCategory === c ? 'is-active' : ''}" data-cat="${esc(c)}">${esc(c)} <span class="ug-chip-cnt">${cnt}</span></button>`;
      })
    ].join('');

    chipsEl.querySelectorAll('.ug-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        activeCategory = btn.dataset.cat || 'all';
        render();
      });
    });
  }

  function render() {
    renderChips();
    const kw = (keywordEl.value || '').trim().toLowerCase();
    const filtered = allItems.filter(it => {
      if (activeDomain !== 'all' && it.domain !== activeDomain) return false;
      if (activeCategory !== 'all' && it.category !== activeCategory) return false;
      if (kw) {
        const hay = [
          it.name, it.category, it.organizer, it.season, it.duration, it.venue,
          it.qualifying, it.entry_procedure, it.history, it.advice
        ].filter(Boolean).join(' ').toLowerCase();
        if (!hay.includes(kw)) return false;
      }
      return true;
    });

    countEl.textContent = `${filtered.length} 大会を表示中（全 ${allItems.length} 大会）`;
    renderCalendar(filtered.length ? filtered : allItems);

    if (!filtered.length) {
      listEl.innerHTML = '<p style="color:#64748b;padding:24px 0;text-align:center;background:#fff;border-radius:14px;border:1px solid #e2e8f0;">該当する大会ガイドが見つかりませんでした。</p>';
      return;
    }

    listEl.innerHTML = filtered.map(it => {
      const mod = it.domain === 'culture' ? 'ug-card--culture' : (it.domain === 'music' ? 'ug-card--music' : '');
      return `
        <article class="ug-card ${mod}" id="${esc(it.id)}">
          <div class="ug-card-head">
            <div>
              <div class="ug-card-top">
                <span class="ug-cat-badge">${esc(it.category)}</span>
                <span class="ug-org">${esc(it.organizer)}</span>
              </div>
              <h2>${esc(it.name)}</h2>
            </div>
            <a class="ug-db-btn" href="${esc(it.target_href || '/tools/university-database/awards/')}">実績大学をDBで見る →</a>
          </div>

          <div class="ug-meta-grid">
            <div class="ug-meta-box">
              <span class="ug-meta-ic">📅</span>
              <div><div class="ug-meta-label">開催時期</div><div class="ug-meta-val">${esc(it.season)}</div></div>
            </div>
            <div class="ug-meta-box">
              <span class="ug-meta-ic">⏱️</span>
              <div><div class="ug-meta-label">開催期間</div><div class="ug-meta-val">${esc(it.duration)}</div></div>
            </div>
            <div class="ug-meta-box">
              <span class="ug-meta-ic">📍</span>
              <div><div class="ug-meta-label">主な会場</div><div class="ug-meta-val">${esc(it.venue)}</div></div>
            </div>
          </div>

          <div class="ug-roadmap">
            <div class="ug-step">
              <div class="ug-step-head"><span class="ug-step-num">1</span><h3>予選方法・代表枠</h3></div>
              <p>${esc(it.qualifying)}</p>
            </div>
            <div class="ug-step">
              <div class="ug-step-head"><span class="ug-step-num">2</span><h3>学連登録・出場手続き</h3></div>
              <p>${esc(it.entry_procedure)}</p>
            </div>
            <div class="ug-step ug-step--advice">
              <div class="ug-step-head"><span class="ug-step-num">3</span><h3>参加校・学生幹部アドバイス</h3></div>
              <p>${esc(it.advice)}</p>
            </div>
          </div>

          <details class="ug-history">
            <summary>🏛️ 大会の歴史・記録をひらく</summary>
            <p>${esc(it.history)}</p>
          </details>
        </article>
      `;
    }).join('');
  }

  domainBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      activeDomain = btn.dataset.domain || 'all';
      activeCategory = 'all';
      domainBtns.forEach(b => b.classList.toggle('is-active', b === btn));
      render();
    });
  });

  keywordEl.addEventListener('input', render);

  const params = new URLSearchParams(window.location.search);
  const initDomain = params.get('domain');
  if (initDomain && ['all', 'sports', 'culture', 'music'].includes(initDomain)) {
    activeDomain = initDomain;
    domainBtns.forEach(b => b.classList.toggle('is-active', b.dataset.domain === activeDomain));
  }

  fetch(DATA_URL)
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(data => {
      allItems = data.tournaments || [];
      render();
    })
    .catch(err => {
      countEl.textContent = 'ガイドデータの読み込みに失敗しました。';
      console.error(err);
    });
})();
