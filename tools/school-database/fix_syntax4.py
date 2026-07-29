import glob
import re

files = ['tools/school-database/convert_ishikawa_sources.py', 'tools/school-database/convert_fukui_sources.py', 'tools/school-database/convert_shiga_sources.py']
for f in files:
    content = open(f, encoding='utf-8').read()
    
    # We want to replace the broken df.columns = [c.replace(
    new_content = []
    for line in content.split('\n'):
        if 'df.columns = [c.replace(' in line:
            new_content.append('            df.columns = [c.replace("\\n", "").strip() for c in df.columns]')
        else:
            new_content.append(line)
            
    open(f, 'w', encoding='utf-8', newline='\n').write('\n'.join(new_content))
