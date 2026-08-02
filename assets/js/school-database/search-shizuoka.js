// 静岡県学校データベース - 検索・並び替え制御JS (assets/js/school-database/search-shizuoka.js)
// フィールド名は千葉県版・神奈川県版・山梨県版と同じ（name, establishment, course は配列）。

document.addEventListener('DOMContentLoaded', () => {
  let schoolData = [];
  let currentFilteredResults = [];
  let selectedHonorific = '御中';
  let displayedCount = 100;

  const keywordInput = document.getElementById('keyword');
  const citySelect = document.getElementById('city');
  const sortSelect = document.getElementById('sort-order');
  const typeCheckboxes = document.querySelectorAll('.type-checkbox');
  const estCheckboxes = document.querySelectorAll('.est-checkbox');
  const resultsContainer = document.getElementById('results-list');
  const countSpan = document.getElementById('count');
  const honorificRadios = document.querySelectorAll('.honorific-radio');

  // 静岡県行政順（市部 -> 郡部）
  const MUNICIPALITY_ORDER = [
    '静岡市葵区', '静岡市駿河区', '静岡市清水区', '浜松市中央区', '浜松市浜名区', '浜松市天竜区',
    '沼津市', '熱海市', '三島市', '富士宮市', '伊東市', '島田市',
    '富士市', '磐田市', '焼津市', '掛川市', '藤枝市', '御殿場市',
    '袋井市', '下田市', '裾野市', '湖西市', '伊豆市', '御前崎市',
    '菊川市', '伊豆の国市', '牧之原市', '賀茂郡東伊豆町', '賀茂郡河津町', '賀茂郡南伊豆町',
    '賀茂郡松崎町', '賀茂郡西伊豆町', '田方郡函南町', '駿東郡清水町', '駿東郡長泉町', '駿東郡小山町',
    '榛原郡吉田町', '榛原郡川根本町', '周智郡森町'
  ];

  const SCHOOL_TYPE_ORDER = [
    '幼稚園', '小学校', '中学校', '義務教育学校', '高等学校', '中等教育学校', '特別支援学校'
  ];

  const ESTABLISHMENT_TYPE_ORDER = [
    '国立', '公立', '私立'
  ];

  // 1. 静岡県データの読み込み
  fetch('/data/school-database/shizuoka.json')
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      schoolData = data;
      initCitySelect(data);
      performSearch();
    })
    .catch(error => {
      console.error('Error fetching Shizuoka school data:', error);
      resultsContainer.innerHTML = '<p style="color:red; text-align:center; padding: 20px;">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
    });

  // 2. 市町村セレクトボックスの初期化
  function initCitySelect(data) {
    const availableCities = new Set(
      data.map(item => item.municipality).filter(c => c && c !== '静岡県')
    );
    MUNICIPALITY_ORDER.forEach(city => {
      if (availableCities.has(city)) {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
      }
    });
    availableCities.forEach(city => {
      if (!MUNICIPALITY_ORDER.includes(city)) {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
      }
    });
  }

  // 3. イベントリスナーの登録
  let searchTimeout;
  if (keywordInput) {
    keywordInput.addEventListener('input', () => {
      performSearch();
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        if (keywordInput.value.trim()) {
          trackEvent('school_search', {
            'results_count': currentFilteredResults.length
          });
        }
      }, 1500);
    });
  }

  if (citySelect) {
    citySelect.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'municipality',
        'results_count': currentFilteredResults.length
      });
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'sort_order',
        'sort_order': sortSelect.value,
        'results_count': currentFilteredResults.length
      });
    });
  }

  typeCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'school_type',
        'results_count': currentFilteredResults.length
      });
    });
  });

  estCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'establishment_type',
        'results_count': currentFilteredResults.length
      });
    });
  });

  honorificRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      selectedHonorific = e.target.value;
      updatePreviews();
    });
  });

  // 4. 並び替えロジック
  function applySorting(items, mode = 'admin') {
    const sorted = [...items];
    sorted.sort((a, b) => {
      if (mode === 'admin') {
        const mIdxA = MUNICIPALITY_ORDER.indexOf(a.municipality);
        const mIdxB = MUNICIPALITY_ORDER.indexOf(b.municipality);
        const mDiff = (mIdxA >= 0 ? mIdxA : 999) - (mIdxB >= 0 ? mIdxB : 999);
        if (mDiff !== 0) return mDiff;

        const tIdxA = SCHOOL_TYPE_ORDER.indexOf(a.school_type);
        const tIdxB = SCHOOL_TYPE_ORDER.indexOf(b.school_type);
        const tDiff = (tIdxA >= 0 ? tIdxA : 999) - (tIdxB >= 0 ? tIdxB : 999);
        if (tDiff !== 0) return tDiff;

        const eIdxA = ESTABLISHMENT_TYPE_ORDER.indexOf(a.establishment);
        const eIdxB = ESTABLISHMENT_TYPE_ORDER.indexOf(b.establishment);
        const eDiff = (eIdxA >= 0 ? eIdxA : 999) - (eIdxB >= 0 ? eIdxB : 999);
        if (eDiff !== 0) return eDiff;

        const nameA = a.name_kana || a.name;
        const nameB = b.name_kana || b.name;
        return nameA.localeCompare(nameB, 'ja');
      } else if (mode === 'name') {
        const nameA = a.name_kana || a.name;
        const nameB = b.name_kana || b.name;
        return nameA.localeCompare(nameB, 'ja');
      } else if (mode === 'zip') {
        return (a.postal_code || '').localeCompare(b.postal_code || '');
      } else if (mode === 'est') {
        const eIdxA = ESTABLISHMENT_TYPE_ORDER.indexOf(a.establishment);
        const eIdxB = ESTABLISHMENT_TYPE_ORDER.indexOf(b.establishment);
        const eDiff = (eIdxA >= 0 ? eIdxA : 999) - (eIdxB >= 0 ? eIdxB : 999);
        if (eDiff !== 0) return eDiff;
        const nameA = a.name_kana || a.name;
        const nameB = b.name_kana || b.name;
        return nameA.localeCompare(nameB, 'ja');
      } else if (mode === 'type') {
        const tIdxA = SCHOOL_TYPE_ORDER.indexOf(a.school_type);
        const tIdxB = SCHOOL_TYPE_ORDER.indexOf(b.school_type);
        const tDiff = (tIdxA >= 0 ? tIdxA : 999) - (tIdxB >= 0 ? tIdxB : 999);
        if (tDiff !== 0) return tDiff;
        const nameA = a.name_kana || a.name;
        const nameB = b.name_kana || b.name;
        return nameA.localeCompare(nameB, 'ja');
      }
      return 0;
    });
    return sorted;
  }

  // 5. 検索処理の本体
  function performSearch() {
    displayedCount = 100;
    const keyword = keywordInput ? keywordInput.value.trim().toLowerCase() : '';
    const selectedCity = citySelect ? citySelect.value : '';
    const sortMode = sortSelect ? sortSelect.value : 'admin';

    const checkedTypes = Array.from(typeCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    const checkedEsts = Array.from(estCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    const filtered = schoolData.filter(school => {
      const matchesKeyword = !keyword ||
        school.name.toLowerCase().includes(keyword) ||
        (school.name_kana && school.name_kana.toLowerCase().includes(keyword)) ||
        (school.municipality && school.municipality.toLowerCase().includes(keyword)) ||
        (school.postal_code && school.postal_code.includes(keyword)) ||
        (school.address && school.address.toLowerCase().includes(keyword)) ||
        (school.phone && school.phone.includes(keyword));

      const matchesCity = !selectedCity || school.municipality === selectedCity;
      const matchesType = checkedTypes.length === 0 || checkedTypes.includes(school.school_type);
      const matchesEst = checkedEsts.length === 0 || checkedEsts.includes(school.establishment);

      return matchesKeyword && matchesCity && matchesType && matchesEst;
    });

    const sortedResults = applySorting(filtered, sortMode);
    currentFilteredResults = sortedResults;
    renderResults(sortedResults);
  }

  // 6. 検索結果の描画
  function renderResults(results) {
    resultsContainer.innerHTML = '';
    countSpan.textContent = results.length.toLocaleString();

    if (results.length === 0) {
      resultsContainer.innerHTML = '<p style="text-align:center; color:var(--muted, #718096); padding:40px 0;">条件に一致する学校が見つかりませんでした。</p>';
      return;
    }

    const fragment = document.createDocumentFragment();
    const itemsToRender = results.slice(0, displayedCount);

    itemsToRender.forEach((school, index) => {
      const card = document.createElement('div');
      card.className = 'school-card';

      const copyText = formatAddress(school, selectedHonorific);
      const schoolId = `school-shizuoka-${index}`;
      const estBadgeClass = school.establishment === '私立' ? 'school-badge-est-private' : 'school-badge-est-public';
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(school.name + ' ' + school.address)}`;
      const courseText = Array.isArray(school.course) && school.course.length > 0 ? school.course.join('・') : '';

      let websiteBtnHtml = '';
      if (school.website && (school.website.startsWith('http://') || school.website.startsWith('https://'))) {
        websiteBtnHtml = `
          <a class="btn-website" href="${escapeHtml(school.website)}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHtml(school.name)}の公式ホームページを開く" title="公式ホームページを開く">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
            公式HP
          </a>
        `;
      }

      card.innerHTML = `
        <div class="school-info">
          <div class="school-badges">
            <span class="${estBadgeClass}">${school.establishment}</span>
            <span class="school-badge-type">${school.school_type}</span>
            ${school.municipality ? `<span class="school-badge-city">${school.municipality}</span>` : ''}
            ${courseText ? `<span class="school-badge-city">${escapeHtml(courseText)}</span>` : ''}
          </div>
          <h3 class="school-name">${escapeHtml(school.name)}</h3>
          <div class="school-address-row">
            <span class="zip">〒${escapeHtml(school.postal_code)}</span>
            <span class="addr">${escapeHtml(school.address)}</span>
          </div>
          <div class="school-tel-row">TEL: ${school.phone ? escapeHtml(school.phone) : 'なし'}</div>
        </div>
        <div class="school-actions">
          <div class="action-buttons-group">
            <button class="btn-copy" data-id="${schoolId}" data-index="${index}" type="button">
              <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
              住所コピー
            </button>
            <a class="btn-map" href="${mapsUrl}" target="_blank" rel="noopener noreferrer" title="Google Mapsで場所を確認">
              <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
              地図
            </a>
            ${websiteBtnHtml}
          </div>
          <div class="copy-preview" id="preview-${schoolId}">${escapeHtml(copyText)}</div>
        </div>
      `;

      const copyBtn = card.querySelector('.btn-copy');
      copyBtn.addEventListener('click', () => {
        const textToCopy = formatAddress(school, selectedHonorific);
        copyToClipboard(textToCopy);

        trackEvent('school_copy', {
          'honorific': selectedHonorific
        });
      });

      const mapBtn = card.querySelector('.btn-map');
      mapBtn.addEventListener('click', () => {
        trackEvent('school_map', {
          'establishment_type': school.establishment,
          'school_type': school.school_type
        });
      });

      const websiteBtn = card.querySelector('.btn-website');
      if (websiteBtn) {
        websiteBtn.addEventListener('click', () => {
          trackEvent('school_website_open', {
            prefecture: 'shizuoka',
            school_type: school.school_type,
            establishment_type: school.establishment,
            municipality: school.municipality
          });
        });
      }

      fragment.appendChild(card);
    });

    resultsContainer.appendChild(fragment);

    if (results.length > displayedCount) {
      const showMoreContainer = document.createElement('div');
      showMoreContainer.className = 'show-more-container';
      showMoreContainer.style.textAlign = 'center';
      showMoreContainer.style.padding = '24px 0 10px';

      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'btn btn-light';
      showMoreBtn.id = 'btn-show-more';
      showMoreBtn.type = 'button';
      showMoreBtn.innerHTML = `さらに表示する (${displayedCount} / ${results.length.toLocaleString()}件表示中)`;
      showMoreBtn.style.minWidth = '240px';
      showMoreBtn.style.borderColor = 'var(--gold, #c5a059)';
      showMoreBtn.style.color = 'var(--navy, #0c1b33)';
      showMoreBtn.style.boxShadow = '0 4px 10px rgba(197, 160, 89, 0.15)';

      showMoreBtn.addEventListener('click', () => {
        displayedCount += 100;
        renderResults(results);
      });

      showMoreContainer.appendChild(showMoreBtn);
      resultsContainer.appendChild(showMoreContainer);
    }
  }

  // 7. プレビュー更新
  function updatePreviews() {
    resultsContainer.querySelectorAll('.school-card').forEach(card => {
      const copyBtn = card.querySelector('.btn-copy');
      if (!copyBtn) return;
      const schoolIndex = parseInt(copyBtn.getAttribute('data-index'), 10);
      const school = currentFilteredResults[schoolIndex];
      if (school) {
        const previewDiv = card.querySelector('.copy-preview');
        previewDiv.textContent = formatAddress(school, selectedHonorific);
      }
    });
  }

  // 8. 住所フォーマット
  function formatAddress(school, honorific) {
    let nameWithHonorific = '';
    if (honorific === '御中') {
      nameWithHonorific = `${school.name} 御中`;
    } else if (honorific === '校長先生') {
      nameWithHonorific = `${school.name}\n校長 殿`;
    } else if (honorific === '園長先生') {
      nameWithHonorific = `${school.name}\n園長 殿`;
    } else if (honorific === '副校長先生') {
      nameWithHonorific = `${school.name}\n副校長 殿`;
    } else if (honorific === '事務室御中') {
      nameWithHonorific = `${school.name} 事務室 御中`;
    } else if (honorific === 'ご担当者様') {
      nameWithHonorific = `${school.name}\nご担当者 様`;
    } else {
      nameWithHonorific = `${school.name} ${honorific}`;
    }

    return `〒${school.postal_code}\n${school.address}\n${nameWithHonorific}`;
  }

  // 9. クリップボード機能
  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => showToast('宛名住所をコピーしました！'))
        .catch(err => {
          console.error('Clipboard copy failed:', err);
          fallbackCopyToClipboard(text);
        });
    } else {
      fallbackCopyToClipboard(text);
    }
  }

  function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      showToast('宛名住所をコピーしました！');
    } catch (err) {
      console.error('Fallback copy failed:', err);
      alert('コピーに失敗しました。手動でコピーしてください。');
    }
    document.body.removeChild(textArea);
  }

  function showToast(message) {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast';
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  // 10. CSVダウンロード
  const downloadBtn = document.getElementById('csv-download-btn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', (e) => {
      e.preventDefault();
      downloadFilteredCSV(currentFilteredResults);
      trackEvent('school_csv', {
        'file_name': 'shizuoka_schools_address_filtered.csv',
        'results_count': currentFilteredResults.length
      });
    });
  }

  function downloadFilteredCSV(data) {
    if (!data || data.length === 0) {
      alert('ダウンロードするデータがありません。');
      return;
    }

    let csvContent = '﻿';
    csvContent += '"都道府県","市町村","設置区分","学校種別","学校名","学校名（かな）","郵便番号","所在地","電話番号","課程","出典元","公式ホームページ"\n';

    data.forEach(item => {
      const row = [
        item.prefecture || '静岡県',
        item.municipality || '',
        item.establishment || '',
        item.school_type || '',
        item.name || '',
        item.name_kana || '',
        item.postal_code || '',
        item.address || '',
        item.phone || '',
        Array.isArray(item.course) ? item.course.join('・') : '',
        item.source_name || '',
        item.website || ''
      ].map(val => sanitizeForCSV(val));

      csvContent += row.join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `shizuoka_schools_address_filtered_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function sanitizeForCSV(val) {
    if (val === null || val === undefined) val = '';
    let str = String(val).strip ? String(val).trim() : String(val);
    if (str.startsWith('=') || str.startsWith('+') || str.startsWith('-') || str.startsWith('@')) {
      str = "'" + str;
    }
    return `"${str.replace(/"/g, '""')}"`;
  }

  // 11. GA4 イベント送信
  function trackEvent(eventName, params = {}) {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params);
      console.log(`[GA4 Event] ${eventName}`, params);
    }
  }

  // 12. 上に戻るボタン
  const backToTopBtn = document.getElementById('back-to-top');
  if (backToTopBtn) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 400) {
        backToTopBtn.classList.add('visible');
      } else {
        backToTopBtn.classList.remove('visible');
      }
    }, { passive: true });

    backToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
