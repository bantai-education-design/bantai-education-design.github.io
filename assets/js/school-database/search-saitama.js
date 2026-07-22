// 埼玉県学校宛先データベース - 検索制御用JS (assets/js/school-database/search-saitama.js)

document.addEventListener('DOMContentLoaded', () => {
  let schoolData = [];
  let currentFilteredResults = [];
  let selectedHonorific = '御中';
  let displayedCount = 100;

  const keywordInput = document.getElementById('keyword');
  const citySelect = document.getElementById('city');
  const typeCheckboxes = document.querySelectorAll('.type-checkbox');
  const estCheckboxes = document.querySelectorAll('.est-checkbox');
  const resultsContainer = document.getElementById('results-list');
  const countSpan = document.getElementById('count');
  const honorificRadios = document.querySelectorAll('.honorific-radio');

  // 埼玉県行政順（さいたま市各区 -> 各市 -> 町村）
  const MUNICIPALITY_ORDER = [
    // さいたま市各区
    'さいたま市西区', 'さいたま市北区', 'さいたま市大宮区', 'さいたま市見沼区', 'さいたま市中央区',
    'さいたま市桜区', 'さいたま市浦和区', 'さいたま市南区', 'さいたま市緑区', 'さいたま市岩槻区',
    // 市部
    '川越市', '熊谷市', '川口市', '行田市', '秩父市', '所沢市', '飯能市',
    '加須市', '本庄市', '東松山市', '春日部市', '狭山市', '羽生市', '鴻巣市', '深谷市',
    '上尾市', '草加市', '越谷市', '蕨市', '戸田市', '入間市', '朝霞市', '志木市',
    '和光市', '新座市', '桶川市', '久喜市', '北本市', '八潮市', '富士見市', '三郷市',
    '蓮田市', '坂戸市', '幸手市', '鶴ヶ島市', '日高市', '吉川市', 'ふじみ野市', '白岡市',
    // 町村部
    '伊奈町', '三芳町', '毛呂山町', '越生町', '滑川町', '嵐山町', '小川町', '川島町',
    '吉見町', '鳩山町', 'ときがわ町', '横瀬町', '皆野町', '長瀞町', '小鹿野町', '東秩父村',
    '美里町', '神川町', '上里町', '寄居町', '宮代町', '杉戸町', '松伏町'
  ];

  // 1. 埼玉県データの読み込み
  fetch('/data/school-database/saitama.json')
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      schoolData = data;
      currentFilteredResults = data;
      initCitySelect(data);
      performSearch();
    })
    .catch(error => {
      console.error('Error fetching Saitama school data:', error);
      resultsContainer.innerHTML = '<p style="color:red; text-align:center; padding: 20px;">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
    });

  // 2. 市町村セレクトボックスの初期化
  function initCitySelect(data) {
    const availableCities = new Set(
      data.map(item => item.municipality).filter(c => c && c !== '埼玉県')
    );
    MUNICIPALITY_ORDER.forEach(city => {
      if (availableCities.has(city)) {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
      }
    });
    // 万一リストに含まれない自治体があれば末尾に追加
    availableCities.forEach(city => {
      if (!MUNICIPALITY_ORDER.includes(city)) {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
      }
    });
  }

  // 3. イベントリスナーの登録 (GA4規約遵守: 入力文字列は絶対送信しない)
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

  // 4. 検索フィルタリング
  function performSearch() {
    displayedCount = 100;
    const keyword = keywordInput.value.trim().toLowerCase();
    const selectedCity = citySelect.value;
    
    const checkedTypes = Array.from(typeCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    const checkedEsts = Array.from(estCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    const filtered = schoolData.filter(school => {
      const matchesKeyword = !keyword || 
        school.school_name.toLowerCase().includes(keyword) ||
        (school.school_name_kana && school.school_name_kana.toLowerCase().includes(keyword)) ||
        (school.municipality && school.municipality.toLowerCase().includes(keyword)) ||
        (school.postal_code && school.postal_code.includes(keyword)) ||
        (school.address && school.address.toLowerCase().includes(keyword)) ||
        (school.phone && school.phone.includes(keyword));

      const matchesCity = !selectedCity || school.municipality === selectedCity;
      const matchesType = checkedTypes.length === 0 || checkedTypes.includes(school.school_type);
      const matchesEst = checkedEsts.length === 0 || checkedEsts.includes(school.establishment_type);

      return matchesKeyword && matchesCity && matchesType && matchesEst;
    });

    currentFilteredResults = filtered;
    renderResults(filtered);
  }

  // 5. 検索結果のレンダリング
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
      const schoolId = `school-saitama-${index}`;
      const estBadgeClass = school.establishment_type === '私立' ? 'school-badge-est-private' : 'school-badge-est-public';
      const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(school.school_name + ' ' + school.address)}`;

      card.innerHTML = `
        <div class="school-info">
          <div class="school-badges">
            <span class="${estBadgeClass}">${school.establishment_type}</span>
            <span class="school-badge-type">${school.school_type}</span>
            ${school.municipality ? `<span class="school-badge-city">${school.municipality}</span>` : ''}
          </div>
          <h3 class="school-name">${escapeHtml(school.school_name)}</h3>
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
          </div>
          <div class="copy-preview" id="preview-${schoolId}">${escapeHtml(copyText)}</div>
        </div>
      `;

      // コピーボタンイベント
      const copyBtn = card.querySelector('.btn-copy');
      copyBtn.addEventListener('click', () => {
        const textToCopy = formatAddress(school, selectedHonorific);
        copyToClipboard(textToCopy);
        
        trackEvent('school_copy', {
          'honorific': selectedHonorific
        });
      });

      // Google Mapsボタンイベント
      const mapBtn = card.querySelector('.btn-map');
      mapBtn.addEventListener('click', () => {
        trackEvent('school_map', {
          'establishment_type': school.establishment_type,
          'school_type': school.school_type
        });
      });

      fragment.appendChild(card);
    });

    resultsContainer.appendChild(fragment);

    // さらに表示ボタン
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

  // 6. プレビュー更新
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

  // 7. 住所フォーマット
  function formatAddress(school, honorific) {
    let nameWithHonorific = '';
    if (honorific === '御中') {
      nameWithHonorific = `${school.school_name} 御中`;
    } else if (honorific === '校長先生') {
      nameWithHonorific = `${school.school_name}\n校長 殿`;
    } else if (honorific === '園長先生') {
      nameWithHonorific = `${school.school_name}\n園長 殿`;
    } else if (honorific === '副校長先生') {
      nameWithHonorific = `${school.school_name}\n副校長 殿`;
    } else if (honorific === '事務室御中') {
      nameWithHonorific = `${school.school_name} 事務室 御中`;
    } else if (honorific === 'ご担当者様') {
      nameWithHonorific = `${school.school_name}\nご担当者 様`;
    } else {
      nameWithHonorific = `${school.school_name} ${honorific}`;
    }

    return `〒${school.postal_code}\n${school.address}\n${nameWithHonorific}`;
  }

  // 8. クリップボード機能
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

  // 9. CSVダウンロード (Phase 8: 数式インジェクション対策 & UTF-8 BOM & 検索結果のみ)
  const downloadBtn = document.getElementById('csv-download-btn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', (e) => {
      e.preventDefault();
      downloadFilteredCSV(currentFilteredResults);
      trackEvent('school_csv', {
        'file_name': 'saitama_schools_address_filtered.csv',
        'results_count': currentFilteredResults.length
      });
    });
  }

  function downloadFilteredCSV(data) {
    if (!data || data.length === 0) {
      alert('ダウンロードするデータがありません。');
      return;
    }

    let csvContent = '\ufeff'; // UTF-8 BOM
    csvContent += '"都道府県","市町村","設置区分","学校種別","学校名","学校名（かな）","郵便番号","所在地","電話番号","出典元"\n';

    data.forEach(item => {
      const row = [
        item.prefecture || '埼玉県',
        item.municipality || '',
        item.establishment_type || '',
        item.school_type || '',
        item.school_name || '',
        item.school_name_kana || '',
        item.postal_code || '',
        item.address || '',
        item.phone || '',
        item.source_name || ''
      ].map(val => sanitizeForCSV(val));

      csvContent += row.join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `saitama_schools_address_filtered_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // 数式インジェクション対策 (Formula Injection Protection)
  function sanitizeForCSV(val) {
    if (val === null || val === undefined) val = '';
    let str = String(val).trim();
    if (str.startsWith('=') || str.startsWith('+') || str.startsWith('-') || str.startsWith('@')) {
      str = "'" + str; // 前置シングルクォートで数式実行を防止
    }
    return `"${str.replace(/"/g, '""')}"`;
  }

  // 10. GA4 イベント送信
  function trackEvent(eventName, params = {}) {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params);
      console.log(`[GA4 Event] ${eventName}`, params);
    }
  }

  // 11. 上に戻るボタン
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
