with open(r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<button class="button_main"', text)]
print(f'button_main count: {len(matches)}')
for m in matches[:5]:
    end = text.find('>', m)
    # also check if there is a <pos> child
    close_btn = text.find('</button>', m)
    snippet = text[m:min(close_btn+9, m+300)]
    print(snippet)
    print('='*40)
