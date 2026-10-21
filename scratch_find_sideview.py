import glob, os

files = glob.glob(r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\*.xml')
for fpath in files:
    fname = os.path.basename(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        t = f.read()
    if 'class name="browser"' in t:
        print(f'Found class name="browser" in {fname}')
    if 'sideview' in t.lower():
        print(f'Found sideview in {fname}')
        # print contexts of sideview
        pos = 0
        while True:
            pos = t.lower().find('sideview', pos)
            if pos == -1: break
            snippet = t[max(0, pos-80):min(len(t), pos+120)].replace('\n', ' ')
            print(f'   [{pos}] {snippet}')
            pos += 8
