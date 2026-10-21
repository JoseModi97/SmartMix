import xml.etree.ElementTree as ET

tree = ET.parse(r'C:\Users\odhis\AppData\Local\VirtualDJ\database.xml')
root = tree.getroot()

for song in root.findall('Song'):
    cues = [p for p in song.findall('Poi') if p.get('Type') == 'cue' and p.get('Pos') is not None]
    if len(cues) >= 1:
        fpath = song.get('FilePath')
        print(f'Track: {fpath}')
        for c in cues:
            print(f'   Cue {c.get("Num")}: {c.get("Pos")}s ({c.get("Name")})')
