import os
base_dir = r"C:\Users\User\Documents\bantai-education-design.github.io"
files = [
    "tools/school-database/convert_fukui_sources.py",
    "tools/school-database/convert_shiga_sources.py"
]
for p in files:
    full_path = os.path.join(base_dir, p)
    with open(full_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # We want to delete any line that ends with "df.columns = [c.replace(" or contains it and the next line
    lines = text.split('\n')
    new_lines = []
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        if 'df.columns = [c.replace(' in line and line.strip().endswith('replace("'):
            new_lines.append('            df.columns = [c.replace("\\n", "").strip() for c in df.columns]')
            skip_next = True
        elif 'df.columns = [c.replace(' in line and 'for c in df.columns]' not in line:
             new_lines.append('            df.columns = [c.replace("\\n", "").strip() for c in df.columns]')
             skip_next = True
        elif '", "").strip() for c in df.columns]' in line:
            pass # Skip orphan line
        else:
            new_lines.append(line)
            
    with open(full_path, "w", encoding="utf-8", newline='\n') as f:
        f.write('\n'.join(new_lines))
