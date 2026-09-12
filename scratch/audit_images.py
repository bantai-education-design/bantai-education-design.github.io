import json
import os
import re

columns_file = r"C:\Users\User\.gemini\antigravity\scratch\bantai-education-design.github.io\data\columns.json"

with open(columns_file, "r", encoding="utf-8") as f:
    columns = json.load(f)

image_refs = []
for c in columns:
    cid = c.get("id")
    title = c.get("title")
    thumb = c.get("thumbnail")
    if thumb:
        image_refs.append((cid, title, "thumbnail", thumb))
    content = c.get("content", "")
    imgs = re.findall(r'src=["\']([^"\']+)["\']', content)
    for img in imgs:
        image_refs.append((cid, title, "inline", img))

print(f"Total image references found across {len(columns)} columns: {len(image_refs)}")
for cid, title, itype, img in image_refs:
    print(f"[{cid}] ({itype}): {img}")
