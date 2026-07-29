import re
import urllib.request

for pref in ['aomori', 'akita']:
    print(f'--- {pref.upper()} ---')
    try:
        with open(f'tools/school-database/{pref}/index.html', encoding='utf-8') as f:
            html = f.read()
        matches = re.findall(r'<a class="edu-portal-card" href="(.*?)"', html)
        for url in matches:
            print(f"URL: {url}")
            try:
                urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}))
                print("  -> OK")
            except Exception as e:
                print(f"  -> ERROR: {e}")
    except Exception as e:
        print(f"File error: {e}")
