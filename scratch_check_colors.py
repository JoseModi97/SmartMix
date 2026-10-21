with open(r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<define color=\"browser', text)]
print(f'Browser color defines: {len(matches)}')
for m in matches[:15]:
    end = text.find('/>', m)
    print(text[m:end+2])
