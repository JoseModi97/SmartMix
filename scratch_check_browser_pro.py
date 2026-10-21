with open(r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\Pro.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

pos = text.find('<browser')
if pos != -1:
    print(text[pos:pos+1500])
