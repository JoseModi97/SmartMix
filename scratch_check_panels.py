with open(r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\Pro.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<panel ', text)]
print(f'Pro.xml has {len(matches)} <panel> tags')
for m in matches[:15]:
    end = text.find('>', m)
    print(text[m:end+1])
