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
    return "\n".join(
        [
            f'    <section class="{html_attr(section["class"])}">',
            f'      <div class="{html_attr(section["containerClass"])}">',
            f'        <div class="{html_attr(section["textClass"])}">',
            f'          <div class="kicker">{html_text(section["kicker"])}</div>',
            f'          <h1>{render_heading_lines(section["headingLines"])}</h1>',
            f'          <p class="lead">{html_text(section["lead"])}</p>',
            f'          <p class="hero-note">{html_text(section["note"])}</p>',
            actions,
            '        </div>',
            f'        <div class="{html_attr(section["imageContainerClass"])}">',
            f'          <img src="{html_attr(section["image"]["src"])}" alt="{html_attr(section["image"]["alt"])}">',
            '        </div>',
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
    card_lines = [
        f'        <div class="{html_attr(section.get("cardClass", "card"))}" style="display:flex; flex-direction:column; justify-content:center;">',
        f'          <span class="badge" style="width:fit-content; margin-bottom:12px;">{html_text(section["badge"])}</span>',
        f'          <h2>{render_heading_lines(section["headingLines"])}</h2>',
    ]
    card_lines.extend(f'          <p>{html_text(paragraph)}</p>' for paragraph in section["paragraphs"])
    if section.get("actions"):
        card_lines.append(render_actions(section["actions"], spaces=10, style=section.get("actionsStyle")))
    card_lines.append('        </div>')
    card_html = "\n".join(card_lines)
    columns = [image_html, card_html] if section.get("imagePosition") == "left" else [card_html, image_html]
    section_id = f' id="{html_attr(section["id"])}"' if section.get("id") else ""
    return "\n".join(
        [
            f'    <section{section_id} class="section" style="background:{html_attr(section["background"])};">',
            '      <div class="container grid grid-2" style="align-items:center;">',
            "\n".join(columns),
            '      </div>',
            '    </section>',
        ]
    )


def render_download_cta(section: dict[str, Any], data: dict[str, Any]) -> str:
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


SECTION_RENDERERS = {
    "classRosterHero": render_class_roster_hero,
    "summaryGrid": render_class_roster_summary,
    "featureCards": render_class_roster_features,
    "documentList": render_class_roster_document_list,
    "steps": render_class_roster_steps,
    "classRosterDownloadCta": render_class_roster_download_cta,
    "hero": render_hero,
    "imageText": render_image_text,
    "purchase": render_image_text,
    "downloadCta": render_download_cta,
    "specs": render_specs,
    "faq": render_faq,
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
        style_version=html_attr(data["styleVersion"]),
        body_tag=body_tag,
        slug=html_text(slug),
        menu_toggle=render_menu_toggle(data),
        nav_attrs=render_nav_attrs(data),
        nav_links=render_nav_links(data),
        main_html=render_sections(data),
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
