import sqlite3
import os
import time
import uuid
import xml.etree.ElementTree as ET

DB_PATH = r'C:\Users\odhis\AppData\Local\VirtualDJ\smartmix.db'
VDJ_DB_PATH = r'C:\Users\odhis\AppData\Local\VirtualDJ\database.xml'

def init_database(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS playlists (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS playlist_tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        playlist_id TEXT NOT NULL,
        track_order INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        title TEXT,
        artist TEXT,
        bpm REAL,
        musical_key TEXT,
        duration_sec REAL,
        trigger_cue_num INTEGER DEFAULT 1,
        trigger_cue_pos_sec REAL DEFAULT 0.0,
        start_cue_num INTEGER DEFAULT 1,
        start_cue_pos_sec REAL DEFAULT 0.0,
        cutoff_cue_num INTEGER DEFAULT 0,
        cutoff_cue_pos_sec REAL DEFAULT 0.0,
        transition_preset TEXT DEFAULT 'Smooth',
        fade_curve TEXT DEFAULT 'EqualPower',
        fade_length_beats REAL DEFAULT 16.0,
        eq_bass_swap INTEGER DEFAULT 1,
        bpm_sync_mode TEXT DEFAULT 'Instant',
        notes TEXT,
        FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS transition_presets (
        preset_name TEXT PRIMARY KEY,
        fade_curve TEXT NOT NULL,
        fade_duration_beats REAL NOT NULL,
        eq_crossover_mode TEXT NOT NULL,
        volume_curve_json TEXT,
        tempo_curve_json TEXT
    )
    ''')

    # Seed standard transition presets
    presets = [
        ('Smooth', 'EqualPower', 16.0, 'BassSwap', '{"out": "cos", "in": "sin"}', '{"mode": "sync"}'),
        ('Linear Fade', 'Linear', 8.0, 'EqualBlend', '{"out": "linear", "in": "linear"}', '{"mode": "sync"}'),
        ('Sharp Cut', 'Cut', 0.0, 'Instant', '{"out": "cut", "in": "instant"}', '{"mode": "instant"}'),
        ('Equal Power', 'EqualPower', 32.0, 'MultiBand', '{"out": "equal_power", "in": "equal_power"}', '{"mode": "sync"}'),
        ('Drop Swap', 'BassCut', 8.0, 'DropBass', '{"out": "bass_kill", "in": "full"}', '{"mode": "sync"}')
    ]
    cur.executemany('''
    INSERT OR REPLACE INTO transition_presets 
    (preset_name, fade_curve, fade_duration_beats, eq_crossover_mode, volume_curve_json, tempo_curve_json)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', presets)

    conn.commit()
    return conn

def parse_vdj_database(vdj_db_path=VDJ_DB_PATH):
    if not os.path.exists(vdj_db_path):
        return []
    tree = ET.parse(vdj_db_path)
    root = tree.getroot()
    tracks = []
    for song in root.findall('Song'):
        fpath = song.get('FilePath', '')
        if not fpath:
            continue
        infos = song.find('Infos')
        scan = song.find('Scan')
        length = float(infos.get('SongLength', 0.0)) if infos is not None else 0.0
        bpm_val = float(scan.get('Bpm', 0.0)) if scan is not None else 0.0
        # VirtualDJ BPM in Scan is stored as fraction or raw frequency, often AltBpm or needs scaling
        # In VDJ, standard BPM is typically between 60 and 200
        bpm = round(bpm_val * 60.0 if bpm_val > 0 and bpm_val < 5.0 else bpm_val, 1)
        key = scan.get('Key', '') if scan is not None else ''

        cues = []
        for poi in song.findall('Poi'):
            if poi.get('Type') == 'cue':
                cnum = int(poi.get('Num', 1))
                pos_str = poi.get('Pos')
                pos = float(pos_str) if pos_str is not None else 0.0
                name = poi.get('Name', f'Cue {cnum}')
                cues.append({'num': cnum, 'pos': pos, 'name': name})
        
        cues.sort(key=lambda x: x['num'])
        tracks.append({
            'file_path': fpath,
            'title': os.path.splitext(os.path.basename(fpath))[0],
            'artist': 'Local Artist',
            'duration_sec': length,
            'bpm': bpm if bpm > 0 else 90.0,
            'key': key if key else '8A',
            'cues': cues
        })
    return tracks

def seed_sample_smartmix_playlist(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM playlists WHERE name = 'SmartMix Master Set'")
    existing = cur.fetchone()
    if existing:
        return existing[0]

    playlist_id = str(uuid.uuid4())
    now = int(time.time())
    cur.execute('''
    INSERT INTO playlists (id, name, description, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (playlist_id, 'SmartMix Master Set', 'Exact Hot Cue transition playlist with absolute cutoffs', now, now))

    all_tracks = parse_vdj_database()
    # Filter for tracks that have cue points
    tracks_with_cues = [t for t in all_tracks if len(t['cues']) >= 1]
    sample_tracks = tracks_with_cues[:4] if len(tracks_with_cues) >= 4 else all_tracks[:4]

    for order, t in enumerate(sample_tracks, start=1):
        cues = t['cues']
        # Default cue assignments:
        # Trigger cue: Cue 1 or last cue if multiple
        # Start cue: Cue 1
        # Cutoff cue: last cue or duration - 15s
        trigger_cue = cues[-1]['num'] if len(cues) > 1 else 1
        trigger_pos = cues[-1]['pos'] if len(cues) > 1 else max(10.0, t['duration_sec'] * 0.75)
        
        start_cue = cues[0]['num'] if len(cues) > 0 else 1
        start_pos = cues[0]['pos'] if len(cues) > 0 else 0.0

        cutoff_cue = cues[-1]['num'] if len(cues) > 1 else 1
        cutoff_pos = trigger_pos + 15.0 if trigger_pos > 0 else max(20.0, t['duration_sec'] * 0.85)

        cur.execute('''
        INSERT INTO playlist_tracks (
            playlist_id, track_order, file_path, title, artist, bpm, musical_key,
            duration_sec, trigger_cue_num, trigger_cue_pos_sec, start_cue_num,
            start_cue_pos_sec, cutoff_cue_num, cutoff_cue_pos_sec, transition_preset,
            fade_curve, fade_length_beats, eq_bass_swap, bpm_sync_mode, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            playlist_id, order, t['file_path'], t['title'], t['artist'], t['bpm'], t['key'],
            t['duration_sec'], trigger_cue, trigger_pos, start_cue, start_pos,
            cutoff_cue, cutoff_pos, 'Smooth', 'EqualPower', 16.0, 1, 'Instant',
            'Non-destructive cutoff strictly enforced'
        ))

    conn.commit()
    return playlist_id

if __name__ == '__main__':
    conn = init_database()
    pid = seed_sample_smartmix_playlist(conn)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = ?", (pid,))
    count = cur.fetchone()[0]
    print(f'SmartMix Database initialized successfully at: {DB_PATH}')
    print(f'Created sample playlist {pid} with {count} cue-configured tracks.')
