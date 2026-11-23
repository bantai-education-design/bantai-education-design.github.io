(() => {
  'use strict';

  const rootEl = document.getElementById('guide-app');
  if (!rootEl) return;

  const dataUrl = rootEl.dataset.jsonUrl;
  const defaultTab = rootEl.dataset.defaultTab || 'sports';
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

    if (filtered.length === 0) {
      listEl.innerHTML = '<p style="color:#64748b;padding:24px 0;">該当する大会ガイドが見つかりませんでした。</p>';
      return;
    }

    listEl.innerHTML = filtered.map(it => {
      const tab = it.tab || defaultTab;
      const filterVal = it.filter_value || it.sport_filter || '';
      const searchHref = `/tools/school-database/awards/?tab=${encodeURIComponent(tab)}` +
        (filterVal ? `&category=${encodeURIComponent(filterVal)}` : '');

      return `
        <article class="tg-card" id="${esc(it.id)}">
          <div class="tg-card-top">
            <span class="tg-cat-badge">${esc(it.category)}</span>
            <span class="tg-org">${esc(it.organizer)}</span>
          </div>
          <h2>${esc(it.name)}</h2>

          <div class="tg-meta-grid">
            <div class="tg-meta-box">
              <div class="tg-meta-label">開催時期</div>
              <div class="tg-meta-val">${esc(it.season)}</div>
            </div>
            <div class="tg-meta-box">
              <div class="tg-meta-label">開催期間</div>
              <div class="tg-meta-val">${esc(it.duration)}</div>
            </div>
            <div class="tg-meta-box">
              <div class="tg-meta-label">主な会場</div>
              <div class="tg-meta-val">${esc(it.venue)}</div>
            </div>
          </div>

          <div class="tg-sections">
            <div class="tg-sec">
              <h3>大会までの予選方法・代表枠</h3>
              <p>${esc(it.qualifying)}</p>
            </div>
            <div class="tg-sec">
              <h3>出場するための手続き</h3>
              <p>${esc(it.entry_procedure)}</p>
            </div>
            <div class="tg-sec">
              <h3>大会の記録・歴史</h3>
              <p>${esc(it.history)}</p>
            </div>
            <div class="tg-sec tg-sec--advice">
              <h3>参加校・顧問・生徒向けの実践アドバイス</h3>
              <p>${esc(it.advice)}</p>
            </div>
          </div>

          <div class="tg-card-foot">
            <a class="tg-db-btn" href="${searchHref}">この大会の全国実績校をDBで見る →</a>
          </div>
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
        '<button type="button" class="tg-chip is-active" data-cat="all">すべて表示</button>',
        ...cats.map(c => `<button type="button" class="tg-chip" data-cat="${esc(c)}">${esc(c)}</button>`)
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
