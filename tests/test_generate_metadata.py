import os
import sys
import importlib.util

file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'school-database', 'generate_prefecture_metadata.py'))
spec = importlib.util.spec_from_file_location("generate_prefecture_metadata", file_path)
gm = importlib.util.module_from_spec(spec)
sys.modules["generate_prefecture_metadata"] = gm
spec.loader.exec_module(gm)

def test_process_prefecture_data():
    fake_data = [
        {"name": "School A", "establishment": "公立", "municipality": "City A", "school_type": "小学校"},
        {"school_name": "School B", "establishment_type": "私立", "municipality": "City B", "school_type": "中学校"},
        {"name": "School C", "establishment": "国立", "municipality": "", "school_type": "高等学校"},
        {"establishment": "公立", "municipality": "City A", "school_type": "小学校"},
        "bad_row",
        {"name": "School D", "municipality": "City C", "school_type": "特別支援学校"},
    ]
    
    meta = gm.process_prefecture_data(fake_data, "test_slug", "Test Prefecture")
    
    assert meta["total"] == 6, f"Expected 6, got {meta['total']}"
    assert meta["municipality_count"] == 3, f"Expected 3, got {meta['municipality_count']}"
    assert sum(meta["establishment_counts"].values()) == 5, f"Expected 5, got {sum(meta['establishment_counts'].values())}"
    assert len(meta["warnings"]) > 0, "Should have warnings"
    print("Test passed successfully.")

if __name__ == "__main__":
    test_process_prefecture_data()
