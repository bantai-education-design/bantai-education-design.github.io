/*
 * トップページのお問い合わせフォーム
 * 静的サイトのため、サーバーへは送信しない。入力内容を宛先・件名・本文に入れた状態で
 * メールソフトを開き、開けない場合に備えてアドレスと本文をコピーできる案内を表示する。
 * 入力内容は計測（GA4など）へ送らない。
 */
(function () {
  'use strict';

  var TO = 'ban.tai3educationdesign@gmail.com';
  // メールソフトによっては長いURLを開けないため、超えたらコピーでの送信を案内する
  var MAILTO_LIMIT = 1800;

  var form = document.getElementById('contact-form');
  if (!form) return;

  var panel = document.getElementById('contact-result');
  var bodyBox = document.getElementById('contact-result-body');
  var openLink = document.getElementById('contact-open-mail');
  var longNote = document.getElementById('contact-long-note');

  function value(id) {
    var el = document.getElementById(id);
    return el ? el.value.trim() : '';
  }

  function categoryLabel() {
    var sel = document.getElementById('contact-category');
    if (!sel || !sel.value) return '';
    return sel.options[sel.selectedIndex].text;
  }

  function buildMail() {
    var name = value('contact-name');
    var email = value('contact-email');
    var category = categoryLabel();
    var message = value('contact-message');
    var subject = '【Ban.Tai お問い合わせ】' + category;
    var body = [
      'お名前 / 学校名：' + (name || '（未記入）'),
      '返信先メールアドレス：' + email,
      'お問い合わせ種別：' + category,
      '',
      message,
      '',
      '（Ban.Tai Education Design 公式サイトのフォームから作成）'
    ].join('\n');
    return { subject: subject, body: body };
  }

  function copyText(text, button) {
    var done = function () {
      var original = button.textContent;
      button.textContent = 'コピーしました';
      setTimeout(function () { button.textContent = original; }, 2000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
    } else {
      fallbackCopy(text);
      done();
    }
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) { /* 手動でコピーしてもらう */ }
    document.body.removeChild(ta);
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;

    var mail = buildMail();
    var href = 'mailto:' + TO + '?subject=' + encodeURIComponent(mail.subject) + '&body=' + encodeURIComponent(mail.body);
    var tooLong = href.length > MAILTO_LIMIT;

    bodyBox.value = mail.subject + '\n\n' + mail.body;
    openLink.href = tooLong ? 'mailto:' + TO + '?subject=' + encodeURIComponent(mail.subject) : href;
    longNote.hidden = !tooLong;
    panel.hidden = false;
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // 種別だけを計測する（入力内容やアドレスは送らない）
    if (typeof window.gtag === 'function') {
      var sel = document.getElementById('contact-category');
      window.gtag('event', 'contact_form_compose', { contact_category: sel ? sel.value : '' });
    }

    if (!tooLong) window.location.href = href;
  });

  document.getElementById('contact-copy-address').addEventListener('click', function () {
    copyText(TO, this);
  });
  document.getElementById('contact-copy-body').addEventListener('click', function () {
    copyText(bodyBox.value, this);
  });
})();
