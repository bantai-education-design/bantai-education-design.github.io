import json
import os
import re
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

repo_root = r"C:\Users\User\Documents\bantai-education-design.github.io"
saitama_json = os.path.join(repo_root, "data", "school-database", "saitama.json")
tokyo_json = os.path.join(repo_root, "data", "school-database", "tokyo.json")

def validate_dataset(filepath, name):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_schools = len(data)
    with_url = 0
    invalid_scheme = 0
    url_counts = {}

    for school in data:
        url = school.get('website', '').strip()
        if url:
            with_url += 1
            # Check scheme
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                invalid_scheme += 1
                print(f"[{name}] Invalid scheme detected in {school['school_name']}: {url}")
            
            url_counts[url] = url_counts.get(url, 0) + 1

    shared_urls = {u: c for u, c in url_counts.items() if c > 1}

    print(f"=== Website Validation Report: {name} ===")
    print(f"Total schools: {total_schools}")
    print(f"Schools with verified official website: {with_url} ({(with_url/total_schools)*100:.1f}%)")
    print(f"Schools without website (blank): {total_schools - with_url}")
    print(f"Invalid schemes (non-http/https): {invalid_scheme}")
    print(f"Shared URLs across multiple schools: {len(shared_urls)}")
    if shared_urls:
        for u, c in list(shared_urls.items())[:5]:
            print(f"  - {u}: {c} schools")
    print("-" * 50)

if __name__ == '__main__':
    validate_dataset(saitama_json, "Saitama Database")
    validate_dataset(tokyo_json, "Tokyo Database")
