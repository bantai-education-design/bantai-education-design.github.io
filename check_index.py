import re
html = open('tools/school-database/index.html', encoding='utf-8').read()
cards = re.findall(r'<a class="pref-card.*?href="(.*?)".*?<h2>(.*?)</h2>', html, re.DOTALL)
print('Total cards (links):', len(cards))
for c in cards[:5]: print(c)

divs = re.findall(r'<div class="pref-card.*?<h2>(.*?)</h2>', html, re.DOTALL)
print('Total inactive cards:', len(divs))
for d in divs[:5]: print(d)
