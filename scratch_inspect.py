with open(r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('class name="browser"')
if idx != -1:
    print(text[idx-10:idx+3500])
else:
    print('class name="browser" not found')
    # search for <browser
    pos = 0
    while True:
        pos = text.find('<browser', pos)
        if pos == -1: break
        print(text[pos:pos+300])
        print('='*40)
        pos += 8
