#!/usr/bin/env python3
"""Enable compact collapsible culture_awards filter and card display UI across all 47 prefectures."""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mext_national_research import PREF_SLUGS

CULTURE_OPTIONS = [
    "演劇",
    "書道",
    "将棋",
    "囲碁",
    "箏曲・日本音楽",
    "華道",
    "絵画・漫画",
    "ロボット",
]


def update_html(slug: str) -> bool:
    html_path = ROOT / "tools" / "school-database" / slug / "index.html"
    html = html_path.read_text(encoding="utf-8")
    if "culture-filter:start" in html:
        return False

    options_html = "\n".join(
        ['                  <option value="">すべての文化部分野</option>']
        + [f'                  <option value="{c}">{c}</option>' for c in CULTURE_OPTIONS]
    )

    block = f"""            <!-- culture-filter:start -->
            <div class="form-group culture-filter-group">
              <label>文化部全国大会実績（演劇・書道・将棋・囲碁・箏曲・華道・絵画・ロボット）</label>
              <div class="checkbox-group" style="align-items: center;">
                <label class="filter-chip filter-chip--culture">
                  <input type="checkbox" id="culture-only" class="culture-checkbox" value="1">
                  <span>文化部全国実績校のみ表示</span>
                </label>
                <select id="culture-category" class="form-control" aria-label="文化部大会分野で絞り込み" style="width: auto; min-width: 220px; padding: 8px 12px; font-size: 0.86rem;">
{options_html}
                </select>
              </div>
            </div>
            <!-- culture-filter:end -->"""

    anchor = "            <!-- sports-filter:end -->"
    assert anchor in html, f"Could not find sports-filter:end in {html_path}"
    html = html.replace(anchor, f"{anchor}\n\n{block}", 1)
    html_path.write_text(html, encoding="utf-8")
    return True


def update_js(slug: str) -> bool:
    js_path = ROOT / "assets" / "js" / "school-database" / f"search-{slug}.js"
    js = js_path.read_text(encoding="utf-8")
    if "culture-only" in js:
        return False

    # 1. DOM refs
    ref_target = "  const sportsCategorySelect = document.getElementById('sports-category');\n"
    ref_add = (
        ref_target
        + "  const cultureOnlyCheckbox = document.getElementById('culture-only');\n"
        + "  const cultureCategorySelect = document.getElementById('culture-category');\n"
    )
    assert ref_target in js, f"Ref target not found in {js_path}"
    js = js.replace(ref_target, ref_add, 1)

    # 2. Listeners
    listener_target = """  if (sportsCategorySelect) {
    sportsCategorySelect.addEventListener('change', () => {
      if (sportsCategorySelect.value && sportsOnlyCheckbox && !sportsOnlyCheckbox.checked) {
        sportsOnlyCheckbox.checked = true;
      }
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'sports_category',
        'results_count': currentFilteredResults.length
      });
    });
  }"""
    listener_add = """
  if (cultureOnlyCheckbox) {
    cultureOnlyCheckbox.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'culture_only',
        'results_count': currentFilteredResults.length
      });
    });
  }

  if (cultureCategorySelect) {
    cultureCategorySelect.addEventListener('change', () => {
      if (cultureCategorySelect.value && cultureOnlyCheckbox && !cultureOnlyCheckbox.checked) {
        cultureOnlyCheckbox.checked = true;
      }
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'culture_category',
        'results_count': currentFilteredResults.length
      });
    });
  }"""
    assert listener_target in js, f"Listener target not found in {js_path}"
    js = js.replace(listener_target, listener_target + "\n" + listener_add, 1)

    # 3. Filter logic in performSearch()
    f1_target = "    const selectedSport = sportsCategorySelect ? sportsCategorySelect.value : '';"
    f1_add = (
        f1_target
        + "\n    const cultureOnly = cultureOnlyCheckbox ? cultureOnlyCheckbox.checked : false;"
        + "\n    const selectedCulture = cultureCategorySelect ? cultureCategorySelect.value : '';"
    )
    assert f1_target in js, f"Filter target 1 not found in {js_path}"
    js = js.replace(f1_target, f1_add, 1)

    f2_target = "      const sportsAwards = Array.isArray(school.sports_awards) ? school.sports_awards : [];"
    f2_add = (
        f2_target
        + "\n      const cultureAwards = Array.isArray(school.culture_awards) ? school.culture_awards : [];"
        + "\n      const matchesCultureKeyword = keyword && cultureAwards.some(cu =>"
        + "\n        (cu.category && cu.category.toLowerCase().includes(keyword)) ||"
        + "\n        (cu.contest && cu.contest.toLowerCase().includes(keyword)) ||"
        + "\n        (cu.year && cu.year.toLowerCase().includes(keyword)) ||"
        + "\n        (cu.division && cu.division.toLowerCase().includes(keyword)) ||"
        + "\n        (cu.award && cu.award.toLowerCase().includes(keyword))"
        + "\n      );"
    )
    assert f2_target in js, f"Filter target 2 not found in {js_path}"
    js = js.replace(f2_target, f2_add, 1)

    js = js.replace(
        "matchesSportsKeyword;",
        "matchesSportsKeyword ||\n        matchesCultureKeyword;",
        1,
    )

    f3_target = "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch && matchesMusic && matchesSports;"
    f3_add = (
        "      const matchesCulture = (!cultureOnly || cultureAwards.length > 0) &&\n"
        "        (!selectedCulture || cultureAwards.some(cu => cu.category === selectedCulture));\n\n"
        "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch && matchesMusic && matchesSports && matchesCulture;"
    )
    assert f3_target in js, f"Filter target 3 not found in {js_path}"
    js = js.replace(f3_target, f3_add, 1)

    # 4. Compact collapsible card rendering in renderResults()
    c1_target = "      const sportsAwards = Array.isArray(school.sports_awards) ? school.sports_awards : [];\n      const sportsBadgeHtml ="
    culture_card_prep = """      const cultureAwards = Array.isArray(school.culture_awards) ? school.culture_awards : [];
      const cultureBadgeHtml = cultureAwards.length > 0
        ? '<span class="school-badge-culture">文化部全国実績</span>'
        : '';

      let cultureListHtml = '';
      if (cultureAwards.length > 0) {
        const topCu = cultureAwards[0];
        const cuSummaryMeta = [topCu.category, topCu.award, topCu.year].filter(Boolean).join('・');
        const cuItemsHtml = cultureAwards.map(cu => {
          const aw = cu.award || '';
          const awClass = (aw.includes('最優秀') || (aw.includes('優勝') && !aw.includes('準優勝')))
            ? 'culture-award-tag--top'
            : (aw.includes('準優勝') || aw.includes('優秀'))
              ? 'culture-award-tag--second'
              : 'culture-award-tag--other';
          const metaParts = [cu.year, cu.division].filter(Boolean).join(' / ');
          return `
            <div class="school-culture-item">
              <span class="culture-award-tag ${awClass}">${escapeHtml(aw)}</span>
              <span class="culture-contest-name">${escapeHtml(cu.contest || cu.category || '')}</span>
              ${metaParts ? `<span class="culture-meta">${escapeHtml(metaParts)}</span>` : ''}
            </div>
          `;
        }).join('');
        cultureListHtml = `
          <details class="school-culture-details">
            <summary class="school-culture-summary">文化部全国実績（${cultureAwards.length}件） ${escapeHtml(cuSummaryMeta)}</summary>
            <div class="school-culture-list">${cuItemsHtml}</div>
          </details>
        `;
      }

"""
    assert c1_target in js, f"Card target 1 not found in {js_path}"
    js = js.replace(c1_target, culture_card_prep + c1_target, 1)

    js = js.replace(
        "${sportsBadgeHtml}",
        "${sportsBadgeHtml}\n            ${cultureBadgeHtml}",
        1,
    )
    js = js.replace(
        "${sportsListHtml}",
        "${sportsListHtml}\n          ${cultureListHtml}",
        1,
    )

    js_path.write_text(js, encoding="utf-8")
    return True


def update_css() -> bool:
    css_path = ROOT / "assets" / "css" / "school-database.css"
    css = css_path.read_text(encoding="utf-8")
    if ".school-badge-culture" in css:
        return False

    addition = """
/* Cultural club national tournament awards (compact collapsible UI) */
.filter-chip--culture {
  border-color: #7c3aed;
  background: #f5f3ff;
  color: #5b21b6;
}
.school-badge-culture {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  background: #ede9fe;
  color: #5b21b6;
  border: 1px solid #c4b5fd;
  margin-left: 4px;
}
.school-culture-details {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #faf5ff;
  border: 1px solid #ddd6fe;
  font-size: 0.84rem;
}
.school-culture-summary {
  cursor: pointer;
  font-weight: 600;
  color: #4c1d95;
  list-style: none;
}
.school-culture-summary::-webkit-details-marker {
  display: none;
}
.school-culture-summary::before {
  content: "▸ ";
  color: #7c3aed;
}
.school-culture-details[open] .school-culture-summary::before {
  content: "▾ ";
}
.school-culture-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.school-culture-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  line-height: 1.4;
}
.culture-award-tag {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 700;
}
.culture-award-tag--top {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}
.culture-award-tag--second {
  background: #ede9fe;
  color: #5b21b6;
  border: 1px solid #c4b5fd;
}
.culture-award-tag--other {
  background: #e2e8f0;
  color: #334155;
  border: 1px solid #94a3b8;
}
.culture-contest-name {
  color: #1e293b;
  font-weight: 600;
}
.culture-meta {
  color: #64748b;
  font-size: 0.78rem;
}
"""
    css_path.write_text(css + addition, encoding="utf-8")
    return True


def main() -> None:
    h_cnt = 0
    j_cnt = 0
    for slug in PREF_SLUGS.values():
        if update_html(slug):
            h_cnt += 1
        if update_js(slug):
            j_cnt += 1
    css_updated = update_css()
    print(f"Culture UI enabled across 47 prefectures: HTML={h_cnt}, JS={j_cnt}, CSS={css_updated}")


if __name__ == "__main__":
    main()
