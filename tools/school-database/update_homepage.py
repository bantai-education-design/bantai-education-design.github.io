import os
path = 'index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = '<p style="color:rgba(255,255,255,0.8); font-size:0.86rem; line-height:1.75; margin:0 0 20px;">各都道府県教育委員会等の'
end_marker = '          <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:10px;">'
start_idx = text.find(start_marker)
end_idx = text.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_html = '''<p style="color:rgba(255,255,255,0.8); font-size:0.86rem; line-height:1.75; margin:0 0 20px;">文部科学省のデータおよび各都道府県教育委員会等の公式公開データをもとに、全国の学校・園の住所や電話番号をデータベース化しています（都道府県ごとに順次対応中）。自治体・学校種・設置区分で絞り込み、封筒宛名コピーやCSVダウンロード、Google Maps連携が可能です。</p>

          <!-- 収録範囲 -->
          <div style="margin-bottom:24px; padding:16px; background:rgba(0,0,0,0.25); border-radius:8px; border:1px solid rgba(197,160,89,0.3);">
            <div style="font-size:0.85rem; font-weight:bold; color:var(--gold2); margin-bottom:10px;">✅ 収録対象の学校種別（国・公・私立対応）</div>
            <div style="font-size:0.8rem; color:rgba(255,255,255,0.85); line-height:1.6;">
              幼稚園 ／ 小学校 ／ 中学校 ／ 義務教育学校 ／ 高等学校 ／ 中等教育学校 ／ 特別支援学校
            </div>
          </div>

'''
    new_text = text[:start_idx] + new_html + text[end_idx:]
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_text)
    print('Updated successfully')
else:
    print('Markers not found')
