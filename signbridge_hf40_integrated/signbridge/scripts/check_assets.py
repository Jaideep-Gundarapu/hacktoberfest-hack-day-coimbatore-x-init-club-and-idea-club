from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
data = json.loads((root/'data'/'signs.json').read_text(encoding='utf-8'))
asset_dir = root/'assets'/'signs'
missing=[]; present=[]
for s in data['signs']:
    p=asset_dir/s['filename']
    (present if p.exists() else missing).append(s['label'])
print(f'Loaded assets: {len(present)}')
print('Missing assets:', ', '.join(missing))
