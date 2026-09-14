/**
 * Ban.Tai Education Design 公式サイト - KARTEクリックイベント計測用スクリプト
 * 
 * [概要]
 * ページ内の特定の配布リンクやボタンのクリック数を正確に計測し、
 * KARTE (karte.io) にカスタムイベントを送信します。
 * 
 * [送信イベント仕様]
 * - イベント名: click_action
 * - パラメータ: item_name (値: "製品名 - アクション名" の形式)
 */

document.addEventListener('DOMContentLoaded', () => {
  // すべてのリンク(a)とボタン(button)を監視対象にする
  const interactiveElements = document.querySelectorAll('a, button');

  interactiveElements.forEach(element => {
    const href = element.getAttribute('href') || '';
    const text = (element.textContent || element.innerText || '').trim();
    
    let itemName = '';

    // --- 1. ダウンロードリンクの判定 ---
    // ローカルのZIPダウンロード、またはGitHub Releasesからのダウンロード
    if (
      href.endsWith('.zip') || 
      href.endsWith('.exe') || 
      element.hasAttribute('download') || 
      href.includes('/downloads/') || 
      href.includes('/releases/download/')
    ) {
      let appName = getAppNameFromContext(href, text);
      itemName = `${appName} - 無料ダウンロード`;
    }

    // --- 2. BOOTH（販売・配布ページ）への遷移の判定 ---
    else if (href.includes('booth.pm')) {
      let appName = getAppNameFromContext(href, text);
      itemName = `${appName} - BOOTH遷移`;
    }

    // --- 3. Google フォーム（モニター登録やライセンス申請など）への遷移の判定 ---
    else if (href.includes('docs.google.com/forms')) {
      let appName = getAppNameFromContext(href, text);
      let actionType = 'フォーム遷移';
      
      // テキスト内容から詳細なアクションを判定
      if (text.includes('モニター')) {
        actionType = 'モニター登録フォーム遷移';
      } else if (text.includes('ライセンス')) {
        actionType = 'ライセンス申請フォーム遷移';
      }
      
      itemName = `${appName} - ${actionType}`;
    }

    // --- 4. 製品画像から詳細ページへの遷移の判定 ---
    // 専用イベントは増やさず、サイト共通の click_action として計測する。
    else if (
      element.classList.contains('showcase-panel-link') ||
      element.classList.contains('category-card-media-link') ||
      element.classList.contains('feature-image-link') ||
      element.classList.contains('product-card-image-link')
    ) {
      let appName = getAppNameFromContext(href, text);
      itemName = `${appName} - 詳細ページ遷移`;
    }

    // イベントが特定できた場合のみ、クリックリスナーを登録
    if (itemName) {
      element.addEventListener('click', () => {
        if (typeof krt === 'function') {
          krt('send', 'click_action', {
            'item_name': itemName
          });
          // 開発時の動作確認用（管理者除外時やローカル確認用にコンソール出力）
          console.log(`[KARTE Event] click_action | item_name: "${itemName}"`);
        } else {
          console.warn('[KARTE Warning] krt function is not defined.');
        }
      });
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const sendEducationEvent = (eventName, params = {}) => {
    if (typeof krt === 'function') {
      krt('send', eventName, params);
      console.log(`[KARTE Event] ${eventName}`, params);
    }
    if (typeof gtag === 'function') {
      gtag('event', eventName, params);
    }
  };

  const pv = document.querySelector('[data-education-pv]');
  if (pv) {
    let played = false;
    let halfway = false;
    let completed = false;
    let playbackEnded = false;

    const resetPlaybackTracking = () => {
      played = false;
      halfway = false;
      completed = false;
      playbackEnded = false;
    };

    pv.addEventListener('play', () => {
      if (playbackEnded) {
        resetPlaybackTracking();
      }
      if (played) return;
      played = true;
      sendEducationEvent('education_pv_play', {
        item_name: '小学校教育計画作成・運営システム - PV再生開始'
      });
    });

    pv.addEventListener('timeupdate', () => {
      if (halfway || !pv.duration || Number.isNaN(pv.duration)) return;
      if (pv.currentTime / pv.duration >= 0.5) {
        halfway = true;
        sendEducationEvent('education_pv_50', {
          item_name: '小学校教育計画作成・運営システム - PV 50%視聴'
        });
      }
    });

    pv.addEventListener('ended', () => {
      if (completed) return;
      completed = true;
      sendEducationEvent('education_pv_complete', {
        item_name: '小学校教育計画作成・運営システム - PV完了'
      });
      playbackEnded = true;
    });
  }

  document.querySelectorAll('[data-education-event]').forEach(element => {
    // Keep the site-wide click_action and these campaign events as separate measurements.
    element.addEventListener('click', () => {
      sendEducationEvent(element.dataset.educationEvent, {
        item_name: (element.textContent || '').trim()
      });
    });
  });
});

/**
 * リンクのURLやボタンのテキスト、現在のページのタイトルからアプリ名を推測するヘルパー関数
 * @param {string} url - リンク先URL
 * @param {string} text - リンク/ボタンのテキスト
 * @returns {string} 推測されたアプリ名
 */
function getAppNameFromContext(url, text) {
  // URLに含まれるキーワードから判定
  const lowerUrl = url.toLowerCase();
  if (lowerUrl.includes('bannerstudio') || lowerUrl.includes('banner-studio')) {
    return 'Ban.Tai バナースタジオ';
  }
  if (lowerUrl.includes('classrostermaker') || lowerUrl.includes('gakkyu-meibo')) {
    return '学級名簿メーカー';
  }
  if (lowerUrl.includes('kanji-practice') || lowerUrl.includes('8305799')) {
    return '漢字練習帳';
  }
  if (lowerUrl.includes('houganshi') || lowerUrl.includes('8479863')) {
    return '方眼紙メーカー';
  }
  if (lowerUrl.includes('id-photo') || lowerUrl.includes('8467855')) {
    return '証明写真メーカー';
  }
  if (lowerUrl.includes('first-staff-paper')) {
    return 'はじめての五線紙メーカー';
  }
  if (lowerUrl.includes('staff-paper') || lowerUrl.includes('8302315') || lowerUrl.includes('1faipqlsc76qki1tyyd3uke_42lb3rmgpxcwcwkfirz_7szifphq1c_g')) {
    return '五線紙作成メーカー';
  }
  if (lowerUrl.includes('observation-card') || lowerUrl.includes('8579732')) {
    return '観察カード';
  }
  if (lowerUrl.includes('text-overlay') || lowerUrl.includes('image-text')) {
    return '画像文字入れくん';
  }
  if (lowerUrl.includes('resume-generator')) {
    return 'スマート履歴書ジェネレーター';
  }
  if (lowerUrl.includes('education-planning') || lowerUrl.includes('education-hero')) {
    return '小学校教育計画作成・運営システム';
  }

  // 現在のページのタイトルまたはパスから推測
  const title = document.title || '';
  const path = window.location.pathname;

  if (title.includes('Noteバナー') || path.includes('banner-studio')) return 'Ban.Tai バナースタジオ';
  if (title.includes('名簿') || path.includes('gakkyu-meibo')) return '学級名簿メーカー';
  if (title.includes('漢字') || path.includes('kanji-practice')) return '漢字練習帳';
  if (title.includes('方眼紙') || path.includes('houganshi')) return '方眼紙メーカー';
  if (title.includes('証明写真') || path.includes('id-photo')) return '証明写真メーカー';
  if (title.includes('はじめての五線紙') || path.includes('first-staff-paper')) return 'はじめての五線紙メーカー';
  if (title.includes('五線紙') || title.includes('楽譜') || path.includes('staff-paper')) return '五線紙作成メーカー';
  if (title.includes('観察') || path.includes('observation-card')) return '観察カード';
  if (title.includes('文字入れ') || path.includes('text-overlay')) return '画像文字入れくん';
  if (title.includes('履歴書') || path.includes('resume-generator')) return 'スマート履歴書ジェネレーター';
  if (title.includes('教育計画') || path.includes('education-planning')) return '小学校教育計画作成・運営システム';

  // テキスト情報からのフォールバック
  if (text.includes('バナー')) return 'Ban.Tai バナースタジオ';
  if (text.includes('名簿')) return '学級名簿メーカー';
  if (text.includes('漢字')) return '漢字練習帳';
  if (text.includes('方眼紙')) return '方眼紙メーカー';
  if (text.includes('証明写真')) return '証明写真メーカー';
  if (text.includes('はじめての五線紙')) return 'はじめての五線紙メーカー';
  if (text.includes('五線紙') || text.includes('楽譜')) return '五線紙作成メーカー';
  if (text.includes('観察カード')) return '観察カード';
  if (text.includes('文字入れ')) return '画像文字入れくん';
  if (text.includes('履歴書')) return 'スマート履歴書ジェネレーター';
  if (text.includes('教育計画') || text.includes('モニター')) return '小学校教育計画作成・運営システム';

  return 'その他の製品';
}

// School DB analytics only: overlay canonical official statistics before analytics.js consumes the dataset.
(() => {
  if (!window.location.pathname.startsWith('/tools/school-database/analytics')) return;

  const MAIN = '/data/school-database/national-analytics-dataset.json';
  const ABS = '/data/school-database/mext-absenteeism-r6-ground-truth.json';
  const MOV = '/data/school-database/population-movement-2025.json';
  const originalFetch = window.fetch.bind(window);
  const officialNational = {};

  const rank = (data, keys) => {
    keys.forEach((key) => {
      [...data.prefectures]
        .sort((a, b) => (b[key] ?? -Infinity) - (a[key] ?? -Infinity))
        .forEach((pref, index) => {
          pref.ranks = pref.ranks || {};
          pref.ranks[key] = index + 1;
        });
    });
  };

  const mergeAbsenteeism = (data, official) => {
    const byCode = new Map(official.prefectures.map((p) => [p.prefecture_code, p]));
    if (byCode.size !== 47) throw new Error(`MEXT absenteeism prefecture count mismatch: ${byCode.size}`);
    const keys = [
      'absenteeism_combined_rate', 'absenteeism_combined_count',
      'elem_absenteeism_rate', 'elem_absenteeism_count',
      'jhs_absenteeism_rate', 'jhs_absenteeism_count'
    ];
    data.national_summary = data.national_summary || {};
    Object.assign(data.national_summary, official.national);
    Object.assign(officialNational, official.national);
    data.prefectures.forEach((pref) => {
      const source = byCode.get(pref.code);
      if (!source) throw new Error(`MEXT absenteeism missing prefecture: ${pref.code}`);
      keys.forEach((key) => { pref[key] = source[key]; });
    });
    data.indicators_definition = data.indicators_definition || {};
    const source = '文部科学省「令和6年度 児童生徒の問題行動・不登校等生徒指導上の諸課題に関する調査」表4-15（都道府県別・国公私立）';
    const base = '2024年度（令和6年度）実績';
    Object.assign(data.indicators_definition, {
      absenteeism_combined_rate: {label:'小中学校 1,000人当たり不登校児童生徒数',unit:'人/1,000人',description:'小学校・中学校の在籍児童生徒1,000人当たり不登校児童生徒数。都道府県別（国公私立）の公式公表値。',source,base_date:base},
      absenteeism_combined_count: {label:'小中学校 不登校児童生徒数',unit:'人',description:'小学校・中学校の不登校児童生徒数の合計。都道府県別（国公私立）の公式公表値。',source,base_date:base},
      elem_absenteeism_rate: {label:'小学校 1,000人当たり不登校児童数',unit:'人/1,000人',description:'小学校の在籍児童1,000人当たり不登校児童数。',source,base_date:base},
      elem_absenteeism_count: {label:'小学校 不登校児童数',unit:'人',description:'小学校の不登校児童数。',source,base_date:base},
      jhs_absenteeism_rate: {label:'中学校 1,000人当たり不登校生徒数',unit:'人/1,000人',description:'中学校の在籍生徒1,000人当たり不登校生徒数。',source,base_date:base},
      jhs_absenteeism_count: {label:'中学校 不登校生徒数',unit:'人',description:'中学校の不登校生徒数。',source,base_date:base}
    });
    rank(data, keys);
  };

  const mergeMovement = (data, official) => {
    const byCode = new Map(official.prefectures.map((p) => [p.prefecture_code, p]));
    if (byCode.size !== 47) throw new Error(`Population movement prefecture count mismatch: ${byCode.size}`);
    const allKeys = ['interpref_in_migrants','interpref_out_migrants','net_migration_2025','net_migration_rate_2025'];
    data.national_summary = data.national_summary || {};
    Object.assign(data.national_summary, official.national);
    Object.assign(officialNational, official.national);
    data.prefectures.forEach((pref) => {
      const source = byCode.get(pref.code);
      if (!source) throw new Error(`Population movement missing prefecture: ${pref.code}`);
      allKeys.forEach((key) => { pref[key] = source[key]; });
    });
    data.indicators_definition = data.indicators_definition || {};
    const source = '総務省統計局「住民基本台帳人口移動報告 2025年（令和7年）結果」表7・表27';
    Object.assign(data.indicators_definition, {
      net_migration_2025: {label:'2025年 転入超過数（－は転出超過）',unit:'人',description:'他都道府県からの転入者数から他都道府県への転出者数を差し引いた人数。プラスは転入超過、マイナスは転出超過を示します。',source,base_date:'2025年年間'},
      net_migration_rate_2025: {label:'2025年 転入超過率（住民基本台帳人口比）',unit:'%',description:'2025年の転入超過数を2025年1月1日現在の住民基本台帳人口で除した比率。プラスは転入超過、マイナスは転出超過を示します。',source,base_date:'2025年／人口は2025年1月1日現在'}
    });
    rank(data, ['net_migration_2025','net_migration_rate_2025']);
  };

  window.fetch = async (input, init) => {
    const url = typeof input === 'string' ? new URL(input, window.location.href) : new URL(input.url, window.location.href);
    if (url.pathname !== MAIN) return originalFetch(input, init);

    const [mainRes, absRes, movRes] = await Promise.all([
      originalFetch(input, init), originalFetch(ABS), originalFetch(MOV)
    ]);
    if (!mainRes.ok) return mainRes;
    const data = await mainRes.clone().json();
    if (!absRes.ok) throw new Error(`Official absenteeism data load failed: HTTP ${absRes.status}`);
    if (!movRes.ok) throw new Error(`Population movement data load failed: HTTP ${movRes.status}`);
    mergeAbsenteeism(data, await absRes.json());
    mergeMovement(data, await movRes.json());
    return new Response(JSON.stringify(data), {
      status: mainRes.status,
      statusText: mainRes.statusText,
      headers: {'Content-Type':'application/json; charset=utf-8'}
    });
  };

  const select = document.getElementById('metric-select');
  if (select) {
    const add = (group, value, label) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      group.appendChild(option);
    };
    const absence = document.createElement('optgroup');
    absence.label = '🚸 不登校（文部科学省 2024年度公式値）';
    add(absence,'absenteeism_combined_rate','🚸 小中学校 1,000人当たり不登校児童生徒数');
    add(absence,'elem_absenteeism_rate','🎒 小学校 1,000人当たり不登校児童数');
    add(absence,'jhs_absenteeism_rate','🏫 中学校 1,000人当たり不登校生徒数');
    add(absence,'absenteeism_combined_count','🚸 小中学校 不登校児童生徒数（人）');
    select.appendChild(absence);

    const movement = document.createElement('optgroup');
    movement.label = '🚚 人口移動（総務省 2025年）';
    add(movement,'net_migration_2025','🚚 転入超過数（－は転出超過）');
    add(movement,'net_migration_rate_2025','📈 転入超過率（住民基本台帳人口比 %）');
    select.appendChild(movement);

    const patchPresentation = () => {
      const key = select.value;
      if (key === 'net_migration_rate_2025' || key.endsWith('absenteeism_rate')) {
        const label = document.getElementById('metric-national-avg-label');
        const value = document.getElementById('metric-national-avg');
        if (label) label.textContent = key === 'net_migration_rate_2025' ? '全国転入超過率' : '全国値（1,000人当たり）';
        if (value && officialNational[key] !== undefined) {
          const digits = key === 'net_migration_rate_2025' ? 2 : 1;
          const unit = key === 'net_migration_rate_2025' ? '%' : '人/1,000人';
          value.innerHTML = `${Number(officialNational[key]).toFixed(digits)} <span style="font-size:0.85rem; font-weight:600;">${unit}</span>`;
        }
      }
      if (key === 'net_migration_2025' || key === 'net_migration_rate_2025') {
        const rows = [...document.querySelectorAll('#bar-chart-container .bar-row')];
        const parsed = rows.map((row) => {
          const text = row.querySelector('.bar-value')?.textContent || '';
          const match = text.replace(/,/g,'').match(/-?\d+(?:\.\d+)?/);
          return match ? Number(match[0]) : 0;
        });
        const maxAbs = Math.max(...parsed.map(Math.abs), 1);
        rows.forEach((row, i) => {
          const fill = row.querySelector('.bar-fill');
          if (fill) fill.style.width = `${Math.max(4, Math.abs(parsed[i]) / maxAbs * 100)}%`;
        });
      }
    };
    select.addEventListener('change', () => setTimeout(patchPresentation, 0));
  }
})();
