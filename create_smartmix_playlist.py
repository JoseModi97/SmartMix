import os

playlists_dir = r'C:\Users\odhis\AppData\Local\VirtualDJ\Playlists'
os.makedirs(playlists_dir, exist_ok=True)

# Write SmartMix.m3u playlist
m3u_content = '''#EXTM3U
#EXTINF:207,Toxic Lyrikali - Hate (Audio)
C:\\Users\\odhis\\Downloads\\TOXIC LYRIKALI - HATE (Audio).mp3
#EXTINF:275,Drake - 0 to 100
C:\\Users\\odhis\\Downloads\\Drake-0-to-100-Instrumental-Prod.-By-Vinylz-Boi-1da.mp3
#EXTINF:225,PHY - RUKA
C:\\Users\\odhis\\Downloads\\Music\\PHY - RUKA  ft. King Kaka & Khaligraph Jones.mp3
'''

m3u_path = os.path.join(playlists_dir, 'SmartMix.m3u')
with open(m3u_path, 'w', encoding='utf-8') as f:
    f.write(m3u_content)

print('Created playlist at:', m3u_path)
