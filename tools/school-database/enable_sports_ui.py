#!/usr/bin/env python3
"""Enable compact collapsible sports_awards filter and card display UI across all 47 prefectures."""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mext_national_research import PREF_SLUGS

SPORT_OPTIONS = [
    "野球（甲子園）",
    "サッカー",
    "駅伝（都大路）",
    "バレーボール（春高）",
    "バスケットボール（ウインターカップ）",
    "ラグビー（花園）",
]


def update_html(slug: str) -> bool:
    html_path = ROOT / "tools" / "school-database" / slug / "index.html"
    html = html_path.read_text(encoding="utf-8")
    if "sports-filter:start" in html:
        return False

    options_html = "\n".join(
        ['                  <option value="">すべての競技（高校主要6大会）</option>']
        + [f'                  <option value="{s}">{s}</option>' for s in SPORT_OPTIONS]
    )

    block = f"""            <!-- sports-filter:start -->
            <div class="form-group sports-filter-group">
              <label>スポーツ全国大会実績（高校主要6大会・上位校）</label>
              <div class="checkbox-group" style="align-items: center;">
                <label class="filter-chip filter-chip--sports">
                  <input type="checkbox" id="sports-only" class="sports-checkbox" value="1">
                  <span>スポーツ全国実績校のみ表示</span>
                </label>
                <select id="sports-category" class="form-control" aria-label="スポーツ競技で絞り込み" style="width: auto; min-width: 220px; padding: 8px 12px; font-size: 0.86rem;">
{options_html}
                </select>
              </div>
            </div>
            <!-- sports-filter:end -->"""

    anchor = "            <!-- music-filter:end -->"
    assert anchor in html, f"Could not find music-filter:end in {html_path}"
    html = html.replace(anchor, f"{anchor}\n\n{block}", 1)
    html_path.write_text(html, encoding="utf-8")
    return True


def update_js(slug: str) -> bool:
    js_path = ROOT / "assets" / "js" / "school-database" / f"search-{slug}.js"
    js = js_path.read_text(encoding="utf-8")
    if "sports-only" in js:
        return False

    # 1. DOM refs
    ref_target = "  const musicContestSelect = document.getElementById('music-contest');\n"
    ref_add = (
        ref_target
        + "  const sportsOnlyCheckbox = document.getElementById('sports-only');\n"
        + "  const sportsCategorySelect = document.getElementById('sports-category');\n"
    )
    assert ref_target in js, f"Ref target not found in {js_path}"
    js = js.replace(ref_target, ref_add, 1)

    # 2. Listeners
    listener_target = """  if (musicContestSelect) {
    musicContestSelect.addEventListener('change', () => {
      if (musicContestSelect.value && musicOnlyCheckbox && !musicOnlyCheckbox.checked) {
        musicOnlyCheckbox.checked = true;
      }
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'music_contest',
        'results_count': currentFilteredResults.length
      });
    });
  }"""
    listener_add = """
  if (sportsOnlyCheckbox) {
    sportsOnlyCheckbox.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'sports_only',
        'results_count': currentFilteredResults.length
      });
    });
  }

  if (sportsCategorySelect) {
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
    assert listener_target in js, f"Listener target not found in {js_path}"
    js = js.replace(listener_target, listener_target + "\n" + listener_add, 1)

    # 3. Filter logic in performSearch()
    f1_target = "    const selectedContest = musicContestSelect ? musicContestSelect.value : '';"
    f1_add = (
        f1_target
        + "\n    const sportsOnly = sportsOnlyCheckbox ? sportsOnlyCheckbox.checked : false;"
        + "\n    const selectedSport = sportsCategorySelect ? sportsCategorySelect.value : '';"
    )
    assert f1_target in js, f"Filter target 1 not found in {js_path}"
    js = js.replace(f1_target, f1_add, 1)

    f2_target = "      const musicAwards = Array.isArray(school.music_awards) ? school.music_awards : [];"
    f2_add = (
        f2_target
        + "\n      const sportsAwards = Array.isArray(school.sports_awards) ? school.sports_awards : [];"
        + "\n      const matchesSportsKeyword = keyword && sportsAwards.some(sp =>"
        + "\n        (sp.sport && sp.sport.toLowerCase().includes(keyword)) ||"
        + "\n        (sp.contest && sp.contest.toLowerCase().includes(keyword)) ||"
        + "\n        (sp.year && sp.year.toLowerCase().includes(keyword)) ||"
        + "\n        (sp.division && sp.division.toLowerCase().includes(keyword)) ||"
        + "\n        (sp.award && sp.award.toLowerCase().includes(keyword))"
        + "\n      );"
    )
    assert f2_target in js, f"Filter target 2 not found in {js_path}"
    js = js.replace(f2_target, f2_add, 1)

    js = js.replace(
        "matchesMusicKeyword;",
        "matchesMusicKeyword ||\n        matchesSportsKeyword;",
        1,
    )

    f3_target = "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch && matchesMusic;"
    f3_add = (
        "      const matchesSports = (!sportsOnly || sportsAwards.length > 0) &&\n"
        "        (!selectedSport || sportsAwards.some(sp => sp.sport === selectedSport));\n\n"
        "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch && matchesMusic && matchesSports;"
    )
    assert f3_target in js, f"Filter target 3 not found in {js_path}"
    js = js.replace(f3_target, f3_add, 1)

    # 4. Compact collapsible card rendering in renderResults()
    c1_target = "      const musicAwards = Array.isArray(school.music_awards) ? school.music_awards : [];\n      const musicBadgeHtml ="
    sports_card_prep = """      const sportsAwards = Array.isArray(school.sports_awards) ? school.sports_awards : [];
      const sportsBadgeHtml = sportsAwards.length > 0
        ? '<span class="school-badge-sports">スポーツ全国実績</span>'
        : '';

      let sportsListHtml = '';
      if (sportsAwards.length > 0) {
        const topSp = sportsAwards[0];
        const summaryMeta = [topSp.sport, topSp.award, topSp.year].filter(Boolean).join('・');
        const spItemsHtml = sportsAwards.map(sp => {
          const aw = sp.award || '';
          const awClass = aw.includes('優勝') && !aw.includes('準優勝')
            ? 'sports-award-tag--champ'
            : aw.includes('準優勝')
              ? 'sports-award-tag--runnerup'
              : 'sports-award-tag--semi';
          const metaParts = [sp.year, sp.division].filter(Boolean).join(' / ');
          return `
            <div class="school-sports-item">
              <span class="sports-award-tag ${awClass}">${escapeHtml(aw)}</span>
              <span class="sports-contest-name">${escapeHtml(sp.contest || sp.sport || '')}</span>
              ${metaParts ? `<span class="sports-meta">${escapeHtml(metaParts)}</span>` : ''}
            </div>
          `;
        }).join('');
        sportsListHtml = `
          <details class="school-sports-details">
            <summary class="school-sports-summary">スポーツ全国実績（${sportsAwards.length}件） ${escapeHtml(summaryMeta)}</summary>
            <div class="school-sports-list">${spItemsHtml}</div>
          </details>
        `;
      }

"""
    assert c1_target in js, f"Card target 1 not found in {js_path}"
    js = js.replace(c1_target, sports_card_prep + c1_target, 1)

    js = js.replace(
        "${musicBadgeHtml}",
        "${musicBadgeHtml}\n            ${sportsBadgeHtml}",
        1,
    )
    js = js.replace(
        "${musicListHtml}",
        "${musicListHtml}\n          ${sportsListHtml}",
        1,
    )

    js_path.write_text(js, encoding="utf-8")
    return True


def update_css() -> bool:
    css_path = ROOT / "assets" / "css" / "school-database.css"
    css = css_path.read_text(encoding="utf-8")
    if ".school-badge-sports" in css:
        return False

    addition = """
/* Sports national tournament awards (compact collapsible UI) */
.filter-chip--sports {
  border-color: #16a34a;
  background: #f0fdf4;
  color: #166534;
}
.school-badge-sports {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
  margin-left: 4px;
}
.school-sports-details {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  font-size: 0.84rem;
}
.school-sports-summary {
  cursor: pointer;
  font-weight: 600;
  color: #14532d;
  list-style: none;
}
.school-sports-summary::-webkit-details-marker {
  display: none;
}
.school-sports-summary::before {
  content: "▸ ";
  color: #16a34a;
}
.school-sports-details[open] .school-sports-summary::before {
  content: "▾ ";
}
.school-sports-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.school-sports-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  line-height: 1.4;
}
.sports-award-tag {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 4px;
  font-size: 0.74rem;
  font-weight: 700;
}
.sports-award-tag--champ {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}
.sports-award-tag--runnerup {
  background: #e2e8f0;
  color: #334155;
  border: 1px solid #94a3b8;
}
.sports-award-tag--semi {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}
.sports-contest-name {
  color: #1e293b;
  font-weight: 600;
}
.sports-meta {
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
    print(f"Sports UI enabled across 47 prefectures: HTML={h_cnt}, JS={j_cnt}, CSS={css_updated}")


if __name__ == "__main__":
    main()
