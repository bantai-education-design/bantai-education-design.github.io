from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "detail": ROOT / "products/education-planning/index.html",
    "overview": ROOT / "monitor/index.html",
    "download": ROOT / "products/education-planning/monitor-download/index.html",
    "adjusted": ROOT / "products/education-planning/adjusted/index.html",
}

def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")

text = {k: p.read_text(encoding="utf-8") for k, p in FILES.items()}

download = text["download"]
adjusted = text["adjusted"]
detail = text["detail"]
overview = text["overview"]

# Current normal monitor assets
require("Ver.5.70.12" in download, "normal monitor version missing")
require("48b39454252b68f15ac1c36cdb7f2d22c5d75277d4c3272c4f09f5ebb94f1315" in download, "support SHA-256 missing")
require("40dd1486d8bf233d378cda883ec4248875ba661fae713c5fa3e0996b5f36d0a2" in download, "weekplan SHA-256 missing")
require("2027年3月31日" in download, "normal monitor deadline missing")
require("https://www.vector.co.jp/soft/winnt/edu/se528971.html" in download, "support Vector link missing")
require("https://www.vector.co.jp/soft/winnt/edu/se528974.html" in download, "weekplan Vector link missing")

# Adjusted monitor candidate
require("Ver.1.0.6" in download, "adjusted version missing")
require("ddb6466ea032413e7fa17479e49ee730c57acd6fc433fb5634c496afaed4730b" in download, "adjusted SHA-256 missing")
require("2027年8月31日" in download, "adjusted monitor deadline missing")
require("verify:setup" in download, "adjusted local release gate missing")
require("2027年8月31日" in adjusted, "adjusted detail deadline missing")
require("制度未確定" in adjusted, "adjusted policy wording missing")

# Navigation and distribution policy
monitor_path = "/products/education-planning/monitor-download/"
require(monitor_path in detail, "detail page does not link monitor download page")
require(monitor_path in overview, "monitor overview does not link monitor download page")
require("公式HP" in download and "Vector" in download, "dual distribution wording missing")
require("BOOTH" in download, "BOOTH product route missing")

# Old distribution wording must not return
all_public = "\n".join(text.values())
for stale in [
    "https://bantai3.booth.pm/items/8547376",
    "Ver.5.70.7 モニター版ダウンロード",
    "固定ライセンスキー",
    "無料モニター登録",
    "モニター用ライセンスキー",
]:
    require(stale not in all_public, f"stale wording remains: {stale}")

# Normal monitor direct-download links must be present and point to verified release
require("releases/download/education-monitor-v5.70.12/bantai_kyomu_support_monitor_v5.70.12.zip" in download, "normal support direct link missing")
require("releases/download/education-monitor-v5.70.12/bantai_weekplan_monitor_v5.70.12.zip" in download, "normal weekplan direct link missing")
require("releases/download/education-monitor-v5.70.12/bantai_education_planning_monitor_manual_v5.70.12.pdf" in download, "normal manual direct link missing")

# Adjusted monitor candidate must remain staged before verify:setup completes
require("releases/download/adjusted-monitor-v1.0.6/" not in download, "adjusted direct Release links enabled before asset verification")
require("最終確認中" in download, "adjusted release gate should remain visible")

print("PASS: monitor distribution pages are consistent with staged release policy")
