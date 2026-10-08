from pathlib import Path
import json

p = Path(__file__).resolve().parents[1] / 'data' / 'signs.json'
data = json.loads(p.read_text(encoding='utf-8'))
seen = set(); out=[]
for item in data['signs']:
    if item['id'] not in seen:
        seen.add(item['id']); out.append(item)
data['signs']=out
p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'Wrote {len(out)} unique signs')
