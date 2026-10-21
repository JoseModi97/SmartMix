with open(r'C:\Users\odhis\AppData\Local\VirtualDJ\Skins\SmartMix\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

pos = text.find('name="layout_options"')
end_group = text.find('</group>', pos) + len('</group>')
print(text[end_group:end_group+600])
