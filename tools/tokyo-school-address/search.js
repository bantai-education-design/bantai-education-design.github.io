// 東京都公立小中学校 宛先検索データベース - 検索制御用JS

document.addEventListener('DOMContentLoaded', () => {
  let schoolData = [];
  let selectedHonorific = '御中';

  const keywordInput = document.getElementById('keyword');
  const citySelect = document.getElementById('city');
  const typeCheckboxes = document.querySelectorAll('.type-checkbox');
  const resultsContainer = document.getElementById('results-list');
  const countSpan = document.getElementById('count');
  const honorificRadios = document.querySelectorAll('.honorific-radio');

  // 1. サンプルデータの読み込み
  fetch('/data/tokyo_public_schools_address_sample.json')
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
      console.error('Error fetching school data:', error);
      resultsContainer.innerHTML = '<p style="color:red; text-align:center; padding: 20px;">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
    });

  // 2. 区市町村セレクトボックスの初期化
  function initCitySelect(data) {
    const cities = [...new Set(data.map(item => item.city))].sort();
    cities.forEach(city => {
      const option = document.createElement('option');
      option.value = city;
      option.textContent = city;
      citySelect.appendChild(option);
    });
  }

  // 3. 検索イベントリスナーの登録
  keywordInput.addEventListener('input', performSearch);
  citySelect.addEventListener('change', performSearch);
  typeCheckboxes.forEach(cb => cb.addEventListener('change', performSearch));

  // 4. 敬称ラジオボタンの変更監視
  honorificRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      selectedHonorific = e.target.value;
      updatePreviews();
    });
  });

  // 5. 検索処理の本体
  function performSearch() {
    const keyword = keywordInput.value.trim().toLowerCase();
    const selectedCity = citySelect.value;
    
    // チェックされている学校種を取得
    const checkedTypes = Array.from(typeCheckboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    // フィルタリング
    const filtered = schoolData.filter(school => {
      // キーワードマッチ（学校名、よみがな、住所）
      const matchesKeyword = !keyword || 
        school.name.toLowerCase().includes(keyword) ||
        school.kana.toLowerCase().includes(keyword) ||
        (school.prefecture + school.city + school.address).toLowerCase().includes(keyword);

      // 区市町村マッチ
      const matchesCity = !selectedCity || school.city === selectedCity;

      // 学校種マッチ
      const matchesType = checkedTypes.length === 0 || checkedTypes.includes(school.type);

      return matchesKeyword && matchesCity && matchesType;
    });

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

    results.forEach(school => {
      const card = document.createElement('div');
      card.className = 'school-card';
      
      const copyText = formatAddress(school, selectedHonorific);

      card.innerHTML = `
        <div class="school-info">
          <div class="school-badges">
            <span class="school-badge-type">${school.type}</span>
            <span class="school-badge-city">${school.city}</span>
          </div>
          <h3 class="school-name">${school.name}</h3>
          <div class="school-address-row">
            <span class="zip">〒${school.postcode}</span>
            <span class="addr">${school.prefecture}${school.city}${school.address}</span>
          </div>
          <div class="school-tel-row">TEL: ${school.tel}</div>
        </div>
        <div class="school-actions">
          <button class="btn-copy" data-id="${school.id}" type="button">
            <svg viewBox="0 0 24 24"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
            住所コピー
          </button>
          <div class="copy-preview" id="preview-${school.id}">${copyText}</div>
        </div>
      `;

      // コピーボタンのイベント登録
      const copyBtn = card.querySelector('.btn-copy');
      copyBtn.addEventListener('click', () => {
        const textToCopy = formatAddress(school, selectedHonorific);
        copyToClipboard(textToCopy);
      });

      resultsContainer.appendChild(card);
    });
  }

  // 7. プレビューのリアルタイム更新
  function updatePreviews() {
    resultsContainer.querySelectorAll('.school-card').forEach(card => {
      const copyBtn = card.querySelector('.btn-copy');
      const schoolId = copyBtn.getAttribute('data-id');
      const school = schoolData.find(s => s.id === schoolId);
      
      if (school) {
        const previewDiv = card.querySelector('.copy-preview');
        previewDiv.textContent = formatAddress(school, selectedHonorific);
      }
    });
  }

  // 8. 住所フォーマットユーティリティ
  function formatAddress(school, honorific) {
    // 敬称によって御中か個人名宛てにするか切り替える
    let nameWithHonorific = '';
    if (honorific === '御中') {
      nameWithHonorific = `${school.name} 御中`;
    } else if (honorific === '校長先生') {
      nameWithHonorific = `${school.name}\n校長 殿`;
    } else if (honorific === '副校長先生') {
      nameWithHonorific = `${school.name}\n副校長 殿`;
    } else if (honorific === '事務室御中') {
      nameWithHonorific = `${school.name} 事務室 御中`;
    } else if (honorific === 'ご担当者様') {
      nameWithHonorific = `${school.name}\nご担当者 様`;
    } else {
      nameWithHonorific = `${school.name} ${honorific}`;
    }

    return `〒${school.postcode}\n${school.prefecture}${school.city}${school.address}\n${nameWithHonorific}`;
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
    textArea.style.position = 'fixed'; // 画面外へ
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
});
