with open(r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<panel name=', text)]
print(f'panel name count: {len(matches)}')
for m in matches[:5]:
    end = text.find('</panel>', m)
    snippet = text[m:min(end+8, m+250)]
    print(snippet)
    print('='*40)
