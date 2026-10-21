with open(r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

pos = text.find('<browser')
print('browser pos:', pos)
print(text[pos:pos+1500])
