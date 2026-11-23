(() => {
  'use strict';

  const rootEl = document.getElementById('guide-app');
  if (!rootEl) return;

  const dataUrl = rootEl.dataset.jsonUrl;
  const defaultTab = rootEl.dataset.defaultTab || 'sports';
  const calEl = document.getElementById('guide-calendar');
  const chipsEl = document.getElementById('guide-chips');
  const keywordEl = document.getElementById('guide-keyword');
  const countEl = document.getElementById('guide-count');
  const listEl = document.getElementById('guide-list');

  let allItems = [];
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
    const s = String(seasonStr || '');
    const months = new Set();
    const matches = s.matchAll(/(\d{1,2})月/g);
    for (const m of matches) {
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
    if (!calEl) return;
    const header = `
      <div class="tg-cal-months">
        <span>大会名</span>
        ${Array.from({ length: 12 }, (_, i) => `<span>${i + 1}月</span>`).join('')}
      </div>
    `;
    const rows = items.map(it => {
      const months = extractMonths(it.season);
      const shortName = it.name.replace(/（.*?）/g, '').slice(0, 18);
      const cells = Array.from({ length: 12 }, (_, idx) => {
        const m = idx + 1;
        const on = months.has(m);
        return `<span class="tg-cal-cell ${on ? seasonClass(m) : ''}" title="${esc(it.name)}：${m}月${on ? '（開催期）' : ''}"></span>`;
      }).join('');
      return `
        <a class="tg-cal-row" href="#${esc(it.id)}">
          <span class="tg-cal-name" title="${esc(it.name)}">${esc(shortName)}</span>
          ${cells}
        </a>
      `;
    }).join('');
    calEl.innerHTML = header + rows;
  }

  function render() {
    const kw = (keywordEl.value || '').trim().toLowerCase();
    const filtered = allItems.filter(it => {
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

    if (filtered.length === 0) {
      listEl.innerHTML = '<p style="color:#64748b;padding:24px 0;text-align:center;background:#fff;border-radius:14px;border:1px solid #e2e8f0;">該当する大会ガイドが見つかりませんでした。</p>';
      return;
    }

    listEl.innerHTML = filtered.map(it => {
      const tab = it.tab || defaultTab;
      const filterVal = it.filter_value || it.sport_filter || '';
      const searchHref = `/tools/school-database/awards/?tab=${encodeURIComponent(tab)}` +
        (filterVal ? `&category=${encodeURIComponent(filterVal)}` : '');

      return `
        <article class="tg-card" id="${esc(it.id)}">
          <div class="tg-card-head">
            <div>
              <div class="tg-card-top">
                <span class="tg-cat-badge">${esc(it.category)}</span>
                <span class="tg-org">${esc(it.organizer)}</span>
              </div>
              <h2>${esc(it.name)}</h2>
            </div>
            <a class="tg-db-btn" href="${searchHref}">全国実績校をDBで見る →</a>
          </div>

          <div class="tg-meta-grid">
            <div class="tg-meta-box">
              <span class="tg-meta-ic">📅</span>
              <div>
                <div class="tg-meta-label">開催時期</div>
                <div class="tg-meta-val">${esc(it.season)}</div>
              </div>
            </div>
            <div class="tg-meta-box">
              <span class="tg-meta-ic">⏱️</span>
              <div>
                <div class="tg-meta-label">開催期間</div>
                <div class="tg-meta-val">${esc(it.duration)}</div>
              </div>
            </div>
            <div class="tg-meta-box">
              <span class="tg-meta-ic">📍</span>
              <div>
                <div class="tg-meta-label">主な会場</div>
                <div class="tg-meta-val">${esc(it.venue)}</div>
              </div>
            </div>
          </div>

          <div class="tg-roadmap">
            <div class="tg-step">
              <div class="tg-step-head">
                <span class="tg-step-num">1</span>
                <h3>予選方法・代表枠</h3>
              </div>
              <p>${esc(it.qualifying)}</p>
            </div>
            <div class="tg-step">
              <div class="tg-step-head">
                <span class="tg-step-num">2</span>
                <h3>出場手続き</h3>
              </div>
              <p>${esc(it.entry_procedure)}</p>
            </div>
            <div class="tg-step tg-step--advice">
              <div class="tg-step-head">
                <span class="tg-step-num">3</span>
                <h3>参加校・顧問アドバイス</h3>
              </div>
              <p>${esc(it.advice)}</p>
            </div>
          </div>

          <details class="tg-history">
            <summary>🏛️ 大会の歴史・記録をひらく</summary>
            <p>${esc(it.history)}</p>
          </details>
        </article>
      `;
    }).join('');
  }

  async function init() {
    try {
      const res = await fetch(dataUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      allItems = data.tournaments || [];

      const cats = Array.from(new Set(allItems.map(x => x.category).filter(Boolean)));
      chipsEl.innerHTML = [
        `<button type="button" class="tg-chip is-active" data-cat="all">すべて表示 <span class="tg-chip-cnt">${allItems.length}</span></button>`,
        ...cats.map(c => {
          const cnt = allItems.filter(x => x.category === c).length;
          return `<button type="button" class="tg-chip" data-cat="${esc(c)}">${esc(c)} <span class="tg-chip-cnt">${cnt}</span></button>`;
        })
      ].join('');

      chipsEl.querySelectorAll('.tg-chip').forEach(btn => {
        btn.addEventListener('click', () => {
          activeCategory = btn.dataset.cat || 'all';
          chipsEl.querySelectorAll('.tg-chip').forEach(b => b.classList.toggle('is-active', b === btn));
          render();
        });
      });

      render();
    } catch (err) {
      countEl.textContent = 'ガイドデータの読み込みに失敗しました。';
      console.error(err);
    }
  }

  keywordEl.addEventListener('input', render);
  init();
})();
