"""GA4 計測タグを、生成ページの <head> に必ず入れるためのヘルパー。

テンプレート(templates/*.html)は audit_html_ga4.py の仕様で「GA4対象外」のため、
タグはテンプレートではなく、生成スクリプトが出力直前に挿入する。
(再生成のたびにタグが消える問題の再発防止)
"""

GA4_MARKER = "googletagmanager.com/gtag/js?id=G-KPGJ0R2KXR"

GA4_SNIPPET = '  <!-- Google tag (gtag.js) -->\n  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KPGJ0R2KXR"></script>\n  <script>\n    (function() {\n      try {\n        var url = new URL(window.location.href);\n        var adminParam = url.searchParams.get(\'bantai_admin\');\n        if (adminParam === \'true\') {\n          localStorage.setItem(\'bantai_admin\', \'true\');\n        } else if (adminParam === \'clear\') {\n          localStorage.removeItem(\'bantai_admin\');\n        }\n\n        if (adminParam !== null) {\n          url.searchParams.delete(\'bantai_admin\');\n          var cleanSearch = url.searchParams.toString();\n          var newUrl = url.pathname + (cleanSearch ? \'?\' + cleanSearch : \'\') + url.hash;\n          window.history.replaceState(null, \'\', newUrl);\n        }\n      } catch (e) {}\n\n      var isLocal = window.location.hostname === \'localhost\' ||\n                    window.location.hostname === \'127.0.0.1\' ||\n                    window.location.protocol === \'file:\';\n      var isExcluded = false;\n      try {\n        isExcluded = localStorage.getItem(\'bantai_admin\') === \'true\';\n      } catch (e) {}\n\n      if (isLocal || isExcluded) {\n        window[\'ga-disable-G-KPGJ0R2KXR\'] = true;\n      }\n    })();\n\n    window.dataLayer = window.dataLayer || [];\n    function gtag(){dataLayer.push(arguments);}\n    gtag(\'js\', new Date());\n    gtag(\'config\', \'G-KPGJ0R2KXR\');\n  </script>\n\n'


def inject_ga4(html: str) -> str:
    """GA4タグが無ければ、KARTE タグ(無ければ analytics-events.js)の直前に挿入する。"""
    if GA4_MARKER in html:
        return html
    for anchor in ("  <!-- KARTE Tag -->", '  <script src="/assets/js/analytics-events.js"'):
        if anchor in html:
            return html.replace(anchor, GA4_SNIPPET + anchor, 1)
    raise ValueError("GA4 タグの挿入位置が見つかりません（KARTE / analytics-events.js）")
