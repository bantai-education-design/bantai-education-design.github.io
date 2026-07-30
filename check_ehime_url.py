import re

html = open('tools/school-database/ehime/index.html', encoding='utf-8').read()
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>', html):
    url = m.group(1)
    if 'pref' in url or 'ehime' in url:
        print('URL is:', url)
