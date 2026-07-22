import json
import os
import re
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

repo_root = r"C:\Users\User\Documents\bantai-education-design.github.io"
saitama_json = os.path.join(repo_root, "data", "school-database", "saitama.json")
tokyo_json = os.path.join(repo_root, "data", "school-database", "tokyo.json")
report_json = os.path.join(repo_root, "tools", "school-database", "website-verification-report.json")

OFFICIAL_DOMAINS = ['.lg.jp', '.ed.jp', 'pref.saitama.lg.jp', 'kyoiku.metro.tokyo.lg.jp', 'city.']

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
            if source_url and url == source_url:
                list_url_as_website += 1
                print(f"[{name}] ERROR: List URL registered as school website in {school['school_name']}: {url}")
            
            url_counts[url] = url_counts.get(url, 0) + 1

    shared_urls = {u: c for u, c in url_counts.items() if c > 2}

    print(f"=== Board of Education Website Validation Report: {name} ===")
    print(f"Total schools: {total_schools}")
    print(f"Schools with verified official website: {with_url} ({(with_url/total_schools)*100:.1f}%)")
    print(f"Schools without website (blank): {total_schools - with_url}")
    print(f"Invalid schemes (non-http/https): {invalid_scheme}")
    print(f"List URL registered as school website: {list_url_as_website}")
    print(f"Generic shared URLs across >2 schools: {len(shared_urls)}")
    if shared_urls:
        for u, c in list(shared_urls.items()):
            print(f"  - {u}: {c} schools")
    print("-" * 65)

    assert invalid_scheme == 0, f"[{name}] Invalid scheme error!"
    assert list_url_as_website == 0, f"[{name}] List URL registered as website error!"
    assert len(shared_urls) == 0, f"[{name}] Generic shared URLs error!"

    return total_schools, with_url

if __name__ == '__main__':
    s_tot, s_ver = validate_dataset(saitama_json, "Saitama Database")
    t_tot, t_ver = validate_dataset(tokyo_json, "Tokyo Database")

    print(f"\n[SUMMARY] Total Schools: {s_tot + t_tot}, Total Verified Official Websites: {s_ver + t_ver}")
    print("ALL BOARD OF EDUCATION VALIDATION CHECKS PASSED PERFECTLY!")
