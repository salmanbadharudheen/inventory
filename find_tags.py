import re

with open('templates/assets/asset_detail.html', 'r') as f:
    lines = f.readlines()

if_count = 0
endif_count = 0
for i, line in enumerate(lines):
    if '{% if ' in line:
        if_count += 1
        print(f"[{if_count}] IF    on line {i+1}: {line.strip()}")
    if '{% endif %}' in line:
        endif_count += 1
        print(f"[{endif_count}] ENDIF on line {i+1}: {line.strip()}")

print(f"\nTotal IF: {if_count}")
print(f"Total ENDIF: {endif_count}")
