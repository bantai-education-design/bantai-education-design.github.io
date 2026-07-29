import os

base_dir = r'C:\Users\User\Documents\bantai-education-design.github.io\tools\school-database'

def fix_urls(pref, urls):
    p = os.path.join(base_dir, pref, 'index.html')
    if not os.path.exists(p): return
    text = open(p, 'r', encoding='utf-8').read()
    
    text = text.replace('href="https://kyoiku.pref.' + pref + '.jp/"', 'href="' + urls[0] + '"')
    text = text.replace('href="https://kyoiku.pref.' + pref + '.jp/about/survey/school-list/"', 'href="' + urls[1] + '"')
    text = text.replace('href="https://kyoiku.pref.' + pref + '.jp/gakko/private-schools/"', 'href="' + urls[2] + '"')
    
    open(p, 'w', encoding='utf-8', newline='\n').write(text)

fix_urls('ishikawa', [
    'https://www.pref.ishikawa.lg.jp/kyoiku/index.html',
    'https://www.pref.ishikawa.lg.jp/kyoiku/index.html',
    'https://www.pref.ishikawa.lg.jp/kyoiku/index.html'
])

fix_urls('fukui', [
    'https://www.pref.fukui.lg.jp/kyouiku/education/cat2001/index.html',
    'https://www.pref.fukui.lg.jp/kyouiku/education/cat2001/index.html',
    'https://www.pref.fukui.lg.jp/kyouiku/education/cat2001/index.html'
])

fix_urls('shiga', [
    'https://www.pref.shiga.lg.jp/edu/',
    'https://www.pref.shiga.lg.jp/edu/',
    'https://www.pref.shiga.lg.jp/edu/'
])
