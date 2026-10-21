import glob, os

files = glob.glob(r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\*.xml')
for fpath in files:
    fname = os.path.basename(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        t = f.read()
    for word in ['sidelist', 'karaoke']:
        if word in t.lower():
            print(f'{fname} has {word}')
            pos = 0
            while True:
                pos = t.lower().find(word, pos)
                if pos == -1: break
                print(f'   [{pos}] {t[max(0, pos-40):min(len(t), pos+80)].replace(chr(10), " ")}')
                pos += len(word) + 5
