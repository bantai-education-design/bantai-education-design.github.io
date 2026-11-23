#!/usr/bin/env python3
"""Add direct nationwide awards search links to tools/school-database/index.html
and all 47 prefecture pages (music / sports / culture filter rows).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mext_national_research import PREF_SLUGS


def update_portal() -> bool:
    p = ROOT / "tools" / "school-database" / "index.html"
    html = p.read_text(encoding="utf-8")
    if "/tools/school-database/awards/" in html:
        return False

    banner = """    <!-- national-awards-banner:start -->
    <section style="max-width:1100px;margin:0 auto 20px;padding:0 18px;">
      <div style="background:linear-gradient(135deg,#f0fdf4 0%,#f5f3ff 100%);border:1px solid #cbd5e1;border-radius:16px;padding:18px 22px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px;">
        <div>
          <div style="font-size:0.78rem;font-weight:800;color:#0f766e;letter-spacing:0.08em;">全国47都道府県 横断検索</div>
          <div style="font-size:1.05rem;font-weight:700;color:#0f172a;margin-top:2px;">スポーツ・武道・文化部・漢検・音楽コンクール 全国大会実績校をまとめて探す</div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          <a href="/tools/school-database/awards/?tab=sports" style="padding:8px 14px;border-radius:999px;background:#166534;color:#fff;font-size:0.84rem;font-weight:700;text-decoration:none;">全国スポーツ・武道 →</a>
          <a href="/tools/school-database/awards/?tab=culture" style="padding:8px 14px;border-radius:999px;background:#5b21b6;color:#fff;font-size:0.84rem;font-weight:700;text-decoration:none;">全国文化部・漢検 →</a>
          <a href="/tools/school-database/awards/?tab=music" style="padding:8px 14px;border-radius:999px;background:#0369a1;color:#fff;font-size:0.84rem;font-weight:700;text-decoration:none;">全国音楽コンクール →</a>
        </div>
      </div>
    </section>
    <!-- national-awards-banner:end -->
"""
    if "<main" in html:
        idx = html.find(">", html.find("<main")) + 1
        html = html[:idx] + "\n" + banner + html[idx:]
        p.write_text(html, encoding="utf-8")
        return True
    return False


def update_pref_pages() -> int:
    updated = 0
    for slug in PREF_SLUGS.values():
        p = ROOT / "tools" / "school-database" / slug / "index.html"
        html = p.read_text(encoding="utf-8")
        if "/tools/school-database/awards/" in html:
            continue
        html = html.replace(
            '                </select>\n              </div>\n            </div>\n            <!-- music-filter:end -->',
            '                </select>\n                <a href="/tools/school-database/awards/?tab=music" style="font-size:0.82rem;font-weight:700;color:#0369a1;text-decoration:none;white-space:nowrap;">全国から探す →</a>\n              </div>\n            </div>\n            <!-- music-filter:end -->',
            1,
        )
        html = html.replace(
            '                </select>\n              </div>\n            </div>\n            <!-- sports-filter:end -->',
            '                </select>\n                <a href="/tools/school-database/awards/?tab=sports" style="font-size:0.82rem;font-weight:700;color:#166534;text-decoration:none;white-space:nowrap;">全国から探す →</a>\n              </div>\n            </div>\n            <!-- sports-filter:end -->',
            1,
        )
        html = html.replace(
            '                </select>\n              </div>\n            </div>\n            <!-- culture-filter:end -->',
            '                </select>\n                <a href="/tools/school-database/awards/?tab=culture" style="font-size:0.82rem;font-weight:700;color:#5b21b6;text-decoration:none;white-space:nowrap;">全国から探す →</a>\n              </div>\n            </div>\n            <!-- culture-filter:end -->',
            1,
        )
        p.write_text(html, encoding="utf-8")
        updated += 1
    return updated


def main() -> None:
    portal = update_portal()
    prefs = update_pref_pages()
    print(f"Linked nationwide awards search: portal={portal}, prefs={prefs}/47")


if __name__ == "__main__":
    main()
