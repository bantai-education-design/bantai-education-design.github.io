#!/usr/bin/env python3
"""公開ページのGA4計測と本人除外のそろい具合を点検する。

点検内容
1. GA4（gtag.js）を読み込むページは、本人除外（bantai_admin）の判定を gtag('config') より前に持つこと
2. コラムの個別ページ（columns/<slug>/index.html）は GA4 を読み込むこと

--fix を付けると、足りないページに標準の計測コードを差し込む。
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEASUREMENT_ID = "G-KPGJ0R2KXR"
GTAG_SRC = f"https://www.googletagmanager.com/gtag/js?id={MEASUREMENT_ID}"
SKIP_DIRS = {".git", "node_modules", "drafts", "scratch", "templates", "tests"}

# トップページなどと同じ判定。?bantai_admin=true で開いたブラウザは以後送信しない（?bantai_admin=clear で解除）
EXCLUSION = (
    "<script>(function(){try{var u=new URL(location.href),a=u.searchParams.get('bantai_admin');"
    "if(a==='true')localStorage.setItem('bantai_admin','true');else if(a==='clear')localStorage.removeItem('bantai_admin');"
    "if(a!==null){u.searchParams.delete('bantai_admin');var s=u.searchParams.toString();"
    "history.replaceState(null,'',u.pathname+(s?'?'+s:'')+u.hash);}}catch(e){}"
    "var l=location.hostname==='localhost'||location.hostname==='127.0.0.1'||location.protocol==='file:',x=false;"
    "try{x=localStorage.getItem('bantai_admin')==='true';}catch(e){}"
    f"if(l||x)window['ga-disable-{MEASUREMENT_ID}']=true;}})();</script>"
)
FULL_TAG = (
    "<!-- Google tag (gtag.js) -->"
    + EXCLUSION
    + f'<script async src="{GTAG_SRC}"></script>'
    + "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}"
    + f"gtag('js',new Date());gtag('config','{MEASUREMENT_ID}');</script>"
)
CONFIG_RE = re.compile(r"gtag\(\s*['\"]config['\"]")


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        yield rel, p


def is_column_page(rel):
    return len(rel.parts) == 3 and rel.parts[0] == "columns" and rel.name == "index.html"


def check(text, rel):
    problems = []
    has_gtag = "googletagmanager.com/gtag/js" in text
    if is_column_page(rel) and not has_gtag:
        problems.append("no_ga")
    if has_gtag:
        m = CONFIG_RE.search(text)
        ex = text.find("bantai_admin")
        if ex < 0 or (m and ex > m.start()):
            problems.append("no_exclusion")
    return problems


def fix(text, problems):
    if "no_ga" in problems:
        return text.replace("</head>", FULL_TAG + "</head>", 1)
    if "no_exclusion" in problems:
        i = text.find('<script async src="https://www.googletagmanager.com/gtag/js')
        return text[:i] + EXCLUSION + text[i:]
    return text


def main():
    do_fix = "--fix" in sys.argv
    bad = []
    for rel, p in pages():
        text = p.read_text(encoding="utf-8")
        problems = check(text, rel)
        if not problems:
            continue
        if do_fix:
            new = fix(text, problems)
            if check(new, rel):
                print(f"直せませんでした: {rel} {problems}")
                bad.append(rel)
                continue
            p.write_text(new, encoding="utf-8")
            print(f"修正: {rel} {problems}")
        else:
            print(f"要修正: {rel} {problems}")
            bad.append(rel)
    if bad:
        print(f"{len(bad)} ページに問題があります。python3 scripts/check_ga_tracking.py --fix で直せます。")
        return 1
    print("GA4計測と本人除外：問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
