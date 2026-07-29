import glob

for p in glob.glob('tools/school-database/convert_*_sources.py'):
    text = open(p, encoding='utf-8').read()
    
    # Let's just fix the specific line
    new_text = []
    for line in text.split('\n'):
        if "df.columns = [c.replace('" in line and len(line) < 40:
            # this is the broken line: df.columns = [c.replace('
            continue
        if "df.columns = [c.replace(" in line:
            new_text.append('            df.columns = [c.replace("\\n", "").strip() for c in df.columns]')
            continue
        new_text.append(line)
        
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(new_text))
