import re

with open('templates/assets/depreciation_report.html', 'r', encoding='utf-8') as f:
    content = f.read()

for tag in ['if', 'for', 'block', 'with']:
    opens = len(re.findall(r'\{%%\s*%s[\s%%]' % tag, content))
    closes = len(re.findall(r'\{%%\s*end%s[\s%%]' % tag, content))
    status = 'OK' if opens == closes else 'MISMATCH!'
    print(f'{tag}: {opens} opens, {closes} closes - {status}')

# Check asset_import_preview too
with open('templates/assets/asset_import_preview.html', 'r', encoding='utf-8') as f:
    content2 = f.read()

print('\n--- asset_import_preview.html ---')
for tag in ['if', 'for', 'block', 'with']:
    opens = len(re.findall(r'\{%%\s*%s[\s%%]' % tag, content2))
    closes = len(re.findall(r'\{%%\s*end%s[\s%%]' % tag, content2))
    status = 'OK' if opens == closes else 'MISMATCH!'
    print(f'{tag}: {opens} opens, {closes} closes - {status}')

# Check all templates
import os
print('\n--- Scanning all templates ---')
for root, dirs, files in os.walk('templates'):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                c = fh.read()
            for tag in ['if', 'for', 'block', 'with']:
                o = len(re.findall(r'\{%%\s*%s[\s%%]' % tag, c))
                cl = len(re.findall(r'\{%%\s*end%s[\s%%]' % tag, c))
                if o != cl:
                    print(f'MISMATCH in {path}: {tag} has {o} opens vs {cl} closes')
print('Template scan done')
