import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'school-database'))

from build_perfect_mext_2025_from_estat_tables import main

if __name__ == '__main__':
    main()
