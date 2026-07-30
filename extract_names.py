import re
html = open('tools/school-database/index.html', encoding='utf-8').read()
cards = re.findall(r'<a class=".*?pref-card.*?href=".*?/([^/]+)/?".*?<h2>(.*?)</h2>', html, re.DOTALL)
mapping = {}
for slug, name in cards:
    if slug == 'tokyo-school-address':
        slug = 'tokyo'
    mapping[slug] = name
print('Extracted:', len(mapping))
print(mapping)
