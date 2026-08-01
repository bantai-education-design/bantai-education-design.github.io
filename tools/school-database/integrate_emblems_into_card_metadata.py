#!/usr/bin/env python3
"""Add an `emblem` (prefectural crest / official symbol mark) block to every
prefecture entry in data/school-database/prefecture-card-metadata.json.

Per docs/school-database/prefecture-emblems-source-manifest.md, only 47
prefectures were surveyed and only 1 (Toyama) had an official mark that is
confirmed freely usable (no prior approval/application required). All other
46 prefectures are marked `{"available": false}` — no placeholder image, no
guessed mark, no third-party source.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD_METADATA_PATH = ROOT / "data" / "school-database" / "prefecture-card-metadata.json"

# Only prefectures with a confirmed, officially-licensed mark go here.
# alt="" is used uniformly (decorative): the prefecture name is already
# rendered as visible text (<h2>) immediately next to the mark, so a screen
# reader re-announcing the name via the image's alt text would be redundant.
EMBLEMS = {
    "toyama": {
        "available": True,
        "name": "富山県新観光シンボルマーク",
        "src": "/assets/images/prefecture-emblems/16-toyama.png",
        "official_source_url": "https://www.pref.toyama.jp/810111/miryokukankou/kankoutokusan/kankou/kj00005907.html",
        "alt": "",
    },
}

UNAVAILABLE = {"available": False}


def main() -> None:
    payload = json.loads(CARD_METADATA_PATH.read_text(encoding="utf-8"))

    payload.setdefault(
        "emblem_policy",
        {
            "no_dummy_values": True,
            "no_unofficial_sources": True,
            "alt_policy": "decorative (alt=\"\") — prefecture name is already visible as adjacent text",
            "unavailable_shape": UNAVAILABLE,
        },
    )

    seen_codes = set()
    for pref in payload["prefectures"]:
        code = pref["prefecture_code"]
        seen_codes.add(code)
        pref["emblem"] = EMBLEMS.get(code, dict(UNAVAILABLE))

    missing_emblem_targets = set(EMBLEMS) - seen_codes
    if missing_emblem_targets:
        raise ValueError(f"emblem defined for unknown prefecture_code: {missing_emblem_targets}")

    available_count = sum(1 for pref in payload["prefectures"] if pref["emblem"]["available"])
    print(f"emblem available for {available_count}/{len(payload['prefectures'])} prefectures")

    CARD_METADATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {CARD_METADATA_PATH}")


if __name__ == "__main__":
    main()
