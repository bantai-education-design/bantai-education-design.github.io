import os
import sys
import importlib.util
import re

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'school-database', 'generate_prefecture_metadata.py'))
spec = importlib.util.spec_from_file_location("generate_prefecture_metadata", file_path)
gm = importlib.util.module_from_spec(spec)
sys.modules["generate_prefecture_metadata"] = gm
spec.loader.exec_module(gm)

def test_process_prefecture_data():
    fake_data = [
        {"name": "School A", "establishment": "国", "municipality": "City A", "school_type": "小学校"},
        {"school_name": "School B", "establishment_type": "公", "municipality": "City B", "school_type": "中学校"},
        {"name": "School C", "establishment": "私", "municipality": "", "school_type": "高等学校"},
        {"establishment": "公", "municipality": "City A", "school_type": "幼稚園"},
        "bad_row",
        {"name": "School D", "municipality": "City C", "school_type": "特別支援学校"},
    ]
    
    meta, warnings = gm.process_prefecture_data(fake_data, "test_slug", "Test Prefecture")
    
    assert meta["total"] == 6, f"Expected 6, got {meta['total']}"
    assert meta["municipality_count"] == 3, f"Expected 3, got {meta['municipality_count']}"
    assert sum(meta["establishment_counts"].values()) == 5, f"Expected 5, got {sum(meta['establishment_counts'].values())}"
    assert len(warnings) > 0, "Should have warnings"
    print("Test passed successfully.")


def test_html_structure():
    with open("tools/school-database/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # 1. 8 regions
    regions = re.findall(r'<h3 class="region-header[^"]*">(.*?)</h3>', html)
    assert len(regions) == 8, f"Expected 8 regions, got {len(regions)}"
    
    # 2. 47 prefectures total
    cards = re.findall(r'<a class="[^"]*pref-card[^"]*".*?<h2>(.*?)</h2>', html, re.DOTALL)
    assert len(cards) == 47, f"Expected 47 cards, got {len(cards)}"
    assert len(set(cards)) == 47, "Expected 47 unique prefectures"
    
    # 3. Check specific leading prefectures per region
    blocks = html.split('<h3 class="region-header')
    
    for block in blocks[1:]:
        region_name = re.search(r'[^>]*>(.*?)</h3>', block).group(1)
        first_pref = re.search(r'<h2>(.*?)</h2>', block).group(1)
        
        if region_name == "関東地方":
            assert first_pref == "東京都", f"Expected 東京都 to lead 関東地方, got {first_pref}"
        elif region_name == "中部地方":
            assert first_pref == "愛知県", f"Expected 愛知県 to lead 中部地方, got {first_pref}"
        elif region_name == "近畿地方":
            assert first_pref == "大阪府", f"Expected 大阪府 to lead 近畿地方, got {first_pref}"
        elif region_name == "中国地方":
            assert first_pref == "広島県", f"Expected 広島県 to lead 中国地方, got {first_pref}"
        elif region_name == "四国地方":
            assert first_pref == "香川県", f"Expected 香川県 to lead 四国地方, got {first_pref}"
        elif region_name == "九州・沖縄地方":
            assert first_pref == "福岡県", f"Expected 福岡県 to lead 九州・沖縄地方, got {first_pref}"

    # 4. Check links
    assert 'href="/tools/tokyo-school-address/"' in html, "Tokyo link missing"
    assert 'href="/tools/school-database/saitama/"' in html, "Saitama link missing"
    
    # 5. Check commas in numbers (e.g. 1,000)
    comma_numbers = re.findall(r'<span class="meta-value">([0-9,]+)</span>', html)
    has_comma = any("," in n for n in comma_numbers)
    assert has_comma, "Expected commas in numbers but found none!"
    
    
    # 6. Check that old phrases are completely removed from the card body area
    # Note: the cards area is between <!-- DATABASE_CARDS_START --> and <!-- DATABASE_CARDS_END -->
    m = re.search(r'<!-- DATABASE_CARDS_START -->(.*?)<!-- DATABASE_CARDS_END -->', html, re.DOTALL)
    assert m is not None, "Could not find DATABASE_CARDS_START and END"
    cards_html = m.group(1)
    
    old_phrases = [
        "国公私立の幼稚園",
        "市部・郡部",
        "市町村・校種",
        "宛名コピー",
        "CSV",
        "Google Maps連携"
    ]
    for phrase in old_phrases:
        assert phrase not in cards_html, f"Old phrase '{phrase}' found in cards_html!"
        
    # 7. Check that new phrases appear exactly 47 times in the cards area
    new_phrases = [
        "収録校・園",
        "対象地域",
        "設置区分",
        "校種"
    ]
    for phrase in new_phrases:
        count = cards_html.count(f'<span class="meta-label">{phrase}</span>')
        assert count == 47, f"Expected 47 instances of '{phrase}', got {count}"

    print("HTML Structure tests passed successfully.")

if __name__ == "__main__":
    test_process_prefecture_data()
    test_html_structure()
