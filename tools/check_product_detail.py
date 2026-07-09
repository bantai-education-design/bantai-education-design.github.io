from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "product-details"


VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "source",
    "track",
    "wbr",
}


class DetailPageParser(HTMLParser):
    def __init__(self, expected_comment: str) -> None:
        super().__init__()
        self.expected_comment = expected_comment
        self.generated_comment = False
        self.empty_hrefs: list[str] = []
        self.images: list[dict[str, str]] = []
        self.headings: list[str] = []
        self.links: list[str] = []
        self.class_counts: dict[str, int] = {}
        self.in_heading: str | None = None

    def handle_comment(self, data: str) -> None:
        if self.expected_comment in data:
            self.generated_comment = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        for class_name in attr.get("class", "").split():
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        if tag == "a":
            href = attr.get("href", "")
            self.links.append(href)
            if not href:
                self.empty_hrefs.append(self.get_starttag_text() or "<a>")
        if tag == "img":
            self.images.append({"src": attr.get("src", ""), "alt": attr.get("alt", "")})
        if tag in {"h1", "h2", "h3"}:
            self.in_heading = tag
            self.headings.append("")

    def handle_endtag(self, tag: str) -> None:
        if tag == self.in_heading:
            self.in_heading = None

    def handle_data(self, data: str) -> None:
        if self.in_heading and self.headings:
            self.headings[-1] += data.strip()


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_keys(mapping: dict, keys: set[str], label: str) -> None:
    missing = sorted(keys - mapping.keys())
    require(not missing, f"{label}: missing required keys: {', '.join(missing)}")


def data_path(slug: str) -> Path:
    return DATA_DIR / f"{slug}.json"


def output_path(slug: str) -> Path:
    return ROOT / "products" / slug / "index.html"


def load_data(slug: str) -> dict:
    path = data_path(slug)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")


def validate_url(url: str, label: str, *, require_zip: bool = False) -> None:
    parsed = urlparse(url)
    require(parsed.scheme in {"https", "mailto"} or url.startswith(("/", "#")), f"{label}: invalid URL: {url}")
    if require_zip:
        require(parsed.scheme == "https" and url.endswith(".zip"), f"{label}: expected HTTPS ZIP URL")


def validate_image_path(src: str, label: str) -> None:
    require(src.startswith("/"), f"{label}: image path must be root-relative")
    path = ROOT / src.lstrip("/")
    require(path.exists(), f"{label}: image file does not exist: {src}")


def walk_values(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)
    else:
        yield value


def validate_common(slug: str, data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(
        data,
        {"pageTitle", "metaDescription", "navLinks", "productName", "sections"},
        "root",
    )
    require("styleVersion" in data or "styleHref" in data, "root: missing styleVersion or styleHref")
    require(parser.generated_comment, "generated file comment is missing")
    require(not parser.empty_hrefs, "empty href found")
    require(data["pageTitle"] in html, "page title missing from generated HTML")
    require(data["metaDescription"] in html, "meta description missing from generated HTML")
    require(data["productName"] in "".join(parser.headings) or data["productName"] in html, "product name missing")
    require(not re.search(r"\$[a-zA-Z_][a-zA-Z0-9_]*", html), "unresolved template variable found")
    for link in data["navLinks"]:
        validate_url(link["href"], f"navLinks {link['label']}")
    for src in {image["src"] for image in parser.images if image["src"].startswith("/assets/")}:
        validate_image_path(src, "html image")


def validate_class_roster(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(
        data,
        {
            "bodyClass",
            "scriptVersion",
            "productNameParts",
            "englishLabels",
            "badges",
            "heroLeadLines",
            "heroDescription",
            "image",
            "downloadUrl",
            "heroActions",
        },
        "class-roster root",
    )
    validate_image_path(data["image"]["src"], "class-roster image")
    validate_url(data["downloadUrl"], "downloadUrl", require_zip=True)
    sections = {section["type"]: section for section in data["sections"]}
    require(len(sections["summaryGrid"]["items"]) == 4, "summaryGrid must have 4 items")
    require(len(sections["featureCards"]["items"]) == 4, "featureCards must have 4 items")
    require(len(sections["documentList"]["items"]) == 8, "documentList must have 8 items")
    require(len(sections["steps"]["steps"]) == 4, "steps must have 4 steps")
    require(parser.class_counts.get("class-roster-feature-card", 0) == 4, "generated feature card count mismatch")
    require("product-detail-class-roster" in data["bodyClass"], "class roster body class missing")
    require(data["downloadUrl"] in html, "class roster download URL missing")


def validate_houganshi(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"boothUrl", "images", "englishName"}, "houganshi root")
    validate_url(data["boothUrl"], "boothUrl")
    require(data["boothUrl"] in html, "BOOTH URL missing from generated HTML")
    require(len(data["images"]) == 5, "houganshi images must have 5 items")
    for src in data["images"]:
        validate_image_path(src, "houganshi image")
        require(src in html, f"houganshi image missing from HTML: {src}")
    section_types = [section["type"] for section in data["sections"]]
    require(section_types.count("imageText") + section_types.count("purchase") == 4, "description sections must total 4")
    require("downloadCta" in section_types, "downloadCta section missing")
    specs = next((section for section in data["sections"] if section["type"] == "specs"), None)
    require(specs is not None and len(specs["items"]) == 3, "specs must have 3 items")
    faq = next((section for section in data["sections"] if section["type"] == "faq"), None)
    require(faq is not None and len(faq["items"]) == 4, "FAQ must have 4 items")
    require(parser.class_counts.get("visual", 0) >= 4, "visual image sections missing")
    require(html.count(data["boothUrl"]) == 3, "BOOTH link count changed")


def validate_kanji_practice(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"boothUrl", "images", "englishName"}, "kanji-practice root")
    validate_url(data["boothUrl"], "boothUrl")
    require(data["boothUrl"] in html, "BOOTH URL missing from generated HTML")
    require(len(data["images"]) == 5, "kanji-practice images must have 5 items")
    for src in data["images"]:
        validate_image_path(src, "kanji-practice image")
        require(src in html, f"kanji-practice image missing from HTML: {src}")
    section_types = [section["type"] for section in data["sections"]]
    require(section_types.count("imageText") + section_types.count("purchase") == 4, "description sections must total 4")
    require("downloadCta" in section_types, "downloadCta section missing")
    specs = next((section for section in data["sections"] if section["type"] == "specs"), None)
    require(specs is not None and len(specs["items"]) == 3, "specs must have 3 items")
    faq = next((section for section in data["sections"] if section["type"] == "faq"), None)
    require(faq is not None and len(faq["items"]) == 3, "FAQ must have 3 items")
    require(parser.class_counts.get("visual", 0) >= 4, "visual image sections missing")
    require(html.count(data["boothUrl"]) == 3, "BOOTH link count changed")


def validate_observation_card(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"englishName", "versionLabel", "boothUrl"}, "observation-card root")
    require(data["versionLabel"] in html, "version label missing")
    validate_url(data["boothUrl"], "boothUrl")
    require(data["boothUrl"] in html, "BOOTH URL missing from generated HTML")
    require("BOOTH公開中" in html and "Vector準備中" in html and "note準備中" in html, "distribution cards missing")
    forbidden = [
        "vector.co.jp",
        "note.com",
        "github.com/",
        "/assets/images/observation-card/",
        "/assets/videos/observation-card",
    ]
    visible_html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    for value in forbidden:
        require(value not in visible_html, f"forbidden live link or asset reference found: {value}")
    section_types = [section["type"] for section in data["sections"]]
    require("hero" in section_types, "hero section missing")
    targets = next((section for section in data["sections"] if section["type"] == "textCardGrid" and section.get("eyebrow") == "For Whom"), None)
    require(targets is not None and len(targets["items"]) == 3, "target cards must have 3 items")
    features = next((section for section in data["sections"] if section.get("id") == "features"), None)
    require(features is not None and len(features["items"]) == 3, "feature cards must have 3 items")
    howto = next((section for section in data["sections"] if section["type"] == "orderedListWithInfo"), None)
    require(howto is not None and len(howto["steps"]) == 4, "howto must have 4 steps")
    require(howto is not None and len(howto["info"]["rows"]) == 4, "environment info must have 4 rows")
    video = next((section for section in data["sections"] if section["type"] == "videoPlaceholder"), None)
    require(video is not None and len(video["steps"]) == 5, "video steps must have 5 items")
    distribution = next((section for section in data["sections"] if section.get("id") == "distribution"), None)
    require(distribution is not None and len(distribution["items"]) == 3, "distribution cards must have 3 items")
    notes = next((section for section in data["sections"] if section["type"] == "noticeList"), None)
    require(notes is not None and len(notes["items"]) == 6, "notice list must have 6 items")
    require("PDF出力 / 印刷" in html, "print/PDF wording missing")
    require("画像なしでも崩れない掲載構成" in html, "placeholder explanation missing")


def validate_text_overlay(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"englishName", "vectorUrl", "images"}, "text-overlay root")
    validate_url(data["vectorUrl"], "vectorUrl")
    require(data["vectorUrl"] in html, "Vector URL missing from generated HTML")
    require(len(data["images"]) == 3, "text-overlay images must have 3 items")
    for src in data["images"]:
        validate_image_path(src, "text-overlay image")
        require(src in html, f"text-overlay image missing from HTML: {src}")
    section_types = [section["type"] for section in data["sections"]]
    require(
        section_types == ["pageHero", "imageText", "textCardGrid", "imageGallery", "downloadCta"],
        "text-overlay section order changed",
    )
    features = next((section for section in data["sections"] if section.get("id") == "howto"), None)
    require(features is not None and len(features["items"]) == 4, "feature cards must have 4 items")
    gallery = next((section for section in data["sections"] if section["type"] == "imageGallery"), None)
    require(gallery is not None and len(gallery["images"]) == 2, "gallery must have 2 images")
    require("10日間無料で試用" in html, "10-day trial wording missing")
    require("Vectorからダウンロード・購入" in html, "Vector button label missing")
    require('target="_blank"' in html and 'rel="noopener noreferrer"' in html, "external link attributes missing")
    forbidden = [
        "bantai3.booth.pm",
        "note.com",
        "github.com/bantai-education-design/",
        ".zip",
        ".exe",
    ]
    for value in forbidden:
        require(value not in html, f"forbidden distribution link found: {value}")
    require(html.count(data["vectorUrl"]) == 1, "Vector link count changed")


def validate_resume_generator(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"englishName", "images", "bodyClass"}, "resume-generator root")
    require("product-detail-resume" in data["bodyClass"], "resume body class missing")
    require("resume-generator-hero" in html, "resume hero class missing")
    require(len(data["images"]) == 3, "resume images must have 3 items")
    for src in data["images"]:
        validate_image_path(src, "resume image")
        require(src in html, f"resume image missing from HTML: {src}")
    section_types = [section["type"] for section in data["sections"]]
    require(
        section_types == ["hero", "splitTextCard", "textCardGrid", "splitListNotice", "imageGallery", "textCardGrid"],
        "resume section order changed",
    )
    features = next((section for section in data["sections"] if section.get("id") == "features"), None)
    require(features is not None and len(features["items"]) == 3, "resume feature cards must have 3 items")
    require(features is not None and len(features.get("extraGrids", [])[0]["items"]) == 2, "resume input/output cards must total 2")
    screenshots = next((section for section in data["sections"] if section.get("id") == "screenshots"), None)
    require(screenshots is not None and len(screenshots["images"]) == 2, "resume screenshot image grid must have 2 images")
    require(screenshots is not None and len(screenshots.get("extraImageGrids", [])[0]["images"]) == 1, "resume AI assistant image missing")
    distribution = next((section for section in data["sections"] if section.get("id") == "distribution"), None)
    require(distribution is not None and len(distribution["items"]) == 3, "resume distribution cards must have 3 items")
    require("BOOTH準備中" in html and "Vector準備中" in html and "ダウンロード準備中" in html, "distribution pending labels missing")
    require("外部API実行によるAI機能本体の確認は、現時点ではまだ未実施です。" in html, "AI external API caution missing")
    require("個人情報についての注意" in html, "personal information caution missing")
    require("GitHubリポジトリは private" in html, "private GitHub policy wording missing")
    forbidden = [
        "bantai3.booth.pm",
        "vector.co.jp",
        "github.com/",
        ".zip",
        ".exe",
    ]
    for value in forbidden:
        require(value not in html, f"forbidden live link or asset reference found: {value}")


def validate_banner_studio(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"englishName", "downloadUrl", "images"}, "banner-studio root")
    validate_url(data["downloadUrl"], "downloadUrl")
    require(data["downloadUrl"].startswith("/") and data["downloadUrl"].endswith(".zip"), "downloadUrl must be a local ZIP path")
    require((ROOT / data["downloadUrl"].lstrip("/")).exists(), "download ZIP file does not exist")
    require(data["downloadUrl"] in html, "download URL missing")
    require(html.count(data["downloadUrl"]) == 2, "download URL count changed")
    require(html.count("download=\"\"") == 2, "download attribute count changed")
    require(len(data["images"]) == 2, "banner-studio images must have 2 items")
    for src in data["images"]:
        validate_image_path(src, "banner-studio image")
        require(src in html, f"banner-studio image missing from HTML: {src}")
    section_types = [section["type"] for section in data["sections"]]
    require(
        section_types == [
            "hero",
            "imageText",
            "numberedTextList",
            "textCardGrid",
            "splitTextCard",
            "downloadCta",
            "narrowTextBox",
            "narrowTextBox",
        ],
        "banner-studio section order changed",
    )
    problems = next((section for section in data["sections"] if section["type"] == "numberedTextList"), None)
    require(problems is not None and len(problems["items"]) == 4, "problem list must have 4 items")
    howto = next((section for section in data["sections"] if section.get("id") == "howto"), None)
    require(howto is not None and len(howto["items"]) == 3, "howto cards must have 3 items")
    story = next((section for section in data["sections"] if section["type"] == "splitTextCard"), None)
    require(story is not None and len(story["card"]["bullets"]) == 6, "spec list must have 6 items")
    require("note記事から来てくださった方へ" in html, "article guidance section missing")
    require("ダウンロードできない場合" in html, "download warning section missing")
    forbidden = [
        "bantai3.booth.pm",
        "vector.co.jp",
        "github.com/",
    ]
    for value in forbidden:
        require(value not in html, f"forbidden external distribution link found: {value}")


def validate_staff_paper(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(
        data,
        {"englishName", "image", "imageAlt", "trialDownloadUrl", "boothUrl", "licenseRequestUrl"},
        "staff-paper root",
    )
    is_suspended = any(sec["type"] == "narrowTextBox" for sec in data["sections"])
    validate_image_path(data["image"], "staff-paper image")
    require(html.count(data["image"]) == 2, "staff-paper image reference count changed")
    require(data["imageAlt"] in html, "staff-paper image alt missing")
    validate_url(data["trialDownloadUrl"], "trialDownloadUrl")
    validate_url(data["boothUrl"], "boothUrl")
    validate_url(data["licenseRequestUrl"], "licenseRequestUrl")
    if is_suspended:
        require(html.count(data["trialDownloadUrl"]) == 0, "trial download URL count changed (suspended)")
        require(html.count(data["boothUrl"]) == 0, "BOOTH URL count changed (suspended)")
        require(html.count(data["licenseRequestUrl"]) >= 1, "license request URL count changed (suspended)")
        section_types = [section["type"] for section in data["sections"]]
        require(
            section_types == ["pageHero", "narrowTextBox", "downloadCta"],
            "staff-paper suspended sections mismatch"
        )
        require("新規案内を休止しています" in html, "suspension notice missing")
        require("購入後ライセンスキー申請" in html, "license request button missing")
    else:
        require(html.count(data["trialDownloadUrl"]) == 1, "trial download URL count changed")
        require(html.count(data["boothUrl"]) == 1, "BOOTH URL count changed")
        require(html.count(data["licenseRequestUrl"]) >= 1, "license request URL count changed")
        section_types = [section["type"] for section in data["sections"]]
        require(
            section_types == [
                "pageHero",
                "textCardGrid",
                "textCardGrid",
                "workflowSteps",
                "groupedNotice",
                "downloadCta",
            ],
            "staff-paper section order changed",
        )
        overview = data["sections"][1]
        require(len(overview["items"]) == 3, "overview quote cards must have 3 items")
        features = data["sections"][2]
        require(len(features["items"]) == 3, "feature cards must have 3 items")
        require(len(features["tableCards"]) == 1 and len(features["tableCards"][0]["rows"]) == 4, "spec table must have 4 rows")
        workflow = data["sections"][3]
        require(len(workflow["steps"]) == 7, "workflow must have 7 steps")
        notices = data["sections"][4]
        require(len(notices["groups"]) == 2, "license notice must have 2 groups")
        require(len(notices["groups"][0]["items"]) == 4, "trial notice must have 4 items")
        require(len(notices["groups"][1]["items"]) == 3, "product license notice must have 3 items")
        require("ライセンスキーなしで10日間試用" in html, "10-day trial step missing")
        require("SAMPLE透かし" in html, "SAMPLE watermark notice missing")
        require("個別ライセンスキー方式" in html, "individual license notice missing")
        require("購入後ライセンスキー申請" in html, "license request button missing")
        require(html.count('target="_blank"') == 3, "external target count changed")
    require(not re.search(r"<a\b[^>]*\brel=", html), "unexpected rel attribute added to staff paper links")
    require(not re.search(r"<a\b[^>]*\bdownload=", html), "unexpected download attribute added to staff paper links")
    forbidden = [
        "vector.co.jp",
        "note.com",
        "github.com/bantai-education-design/",
        "ClassRosterMaker",
        "BanTai_BannerStudio",
    ]
    for value in forbidden:
        require(value not in html, f"forbidden unrelated link or asset reference found: {value}")

def validate_first_staff_paper(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(
        data,
        {"englishName", "image", "imageAlt", "trialDownloadUrl", "boothUrl", "licenseRequestUrl"},
        "first-staff-paper root",
    )
    validate_image_path(data["image"], "first-staff-paper image")
    require(html.count(data["image"]) == 2, "first-staff-paper image reference count changed")
    require(data["imageAlt"] in html, "first-staff-paper image alt missing")
    validate_url(data["trialDownloadUrl"], "trialDownloadUrl")
    validate_url(data["boothUrl"], "boothUrl")
    validate_url(data["licenseRequestUrl"], "licenseRequestUrl")
    
    # Since it is published, verify active BOOTH link presence in download action buttons
    require("https://bantai3.booth.pm/items/8587307" in html, "first-staff-paper page must link to active BOOTH product")
    require("公開準備中" not in html, "first-staff-paper page must not mention 公開準備中")
    
    section_types = [section["type"] for section in data["sections"]]
    require(
        section_types == [
            "pageHero",
            "textCardGrid",
            "textCardGrid",
            "workflowSteps",
            "groupedNotice",
            "downloadCta",
        ],
        "first-staff-paper section order changed",
    )
    overview = data["sections"][1]
    require(len(overview["items"]) == 3, "overview quote cards must have 3 items")
    features = data["sections"][2]
    require(len(features["items"]) == 3, "feature cards must have 3 items")
    require(len(features["tableCards"]) == 1 and len(features["tableCards"][0]["rows"]) == 4, "spec table must have 4 rows")
    workflow = data["sections"][3]
    require(len(workflow["steps"]) == 7, "workflow must have 7 steps")
    notices = data["sections"][4]
    require(len(notices["groups"]) == 2, "license notice must have 2 groups")
    require(len(notices["groups"][0]["items"]) == 4, "trial notice must have 4 items")
    require(len(notices["groups"][1]["items"]) == 3, "product license notice must have 3 items")
    require("ライセンスキーなしで10日間試用" in html, "10-day trial step missing")
    require("SAMPLE透かし" in html, "SAMPLE watermark notice missing")
    require("個別ライセンスキー方式" in html, "individual license notice missing")
    
    forbidden = [
        "vector.co.jp",
        "note.com",
        "github.com/bantai-education-design/",
        "ClassRosterMaker",
        "BanTai_BannerStudio",
    ]
    for value in forbidden:
        require(value not in html, f"forbidden unrelated link or asset reference found: {value}")

def validate_id_photo(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"englishName", "sections"}, "id-photo root")
    require(len(parser.images) >= 6, "id-photo must have at least 6 images")

    # Check that booth link is present
    booth_url = "https://bantai3.booth.pm/items/8467855"
    require(booth_url in html, "BOOTH URL missing from generated HTML")
    require(html.count(booth_url) == 2, "BOOTH URL must appear exactly 2 times")

    # Check for duplicate preview image references
    preview_img = "/assets/images/id-photo/id-photo-hero-summary.png"
    require(html.count(preview_img) == 2, "Preview image must appear exactly 2 times (reproducing duplicate)")

    # Check sections
    section_types = [section["type"] for section in data["sections"]]
    require(
        section_types == [
            "hero",
            "imageText",
            "imageText",
            "textCardGrid",
            "imageText",
            "imageGallery",
            "narrowTextBox",
            "downloadCta",
        ],
        "id-photo section order changed",
    )

    # Check that duplication of "画面で確認しながら、印刷・保存へ。" is present
    require("画面で確認しながら、印刷・保存へ。" in html, "Preview heading missing")
    # Verify that the text appears twice in the DOM (under H2 headings)
    require(html.count("画面で確認しながら、印刷・保存へ。") == 2, "Preview heading must be duplicated exactly 2 times")


def validate_education_planning(data: dict, html: str, parser: DetailPageParser) -> None:
    require_keys(data, {"sections"}, "education-planning root")

    # 4 links: 1 Form, 3 Drive downloads
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLScIw2a5brKZL9XYWpqUj_l-vT7uU_ZvN-lEk_SyWe_hHfQaag/viewform"
    drive1 = "https://drive.google.com/file/d/1dvO680x5s4MQ1YLPXmXle1Rn0VdoyZSY/view?usp=drivesdk"
    drive2 = "https://drive.google.com/file/d/12VUsSOeWzdm3FA_zPe5yv1PwWV4GtaQ7/view?usp=drivesdk"
    drive3 = "https://drive.google.com/file/d/12teRmei80Y77NdUu9QrWIA6HZjRJ1jYS/view?usp=drivesdk"

    require(form_url in html, "Form URL missing")
    require(drive1 in html, "Drive URL 1 missing")
    require(drive2 in html, "Drive URL 2 missing")
    require(drive3 in html, "Drive URL 3 missing")

    # Check section order
    section_types = [section["type"] for section in data["sections"]]
    require(
        section_types == ["hero", "educationWorkflow", "textCardGrid", "downloadCta", "flowBrief"],
        "education-planning section order changed"
    )

    # Check headings
    require("小学校教育計画" in html, "Hero heading missing")
    require("年間計画から日々の週案、提出書類まで" in html, "Workflow heading missing")
    require("Excelシートではなく「専用アプリ」である利点" in html, "Excel vs App heading missing")
    require("Ver.5.70.7 モニター版 ダウンロード" in html, "Download heading missing")
    require("ご利用の流れ" in html, "Flow brief heading missing")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated product detail page.")
    parser.add_argument("slug", nargs="?", default="class-roster")
    args = parser.parse_args()

    data = load_data(args.slug)
    html_path = output_path(args.slug)
    require(html_path.exists(), f"generated HTML missing: {html_path.relative_to(ROOT)}")
    html = html_path.read_text(encoding="utf-8")
    expected_comment = f"GENERATED FILE: edit data/product-details/{args.slug}.json and templates/product-detail.html"
    page = DetailPageParser(expected_comment)
    page.feed(html)

    validate_common(args.slug, data, html, page)
    if args.slug == "class-roster":
        validate_class_roster(data, html, page)
    elif args.slug == "houganshi":
        validate_houganshi(data, html, page)
    elif args.slug == "kanji-practice":
        validate_kanji_practice(data, html, page)
    elif args.slug == "observation-card":
        validate_observation_card(data, html, page)
    elif args.slug == "text-overlay":
        validate_text_overlay(data, html, page)
    elif args.slug == "resume-generator":
        validate_resume_generator(data, html, page)
    elif args.slug == "banner-studio":
        validate_banner_studio(data, html, page)
    elif args.slug == "staff-paper":
        validate_staff_paper(data, html, page)
    elif args.slug == "first-staff-paper":
        validate_first_staff_paper(data, html, page)
    elif args.slug == "id-photo":
        validate_id_photo(data, html, page)
    elif args.slug == "education-planning":
        validate_education_planning(data, html, page)
    else:
        fail(f"unsupported product detail slug: {args.slug}")

    print(f"OK: {args.slug} detail page validated")


if __name__ == "__main__":
    main()
