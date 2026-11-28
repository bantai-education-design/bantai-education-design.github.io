#!/usr/bin/env python3
"""Enable music contest awards filter and card display UI across all 47 prefectures."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mext_national_research import PREF_SLUGS

CONTEST_OPTIONS = [
    "NHK全国学校音楽コンクール（Nコン）",
    "全日本合唱コンクール",
    "全日本吹奏楽コンクール",
    "全日本マーチングコンテスト",
    "こども音楽コンクール",
    "日本学校合奏コンクール（全国学校合奏コンクール）",
    "全国高等学校軽音楽コンテスト",
]


def update_html(slug: str) -> bool:
    html_path = ROOT / "tools" / "school-database" / slug / "index.html"
    html = html_path.read_text(encoding="utf-8")
    if "music-filter:start" in html:
        return False

    options_html = "\n".join(
        ['                  <option value="">すべての音楽コンクール</option>']
        + [f'                  <option value="{c}">{c}</option>' for c in CONTEST_OPTIONS]
    )

    block = f"""            <!-- music-filter:start -->
            <div class="form-group music-filter-group">
              <label>音楽コンクール全国大会実績（金・銀・銅・出場校）</label>
              <div class="checkbox-group" style="align-items: center;">
                <label class="filter-chip filter-chip--music">
                  <input type="checkbox" id="music-only" class="music-checkbox" value="1">
                  <span>音楽コンクール実績校のみ表示</span>
                </label>
                <select id="music-contest" class="form-control" aria-label="音楽コンクールで絞り込み" style="width: auto; min-width: 220px; padding: 8px 12px; font-size: 0.86rem;">
{options_html}
                </select>
              </div>
            </div>
            <!-- music-filter:end -->"""

    if "\n          </form>" not in html:
        raise RuntimeError(f"Could not find </form> in {html_path}")
    html = html.replace("\n          </form>", f"\n\n{block}\n\n          </form>", 1)
    html_path.write_text(html, encoding="utf-8")
    return True


def update_js(slug: str) -> bool:
    js_path = ROOT / "assets" / "js" / "school-database" / f"search-{slug}.js"
    js = js_path.read_text(encoding="utf-8")
    if "music-only" in js:
        return False

    # 1. DOM refs
    js = js.replace(
        "  const researchAuthoritySelect = document.getElementById('research-authority');\n",
        "  const researchAuthoritySelect = document.getElementById('research-authority');\n"
        "  const musicOnlyCheckbox = document.getElementById('music-only');\n"
        "  const musicContestSelect = document.getElementById('music-contest');\n",
        1,
    )

    # 2. Event listeners right after researchAuthoritySelect listener
    listener_target = """  if (researchAuthoritySelect) {
    researchAuthoritySelect.addEventListener('change', () => {
      if (researchAuthoritySelect.value && researchOnlyCheckbox && !researchOnlyCheckbox.checked) {
        researchOnlyCheckbox.checked = true;
      }
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'research_authority',
        'results_count': currentFilteredResults.length
      });
    });
  }"""
    listener_add = """
  if (musicOnlyCheckbox) {
    musicOnlyCheckbox.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'music_only',
        'results_count': currentFilteredResults.length
      });
    });
  }

  if (musicContestSelect) {
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
    assert listener_target in js, f"Listener target not found in {js_path}"
    js = js.replace(listener_target, listener_target + "\n" + listener_add, 1)

    # 3. performSearch() filter logic
    target_f1 = "    const selectedAuthority = researchAuthoritySelect ? researchAuthoritySelect.value : '';"
    repl_f1 = (
        target_f1
        + "\n    const musicOnly = musicOnlyCheckbox ? musicOnlyCheckbox.checked : false;"
        + "\n    const selectedContest = musicContestSelect ? musicContestSelect.value : '';"
    )
    assert target_f1 in js, f"Filter target 1 not found in {js_path}"
    js = js.replace(target_f1, repl_f1, 1)

    target_f2 = "      const designations = Array.isArray(school.research_designations) ? school.research_designations : [];"
    repl_f2 = (
        target_f2
        + "\n      const musicAwards = Array.isArray(school.music_awards) ? school.music_awards : [];"
        + "\n      const matchesMusicKeyword = keyword && musicAwards.some(m =>"
        + "\n        (m.contest && m.contest.toLowerCase().includes(keyword)) ||"
        + "\n        (m.year && m.year.toLowerCase().includes(keyword)) ||"
        + "\n        (m.division && m.division.toLowerCase().includes(keyword)) ||"
        + "\n        (m.award && m.award.toLowerCase().includes(keyword)) ||"
        + "\n        (m.detail && m.detail.toLowerCase().includes(keyword))"
        + "\n      );"
    )
    assert target_f2 in js, f"Filter target 2 not found in {js_path}"
    js = js.replace(target_f2, repl_f2, 1)

    js = js.replace(
        "matchesResearchKeyword;",
        "matchesResearchKeyword ||\n        matchesMusicKeyword;",
        1,
    )

    target_f3 = "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch;"
    repl_f3 = (
        "      const matchesMusic = (!musicOnly || musicAwards.length > 0) &&\n"
        "        (!selectedContest || musicAwards.some(m => m.contest === selectedContest));\n\n"
        "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch && matchesMusic;"
    )
    assert target_f3 in js, f"Filter target 3 not found in {js_path}"
    js = js.replace(target_f3, repl_f3, 1)

    # 4. Card rendering (target specifically the one in renderResults followed by researchBadgeHtml)
    target_c1 = "      const designations = Array.isArray(school.research_designations) ? school.research_designations : [];\n      const researchBadgeHtml ="
    music_card_prep = """      const musicAwards = Array.isArray(school.music_awards) ? school.music_awards : [];
      const musicBadgeHtml = musicAwards.length > 0
        ? '<span class="school-badge-music">音楽コンクール</span>'
        : '';

      let musicListHtml = '';
      if (musicAwards.length > 0) {
        const mItemsHtml = musicAwards.map(m => {
          const aw = m.award || '';
          const awClass = (aw.includes('金賞') || aw.includes('文部科学大臣賞') || aw.includes('グランプリ') || aw.includes('最優秀'))
            ? 'music-award-tag--gold'
            : (aw.includes('銀賞') || aw.includes('準グランプリ') || aw.includes('優秀'))
              ? 'music-award-tag--silver'
              : (aw.includes('銅賞') || aw.includes('奨励賞'))
                ? 'music-award-tag--bronze'
                : 'music-award-tag--other';
          const metaParts = [m.year, m.division, m.detail].filter(Boolean).join(' / ');
          return `
            <div class="school-music-item">
              <span class="music-award-tag ${awClass}">${escapeHtml(aw)}</span>
              <span class="music-contest-name">${escapeHtml(m.contest || '')}</span>
              ${metaParts ? `<span class="music-meta">${escapeHtml(metaParts)}</span>` : ''}
            </div>
          `;
        }).join('');
        musicListHtml = `
          <div class="school-music-list">
            <div class="school-music-heading">音楽コンクール全国大会実績</div>
            ${mItemsHtml}
          </div>
        `;
      }

"""
    assert target_c1 in js, f"Card target 1 not found in {js_path}"
    js = js.replace(target_c1, music_card_prep + target_c1, 1)

    js = js.replace(
        "${researchBadgeHtml}",
        "${researchBadgeHtml}\n            ${musicBadgeHtml}",
        1,
    )
    js = js.replace(
        "${researchListHtml}",
        "${researchListHtml}\n          ${musicListHtml}",
        1,
    )

    js_path.write_text(js, encoding="utf-8")
    return True


def main():
    h_cnt = 0
    j_cnt = 0
    for slug in PREF_SLUGS.values():
        if update_html(slug):
            h_cnt += 1
        if update_js(slug):
            j_cnt += 1
    print(f"Music UI enabled across 47 prefectures: HTML={h_cnt}, JS={j_cnt}")


if __name__ == "__main__":
    main()
