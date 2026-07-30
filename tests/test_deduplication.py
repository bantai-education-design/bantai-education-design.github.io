# coding: utf-8
import sys
import os
import importlib.util
from pathlib import Path
import json
import tempfile

# Dynamically load the module because of '-' in the folder name
spec = importlib.util.spec_from_file_location("clean_duplicates", "tools/school-database/clean_duplicates.py")
clean_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean_mod)
clean_file = clean_mod.clean_file

def test_deduplication():
    # Mock data covering all scenarios
    data = [
        # 1. 完全一致2件 -> 1件になる
        {"id": "1", "prefecture": "東京都", "municipality": "港区", "name": "テスト第一", "school_type": "小学校", "establishment": "公立", "postal_code": "100", "address": "東京都港区1", "phone": "03-1111", "operator": "A", "course": []},
        {"id": "2", "prefecture": "東京都", "municipality": "港区", "name": "テスト第一", "school_type": "小学校", "establishment": "公立", "postal_code": "100", "address": "東京都港区1", "phone": "03-1111", "operator": "A", "course": []},

        # 2. 同名だが住所が違う -> 2件残る
        {"id": "3", "prefecture": "東京都", "municipality": "港区", "name": "テスト第二", "school_type": "小学校", "establishment": "公立", "postal_code": "100", "address": "東京都港区2", "phone": "03-2222", "operator": "B", "course": []},
        {"id": "4", "prefecture": "東京都", "municipality": "港区", "name": "テスト第二", "school_type": "小学校", "establishment": "公立", "postal_code": "100", "address": "東京都港区3", "phone": "03-2222", "operator": "B", "course": []},

        # 3. 同名・同住所だが電話番号が違う -> 2件残る
        {"id": "5", "prefecture": "東京都", "municipality": "港区", "name": "テスト第三", "school_type": "小学校", "establishment": "公立", "postal_code": "100", "address": "東京都港区4", "phone": "03-3333", "operator": "C", "course": []},
        {"id": "6", "prefecture": "東京都", "municipality": "港区", "name": "テスト第三", "school_type": "小学校", "establishment": "公立", "postal_code": "100", "address": "東京都港区4", "phone": "03-4444", "operator": "C", "course": []},

        # 4. 同一校でcourseが違う (電話番号同じ) -> 統合される (Option B)
        {"id": "7", "prefecture": "東京都", "municipality": "港区", "name": "テスト第四", "school_type": "高等学校", "establishment": "私立", "postal_code": "100", "address": "東京都港区5", "phone": "03-5555", "operator": "D", "course": ["全日制"]},
        {"id": "8", "prefecture": "東京都", "municipality": "港区", "name": "テスト第四", "school_type": "高等学校", "establishment": "私立", "postal_code": "100", "address": "東京都港区5", "phone": "03-5555", "operator": "D", "course": ["通信制"]},

        # 5. 武蔵台学園の別施設 -> 2件残る
        {"id": "9", "prefecture": "東京都", "municipality": "府中市", "name": "東京都立武蔵台学園", "school_type": "特別支援学校", "establishment": "公立", "postal_code": "183-0042", "address": "東京都府中市武蔵台2-8-28", "phone": "042-324-1111", "operator": "", "course": []},
        {"id": "10", "prefecture": "東京都", "municipality": "府中市", "name": "東京都立武蔵台学園", "school_type": "特別支援学校", "establishment": "公立", "postal_code": "183-0042", "address": "東京都府中市武蔵台2-8-29(都立小児総合医療ｾﾝﾀｰ)", "phone": "042-312-8115", "operator": "", "course": []},
    ]

    saitama_data = [
        # 6. 埼玉県のヘッダー残骸 -> 除外
        {"id": "11", "prefecture": "埼玉県", "municipality": "", "school_name": "さいたま市", "school_type": "小学校", "establishment_type": "私立", "postal_code": "", "address": "", "phone": "", "operator": ""}
    ]

    # Create dummy files
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
        json.dump(data, f)
        tokyo_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
        json.dump(saitama_data, f)
        saitama_path = f.name

    try:
        clean_file(Path(tokyo_path), tokyo_kanagawa_fukushima_miyagi=True)
        clean_file(Path(saitama_path), is_saitama=True)

        with open(tokyo_path, encoding='utf-8') as f:
            tokyo_result = json.load(f)
        
        with open(saitama_path, encoding='utf-8') as f:
            saitama_result = json.load(f)
            
        print("Tests passing...")
        
        # 1.
        t1 = [r for r in tokyo_result if r["name"] == "テスト第一"]
        assert len(t1) == 1, "完全一致2件 -> 1件になる failed"
        
        # 2.
        t2 = [r for r in tokyo_result if r["name"] == "テスト第二"]
        assert len(t2) == 2, "同名だが住所が違う -> 2件残る failed"

        # 3.
        t3 = [r for r in tokyo_result if r["name"] == "テスト第三"]
        assert len(t3) == 2, "同名・同住所だが電話番号が違う -> 2件残る failed"

        # 4.
        t4 = [r for r in tokyo_result if r["name"] == "テスト第四"]
        assert len(t4) == 1, "同一校でcourseが違う -> 統合 failed"
        assert set(t4[0]["course"]) == {"全日制", "通信制"}, "course merged content failed"

        # 5.
        t5 = [r for r in tokyo_result if r["name"] == "東京都立武蔵台学園"]
        assert len(t5) == 2, "武蔵台学園の別施設 -> 2件残る failed"

        # 6.
        assert len(saitama_result) == 0, "埼玉県のヘッダー残骸 -> 除外 failed"

        print("All tests passed!")
    finally:
        os.remove(tokyo_path)
        os.remove(saitama_path)

if __name__ == '__main__':
    test_deduplication()
