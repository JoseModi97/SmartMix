with open(r'C:\Users\odhis\Downloads\SmartMix\default_skin_extracted\Essentials.xml', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if any(k in line.lower() for k in ['<browser', '<sideview', '<filelist', '<folderlist', '<panel name="browser', 'class="browser']):
        print(f'{i+1}: {line.strip()[:100]}')
