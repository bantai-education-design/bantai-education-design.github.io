import urllib.request
import json
url = 'https://machi.jig.jp/api/v1/pref/02/city'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print('Aomori:')
        for x in data:
            print(f'"{x["name"]}",', end=' ')
except Exception as e:
    print('err', e)
print()
url = 'https://machi.jig.jp/api/v1/pref/05/city'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print('Akita:')
        for x in data:
            print(f'"{x["name"]}",', end=' ')
except Exception as e:
    print('err', e)
