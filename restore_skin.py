p = r'C:\Users\odhis\AppData\Local\VirtualDJ\settings.xml'
with open(p, 'r', encoding='utf-8') as f:
    t = f.read()

t = t.replace('<skin modified="yes">SmartMix:Essentials</skin>', '<skin modified="yes">Default:Essentials</skin>')
with open(p, 'w', encoding='utf-8') as f:
    f.write(t)
print('Restored settings.xml to Default:Essentials')
