import glob, json, os
files = glob.glob('data/school-database/*.json')
prefectures = []
for f in files:
    name = os.path.basename(f)
    if name in ('prefectures.json', 'prefecture-metadata-pilot.json', 'prefecture-metadata.json'): continue
    
    try:
        data = json.load(open(f, encoding='utf-8'))
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            prefectures.append(name.replace('.json', ''))
    except Exception as e:
        pass
print('Found:', len(prefectures))
print(prefectures)
