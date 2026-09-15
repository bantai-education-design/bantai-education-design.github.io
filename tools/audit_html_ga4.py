#!/usr/bin/env python3
"""
Ban.Tai Education Design - GA4 Implementation & Page Classification Audit

Verifies:
1. Total tracked HTML file count is exactly 98.
2. Classification breakdown:
   - Public (GA4 Target): 88 files
   - Admin (GA4 Excluded): 6 files
   - Templates (GA4 Excluded): 3 files
   - Verification/Redirect (GA4 Excluded): 1 file
3. Public pages have uniform Pre-config Inline Exclusion GA4 snippet and analytics-events.js.
4. Non-public pages have NO GA4 tracking script.
5. No public visitor counter exists.
"""

import os
import subprocess
import sys

NON_PUBLIC_MAP = {
    'templates/product-card.html': 'テンプレート・GA4対象外',
    'templates/product-detail.html': 'テンプレート・GA4対象外',
    'templates/products-page.html': 'テンプレート・GA4対象外',
    'index-new.html': '検証用・GA4対象外',
    'admin/index.html': '管理・GA4対象外',
    'admin/review-editor.html': '管理・GA4対象外',
    'tools/university-database/tokyo/photo-admin/index.html': '管理・GA4対象外',
    'tools/university-database/tokyo/photo-register/index.html': '管理・GA4対象外',
    'tools/university-database/tokyo/photo-register/public-simple.html': '管理・GA4対象外',
    'tools/university-database/tokyo/photo-submit/index.html': '管理・GA4対象外',
}

GA4_REQUIRED_STRINGS = [
    'https://www.googletagmanager.com/gtag/js?id=G-KPGJ0R2KXR',
    'bantai_ga_disable',
    "window['ga-disable-G-KPGJ0R2KXR'] = true",
    "gtag('config', 'G-KPGJ0R2KXR')",
    '/assets/js/analytics-events.js'
]

def audit():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracked_files = subprocess.check_output(
        ['git', 'ls-files', '*.html'],
        cwd=repo_root,
        text=True
    ).strip().splitlines()

    total_count = len(tracked_files)
    print(f"[1] Total Tracked HTML Files: {total_count}")
    if total_count != 98:
        print(f"FAIL: Expected 98 tracked HTML files, found {total_count}")
        return False

    public_files = []
    admin_files = []
    template_files = []
    verification_files = []

    for rel_path in tracked_files:
        norm_path = rel_path.replace('\\', '/')
        category = NON_PUBLIC_MAP.get(norm_path)
        if category == '管理・GA4対象外':
            admin_files.append(norm_path)
        elif category == 'テンプレート・GA4対象外':
            template_files.append(norm_path)
        elif category == '検証用・GA4対象外':
            verification_files.append(norm_path)
        else:
            public_files.append(norm_path)

    print(f"[2] Classification Count Check:")
    print(f"  - 公開・GA4対象: {len(public_files)} (expected: 88)")
    print(f"  - 管理・GA4対象外: {len(admin_files)} (expected: 6)")
    print(f"  - テンプレート・GA4対象外: {len(template_files)} (expected: 3)")
    print(f"  - 検証用・GA4対象外: {len(verification_files)} (expected: 1)")
    classification_sum = len(public_files) + len(admin_files) + len(template_files) + len(verification_files)
    print(f"  - 分類合計: {classification_sum} (一致確認: {classification_sum == total_count})")

    if (len(public_files) != 88 or len(admin_files) != 6 or 
        len(template_files) != 3 or len(verification_files) != 1):
        print("FAIL: Classification count mismatch!")
        return False

    errors = []

    # Verify Public Files
    for pf in public_files:
        abs_path = os.path.join(repo_root, pf)
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for req in GA4_REQUIRED_STRINGS:
            if req not in content:
                errors.append(f"Public file {pf} missing required string: {req}")

    # Verify Non-Public Files
    non_public_all = admin_files + template_files + verification_files
    for npf in non_public_all:
        abs_path = os.path.join(repo_root, npf)
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'googletagmanager.com/gtag/js' in content or 'G-KPGJ0R2KXR' in content:
            errors.append(f"Non-public file {npf} should NOT contain GA4 tag!")

    # Verify No Public Visitor Counter
    for pf in public_files:
        abs_path = os.path.join(repo_root, pf)
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'pv-counter' in content.lower() or 'access-counter' in content.lower():
            errors.append(f"File {pf} contains unexpected visitor counter element")

    if errors:
        print("\n[Audit Errors]")
        for e in errors:
            print(f"  ERROR: {e}")
        return False

    print("\nSUCCESS: All 98 HTML files correctly audited and classified.")
    return True

if __name__ == '__main__':
    ok = audit()
    sys.exit(0 if ok else 1)
