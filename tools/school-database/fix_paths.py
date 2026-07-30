import os

base_dir = r'C:\Users\User\Documents\bantai-education-design.github.io\tools\school-database'
for f in ['convert_tottori_sources.py', 'convert_shimane_sources.py', 'convert_okayama_sources.py', 'convert_yamaguchi_sources.py', 'convert_hyogo_sources.py']:
    path = os.path.join(base_dir, f)
    with open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    text = text.replace('Path("data-source/mext")', 'Path("data-source/tochigi")')
    text = text.replace("Path('data-source/mext')", "Path('data-source/tochigi')")
    with open(path, 'w', encoding='utf-8') as file:
        file.write(text)
print('Fixed source paths.')
