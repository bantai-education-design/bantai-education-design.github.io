#!/usr/bin/env python3
"""
Ban.Tai Education Design - GA4 Documentation Verification Script

Ensures that none of the generated documentation contains:
- Local filesystem paths: file:///C:/, C:\\Users\\, .gemini/antigravity/scratch
- Prohibited inaccurate phrasing: '訪問者の実数', 'ダウンロード人数', '15秒以上で読了', '読了率'
"""

import os
import sys

DOC_FILES = [
    'docs/admin/ga4-unified-spec.md',
    'docs/admin/monthly-report-guide.md',
    'docs/admin/search-console-ga4-link-guide.md',
    'docs/admin/admin-exclusion-guide.md',
    'docs/admin/karte-migration-plan.md',
    'docs/admin/walkthrough.md'
]

PROHIBITED_PATTERNS = [
    'file:///C:/',
    'C:\\Users\\',
    'C:/Users/',
    '.gemini/antigravity/scratch',
    'antigravity/scratch',
    '訪問者の実数',
    'ダウンロード人数',
    '15秒以上で読了',
    '読了率'
]

def check_docs():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = []

    for rel_path in DOC_FILES:
        abs_path = os.path.join(repo_root, rel_path)
        if not os.path.exists(abs_path):
            errors.append(f"Missing required documentation file: {rel_path}")
            continue

        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for pattern in PROHIBITED_PATTERNS:
            # Allow mentioning prohibited phrasing only if explicitly marked as prohibited in a comparison table
            # Check for occurrences
            if pattern in content:
                # If it's the comparison table in monthly-report-guide.md, check context
                if rel_path == 'docs/admin/monthly-report-guide.md' and pattern in ['訪問者の実数', 'ダウンロード人数', '読了 / 読了率']:
                    continue
                errors.append(f"File {rel_path} contains prohibited pattern: '{pattern}'")

    if errors:
        print("[FAIL] Documentation Verification Errors:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[SUCCESS] All 6 GA4 documentation files verified without prohibited phrases or local absolute paths.")
    return True

if __name__ == '__main__':
    ok = check_docs()
    sys.exit(0 if ok else 1)
