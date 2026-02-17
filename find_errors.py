import re

path = r"c:\Users\Salmanul.Faris\OneDrive - Shamal\Desktop\inventory\templates\dashboard.html"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "depreciation_percentage" in line:
        print(f"Line {i+1}: {line.strip()}")
    if "ion_percentage" in line and "depreciation_percentage" not in line:
         print(f"Line {i+1} (TYPO?): {line.strip()}")

# Look for split tags
content = "".join(lines)
matches = re.findall(r'\{\{.*?\}\}', content, re.DOTALL)
for m in matches:
    if "depreciation_percentage" in m:
        if "\n" in m:
            print(f"SPLIT TAG FOUND: {m}")
