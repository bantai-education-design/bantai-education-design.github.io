import re
html = open('tools/school-database/index.html', encoding='utf-8').read()
cards = re.findall(r'<a class="(.*?pref-card.*?)".*?href=".*?/([^/]+)/?".*?<h2>(.*?)</h2>', html, re.DOTALL)
print('Found:', len(cards))
for c in cards:
    if 'active-card' not in c[0]:
        print('Inactive:', c)
