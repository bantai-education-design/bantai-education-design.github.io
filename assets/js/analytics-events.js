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
