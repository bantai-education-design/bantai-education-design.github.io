import glob
import re

for pref in ['toyama', 'tokushima', 'ehime', 'kochi', 'kagawa']:
    path = f'tools/school-database/{pref}/index.html'
    try:
        html = open(path, encoding='utf-8').read()
        for m in re.finditer(r'href="(https?://[^"]+)"', html):
            url = m.group(1)
            if 'pref' in url:
                print(f'{pref}: {url}')
    except Exception as e:
        pass
