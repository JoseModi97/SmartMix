p = r'C:\Users\odhis\AppData\Local\VirtualDJ\settings.xml'
with open(p, 'r', encoding='utf-8') as f:
    t = f.read()

old_skin = '<skin modified="yes">Default:Essentials</skin>'
new_skin = '<skin modified="yes">SmartMix:Essentials</skin>'

if old_skin in t:
    t_mod = t.replace(old_skin, new_skin)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t_mod)
    print('Successfully set skin to SmartMix:Essentials')
else:
    print('Current skin is already:', [l for l in t.splitlines() if '<skin' in l])
