document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('catalog-search-input');
  const matchingCountSpan = document.getElementById('matching-count');
  const visibleCountSpan = document.getElementById('visible-count');
  const resetBtn = document.getElementById('reset-filter-btn');

  const attributeFilters = document.querySelectorAll('.attribute-filter');
  const statusFilters = document.querySelectorAll('.status-filter');

  const cards = document.querySelectorAll('.catalog-card');
  const groups = document.querySelectorAll('.catalog-group, .catalog-featured-group');
  
  // 空欄表示用要素の作成と追加
  const listContainer = document.querySelector('.catalog-groups');
  const emptyState = document.createElement('div');
  emptyState.className = 'catalog-empty-state';
  emptyState.innerHTML = '<p style="text-align:center; padding:50px 20px; color:var(--muted); font-size:1.05rem; font-weight:600;">該当する製品が見見つかりませんでした。<br>条件を変更してお試しください。</p>';
  emptyState.style.display = 'none';
  if (listContainer) {
    listContainer.appendChild(emptyState);
  }

  function performFilter() {
    const query = searchInput.value.trim().toLowerCase();
    
    // チェックされている条件を取得
    const checkedAttrs = Array.from(attributeFilters)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    const checkedStatuses = Array.from(statusFilters)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    let matchCount = 0;

    // 各カードの判定
    cards.forEach(card => {
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const summary = (card.getAttribute('data-summary') || '').toLowerCase();
      const features = (card.getAttribute('data-features') || '').toLowerCase();

      // 1. キーワードマッチ (名前、要約、特徴に含まれるか)
      const matchesKeyword = !query || 
        name.includes(query) || 
        summary.includes(query) || 
        features.includes(query);

      // 2. 特徴・販路マッチ (AND条件: チェックした特徴をすべて有するか)
      const matchesAttrs = checkedAttrs.every(attr => {
        if (attr === 'flagship') return card.getAttribute('data-flagship') === 'true';
        if (attr === 'hasTrial') return card.getAttribute('data-has-trial') === 'true';
        if (attr === 'hasBooth') return card.getAttribute('data-has-booth') === 'true';
        if (attr === 'hasVector') return card.getAttribute('data-has-vector') === 'true';
        return true;
      });

      // 3. 販売状態マッチ (OR条件: チェックしたいずれかの状態に合致するか)
      const cardStatus = card.getAttribute('data-status') || '';
      const matchesStatus = checkedStatuses.length === 0 || checkedStatuses.some(status => {
        if (status === '販売中') {
          // 「販売中」と「10日間無料体験」を内包する
          return cardStatus === '販売中' || cardStatus === '10日間無料体験';
        }
        return cardStatus === status;
      });

      // 最終判定
      if (matchesKeyword && matchesAttrs && matchesStatus) {
        card.classList.remove('is-hidden');
        matchCount++;
      } else {
        card.classList.add('is-hidden');
      }
    });

    // 各グループのヘッダー/セクションの表示制御
    groups.forEach(group => {
      const visibleCardsInGroup = group.querySelectorAll('.catalog-card:not(.is-hidden)');
      if (visibleCardsInGroup.length === 0) {
        group.style.display = 'none';
      } else {
        group.style.display = '';
      }
    });

    // 空欄状態表示の制御
    if (matchCount === 0) {
      emptyState.style.display = 'block';
    } else {
      emptyState.style.display = 'none';
    }

    // 件数の更新
    matchingCountSpan.textContent = cards.length;
    visibleCountSpan.textContent = matchCount;

    // リセットボタンの表示制御 (何か条件が指定されている場合のみ表示)
    const hasActiveFilters = query.length > 0 || checkedAttrs.length > 0 || checkedStatuses.length > 0;
    if (hasActiveFilters) {
      resetBtn.style.display = 'inline-block';
    } else {
      resetBtn.style.display = 'none';
    }
  }

  // イベントリスナーの登録
  searchInput.addEventListener('input', performFilter);
  attributeFilters.forEach(cb => cb.addEventListener('change', performFilter));
  statusFilters.forEach(cb => cb.addEventListener('change', performFilter));

  // リセット処理
  resetBtn.addEventListener('click', () => {
    searchInput.value = '';
    attributeFilters.forEach(cb => cb.checked = false);
    statusFilters.forEach(cb => cb.checked = false);
    performFilter();
  });

  // 初期読み込み実行
  performFilter();
});
