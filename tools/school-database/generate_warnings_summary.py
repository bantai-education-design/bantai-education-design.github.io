import json
meta = json.load(open('data/school-database/prefecture-metadata.json', encoding='utf-8'))
lines = []
lines.append("## Warning Summary")
for p in meta:
    if p['warnings']:
        lines.append(f"\n### {p['prefecture']} ({len(p['warnings'])} warnings)")
        for w in p['warnings'][:10]:
            lines.append(f"- {w}")
        if len(p['warnings']) > 10:
            lines.append(f"- ... (and {len(p['warnings']) - 10} more)")
with open('data/school-database/warnings_summary.md', 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print("Summary generated")
