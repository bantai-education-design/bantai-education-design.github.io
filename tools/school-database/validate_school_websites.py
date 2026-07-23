import json
import os
import re
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

repo_root = r"C:\Users\User\Documents\bantai-education-design.github.io"
saitama_json = os.path.join(repo_root, "data", "school-database", "saitama.json")
tokyo_json = os.path.join(repo_root, "data", "school-database", "tokyo.json")

# Top-level portal list URLs forbidden from being registered as individual school website
FORBIDDEN_PORTAL_EXACT_URLS = [
    'https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/search/name',
    'https://www.kyoiku.metro.tokyo.lg.jp/school/special_needs_school/school_list',
    'https://www.kyoiku.metro.tokyo.lg.jp/school/high_school/list',
    'https://www.pref.saitama.lg.jp/e2201/school01.html',
    'https://www.tokyoshigaku.com/schools/',
    'https://www.tokyoshigaku.com/'
]

def validate_dataset(filepath, name):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return 0, 0
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_schools = len(data)
    with_url = 0
    invalid_scheme = 0
    list_url_as_website = 0
    url_counts = {}
    url_schools = {}

    for school in data:
        url = school.get('website', '').strip()
        source_url = school.get('source_url', '').strip()
        
        if url:
            with_url += 1
            # Check scheme
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                invalid_scheme += 1
                print(f"[{name}] Invalid scheme detected in {school['school_name']}: {url}")
            
            # Check if list URL itself is registered as school website
            if (source_url and url == source_url) or url in FORBIDDEN_PORTAL_EXACT_URLS:
                list_url_as_website += 1
                print(f"[{name}] ERROR: Portal list URL registered as school website in {school['school_name']}: {url}")
            
            url_counts[url] = url_counts.get(url, 0) + 1
            if url not in url_schools:
                url_schools[url] = []
            url_schools[url].append(school['school_name'])

    # Check forbidden generic shared URLs (shared by > 4 schools or portal URLs)
    forbidden_shared = {}
    for url, count in url_counts.items():
        if count > 4 or url in FORBIDDEN_PORTAL_EXACT_URLS:
            forbidden_shared[url] = (count, url_schools[url])

    print(f"=== Board of Education Website Validation Report: {name} ===")
    print(f"Total schools: {total_schools}")
    print(f"Schools with verified official website: {with_url} ({(with_url/total_schools)*100:.1f}%)")
    print(f"Schools without website (blank): {total_schools - with_url}")
    print(f"Invalid schemes (non-http/https): {invalid_scheme}")
    print(f"List URL registered as school website: {list_url_as_website}")
    print(f"Forbidden generic portal shared URLs (>4 schools or top-level portal): {len(forbidden_shared)}")
    if forbidden_shared:
        for u, (c, schools) in forbidden_shared.items():
            print(f"  - {u} ({c} schools): {schools}")
    print("-" * 65)

    assert invalid_scheme == 0, f"[{name}] Invalid scheme error!"
    assert list_url_as_website == 0, f"[{name}] List URL registered as website error!"
    assert len(forbidden_shared) == 0, f"[{name}] Forbidden generic portal shared URLs error!"

    return total_schools, with_url

if __name__ == '__main__':
    s_tot, s_ver = validate_dataset(saitama_json, "Saitama Database")
    t_tot, t_ver = validate_dataset(tokyo_json, "Tokyo Database")

    print(f"\n[SUMMARY] Total Schools: {s_tot + t_tot}, Total Verified Official Websites: {s_ver + t_ver}")
    print("ALL BOARD OF EDUCATION VALIDATION CHECKS PASSED PERFECTLY!")
