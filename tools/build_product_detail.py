from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from string import Template
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "product-details"
TEMPLATE_PATH = ROOT / "templates" / "product-detail.html"


def html_text(value: object) -> str:
    return escape(str(value), quote=False)


def html_attr(value: object) -> str:
    return escape(str(value), quote=True)


def indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def render_spans(values: list[str], spaces: int = 12) -> str:
    return indent_block("\n".join(f"<span>{html_text(value)}</span>" for value in values), spaces)


def render_inline_spans(values: list[str]) -> str:
    return "".join(f"<span>{html_text(value)}</span>" for value in values)


def render_heading_lines(lines: list[str]) -> str:
    return "<br>".join(html_text(line) for line in lines)


def render_lines_with_breaks(values: list[str], spaces: int = 12) -> str:
    lines = []
    for index, value in enumerate(values):
        suffix = "<br>" if index < len(values) - 1 else ""
        lines.append(f"{html_text(value)}{suffix}")
    return indent_block("\n".join(lines), spaces)


def render_paragraphs(values: list[str], spaces: int = 12) -> str:
    return indent_block("\n".join(f"<p>{html_text(value)}</p>" for value in values), spaces)


def render_attrs(attrs: dict[str, str] | None) -> str:
    if not attrs:
        return ""
    return "".join(f' {key}="{html_attr(value)}"' for key, value in attrs.items())


def render_action(action: dict[str, Any]) -> str:
    attrs = {
        "class": action.get("class", "btn btn-primary"),
        "href": action["href"],
    }
    attrs.update(action.get("attrs", {}))
    return f'<a{render_attrs(attrs)}>{html_text(action["label"])}</a>'


def render_actions(actions: list[dict[str, Any]], spaces: int = 12, style: str | None = None) -> str:
    style_attr = f' style="{html_attr(style)}"' if style else ""
    links = "\n".join(indent_block(render_action(action), spaces + 2) for action in actions)
    return f'{" " * spaces}<div class="actions"{style_attr}>\n{links}\n{" " * spaces}</div>'


def stylesheet_href(data: dict[str, Any]) -> str:
    if data.get("styleHref"):
        return str(data["styleHref"])
    return f'/assets/style.css?v={data["styleVersion"]}'


def render_font_links(data: dict[str, Any]) -> str:
    if data.get("includeFonts", True) is False:
        return ""
    return "\n".join(
        [
            '  <link rel="preconnect" href="https://fonts.googleapis.com">',
            '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            '  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;600;700&family=Noto+Serif+JP:wght@400;700&display=swap" rel="stylesheet">',
        ]
    )


def render_home_floating(data: dict[str, Any]) -> str:
    if data.get("homeFloating", True) is False:
        return ""
    return '  <a class="home-floating" href="/">ホームへ</a>'


def render_paper_placeholder(spaces: int = 10) -> str:
    html = "\n".join(
        [
            '<div style="background:#fff; padding:22px;">',
            '  <div style="border:1px solid rgba(7,27,54,.12); border-radius:18px; background:#fff; padding:18px; box-shadow:0 10px 26px rgba(7,27,54,.08);">',
            '    <div style="height:132px; border:3px double rgba(7,27,54,.28); border-radius:8px; margin-bottom:14px; background:#fcfcfc;"></div>',
            '    <div style="height:176px; border:1px solid rgba(7,27,54,.22); background-image:linear-gradient(rgba(7,27,54,.18) 1px,transparent 1px),linear-gradient(90deg,rgba(7,27,54,.18) 1px,transparent 1px); background-size:22px 22px;"></div>',
            "  </div>",
            "</div>",
        ]
    )
    return indent_block(html, spaces)


def render_visual(section: dict[str, Any], spaces: int = 8) -> str:
    if section.get("placeholderVisual") == "paper":
        return "\n".join(
            [
                f'{" " * spaces}<div class="{html_attr(section.get("imageContainerClass", "hero-image-container"))}">',
                render_paper_placeholder(spaces + 2),
                f'{" " * spaces}</div>',
            ]
        )
    return "\n".join(
        [
            f'{" " * spaces}<div class="{html_attr(section["imageContainerClass"])}">',
            f'{" " * (spaces + 2)}<img src="{html_attr(section["image"]["src"])}" alt="{html_attr(section["image"]["alt"])}">',
            f'{" " * spaces}</div>',
        ]
    )


def render_nav_links(data: dict[str, Any]) -> str:
    lines = []
    for item in data["navLinks"]:
        attrs = {"href": item["href"]}
        if item.get("class"):
            attrs["class"] = item["class"]
        lines.append(f'<a{render_attrs(attrs)}>{html_text(item["label"])}</a>')
    return indent_block("\n".join(lines), 8)


def render_menu_toggle(data: dict[str, Any]) -> str:
    if not data.get("menuToggle"):
        return ""
    return (
        '      <button class="menu-toggle" type="button" aria-label="メニューを開く" '
        'aria-expanded="false" aria-controls="global-menu"><span></span><span></span><span></span></button>'
    )


def render_nav_attrs(data: dict[str, Any]) -> str:
    attrs = {"class": "menu"}
    if data.get("menuToggle"):
        attrs["id"] = "global-menu"
        attrs["aria-label"] = "グローバルナビゲーション"
    return render_attrs(attrs)


def render_class_roster_hero(section: dict[str, Any], data: dict[str, Any]) -> str:
    image = data["image"]
    actions = data["heroActions"]
    return "\n".join(
        [
            '    <section class="class-roster-hero">',
            '      <div class="container class-roster-hero-grid">',
            '        <div class="class-roster-copy">',
            '          <div class="class-roster-labels">',
            render_spans(data["englishLabels"], spaces=12),
            '          </div>',
            '          <div class="class-roster-badges">',
            render_spans(data["badges"], spaces=12),
            '          </div>',
            f'          <h1>{render_inline_spans(data["productNameParts"])}</h1>',
            '          <p class="class-roster-sublead">',
            render_lines_with_breaks(data["heroLeadLines"], spaces=12),
            '          </p>',
            '          <div class="class-roster-lead">',
            render_paragraphs(data["heroDescription"], spaces=12),
            '          </div>',
            '          <div class="actions">',
            f'            <a class="btn btn-primary" href="{html_attr(data["downloadUrl"])}">{html_text(actions["downloadLabel"])}</a>',
            f'            <a class="btn btn-light" href="#features">{html_text(actions["featuresLabel"])}</a>',
            '          </div>',
            '        </div>',
            '        <div class="class-roster-visual">',
            f'          <p>{html_text(image["caption"])}</p>',
            f'          <img src="{html_attr(image["src"])}" alt="{html_attr(image["alt"])}">',
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_class_roster_summary(section: dict[str, Any], data: dict[str, Any]) -> str:
    items = []
    for item in section["items"]:
        items.append(
            "\n".join(
                [
                    '        <div class="class-roster-summary-item">',
                    f'          <span>{html_text(item["number"])}</span>',
                    f'          <h2>{html_text(item["title"])}</h2>',
                    f'          <p>{html_text(item["text"])}</p>',
                    '        </div>',
                ]
            )
        )
    return "\n".join(
        [
            f'    <section class="class-roster-summary" aria-label="{html_attr(section["ariaLabel"])}">',
            '      <div class="container class-roster-summary-grid">',
            "\n".join(items),
            '      </div>',
            '    </section>',
        ]
    )


def render_class_roster_features(section: dict[str, Any], data: dict[str, Any]) -> str:
    cards = []
    for item in section["items"]:
        bullets = "\n".join(f"              <li>{html_text(bullet)}</li>" for bullet in item["bullets"])
        cards.append(
            "\n".join(
                [
                    '          <article class="class-roster-feature-card">',
                    '            <div class="class-roster-card-head">',
                    f'              <span>{html_text(item["number"])}</span>',
                    f'              <h3>{html_text(item["title"])}</h3>',
                    '            </div>',
                    '            <ul>',
                    bullets,
                    '            </ul>',
                    f'            <p class="class-roster-result">{html_text(item["result"])}</p>',
                    '          </article>',
                ]
            )
        )
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="section class-roster-section">',
            '      <div class="container">',
            '        <div class="class-roster-section-heading">',
            f'          <p class="sub">{html_text(section["eyebrow"])}</p>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            '          <p>',
            render_lines_with_breaks(section["descriptionLines"], spaces=12),
            '          </p>',
            '        </div>',
            '',
            '        <div class="class-roster-feature-grid">',
            "\n".join(cards),
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_class_roster_document_list(section: dict[str, Any], data: dict[str, Any]) -> str:
    items = "\n".join(f"          <li>{html_text(item)}</li>" for item in section["items"])
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="section class-roster-documents">',
            '      <div class="container class-roster-split">',
            '        <div>',
            f'          <p class="sub">{html_text(section["eyebrow"])}</p>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            f'          <p>{html_text(section["description"])}</p>',
            '        </div>',
            '        <ul class="class-roster-document-list">',
            items,
            '        </ul>',
            '      </div>',
            '    </section>',
        ]
    )


def render_class_roster_steps(section: dict[str, Any], data: dict[str, Any]) -> str:
    steps = []
    for step in section["steps"]:
        steps.append(
            "\n".join(
                [
                    '          <li>',
                    f'            <span>{html_text(step["number"])}</span>',
                    f'            <strong>{html_text(step["text"])}</strong>',
                    '          </li>',
                ]
            )
        )
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="section class-roster-section">',
            '      <div class="container">',
            '        <div class="class-roster-section-heading">',
            f'          <p class="sub">{html_text(section["eyebrow"])}</p>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            '        </div>',
            '        <ol class="class-roster-steps">',
            "\n".join(steps),
            '        </ol>',
            '      </div>',
            '    </section>',
        ]
    )


def render_class_roster_download_cta(section: dict[str, Any], data: dict[str, Any]) -> str:
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="section class-roster-distribution">',
            '      <div class="container">',
            '        <div class="class-roster-status-card">',
            f'          <span class="status-badge">{html_text(section["status"])}</span>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            f'          <p>{html_text(section["description"])}</p>',
            '          <div class="actions">',
            f'            <a class="btn btn-primary" href="{html_attr(data["downloadUrl"])}">{html_text(section["downloadLabel"])}</a>',
            f'            <a class="secondary-button" href="{html_attr(section["backUrl"])}">{html_text(section["backLabel"])}</a>',
            '          </div>',
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_hero(section: dict[str, Any], data: dict[str, Any]) -> str:
    actions = render_actions(section["actions"], spaces=10)
    note = ""
    if section.get("noteLines"):
        note = "\n".join(
            [
                f'          <p class="{html_attr(section.get("noteClass", "hero-note"))}">',
                render_lines_with_breaks(section["noteLines"], spaces=12),
                '          </p>',
            ]
        )
    elif section.get("note"):
        note = f'          <p class="{html_attr(section.get("noteClass", "hero-note"))}">{html_text(section["note"])}</p>'
    return "\n".join(
        [
            f'    <section class="{html_attr(section["class"])}">',
            f'      <div class="{html_attr(section["containerClass"])}">',
            f'        <div class="{html_attr(section["textClass"])}">',
            f'          <div class="kicker">{html_text(section["kicker"])}</div>',
            f'          <h1>{render_heading_lines(section["headingLines"])}</h1>',
            f'          <p class="lead"{render_attrs({"style": section["leadStyle"]}) if section.get("leadStyle") else ""}>{html_text(section["lead"])}</p>',
            note,
            actions,
            '        </div>',
            render_visual(section, spaces=8),
            '      </div>',
            '    </section>',
        ]
    )


def render_page_hero(section: dict[str, Any], data: dict[str, Any]) -> str:
    style = ""
    if section.get("backgroundImage"):
        style = f' style=\'--page-bg:url("{html_attr(section["backgroundImage"])}")\''
    return "\n".join(
        [
            f'    <section class="{html_attr(section.get("class", "page-hero"))}"{style}>',
            '      <div class="container">',
            f'        <div class="kicker">{html_text(section["kicker"])}</div>',
            f'        <h1>{html_text(section["heading"])}</h1>',
            f'        <p class="lead">{html_text(section["lead"])}</p>',
            '      </div>',
            '    </section>',
        ]
    )


def render_image_text(section: dict[str, Any], data: dict[str, Any]) -> str:
    image_html = "\n".join(
        [
            '        <div class="visual">',
            f'          <img src="{html_attr(section["image"]["src"])}" alt="{html_attr(section["image"]["alt"])}">',
            '        </div>',
        ]
    )
    paragraphs_html = []
    for paragraph in section["paragraphs"]:
        if isinstance(paragraph, dict):
            style_str = render_attrs({"style": paragraph["style"]}) if paragraph.get("style") else ""
            paragraphs_html.append(f'          <p{style_str}>{html_text(paragraph["text"])}</p>')
        else:
            paragraphs_html.append(f'          <p>{html_text(paragraph)}</p>')
    if section.get("simpleText"):
        text_lines = [
            "        <div>",
            f'          <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'          <h2>{html_text(section["heading"])}</h2>',
        ]
        text_lines.extend(paragraphs_html)
        text_lines.append("        </div>")
        text_html = "\n".join(text_lines)
        columns = [image_html, text_html] if section.get("imagePosition") == "left" else [text_html, image_html]
        section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
        section_class = section.get("class", "section")
        background = f' style="background:{html_attr(section["background"])};"' if section.get("background") else ""
        container_class = section.get("containerClass", "container grid grid-2")
        container_style = render_attrs({"style": section.get("containerStyle", "align-items:center;")}) if section.get("containerStyle", "align-items:center;") else ""
        return "\n".join(
            [
                f'    <section{section_id} class="{html_attr(section_class)}"{background}>',
                f'      <div class="{html_attr(container_class)}"{container_style}>',
                "\n".join(columns),
                '      </div>',
                '    </section>',
            ]
        )
    card_lines = [
        f'        <div class="{html_attr(section.get("cardClass", "card"))}" style="display:flex; flex-direction:column; justify-content:center;">',
        *([f'          <span class="badge" style="width:fit-content; margin-bottom:12px;">{html_text(section["badge"])}</span>'] if section.get("badge") else []),
        f'          <h2>{render_heading_lines(section["headingLines"])}</h2>',
    ]
    card_lines.extend(paragraphs_html)
    if section.get("actions"):
        card_lines.append(render_actions(section["actions"], spaces=10, style=section.get("actionsStyle")))
    card_lines.append('        </div>')
    card_html = "\n".join(card_lines)
    columns = [image_html, card_html] if section.get("imagePosition") == "left" else [card_html, image_html]
    section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
    section_class = section.get("class", "section")
    background = f' style="background:{html_attr(section["background"])};"' if section.get("background") else ""
    container_class = section.get("containerClass", "container grid grid-2")
    container_style = render_attrs({"style": section.get("containerStyle", "align-items:center;")}) if section.get("containerStyle", "align-items:center;") else ""
    return "\n".join(
        [
            f'    <section{section_id} class="{html_attr(section_class)}"{background}>',
            f'      <div class="{html_attr(container_class)}"{container_style}>',
            "\n".join(columns),
            '      </div>',
            '    </section>',
        ]
    )


def render_download_cta(section: dict[str, Any], data: dict[str, Any]) -> str:
    section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
    section_class = section.get("sectionClass")
    container_class = section.get("containerClass")
    heading_tag = section.get("headingTag", "h2")
    if section_class or container_class or heading_tag != "h2":
        paragraphs = section.get("descriptionParagraphs") or [section.get("description", "")]
        paragraph_html = "\n".join(f'        <p>{html_text(paragraph)}</p>' for paragraph in paragraphs)
        note = section.get("note")
        note_attrs = {}
        note_class = section.get("noteClass", "note")
        if note_class:
            note_attrs["class"] = note_class
        if section.get("noteStyle"):
            note_attrs["style"] = section["noteStyle"]
        note_html = (
            f'        <p{render_attrs(note_attrs)}>{html_text(note)}</p>'
            if note
            else ""
        )
        return "\n".join(
            [
                f'    <section{section_id} class="{html_attr(section_class or "section")}"{render_attrs({"style": section["sectionStyle"]}) if section.get("sectionStyle") else ""}>',
                f'      <div class="{html_attr(container_class or "container download-cta")}"{render_attrs({"style": section["containerStyle"]}) if section.get("containerStyle") else ""}>',
                *([f'        <div class="sub">{html_text(section["eyebrow"])}</div>'] if section.get("eyebrow") else []),
                f'        <{heading_tag}>{html_text(section["heading"])}</{heading_tag}>',
                paragraph_html,
                render_actions(section["actions"], spaces=8, style=section.get("actionsStyle", "justify-content:center; margin-top:20px;")),
                note_html,
                '      </div>',
                '    </section>',
            ]
        )
    return "\n".join(
        [
            '    <section class="section">',
            '      <div class="container download-cta" style="text-align:center;">',
            f'        <h2>{html_text(section["heading"])}</h2>',
            f'        <p>{html_text(section["description"])}</p>',
            render_actions(section["actions"], spaces=8, style="justify-content:center; margin-top:20px;"),
            f'        <p class="note" style="margin-top:16px;">{html_text(section["note"])}</p>',
            '      </div>',
            '    </section>',
        ]
    )


def render_specs(section: dict[str, Any], data: dict[str, Any]) -> str:
    items = "\n".join(
        f'            <li><strong>{html_text(item["label"])}:</strong> {html_text(item["text"])}</li>'
        for item in section["items"]
    )
    return "\n".join(
        [
            f'    <section class="section" style="background:{html_attr(section["background"])};">',
            '      <div class="container" style="max-width:700px;">',
            '        <div style="text-align:center; margin-bottom:30px;">',
            f'          <h2>{html_text(section["heading"])}</h2>',
            '        </div>',
            '        <div class="card">',
            '          <ul class="spec-list">',
            items,
            '          </ul>',
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_faq(section: dict[str, Any], data: dict[str, Any]) -> str:
    items = []
    for item in section["items"]:
        items.append(
            "\n".join(
                [
                    '          <div class="card">',
                    f'            <h3 style="color:var(--navy); font-size:1.1rem; border-bottom:1px solid rgba(7,27,54,.08); padding-bottom:8px;">{html_text(item["question"])}</h3>',
                    f'            <p style="margin-top:10px;">{html_text(item["answer"])}</p>',
                    '          </div>',
                ]
            )
        )
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="section" style="background:{html_attr(section["background"])};">',
            '      <div class="container" style="max-width:800px;">',
            '        <div style="text-align:center; margin-bottom:40px;">',
            f'          <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            '        </div>',
            '        <div style="display:flex; flex-direction:column; gap:20px;">',
            "\n".join(items),
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_paragraph_list(paragraphs: list[str], spaces: int) -> str:
    return "\n".join(f'{" " * spaces}<p>{html_text(paragraph)}</p>' for paragraph in paragraphs)


def render_text_card_grid(section: dict[str, Any], data: dict[str, Any]) -> str:
    def render_card(item: dict[str, Any], spaces: int = 10) -> str:
        pad = " " * spaces
        inner = " " * (spaces + 2)
        lines = [f'{pad}<div class="{html_attr(item.get("class", "card"))}"{render_attrs({"style": item["style"]}) if item.get("style") else ""}>']
        if item.get("mark"):
            lines.append(f'{inner}<div class="mark">{html_text(item["mark"])}</div>')
        if item.get("badge"):
            lines.append(f'{inner}<span class="badge" style="width:fit-content; margin-bottom:12px;">{html_text(item["badge"])}</span>')
        if item.get("heading"):
            lines.append(f'{inner}<h3>{html_text(item["heading"])}</h3>')
        for paragraph in item.get("paragraphs", []):
            lines.append(f'{inner}<p{render_attrs({"style": item["paragraphStyle"]}) if item.get("paragraphStyle") else ""}>{html_text(paragraph)}</p>')
        if item.get("text"):
            lines.append(f'{inner}<p{render_attrs({"style": item["paragraphStyle"]}) if item.get("paragraphStyle") else ""}>{html_text(item["text"])}</p>')
        if item.get("bullets"):
            lines.append(f'{inner}<ul class="{html_attr(item.get("listClass", "notice-list"))}">')
            lines.extend(f'{" " * (spaces + 4)}<li>{html_text(bullet)}</li>' for bullet in item["bullets"])
            lines.append(f'{inner}</ul>')
        lines.append(f'{pad}</div>')
        return "\n".join(lines)

    cards = []
    for item in section["items"]:
        cards.append(render_card(item))
    section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
    background = f' style="background:{html_attr(section["background"])};"' if section.get("background") else ""
    if section.get("cardsOnly"):
        return "\n".join(
            [
                f'    <section{section_id} class="{html_attr(section.get("class", "section"))}"{background}>',
                f'      <div class="{html_attr(section.get("gridClass", "container grid grid-3"))}"{render_attrs({"style": section["gridStyle"]}) if section.get("gridStyle") else ""}>',
                "\n".join(cards),
                '      </div>',
                '    </section>',
            ]
        )
    extra_grids = []
    for grid in section.get("extraGrids", []):
        extra_cards = "\n".join(render_card(item, spaces=10) for item in grid["items"])
        extra_grids.append(
            "\n".join(
                [
                    f'        <div class="{html_attr(grid.get("gridClass", "grid grid-2"))}"{render_attrs({"style": grid["gridStyle"]}) if grid.get("gridStyle") else ""}>',
                    extra_cards,
                    '        </div>',
                ]
            )
        )
    table_cards = []
    for table_card in section.get("tableCards", []):
        rows = []
        for row in table_card["rows"]:
            label_width = f' width:{html_attr(row["labelWidth"])};' if row.get("labelWidth") else ""
            row_style = render_attrs({"style": row["rowStyle"]}) if row.get("rowStyle") else ""
            rows.append(
                f'          <tr{row_style}><td style="padding:8px; font-weight:bold;{label_width}">{html_text(row["label"])}</td><td style="padding:8px;">{html_text(row["text"])}</td></tr>'
            )
        table_cards.append(
            "\n".join(
                [
                    f'        <div class="{html_attr(table_card.get("class", "card"))}"{render_attrs({"style": table_card["style"]}) if table_card.get("style") else ""}>',
                    f'          <h3{render_attrs({"style": table_card["headingStyle"]}) if table_card.get("headingStyle") else ""}>{html_text(table_card["heading"])}</h3>',
                    f'          <table{render_attrs({"style": table_card["tableStyle"]}) if table_card.get("tableStyle") else ""}>',
                    "\n".join(rows),
                    '          </table>',
                    '        </div>',
                ]
            )
        )
    visual_blocks = []
    if section.get("visual"):
        image = section["visual"]["image"]
        visual_blocks.append(
            "\n".join(
                [
                    f'        <div class="{html_attr(section["visual"].get("class", "visual"))}">',
                    f'          <img src="{html_attr(image["src"])}" alt="{html_attr(image["alt"])}">',
                    '        </div>',
                ]
            )
        )
    heading_html = []
    if section.get("headingContainerStyle") or section.get("headingContainerClass"):
        attrs = {}
        if section.get("headingContainerStyle"):
            attrs["style"] = section["headingContainerStyle"]
        if section.get("headingContainerClass"):
            attrs["class"] = section["headingContainerClass"]
        heading_html.append(f'        <div{render_attrs(attrs)}>')
        heading_html.append(f'          <div class="sub">{html_text(section["eyebrow"])}</div>')
        heading_html.append(f'          <h2>{html_text(section["heading"])}</h2>')
        heading_html.append('        </div>')
    else:
        heading_html.append(f'        <div class="sub">{html_text(section["eyebrow"])}</div>')
        heading_html.append(f'        <h2>{html_text(section["heading"])}</h2>')

    return "\n".join(
        [
            f'    <section{section_id} class="{html_attr(section.get("class", "section"))}"{background}>',
            '      <div class="container">',
            *heading_html,
            *[f'        <p>{html_text(paragraph)}</p>' for paragraph in section.get("descriptionParagraphs", [])],
            *([f'        <p>{html_text(section["description"])}</p>'] if section.get("description") else []),
            f'        <div class="{html_attr(section.get("gridClass", "grid grid-3"))}"{render_attrs({"style": section["gridStyle"]}) if section.get("gridStyle") else ""}>',
            "\n".join(cards),
            '        </div>',
            *extra_grids,
            *table_cards,
            *visual_blocks,
            '      </div>',
            '    </section>',
        ]
    )


def render_workflow_steps(section: dict[str, Any], data: dict[str, Any]) -> str:
    steps = []
    for item in section["steps"]:
        steps.append(
            "\n".join(
                [
                    f'          <div{render_attrs({"style": section.get("stepStyle", "display: flex; align-items: flex-start; gap: 15px;")})}>',
                    f'            <div{render_attrs({"style": section.get("numberStyle", "background: var(--gold); color: #071b36; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;")})}>{html_text(item["number"])}</div>',
                    '            <div>',
                    f'              <h4{render_attrs({"style": section.get("headingStyle", "margin: 0 0 5px 0; color: var(--navy);")})}>{html_text(item["heading"])}</h4>',
                    f'              <p{render_attrs({"style": section.get("textStyle", "margin: 0; font-size: 0.9rem; color: var(--muted);")})}>{html_text(item["text"])}</p>',
                    '            </div>',
                    '          </div>',
                ]
            )
        )
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="{html_attr(section.get("class", "section"))}"{render_attrs({"style": section["style"]}) if section.get("style") else ""}>',
            '      <div class="container">',
            f'        <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'        <h2>{html_text(section["heading"])}</h2>',
            f'        <p>{html_text(section["description"])}</p>',
            f'        <div class="{html_attr(section.get("containerClass", "flow-brief-container"))}"{render_attrs({"style": section["containerStyle"]}) if section.get("containerStyle") else ""}>',
            f'          <div{render_attrs({"style": section.get("listStyle", "display: flex; flex-direction: column; gap: 15px;")})}>',
            "\n".join(steps),
            '          </div>',
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_grouped_notice(section: dict[str, Any], data: dict[str, Any]) -> str:
    groups = []
    for group in section["groups"]:
        items = []
        for item in group["items"]:
            items.append(
                f'        <li{render_attrs({"style": section["itemStyle"]}) if section.get("itemStyle") else ""}><strong>{html_text(item["label"])}</strong> {html_text(item["text"])}</li>'
            )
        groups.extend(
            [
                f'        <h4{render_attrs({"style": section["groupHeadingStyle"]}) if section.get("groupHeadingStyle") else ""}>{html_text(group["heading"])}</h4>',
                f'        <ul{render_attrs({"style": section["listStyle"]}) if section.get("listStyle") else ""}>',
                "\n".join(items),
                '        </ul>',
            ]
        )
    return "\n".join(
        [
            f'    <section class="{html_attr(section.get("class", "section-narrow"))}"{render_attrs({"style": section["style"]}) if section.get("style") else ""}>',
            f'      <div class="{html_attr(section.get("containerClass", "container warning"))}">',
            f'        <h3>{html_text(section["heading"])}</h3>',
            "\n".join(groups),
            '      </div>',
            '    </section>',
        ]
    )


def render_image_gallery(section: dict[str, Any], data: dict[str, Any]) -> str:
    def render_image(image: dict[str, Any], spaces: int = 10) -> str:
        pad = " " * spaces
        inner = " " * (spaces + 2)
        img_style = render_attrs({"style": image["style"]}) if image.get("style") else ""
        img = f'{inner}<img src="{html_attr(image["src"])}" alt="{html_attr(image["alt"])}"{img_style}>'
        if image.get("wrapClass") or image.get("wrapStyle"):
            attrs = {}
            if image.get("wrapClass"):
                attrs["class"] = image["wrapClass"]
            if image.get("wrapStyle"):
                attrs["style"] = image["wrapStyle"]
            return "\n".join([f'{pad}<div{render_attrs(attrs)}>', img, f'{pad}</div>'])
        return f'{pad}<img src="{html_attr(image["src"])}" alt="{html_attr(image["alt"])}"{img_style}>'

    images = "\n".join(render_image(image) for image in section["images"])
    card_blocks = []
    for grid in section.get("cardGrids", []):
        cards = []
        for item in grid["items"]:
            lines = ['          <div class="card">']
            if item.get("heading"):
                lines.append(f'            <h3>{html_text(item["heading"])}</h3>')
            for paragraph in item.get("paragraphs", []):
                lines.append(f'            <p>{html_text(paragraph)}</p>')
            if item.get("text"):
                lines.append(f'            <p>{html_text(item["text"])}</p>')
            lines.append('          </div>')
            cards.append("\n".join(lines))
        card_blocks.append(
            "\n".join(
                [
                    f'        <div class="{html_attr(grid.get("gridClass", "grid grid-2"))}"{render_attrs({"style": grid["gridStyle"]}) if grid.get("gridStyle") else ""}>',
                    "\n".join(cards),
                    '        </div>',
                ]
            )
        )
    extra_images = []
    for block in section.get("extraImageGrids", []):
        block_images = "\n".join(render_image(image) for image in block["images"])
        extra_images.append(
            "\n".join(
                [
                    f'        <div class="{html_attr(block.get("gridClass", "grid grid-1"))}"{render_attrs({"style": block["gridStyle"]}) if block.get("gridStyle") else ""}>',
                    block_images,
                    '        </div>',
                ]
            )
        )
    footer_cards = []
    for item in section.get("footerCards", []):
        lines = [f'        <div class="{html_attr(item.get("class", "card"))}"{render_attrs({"style": item["style"]}) if item.get("style") else ""}>']
        lines.append(f'          <h3>{html_text(item["heading"])}</h3>')
        for paragraph in item.get("paragraphs", []):
            lines.append(f'          <p>{html_text(paragraph)}</p>')
        lines.append('        </div>')
        footer_cards.append("\n".join(lines))
    section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
    background = f' style="background:{html_attr(section["background"])};"' if section.get("background") else ""
    eyebrow_html = [f'        <div class="sub">{html_text(section["eyebrow"])}</div>'] if section.get("eyebrow") else []
    heading_tag = section.get("headingTag", "h2")
    heading_style = render_attrs({"style": section["headingStyle"]}) if section.get("headingStyle") else ""
    heading_html = [f'        <{heading_tag}{heading_style}>{html_text(section["heading"])}</{heading_tag}>'] if section.get("heading") else []
    return "\n".join(
        [
            f'    <section{section_id} class="{html_attr(section.get("class", "section"))}"{background}>',
            '      <div class="container">',
            *eyebrow_html,
            *heading_html,
            f'        <div class="{html_attr(section.get("gridClass", "grid grid-2 gallery"))}"{render_attrs({"style": section["gridStyle"]}) if section.get("gridStyle") else ""}>',
            images,
            '        </div>',
            *card_blocks,
            *extra_images,
            *footer_cards,
            '      </div>',
            '    </section>',
        ]
    )


def render_split_list_notice(section: dict[str, Any], data: dict[str, Any]) -> str:
    list_card = section["listCard"]
    bullets = "\n".join(f'            <li>{html_text(item)}</li>' for item in list_card["items"])
    notices = []
    for notice in section["notices"]:
        notices.append(f'          <h3{render_attrs({"style": notice["headingStyle"]}) if notice.get("headingStyle") else ""}>{html_text(notice["heading"])}</h3>')
        notices.extend(f'          <p>{html_text(paragraph)}</p>' for paragraph in notice["paragraphs"])
    return "\n".join(
        [
            f'    <section class="section"{render_attrs({"style": "background:" + section["background"] + ";"}) if section.get("background") else ""}>',
            '      <div class="container grid grid-2" style="align-items:start;">',
            f'        <div class="{html_attr(list_card.get("class", "card gold"))}">',
            f'          <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            '          <ul class="notice-list">',
            bullets,
            '          </ul>',
            '        </div>',
            f'        <div class="{html_attr(section.get("noticeClass", "warning"))}">',
            "\n".join(notices),
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_split_text_card(section: dict[str, Any], data: dict[str, Any]) -> str:
    card = section["card"]
    bullet_html = ""
    if card.get("bullets"):
        separator = card.get("separator", ":")
        bullet_html = "\n".join(
            [
                f'          <ul class="{html_attr(card.get("listClass", "spec-list"))}">',
                *[f'            <li><strong>{html_text(item["label"])}{html_text(separator)}</strong> {html_text(item["text"])}</li>' for item in card["bullets"]],
                '          </ul>',
            ]
        )
    card_lines = [
        f'        <div class="{html_attr(card.get("class", "card"))}">',
        *([f'          <span class="badge" style="width:fit-content; margin-bottom:12px;">{html_text(card["badge"])}</span>'] if card.get("badge") else []),
        f'          <h3>{html_text(card["heading"])}</h3>',
        *([f'          <p>{html_text(card["text"])}</p>'] if card.get("text") else []),
    ]
    if bullet_html:
        card_lines.append(bullet_html)
    card_lines.append('        </div>')
    return "\n".join(
        [
            f'    <section class="section"{render_attrs({"style": "background:" + section["background"] + ";"}) if section.get("background") else ""}>',
            '      <div class="container grid grid-2" style="align-items:center;">',
            f'        <div{render_attrs({"class": section["textClass"]}) if section.get("textClass") else ""}>',
            f'          <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            render_paragraph_list(section["paragraphs"], spaces=10),
            '        </div>',
            *card_lines,
            '      </div>',
            '    </section>',
        ]
    )


def render_numbered_text_list(section: dict[str, Any], data: dict[str, Any]) -> str:
    items = []
    for item in section["items"]:
        items.append(
            "\n".join(
                [
                    f'      <div class="{html_attr(section.get("itemClass", "problem-item"))}">',
                    f'        <div class="{html_attr(section.get("numberClass", "num"))}">{html_text(item["number"])}</div>',
                    '        <div>',
                    f'          <h3>{html_text(item["heading"])}</h3>',
                    f'          <p>{html_text(item["text"])}</p>',
                    '        </div>',
                    '      </div>',
                ]
            )
        )
    section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
    background = f' style="background:{html_attr(section["background"])};"' if section.get("background") else ""
    return "\n".join(
        [
            f'    <section{section_id} class="{html_attr(section.get("class", "section"))}"{background}>',
            '      <div class="container">',
            f'        <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'        <h2>{html_text(section["heading"])}</h2>',
            f'        <div class="{html_attr(section.get("listClass", "problem-list"))}">',
            "\n".join(items),
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_narrow_text_box(section: dict[str, Any], data: dict[str, Any]) -> str:
    paragraphs = []
    for paragraph in section["paragraphs"]:
        if isinstance(paragraph, dict):
            if paragraph.get("html"):
                body = paragraph["html"]
            else:
                body = html_text(paragraph["text"])
                if paragraph.get("strong"):
                    body = f'<strong>{html_text(paragraph["strong"])}</strong><br><a href="{html_attr(paragraph["href"])}">{html_text(paragraph["text"])}</a>'
            paragraphs.append(f'        <p>{body}</p>')
        else:
            paragraphs.append(f'        <p>{html_text(paragraph)}</p>')
    heading_tag = section.get("headingTag", "h3")
    return "\n".join(
        [
            f'    <section class="{html_attr(section.get("class", "section-narrow"))}">',
            f'      <div class="{html_attr(section.get("containerClass", "container article-link-box"))}">',
            f'        <{heading_tag}>{html_text(section["heading"])}</{heading_tag}>',
            "\n".join(paragraphs),
            '      </div>',
            '    </section>',
        ]
    )


def render_ordered_list_with_info(section: dict[str, Any], data: dict[str, Any]) -> str:
    steps = "\n".join(f'            <li>{html_text(item)}</li>' for item in section["steps"])
    rows = "\n".join(
        f'            <tr{render_attrs({"style": row.get("rowStyle", "")}) if row.get("rowStyle") else ""}><td style="padding:8px; font-weight:bold;{(" width:" + row["labelWidth"] + ";") if row.get("labelWidth") else ""}">{html_text(row["label"])}</td><td style="padding:8px;">{html_text(row["text"])}</td></tr>'
        for row in section["info"]["rows"]
    )
    return "\n".join(
        [
            f'    <section class="section"{render_attrs({"style": "background:" + section["background"] + ";"}) if section.get("background") else ""}>',
            '      <div class="container grid grid-2" style="align-items:start;">',
            '        <div>',
            f'          <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            '          <ol style="line-height:1.9; padding-left:1.4em;">',
            steps,
            '          </ol>',
            '        </div>',
            f'        <div class="{html_attr(section["info"].get("class", "info-box"))}">',
            f'          <h3>{html_text(section["info"]["heading"])}</h3>',
            '          <table style="width:100%; border-collapse:collapse; font-size:.94rem; line-height:1.8;">',
            rows,
            '          </table>',
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_video_placeholder(section: dict[str, Any], data: dict[str, Any]) -> str:
    steps = "\n".join(f'            <li>{html_text(item)}</li>' for item in section["steps"])
    placeholder = section["placeholder"]
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="section">',
            '      <div class="container grid grid-2" style="align-items:center;">',
            '        <div>',
            f'          <div class="sub">{html_text(section["eyebrow"])}</div>',
            f'          <h2>{html_text(section["heading"])}</h2>',
            f'          <p>{html_text(section["description"])}</p>',
            '          <ol style="line-height:1.9; padding-left:1.4em;">',
            steps,
            '          </ol>',
            '        </div>',
            '        <div class="card gold" style="min-height:260px; display:flex; flex-direction:column; justify-content:center;">',
            '          <!--',
            '            将来の差し替え例:',
            '            <video controls playsinline poster="/assets/images/observation-card/video-poster.png">',
            '              <source src="/assets/videos/observation-card-demo.mp4" type="video/mp4">',
            '            </video>',
            '          -->',
            f'          <span class="badge" style="width:fit-content; margin-bottom:12px;">{html_text(placeholder["badge"])}</span>',
            f'          <h3>{html_text(placeholder["heading"])}</h3>',
            f'          <p>{html_text(placeholder["text"])}</p>',
            '        </div>',
            '      </div>',
            '    </section>',
        ]
    )


def render_notice_list(section: dict[str, Any], data: dict[str, Any]) -> str:
    items = "\n".join(f'          <li>{html_text(item)}</li>' for item in section["items"])
    return "\n".join(
        [
            f'    <section id="{html_attr(section["id"])}" class="{html_attr(section.get("class", "section-narrow"))}">',
            '      <div class="container warning">',
            f'        <h3>{html_text(section["heading"])}</h3>',
            '        <ul class="notice-list">',
            items,
            '        </ul>',
            '      </div>',
            '    </section>',
        ]
    )


SECTION_RENDERERS = {
    "classRosterHero": render_class_roster_hero,
    "summaryGrid": render_class_roster_summary,
    "featureCards": render_class_roster_features,
    "documentList": render_class_roster_document_list,
    "steps": render_class_roster_steps,
    "classRosterDownloadCta": render_class_roster_download_cta,
    "hero": render_hero,
    "pageHero": render_page_hero,
    "imageText": render_image_text,
    "purchase": render_image_text,
    "downloadCta": render_download_cta,
    "specs": render_specs,
    "faq": render_faq,
    "splitTextCard": render_split_text_card,
    "textCardGrid": render_text_card_grid,
    "workflowSteps": render_workflow_steps,
    "groupedNotice": render_grouped_notice,
    "imageGallery": render_image_gallery,
    "numberedTextList": render_numbered_text_list,
    "narrowTextBox": render_narrow_text_box,
    "splitListNotice": render_split_list_notice,
    "orderedListWithInfo": render_ordered_list_with_info,
    "videoPlaceholder": render_video_placeholder,
    "noticeList": render_notice_list,
}


def render_sections(data: dict[str, Any]) -> str:
    sections = []
    for section in data["sections"]:
        renderer = SECTION_RENDERERS[section["type"]]
        sections.append(renderer(section, data))
    return "\n\n".join(sections)


def load_data(slug: str) -> dict[str, Any]:
    data_path = DATA_DIR / f"{slug}.json"
    if not data_path.exists():
        raise SystemExit(f"Missing product detail data: {data_path.relative_to(ROOT)}")
    return json.loads(data_path.read_text(encoding="utf-8"))


def output_path(slug: str) -> Path:
    return ROOT / "products" / slug / "index.html"


def build(slug: str) -> Path:
    data = load_data(slug)
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    body_class = data.get("bodyClass", "")
    body_tag = f'<body class="{html_attr(body_class)}">' if body_class else "<body>"
    script_version = data.get("scriptVersion")
    script_html = (
        f'  <script src="/assets/site.js?v={html_attr(script_version)}"></script>'
        if script_version
        else ""
    )
    output = template.substitute(
        page_title=html_text(data["pageTitle"]),
        meta_description=html_attr(data["metaDescription"]),
        stylesheet_href=html_attr(stylesheet_href(data)),
        font_links=render_font_links(data),
        body_tag=body_tag,
        slug=html_text(slug),
        menu_toggle=render_menu_toggle(data),
        nav_attrs=render_nav_attrs(data),
        nav_links=render_nav_links(data),
        main_html=render_sections(data),
        home_floating=render_home_floating(data),
        script_html=script_html,
    )
    path = output_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(
        "Generated "
        f"{path.relative_to(ROOT)} from data/product-details/{slug}.json and "
        f"{TEMPLATE_PATH.relative_to(ROOT)}"
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a generated product detail page.")
    parser.add_argument("slug", nargs="?", default="class-roster")
    args = parser.parse_args()
    build(args.slug)


if __name__ == "__main__":
    main()
