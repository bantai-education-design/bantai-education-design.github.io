import re
html = open('tools/school-database/kagawa/index.html', encoding='utf-8').read()
m = re.search(r'(<a[^>]*href=\"https?://www\.pref\.kagawa\.lg\.jp/[^\"]+\"[^>]*>)', html)
if m: print(m.group(1))
