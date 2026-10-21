with open(r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<define class="button', text)]
print(f'Matches: {len(matches)}')
for m in matches[:5]:
    end = text.find('</define>', m)
    print(text[m:end+9])
    print('='*40)
