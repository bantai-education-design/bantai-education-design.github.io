// 東京都公立小中学校 宛先検索データベース - 検索制御用JS

document.addEventListener('DOMContentLoaded', () => {
  let schoolData = [];
  let currentFilteredResults = []; // 現在のフィルター結果を保持
  let selectedHonorific = '御中';
  let displayedCount = 100;

  const keywordInput = document.getElementById('keyword');
  const citySelect = document.getElementById('city');
  const typeCheckboxes = document.querySelectorAll('.type-checkbox');
  const estCheckboxes = document.querySelectorAll('.est-checkbox'); // 設置区分
  const resultsContainer = document.getElementById('results-list');
  const countSpan = document.getElementById('count');
  const honorificRadios = document.querySelectorAll('.honorific-radio');

  // 1. 本データ（2025年版全件データ）の読み込み
  fetch('/data/tokyo_public_schools_address_2025.json')
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
      console.error('Error fetching school data:', error);
      resultsContainer.innerHTML = '<p style="color:red; text-align:center; padding: 20px;">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
    });

  // 東京都の行政順（23区 → 市部 → 町村部）
  const MUNICIPALITY_ORDER = [
    // 23区
    '千代田区', '中央区', '港区', '新宿区', '文京区',
    '台東区', '墨田区', '江東区', '品川区', '目黒区',
    '大田区', '世田谷区', '渋谷区', '中野区', '杉並区',
    '豊島区', '北区', '荒川区', '板橋区', '練馬区',
    '足立区', '葛飾区', '江戸川区',
    // 市部
    '八王子市', '立川市', '武蔵野市', '三鷹市', '青梅市',
    '府中市', '昭島市', '調布市', '町田市', '小金井市',
    '小平市', '日野市', '東村山市', '国分寺市', '国立市',
    '福生市', '狛江市', '東大和市', '清瀬市', '東久留米市',
    '武蔵村山市', '多摩市', '稲城市', '羽村市', 'あきる野市',
    '西東京市',
    // 町村部
    '瑞穂町', '日の出町', '檜原村', '奥多摩町',
    '大島町', '利島村', '新島村', '神津島村',
    '三宅村', '御蔵島村', '八丈町', '青ヶ島村', '小笠原村'
  ];

  // 2. 区市町村セレクトボックスの初期化（行政順）
  function initCitySelect(data) {
    const availableCities = new Set(
      data.map(item => item.municipality).filter(c => c && c !== '東京都')
    );
    // 行政順で、データに存在する自治体だけを追加
    MUNICIPALITY_ORDER.forEach(city => {
      if (availableCities.has(city)) {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
      }
    });
  }

  // 3. 検索・イベント計測リスナーの登録
  let searchTimeout;
  keywordInput.addEventListener('input', () => {
    performSearch();
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      const keyword = keywordInput.value.trim();
      if (keyword) {
        trackEvent('school_search', {
          'search_keyword': keyword
        });
      }
    }, 1500); // 1.5秒間入力が停止したら検索イベントを送信
  });

  citySelect.addEventListener('change', () => {
    performSearch();
    const city = citySelect.value;
    trackEvent('school_municipality_filter', {
      'municipality': city || 'all'
    });
  });

  typeCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      performSearch();
      const checkedTypes = Array.from(typeCheckboxes)
        .filter(c => c.checked)
        .map(c => c.value)
        .join(',');
      trackEvent('school_type_filter', {
        'checked_types': checkedTypes || 'none'
      });
    });
  });

  // 設置区分チェックボックスの変更監視
  estCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
      performSearch();
      const checkedEsts = Array.from(estCheckboxes)
        .filter(c => c.checked)
        .map(c => c.value)
        .join(',');
      trackEvent('school_establishment_filter', {
        'checked_establishments': checkedEsts || 'none'
      });
    });
  });

  // 4. 敬称ラジオボタンの変更監視
  honorificRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      selectedHonorific = e.target.value;
      updatePreviews();
    });
  });

  // 5. 検索処理の本体
  function performSearch() {
    displayedCount = 100;
    const keyword = keywordInput.value.trim().toLowerCase();
    const selectedCity = citySelect.value;
    
    // チェックされている学校種を取得
    const checkedTypes = Array.from(typeCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    // チェックされている設置区分を取得
    const checkedEsts = Array.from(estCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    // フィルタリング
    const filtered = schoolData.filter(school => {
      // キーワードマッチ（学校名、よみがな、住所）
      const matchesKeyword = !keyword || 
        school.school_name.toLowerCase().includes(keyword) ||
        school.school_name_kana.toLowerCase().includes(keyword) ||
        school.address.toLowerCase().includes(keyword);

      // 区市町村マッチ
      const matchesCity = !selectedCity || school.municipality === selectedCity;

      // 学校種マッチ
      const matchesType = checkedTypes.length === 0 || checkedTypes.includes(school.school_type);

      // 設置区分マッチ（将来のデータ拡張を見据え、データにフィールドがない場合は公立として処理）
      const estType = school.establishment_type || '公立';
      const matchesEst = checkedEsts.length === 0 || checkedEsts.includes(estType);

      return matchesKeyword && matchesCity && matchesType && matchesEst;
    });

    currentFilteredResults = filtered; // CSVダウンロード用
    renderResults(filtered);
  }

  // 6. 結果の描画
  function renderResults(results) {
    resultsContainer.innerHTML = '';
    countSpan.textContent = results.length;

    if (results.length === 0) {
      resultsContainer.innerHTML = '<p style="text-align:center; color:var(--muted); padding:40px 0;">条件に一致する学校が見つかりませんでした。</p>';
      return;
    }

    const fragment = document.createDocumentFragment();
    const itemsToRender = results.slice(0, displayedCount);

    itemsToRender.forEach((school, index) => {
      const card = document.createElement('div');
      card.className = 'school-card';
      
      const copyText = formatAddress(school, selectedHonorific);
      const schoolId = `school-2025-${index}`;

      const mapQuery = encodeURIComponent(`${school.school_name} ${school.address}`);
      const mapUrl = `https://www.google.com/maps/search/?api=1&query=${mapQuery}`;

      card.innerHTML = `
        <div class="school-info">
          <div class="school-badges">
            <span class="school-badge-type">${escapeHtml(school.school_type)}</span>
            <span class="school-badge-city">${escapeHtml(school.municipality)}</span>
          </div>
          <h3 class="school-name">${escapeHtml(school.school_name)}</h3>
          <div class="school-address-row">
            <span class="zip">〒${escapeHtml(school.postal_code)}</span>
            <span class="addr">${escapeHtml(school.address)}</span>
          </div>
          <div class="school-tel-row">TEL: ${escapeHtml(school.phone)}</div>
        </div>
        <div class="school-actions">
          <div class="action-buttons-group">
            <button class="btn-copy" data-id="${schoolId}" data-index="${index}" type="button">
              <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
              住所コピー
            </button>
            <a class="btn-map" href="${mapUrl}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHtml(school.school_name)}をGoogle Mapsで開く" title="Google Mapsで場所を確認">
              <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
              地図
            </a>
          </div>
          <div class="copy-preview" id="preview-${schoolId}">${escapeHtml(copyText)}</div>
        </div>
      `;

      // コピーボタンのイベント登録
      const copyBtn = card.querySelector('.btn-copy');
      copyBtn.addEventListener('click', () => {
        const textToCopy = formatAddress(school, selectedHonorific);
        copyToClipboard(textToCopy);
        
        // 宛名コピーイベントの計測
        trackEvent('school_address_copy', {
          'school_name': school.school_name,
          'honorific': selectedHonorific
        });
      });

      // 地図ボタンのイベント登録 (GA4: school_map)
      const mapBtn = card.querySelector('.btn-map');
      mapBtn.addEventListener('click', () => {
        trackEvent('school_map', {
          prefecture: 'tokyo',
          school_type: school.school_type,
          establishment_type: school.establishment_type || '公立',
          municipality: school.municipality
        });
      });

      fragment.appendChild(card);
    });

    resultsContainer.appendChild(fragment);

    // さらに表示ボタンの制御
    if (results.length > displayedCount) {
      const showMoreContainer = document.createElement('div');
      showMoreContainer.className = 'show-more-container';
      showMoreContainer.style.textAlign = 'center';
      showMoreContainer.style.padding = '24px 0 10px';

      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'btn btn-light';
      showMoreBtn.id = 'btn-show-more';
      showMoreBtn.type = 'button';
      showMoreBtn.innerHTML = `さらに表示する (${displayedCount} / ${results.length}件表示中)`;
      showMoreBtn.style.minWidth = '240px';
      showMoreBtn.style.borderColor = 'var(--gold)';
      showMoreBtn.style.color = 'var(--navy)';
      showMoreBtn.style.boxShadow = '0 4px 10px rgba(197, 160, 89, 0.15)';

      showMoreBtn.addEventListener('click', () => {
        displayedCount += 100;
        renderResults(results);
      });

      showMoreContainer.appendChild(showMoreBtn);
      resultsContainer.appendChild(showMoreContainer);
    }
  }

  // 7. プレビューのリアルタイム更新
  function updatePreviews() {
    resultsContainer.querySelectorAll('.school-card').forEach(card => {
      const copyBtn = card.querySelector('.btn-copy');
      const schoolIndex = parseInt(copyBtn.getAttribute('data-index'), 10);
      const schoolId = copyBtn.getAttribute('data-id');
      
      const school = currentFilteredResults[schoolIndex];
      
      if (school) {
        const previewDiv = card.querySelector('.copy-preview');
        previewDiv.textContent = formatAddress(school, selectedHonorific);
      }
    });
  }

  // 8. 住所フォーマットユーティリティ
  function formatAddress(school, honorific) {
    let nameWithHonorific = '';
    if (honorific === '御中') {
      nameWithHonorific = `${school.school_name} 御中`;
    } else if (honorific === '校長先生') {
      nameWithHonorific = `${school.school_name}\n校長 殿`;
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

  // 9. クリップボードへのコピーとトースト通知
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

  // 10. CSVダウンロードおよびプロモーションバナークリックイベントの計測
  const downloadBtn = document.getElementById('csv-download-btn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', (e) => {
      e.preventDefault(); // ハッシュリンク等のデフォルト動作防止
      
      downloadFilteredCSV(currentFilteredResults);

      trackEvent('school_csv_download', {
        'file_name': 'tokyo_schools_address_filtered.csv',
        'results_count': currentFilteredResults.length
      });
    });
  }

  // 検索結果連動の動的CSVダウンロード生成処理
  function downloadFilteredCSV(data) {
    if (!data || data.length === 0) {
      alert('ダウンロードするデータがありません。');
      return;
    }

    // Excel文字化け防止のためBOM付与
    let csvContent = '\ufeff';
    // ヘッダー
    csvContent += '"学校種別","設置区分","区市町村","学校名","学校名（ふりがな）","郵便番号","所在地","電話番号","デフォルト宛名","用途タグ"\n';

    data.forEach(item => {
      const row = [
        item.school_type || '',
        item.establishment_type || '公立',
        item.municipality || '',
        item.school_name || '',
        item.school_name_kana || '',
        item.postal_code || '',
        item.address || '',
        item.phone || '',
        item.addressee_default || '',
        (item.tags || []).join(',')
      ].map(val => `"${(val || '').replace(/"/g, '""')}"`); // ダブルクォーテーションエスケープ

      csvContent += row.join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `tokyo_schools_address_filtered_${new Date().toISOString().slice(0, 10)}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  const promoBtn = document.getElementById('envelope-promo-btn');
  if (promoBtn) {
    promoBtn.addEventListener('click', () => {
      trackEvent('envelope_app_click', {
        'button_text': promoBtn.textContent.trim(),
        'destination_url': promoBtn.getAttribute('href')
      });
    });
  }

  // 11. GA4イベント送信関数
  function trackEvent(eventName, params = {}) {
    if (typeof gtag === 'function') {
      gtag('event', eventName, params);
      console.log(`[GA4 Event] ${eventName}`, params);
    } else {
      console.warn(`[GA4 Warning] gtag is not defined. Failed to track event: ${eventName}`);
    }
  }

  // 12. 「上に戻る」ボタンの制御
  const backToTopBtn = document.getElementById('back-to-top');
  if (backToTopBtn) {
    // スクロール量が400pxを超えたらボタンを表示
    window.addEventListener('scroll', () => {
      if (window.scrollY > 400) {
        backToTopBtn.classList.add('visible');
      } else {
        backToTopBtn.classList.remove('visible');
      }
    }, { passive: true });

    // クリックでページ最上部までスムーズスクロール
    function scrollToPageTop() {
      // window と scrollingElement の両方に対してスムーズスクロールを実行
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
      const scrollRoot = document.scrollingElement || document.documentElement;
      if (scrollRoot !== document.documentElement) {
        scrollRoot.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
      }
    }

    backToTopBtn.addEventListener('click', scrollToPageTop);
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
