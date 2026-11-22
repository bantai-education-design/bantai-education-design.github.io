#!/usr/bin/env python3
"""Enable research-designated school filter and card display UI on a prefecture's HTML and JS.

Idempotent: safe to re-run to update the source note or filter label.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def update_html(slug: str, pref_name: str, filter_label: str, source_note: str, authorities: list[str]) -> bool:
    html_path = ROOT / "tools" / "school-database" / slug / "index.html"
    html = html_path.read_text(encoding="utf-8")
    orig = html

    # 1. Update keyword placeholder if not already mentioning 研究指定
    html = re.sub(
        r'(<input[^>]+id="keyword"[^>]+placeholder=")([^"]+)(")',
        lambda m: m.group(0)
        if "研究指定" in m.group(2)
        else f'{m.group(1)}{m.group(2).rstrip("）)")}・研究指定の教科や事業名）{m.group(3)}',
        html,
        count=1,
    )

    # 2. Insert or update research source note in the yellow coverage box
    note_marker_start = "<!-- research-source-note:start -->"
    note_marker_end = "<!-- research-source-note:end -->"
    note_block = f"{note_marker_start}<br>※{source_note}{note_marker_end}"
    if note_marker_start in html:
        html = re.sub(
            re.escape(note_marker_start) + r".*?" + re.escape(note_marker_end),
            note_block,
            html,
            flags=re.S,
        )
    else:
        # Insert before the closing </p> of the note right after matrix-table:end
        m = re.search(r"matrix-table:end\s*-->.*?(<p[^>]*>)(.*?)(</p>)", html, re.S)
        if m:
            pos = m.start(3)
            html = html[:pos] + note_block + html[pos:]

    # 3. Insert or update research filter group right before </form>
    filter_marker_start = "<!-- research-filter:start -->"
    filter_marker_end = "<!-- research-filter:end -->"
    auth_options = ['                  <option value="">すべての指定主体</option>']
    for auth in authorities:
        label = (
            "文部科学省指定"
            if auth == "文部科学省"
            else f"{auth}教育委員会指定"
        )
        auth_options.append(f'                  <option value="{auth}">{label}</option>')
    auth_options_html = "\n".join(auth_options)

    filter_block = f"""            {filter_marker_start}
            <div class="form-group research-filter-group">
              <label>{filter_label}</label>
              <div class="checkbox-group" style="align-items: center;">
                <label class="filter-chip filter-chip--research">
                  <input type="checkbox" id="research-only" class="research-checkbox" value="1">
                  <span>研究指定校のみ表示</span>
                </label>
                <select id="research-authority" class="form-control" aria-label="指定主体で絞り込み" style="width: auto; min-width: 180px; padding: 8px 12px; font-size: 0.86rem;">
{auth_options_html}
                </select>
              </div>
            </div>
            {filter_marker_end}"""

    if filter_marker_start in html:
        html = re.sub(
            r"\s*" + re.escape(filter_marker_start) + r".*?" + re.escape(filter_marker_end),
            "\n" + filter_block,
            html,
            flags=re.S,
        )
    else:
        html = html.replace("\n          </form>", f"\n\n{filter_block}\n\n          </form>", 1)

    if html != orig:
        html_path.write_text(html, encoding="utf-8")
        return True
    return False


def update_js(slug: str, heading_label: str) -> bool:
    js_path = ROOT / "assets" / "js" / "school-database" / f"search-{slug}.js"
    js = js_path.read_text(encoding="utf-8")
    if "research-only" in js:
        # Update heading label if needed
        updated = re.sub(
            r'<div class="school-research-heading">[^<]+</div>',
            f'<div class="school-research-heading">{heading_label}</div>',
            js,
        )
        if updated != js:
            js_path.write_text(updated, encoding="utf-8")
            return True
        return False

    orig = js

    # 1. DOM refs
    js = js.replace(
        "  const estCheckboxes = document.querySelectorAll('.est-checkbox');\n",
        "  const estCheckboxes = document.querySelectorAll('.est-checkbox');\n"
        "  const researchOnlyCheckbox = document.getElementById('research-only');\n"
        "  const researchAuthoritySelect = document.getElementById('research-authority');\n",
        1,
    )

    # 2. Event listeners after estCheckboxes listener block
    listener_pat = re.compile(
        r"(  estCheckboxes\.forEach\(cb => \{\s*cb\.addEventListener\('change', \(\) => \{.*?\}\);\s*\}\);)",
        re.S,
    )
    listener_add = """
  if (researchOnlyCheckbox) {
    researchOnlyCheckbox.addEventListener('change', () => {
      performSearch();
      trackEvent('school_filter', {
        'filter_type': 'research_only',
        'results_count': currentFilteredResults.length
      });
    });
  }

  if (researchAuthoritySelect) {
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
    js, n = listener_pat.subn(r"\1\n" + listener_add, js, count=1)
    assert n == 1, f"Failed to patch estCheckboxes listener in {js_path}"

    # 3. performSearch() filter logic
    filter_pat = re.compile(
        r"(    const checkedEsts = Array\.from\(estCheckboxes\)\s*\.filter\(cb => cb\.checked\)\s*\.map\(cb => cb\.value\);\s*\n\s*const filtered = schoolData\.filter\(school => \{\s*\n)(\s*const matchesKeyword = !keyword \|\|.*?)(;\s*\n\s*const matchesCity = .*?\n\s*const matchesType = .*?\n\s*const matchesEst = .*?\n\s*return matchesKeyword && matchesCity && matchesType && matchesEst;\s*\n\s*\}\);)",
        re.S,
    )

    def repl_filter(m: re.Match) -> str:
        head = m.group(1).replace(
            "const filtered = schoolData.filter(school => {",
            "const researchOnly = researchOnlyCheckbox ? researchOnlyCheckbox.checked : false;\n"
            "    const selectedAuthority = researchAuthoritySelect ? researchAuthoritySelect.value : '';\n\n"
            "    const filtered = schoolData.filter(school => {\n"
            "      const designations = Array.isArray(school.research_designations) ? school.research_designations : [];\n"
            "      const matchesResearchKeyword = keyword && designations.some(d =>\n"
            "        (d.subject && d.subject.toLowerCase().includes(keyword)) ||\n"
            "        (d.designation && d.designation.toLowerCase().includes(keyword)) ||\n"
            "        (d.year && d.year.toLowerCase().includes(keyword)) ||\n"
            "        (d.authority && d.authority.toLowerCase().includes(keyword))\n"
            "      );\n",
        )
        kw_expr = m.group(2) + " ||\n        matchesResearchKeyword"
        tail = m.group(3).replace(
            "return matchesKeyword && matchesCity && matchesType && matchesEst;",
            "const matchesResearch = (!researchOnly || designations.length > 0) &&\n"
            "        (!selectedAuthority || designations.some(d => d.authority === selectedAuthority));\n\n"
            "      return matchesKeyword && matchesCity && matchesType && matchesEst && matchesResearch;",
        )
        return head + kw_expr + tail

    js, n = filter_pat.subn(repl_filter, js, count=1)
    assert n == 1, f"Failed to patch performSearch in {js_path}"

    # 4. renderResults() badge & research list block
    card_pat = re.compile(
        r"(      card\.innerHTML = `\s*<div class=\"school-info\">\s*<div class=\"school-badges\">.*?)(          </div>\s*<h3 class=\"school-name\">.*?<div class=\"school-tel-row\">.*?</div>\s*)(        </div>)",
        re.S,
    )

    research_prep = f"""      const designations = Array.isArray(school.research_designations) ? school.research_designations : [];
      const researchBadgeHtml = designations.length > 0
        ? '<span class="school-badge-research">研究指定校</span>'
        : '';

      let researchListHtml = '';
      if (designations.length > 0) {{
        const itemsHtml = designations.map(d => {{
          const auth = d.authority || '';
          const authClass = auth === '文部科学省'
            ? 'research-authority-tag--mext'
            : /[都道府県]$/.test(auth)
              ? 'research-authority-tag--pref'
              : 'research-authority-tag--muni';
          const yearLabel = formatResearchYear(d.year);
          const subjectHtml = d.subject
            ? `<span class="research-subject">${{escapeHtml(d.subject)}}</span>`
            : '';
          const desigHtml = d.designation
            ? `<span class="research-designation">${{d.subject ? `（${{escapeHtml(d.designation)}}）` : escapeHtml(d.designation)}}</span>`
            : '';
          const presHtml = d.presentation
            ? `<span class="research-presentation">発表予定: ${{escapeHtml(d.presentation)}}</span>`
            : '';
          return `
            <div class="school-research-item">
              <span class="research-authority-tag ${{authClass}}">${{escapeHtml(auth)}}</span>
              ${{yearLabel ? `<span class="research-year">${{escapeHtml(yearLabel)}}</span>` : ''}}
              ${{subjectHtml}}${{desigHtml}}${{presHtml}}
            </div>
          `;
        }}).join('');
        researchListHtml = `
          <div class="school-research-list">
            <div class="school-research-heading">{heading_label}</div>
            ${{itemsHtml}}
          </div>
        `;
      }}

"""

    def repl_card(m: re.Match) -> str:
        return (
            research_prep
            + m.group(1)
            + "            ${researchBadgeHtml}\n"
            + m.group(2)
            + "          ${researchListHtml}\n"
            + m.group(3)
        )

    js, n = card_pat.subn(repl_card, js, count=1)
    assert n == 1, f"Failed to patch card.innerHTML in {js_path}"

    # 5. Add formatResearchYear helper right before escapeHtml
    helper = """  function formatResearchYear(year) {
    if (!year) return '';
    const trimmed = String(year).trim();
    if (!trimmed) return '';
    if (trimmed.endsWith('年度') || trimmed.endsWith('年') || trimmed.endsWith('〜') || trimmed.endsWith('～')) {
      return trimmed;
    }
    return `${trimmed}年度`;
  }

  function escapeHtml(str) {"""
    js = js.replace("  function escapeHtml(str) {", helper, 1)

    if js != orig:
        js_path.write_text(js, encoding="utf-8")
        return True
    return False


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: enable_research_ui.py <slug> <pref_name> <filter_label> <source_note> [authorities_comma_sep]")
        sys.exit(1)
    slug, pref_name, filter_label, source_note = sys.argv[1:5]
    auths = sys.argv[5].split(",") if len(sys.argv) > 5 else ["文部科学省", pref_name, "市町村"]
    h_changed = update_html(slug, pref_name, filter_label, source_note, auths)
    j_changed = update_js(slug, filter_label)
    print(f"[{slug}] HTML updated={h_changed}, JS updated={j_changed}")
