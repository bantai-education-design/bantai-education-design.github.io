from __future__ import annotations

import json
from html import escape
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "product-details" / "class-roster.json"
TEMPLATE_PATH = ROOT / "templates" / "product-detail.html"
OUTPUT_PATH = ROOT / "products" / "class-roster" / "index.html"


def html_text(value: object) -> str:
    return escape(str(value), quote=False)


def html_attr(value: object) -> str:
    return escape(str(value), quote=True)


def indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())


def render_spans(values: list[str], class_name: str | None = None, spaces: int = 12) -> str:
    class_attr = f' class="{class_name}"' if class_name else ""
    lines = [f"<span{class_attr}>{html_text(value)}</span>" for value in values]
    return indent_block("\n".join(lines), spaces)


def render_inline_spans(values: list[str]) -> str:
    return "".join(f"<span>{html_text(value)}</span>" for value in values)


def render_lines_with_breaks(values: list[str], spaces: int = 12) -> str:
    lines = []
    for index, value in enumerate(values):
        suffix = "<br>" if index < len(values) - 1 else ""
        lines.append(f"{html_text(value)}{suffix}")
    return indent_block("\n".join(lines), spaces)


def render_paragraphs(values: list[str], spaces: int = 12) -> str:
    lines = [f"<p>{html_text(value)}</p>" for value in values]
    return indent_block("\n".join(lines), spaces)


def render_summary(items: list[dict]) -> str:
    blocks = []
    for item in items:
        blocks.append(
            "\n".join(
                [
                    '<div class="class-roster-summary-item">',
                    f'  <span>{html_text(item["number"])}</span>',
                    f'  <h2>{html_text(item["title"])}</h2>',
                    f'  <p>{html_text(item["text"])}</p>',
                    "</div>",
                ]
            )
        )
    return indent_block("\n".join(blocks), 8)


def render_feature_cards(items: list[dict]) -> str:
    blocks = []
    for item in items:
        bullets = "\n".join(f"    <li>{html_text(bullet)}</li>" for bullet in item["bullets"])
        blocks.append(
            "\n".join(
                [
                    '<article class="class-roster-feature-card">',
                    '  <div class="class-roster-card-head">',
                    f'    <span>{html_text(item["number"])}</span>',
                    f'    <h3>{html_text(item["title"])}</h3>',
                    "  </div>",
                    "  <ul>",
                    bullets,
                    "  </ul>",
                    f'  <p class="class-roster-result">{html_text(item["result"])}</p>',
                    "</article>",
                ]
            )
        )
    return indent_block("\n".join(blocks), 10)


def render_list_items(values: list[str], spaces: int = 10) -> str:
    return indent_block("\n".join(f"<li>{html_text(value)}</li>" for value in values), spaces)


def render_howto_steps(steps: list[dict]) -> str:
    lines = []
    for step in steps:
        lines.append(
            "\n".join(
                [
                    "<li>",
                    f'  <span>{html_text(step["number"])}</span>',
                    f'  <strong>{html_text(step["text"])}</strong>',
                    "</li>",
                ]
            )
        )
    return indent_block("\n".join(lines), 10)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    image = data["image"]
    hero_actions = data["heroActions"]
    features = data["featuresSection"]
    documents = data["documentsSection"]
    howto = data["howtoSection"]
    distribution = data["distributionSection"]

    output = template.substitute(
        page_title=html_text(data["pageTitle"]),
        meta_description=html_attr(data["metaDescription"]),
        style_version=html_attr(data["styleVersion"]),
        body_class=html_attr(data["bodyClass"]),
        english_labels=render_spans(data["englishLabels"]),
        badges=render_spans(data["badges"]),
        product_name_parts=render_inline_spans(data["productNameParts"]),
        hero_lead=render_lines_with_breaks(data["heroLeadLines"]),
        hero_description=render_paragraphs(data["heroDescription"]),
        download_url=html_attr(data["downloadUrl"]),
        hero_download_label=html_text(hero_actions["downloadLabel"]),
        hero_features_label=html_text(hero_actions["featuresLabel"]),
        image_caption=html_text(image["caption"]),
        image_src=html_attr(image["src"]),
        image_alt=html_attr(image["alt"]),
        summary_aria_label=html_attr(data["summaryAriaLabel"]),
        summary_items=render_summary(data["summary"]),
        features_eyebrow=html_text(features["eyebrow"]),
        features_heading=html_text(features["heading"]),
        features_description=render_lines_with_breaks(features["descriptionLines"], spaces=12),
        feature_cards=render_feature_cards(features["items"]),
        documents_eyebrow=html_text(documents["eyebrow"]),
        documents_heading=html_text(documents["heading"]),
        documents_description=html_text(documents["description"]),
        document_items=render_list_items(documents["items"], spaces=10),
        howto_eyebrow=html_text(howto["eyebrow"]),
        howto_heading=html_text(howto["heading"]),
        howto_steps=render_howto_steps(howto["steps"]),
        distribution_status=html_text(distribution["status"]),
        distribution_heading=html_text(distribution["heading"]),
        distribution_description=html_text(distribution["description"]),
        distribution_download_label=html_text(distribution["downloadLabel"]),
        distribution_back_url=html_attr(distribution["backUrl"]),
        distribution_back_label=html_text(distribution["backLabel"]),
        script_version=html_attr(data["scriptVersion"]),
    )

    OUTPUT_PATH.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(
        "Generated "
        f"{OUTPUT_PATH.relative_to(ROOT)} from "
        f"{DATA_PATH.relative_to(ROOT)} and {TEMPLATE_PATH.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
