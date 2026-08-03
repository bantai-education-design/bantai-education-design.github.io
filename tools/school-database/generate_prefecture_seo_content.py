#!/usr/bin/env python3
"""Insert a per-prefecture "about this database" SEO content section
(intro paragraph, population/education stats, feature list, use-case list,
FAQ) into each of the 47 prefecture pages
(tools/school-database/{slug}/index.html), generated entirely from
prefecture-metadata.json / prefecture-card-metadata.json already in this
repository.

Placement: right before the existing pref-related-links marker (i.e. after
the search section / notice-box, before the related-prefectures links at
the bottom of <main>).

Idempotent: re-running replaces the previously-inserted block (marked by
SEO_CONTENT_START/END comments) rather than appending duplicates.

The FAQ text here must match tools/school-database/prefecture_seo_content.py
exactly, since generate_seo_metadata.py's add_prefecture_json_ld() builds the
matching FAQPage JSON-LD from the same build_faq_items() function — run that
script too (or together via a wrapper) whenever this one is re-run, so the
visible FAQ and the structured data never drift apart."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prefecture_seo_content import build_content

ROOT = Path(__file__).resolve().parents[2]
PREFECTURE_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-metadata.json"
CARD_METADATA_JSON = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"
PAGE_DIR = ROOT / "tools" / "school-database"

SEO_CONTENT_START = "    <!-- pref-seo-content:start -->\n"
SEO_CONTENT_END = "    <!-- pref-seo-content:end -->\n"
RELATED_LINKS_START = "    <!-- pref-related-links:start -->\n"


def _render_html(pref_name: str, content: dict) -> str:
    features_html = "".join(f"          <li>{f}</li>\n" for f in content["features"])
    use_cases_html = "".join(f"          <li>{u}</li>\n" for u in content["use_cases"])
    faq_html = "".join(
        '        <details class="pref-faq-item">\n'
        f'          <summary>{item["question"]}</summary>\n'
        f'          <p>{item["answer"]}</p>\n'
        "        </details>\n"
        for item in content["faq"]
    )

    return (
        f"{SEO_CONTENT_START}"
        '    <section class="pref-seo-content">\n'
        '      <div class="container">\n'
        f'        <h2 class="pref-seo-content-heading">{pref_name}学校データベースについて</h2>\n'
        f'        <p class="pref-seo-content-text">{content["intro"]}</p>\n'
        f'        <p class="pref-seo-content-text">{content["stats"]}</p>\n'
        '        <h3 class="pref-seo-content-subheading">このデータベースでできること</h3>\n'
        '        <ul class="pref-feature-list">\n'
        f"{features_html}"
        "        </ul>\n"
        '        <h3 class="pref-seo-content-subheading">こんな時に便利です</h3>\n'
        '        <ul class="pref-usecase-list">\n'
        f"{use_cases_html}"
        "        </ul>\n"
        '        <h3 class="pref-seo-content-subheading">よくある質問</h3>\n'
        '        <div class="pref-faq">\n'
        f"{faq_html}"
        "        </div>\n"
        "      </div>\n"
        "    </section>\n"
        f"{SEO_CONTENT_END}"
    )


def insert_seo_content(
    prefecture_metadata: list[dict], card_payload: dict, only_slugs: set[str] | None = None
) -> list[str]:
    meta_by_slug = {m["slug"]: m for m in prefecture_metadata}
    card_by_slug = {p["prefecture_code"]: p for p in card_payload["prefectures"]}

    added = []
    for slug, meta in meta_by_slug.items():
        if only_slugs is not None and slug not in only_slugs:
            continue
        card_pref = card_by_slug.get(slug)
        if card_pref is None:
            continue
        page_path = PAGE_DIR / slug / "index.html"
        if not page_path.is_file():
            continue

        pref_name = meta["prefecture"]
        content = build_content(pref_name, meta, card_pref)
        block = _render_html(pref_name, content)

        html = page_path.read_text(encoding="utf-8")
        if SEO_CONTENT_START in html:
            start = html.index(SEO_CONTENT_START)
            end = html.index(SEO_CONTENT_END) + len(SEO_CONTENT_END)
            new_html = html[:start] + block + html[end:]
        else:
            if RELATED_LINKS_START not in html:
                raise ValueError(f"{slug}: pref-related-links marker が見つかりません")
            insert_at = html.index(RELATED_LINKS_START)
            new_html = html[:insert_at] + block + html[insert_at:]

        if new_html != html:
            page_path.write_text(new_html, encoding="utf-8")
            added.append(slug)
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--slugs", help="カンマ区切りのslugリスト（例: hokkaido,tokyo）。省略時は47件すべて。"
    )
    args = parser.parse_args()
    only_slugs = set(args.slugs.split(",")) if args.slugs else None

    prefecture_metadata = json.loads(PREFECTURE_METADATA_JSON.read_text(encoding="utf-8"))
    card_payload = json.loads(CARD_METADATA_JSON.read_text(encoding="utf-8"))
    assert len(prefecture_metadata) == 47, "47都道府県データが揃っていません"

    added = insert_seo_content(prefecture_metadata, card_payload, only_slugs)
    print(f"SEOコンテンツセクションを追加/更新: {len(added)}件")
    for slug in added:
        print(f"  {slug}")


if __name__ == "__main__":
    main()
