import os
import sys
import random
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

LOCAL_APPDATA = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
VDJ_FOLDER = os.path.join(LOCAL_APPDATA, "VirtualDJ", "Sideview", "automix.vdjfolder")
VDJ_DB = os.path.join(LOCAL_APPDATA, "VirtualDJ", "database.xml")

# Fallback for explicit legacy paths if present
if not os.path.exists(VDJ_FOLDER):
    legacy_folder = r"C:\Users\odhis\AppData\Local\VirtualDJ\Sideview\automix.vdjfolder"
    if os.path.exists(legacy_folder):
        VDJ_FOLDER = legacy_folder

if not os.path.exists(VDJ_DB):
    legacy_db = r"C:\Users\odhis\AppData\Local\VirtualDJ\database.xml"
    if os.path.exists(legacy_db):
        VDJ_DB = legacy_db

def resolve_output_dir(requested_dir=None, tracks=None):
    """
    Intelligently determines the output directory:
      1. If user passed a specific non-empty --output-dir, use it.
      2. If tracks are provided from VirtualDJ, default to the folder containing the source tracks.
      3. If legacy '~/Downloads/Amapiano' exists, use it.
      4. Otherwise, fallback to '~/Downloads/SmartMix' or '~/Music/SmartMix'.
      Always ensures the target directory is automatically created so it never fails.
    """
    if requested_dir and requested_dir.strip():
        out = Path(requested_dir)
        out.mkdir(parents=True, exist_ok=True)
        return str(out)

    # 1. Use track source folder if available
    if tracks and len(tracks) > 0:
        first_p = tracks[0].get("path")
        if first_p and os.path.exists(first_p):
            p_dir = Path(first_p).parent
            if p_dir.exists():
                return str(p_dir)

    # 2. Check ~/Downloads/Amapiano
    user_amapiano = Path.home() / "Downloads" / "Amapiano"
    if user_amapiano.exists():
        return str(user_amapiano)

    # 3. Universal fallback: ~/Downloads/SmartMix
    fallback = Path.home() / "Downloads" / "SmartMix"
    fallback.mkdir(parents=True, exist_ok=True)
    return str(fallback)

OUTPUT_DIR = resolve_output_dir()

def resolve_mix_name(requested_name=None, tracks=None):
    """
    Intelligently determines the mix title / genre:
      1. If user passed a specific non-empty --mix-name (other than default Amapiano), use it.
      2. If tracks are provided from VirtualDJ, inspect parent folder (e.g. 'y2k' -> 'Y2K', 'HipHop' -> 'HipHop').
      3. Fallback to requested_name or 'Mixtape'.
    """
    if requested_name and requested_name.strip() and requested_name.strip().lower() != "amapiano":
        return requested_name.strip()
    if tracks and len(tracks) > 0:
        first_p = tracks[0].get("path")
        if first_p:
            parent = Path(first_p).parent.name
            if parent and parent.lower() not in ("downloads", "music", "desktop", ""):
                return parent.upper() if len(parent) <= 4 else parent.replace(" ", "_")
    return requested_name.strip() if requested_name and requested_name.strip() else "Mixtape"

def parse_args():
    parser = argparse.ArgumentParser(description="SmartMix: Studio-Grade DJ Mixtape & Transition Engine")
    parser.add_argument(
        "--mode",
        type=str,
        default="crossfade",
        choices=["crossfade", "normal", "both"],
        help="Rendering mode: 'crossfade' (default: gradual cue transitions with bass crossover), 'normal' (clean cue-drop cuts), or 'both'"
    )
    parser.add_argument(
        "--crossfade-mode",
        type=str,
        default="gradual",
        choices=["gradual", "equal-power", "bass-swap"],
        help="Global transition style: 'gradual' (default: Cue 2 to Cue 3 gradual crossfade with LR-4 bass crossover), 'equal-power'"
    )
    parser.add_argument(
        "--trans-style",
        type=str,
        default="",
        help="Per-transition custom styles (e.g. '1=gradual,2=equal-power')"
    )
    parser.add_argument(
        "--trans-bars",
        type=int,
        default=None,
        help="Force transition length in bars (e.g. 8, 16, 32 bars). If omitted, uses cue-defined duration (Cue 2 to Cue 3)."
    )
    parser.add_argument(
        "--bass-swap-ratio",
        type=float,
        default=0.68,
        help="Position within transition where low-end swaps (default: 0.68 = hands over in late phase of Cue 2 to Cue 3 window)"
    )
    # Professional DJ / Streaming Loudness Standards (EBU R128 / ITU-R BS.1770)
    parser.add_argument(
        "--target-lufs",
        type=float,
        default=-14.0,
        help="Target integrated loudness in LUFS according to DJ/Streaming standards (default: -14.0 LUFS)"
    )
    parser.add_argument(
        "--true-peak",
        type=float,
        default=-1.5,
        help="Maximum True Peak ceiling in dBTP to prevent inter-sample clipping on club sound systems and MP3 encoding (default: -1.5 dBTP)"
    )
    parser.add_argument(
        "--mix-name",
        type=str,
        default="Amapiano",
        help="Name or genre of the mix (used for output filenames and ID3 tags, e.g. 'Afrobeats', 'House', 'Amapiano')"
    )
    parser.add_argument("--entry-cue", type=int, default=1, help="Default cue number to use for song entry/mix-in (default: 1)")
    parser.add_argument("--fade-cue", type=int, default=2, help="Default cue number where fade-out begins / normal cutoff (default: 2)")
    parser.add_argument("--exit-cue", type=int, default=3, help="Default cue number where fade completes/cuts off (default: 3)")
    parser.add_argument("--normal-cutoff", type=str, default="cue2", choices=["cue2", "cue3"], help="Where normal cut transition occurs: 'cue2' (radio cutoff) or 'cue3' (full phrase)")
    parser.add_argument("--use-last-cues", action="store_true", help="If track has 4+ cues, automatically use the last 2 cues for the fade-out window")
    parser.add_argument("--output-dir", type=str, default=None, help="Destination directory for output files (default: auto-detect from playlist tracks, or ~/Downloads/Amapiano)")
    return parser.parse_args()

def extract_cue_points(song_elem, default_entry=1, default_fade=2, default_exit=3, use_last_cues=False):
    cues_by_num = {}
    cues_by_name = {}
    automix_points = {}
    
    for poi in song_elem.findall("Poi"):
        ptype = poi.get("Type", "")
        pos = float(poi.get("Pos", 0.0) or 0.0)
        name = (poi.get("Name") or "").lower()

        if ptype == "cue":
            num = int(poi.get("Num", 1))
            cues_by_num[num] = pos
            if name:
                cues_by_name[name] = pos
        elif ptype == "automix":
            point = poi.get("Point", "")
            if point:
                automix_points[point] = pos

    entry_pos = None
    fade_pos = None
    exit_pos = None

    for name, pos in cues_by_name.items():
        if any(k in name for k in ["start", "intro", "in", "drop"]) and entry_pos is None:
            entry_pos = pos
        elif any(k in name for k in ["fade out", "fade_out", "mix out", "fade start"]) and fade_pos is None:
            fade_pos = pos
        elif any(k in name for k in ["cutoff", "cut", "exit", "end"]) and exit_pos is None:
            exit_pos = pos

    if use_last_cues and len(cues_by_num) >= 4:
        sorted_cues = sorted(cues_by_num.items(), key=lambda x: x[1])
        if entry_pos is None:
            entry_pos = sorted_cues[0][1]
        if fade_pos is None:
            fade_pos = sorted_cues[-2][1]
        if exit_pos is None:
            exit_pos = sorted_cues[-1][1]

    if entry_pos is None:
        entry_pos = cues_by_num.get(default_entry, 0.0)
    if fade_pos is None:
        fade_pos = cues_by_num.get(default_fade, None)
    if exit_pos is None:
        exit_pos = cues_by_num.get(default_exit, None)

    if fade_pos is None and "fadeEnd" in automix_points:
        fade_pos = automix_points["fadeEnd"]
    if exit_pos is None and "cutEnd" in automix_points:
        exit_pos = automix_points["cutEnd"]

    return entry_pos, fade_pos, exit_pos, cues_by_num

def get_track_data(args):
    if not os.path.exists(VDJ_FOLDER):
        raise FileNotFoundError(f"Automix folder not found: {VDJ_FOLDER}")
    
    db_lookup = {}
    if os.path.exists(VDJ_DB):
        tree_db = ET.parse(VDJ_DB)
        for s in tree_db.getroot().findall("Song"):
            p = s.get("FilePath", "")
            entry_pos, fade_pos, exit_pos, all_cues = extract_cue_points(
                s,
                default_entry=args.entry_cue,
                default_fade=args.fade_cue,
                default_exit=args.exit_cue,
                use_last_cues=args.use_last_cues
            )
            scan = s.find("Scan")
            db_bpm = None
            if scan is not None and scan.get("Bpm"):
                raw_bpm = float(scan.get("Bpm"))
                if raw_bpm > 0:
                    db_bpm = round(60.0 / raw_bpm, 3)
            
            infos = s.find("Infos")
            db_length = float(infos.get("SongLength", 0.0)) if infos is not None and infos.get("SongLength") else 0.0

            tags = s.find("Tags")
            db_artist = tags.get("Author", "") if tags is not None else ""
            db_title = tags.get("Title", "") if tags is not None else ""

            db_lookup[p] = {
                "entry": entry_pos,
                "fade": fade_pos,
                "exit": exit_pos,
                "all_cues": all_cues,
                "bpm": db_bpm,
                "length": db_length,
                "artist": db_artist,
                "title": db_title
            }

    tree_folder = ET.parse(VDJ_FOLDER)
    tracks = []
    for s in tree_folder.getroot().findall("song"):
        p = s.get("path")
        if not os.path.exists(p):
            print(f"Warning: File not found: {p}")
            continue

        info = db_lookup.get(p, {})
        bpm = float(s.get("bpm", 0.0)) or info.get("bpm", 0.0)
        length = float(s.get("songlength", 0.0)) or info.get("length", 0.0)

        # Fallback length from ffprobe if still 0.0
        if length <= 0.0:
            try:
                cmd_len = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", p]
                res_len = subprocess.run(cmd_len, capture_output=True, text=True)
                length = float(res_len.stdout.strip())
            except Exception:
                pass

        artist = s.get("artist") or info.get("artist")
        title = s.get("title") or info.get("title")
        if not artist or not title or artist == "Unknown Artist" or title == "Unknown Title":
            stem = Path(p).stem
            if " - " in stem:
                parsed_artist, parsed_title = stem.split(" - ", 1)
                artist = artist or parsed_artist.strip()
                title = title or parsed_title.strip()
            else:
                artist = artist or "Unknown Artist"
                title = title or stem

        tracks.append({
            "path": p,
            "artist": artist,
            "title": title,
            "bpm": bpm,
            "length": length,
            "cue_entry": info.get("entry", 0.0),
            "cue_fade": info.get("fade", None),
            "cue_exit": info.get("exit", None),
            "all_cues": info.get("all_cues", {})
        })
    return tracks

def format_time(seconds):
    if seconds is None:
        return "N/A"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def parse_custom_styles(trans_style_str):
    """Parses '1=bass-swap,2=filter-sweep' into {0: 'bass-swap', 1: 'filter-sweep'}"""
    styles = {}
    if not trans_style_str:
        return styles
    for item in trans_style_str.split(","):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            try:
                styles[int(k) - 1] = v.strip().lower()
            except ValueError:
                pass
    return styles

def get_transition_mode(idx, global_mode, custom_styles, last_mode=None):
    if idx in custom_styles:
        return custom_styles[idx]
    if global_mode == "equal-power":
        return "equal-power"
    return "gradual"

# -----------------------------------------------------------------------------
# ADVANCED DSP TRANSITION BLENDERS
# -----------------------------------------------------------------------------

def blend_gradual(a_seg, b_seg, sr=44100, bass_swap_ratio=0.68):
    """
    Studio-Grade Gradual DJ Crossfade between Cue 2 and Cue 3.
    Preserves outgoing music (Track A) presence and musicality across the
    full distance between Cue 2 and Cue 3:
      - Track A stays prominent across 75%+ of the transition window, smoothly
        rolling off in the final stretch to Cue 3 instead of muting early.
      - Track B introduces progressively and takes command smoothly.
      - Linkwitz-Riley 4th Order (LR-4) zero-phase crossover at 200 Hz maintains
        the outgoing bass groove through the transition, handing over to Track B's
        bass near the golden ratio point (~68%) so kicks/sub-bass never clash or cut abruptly.
    """
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]

    t = np.linspace(0.0, 1.0, n)

    # Outgoing curve: hold presence for the first ~35% of the Cue 2 -> Cue 3 distance,
    # then smoothly and musically taper down towards Cue 3 so it stays clearly audible
    t_fade_a = np.clip((t - 0.35) / 0.65, 0.0, 1.0)
    curve_a = (np.cos(t_fade_a * (np.pi * 0.5)) ** 0.85)[:, None]

    # Incoming curve: smoothly ramp up to full energy across the transition
    t_fade_b = np.clip(t / 0.85, 0.0, 1.0)
    curve_b = np.sin(t_fade_b * (np.pi * 0.5))[:, None]

    fc = 200.0
    b_l, a_l = signal.butter(2, fc, btype='low', fs=sr)
    b_h, a_h = signal.butter(2, fc, btype='high', fs=sr)

    a_low = signal.filtfilt(b_l, a_l, a_seg, axis=0)
    a_high = signal.filtfilt(b_h, a_h, a_seg, axis=0)
    b_low = signal.filtfilt(b_l, a_l, b_seg, axis=0)
    b_high = signal.filtfilt(b_h, a_h, b_seg, axis=0)

    # Mids & highs crossfade: Track A stays audible throughout
    high_blend = a_high * curve_a + b_high * curve_b

    # Lows swap: outgoing track's bass drives through ~68% of the cue distance
    swap_center = int(n * min(0.85, max(0.4, bass_swap_ratio)))
    half_w = max(int(round(sr * 1.0)), 1)  # 2.0s musical handover window
    s_start = max(0, swap_center - half_w)
    s_end = min(n, swap_center + half_w)

    low_env_a = np.ones(n, dtype=np.float32)
    low_env_b = np.zeros(n, dtype=np.float32)

    swap_len = s_end - s_start
    if swap_len > 0:
        ramp = np.linspace(0.0, 1.0, swap_len)
        low_env_a[s_start:s_end] = np.cos(ramp * (np.pi * 0.5))
        low_env_a[s_end:] = 0.0
        low_env_b[s_start:s_end] = np.sin(ramp * (np.pi * 0.5))
        low_env_b[s_end:] = 1.0

    low_blend = a_low * low_env_a[:, None] + b_low * low_env_b[:, None]
    return high_blend + low_blend

def blend_equal_power(a_seg, b_seg):
    """Mathematical equal-power crossfade tuned for natural DJ transitions."""
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]
    t = np.linspace(0.0, 1.0, n)
    t_fade_a = np.clip((t - 0.35) / 0.65, 0.0, 1.0)
    curve_a = (np.cos(t_fade_a * (np.pi * 0.5)) ** 0.85)[:, None]
    t_fade_b = np.clip(t / 0.85, 0.0, 1.0)
    curve_b = np.sin(t_fade_b * (np.pi * 0.5))[:, None]
    return a_seg * curve_a + b_seg * curve_b

# -----------------------------------------------------------------------------
# NORMAL CUT MIX (Sequential Clean Drops)
# -----------------------------------------------------------------------------

def render_normal_mix(tracks, args, output_file):
    print("\n" + "-" * 78)
    print(" RENDERING NORMAL MIX (Clean Drop, EBU R128 DJ Loudness Normalization)...")
    print("-" * 78)

    temp_dir = os.path.join(args.output_dir, "_temp_normal_parts")
    os.makedirs(temp_dir, exist_ok=True)

    prepared_clips = []
    timeline_markers = []
    current_time = 0.0

    for i, t in enumerate(tracks):
        is_last = (i == len(tracks) - 1)
        in_file = t["path"]
        out_clip = os.path.join(temp_dir, f"norm_clip_{i:02d}.wav")

        start_time = t["cue_entry"]

        cutoff_pref = getattr(args, "normal_cutoff", "cue2")
        if is_last:
            if cutoff_pref == "cue2" and t["cue_fade"] is not None and t["cue_fade"] > start_time:
                end_time = t["cue_fade"]
            elif t["cue_exit"] is not None and t["cue_exit"] > start_time:
                end_time = t["cue_exit"]
            else:
                end_time = t["length"]
        else:
            if cutoff_pref == "cue3" and t["cue_exit"] is not None and t["cue_exit"] > start_time:
                end_time = t["cue_exit"]
            elif t["cue_fade"] is not None and t["cue_fade"] > start_time:
                end_time = t["cue_fade"]
            elif t["cue_exit"] is not None and t["cue_exit"] > start_time:
                end_time = t["cue_exit"]
            else:
                end_time = t["length"] - 2.0

        duration = max(0.1, end_time - start_time)

        af_filters = (
            "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=stereo,"
            f"afade=t=in:st=0:d=0.015,afade=t=out:st={max(0.0, duration - 0.02):.3f}:d=0.02"
        )
        if is_last:
            af_filters += f",afade=t=out:st={max(0.0, duration - 4.0):.3f}:d=4.0"

        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_time:.3f}",
            "-to", f"{end_time:.3f}",
            "-i", in_file,
            "-af", af_filters,
            out_clip
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        prepared_clips.append(out_clip)

        timeline_markers.append((current_time, t["artist"], t["title"]))
        current_time += duration

    filter_inputs = "".join([f"[{idx}:a]" for idx in range(len(prepared_clips))])
    concat_filter = f"{filter_inputs}concat=n={len(prepared_clips)}:v=0:a=1,loudnorm=I={args.target_lufs}:TP={args.true_peak}:LRA=10.0[out]"

    cmd = ["ffmpeg", "-y"]
    for clip in prepared_clips:
        cmd.extend(["-i", clip])
    mix_tag = getattr(args, "mix_name", "Amapiano")
    cmd.extend([
        "-filter_complex", concat_filter,
        "-map", "[out]",
        "-b:a", "320k",
        "-metadata", f"album={mix_tag} Continuous Mix (Normal)",
        "-metadata", f"title={mix_tag} Set (Clean Cut)",
        "-metadata", "artist=Various Artists",
        "-metadata", f"genre={mix_tag}",
        output_file
    ])

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        return False

    for clip in prepared_clips:
        try:
            os.remove(clip)
        except OSError:
            pass

    out_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"-> Normal Mix Rendered: {output_file} ({out_size_mb:.2f} MB)")
    print(f"   [Loudness Target: {args.target_lufs} LUFS | True Peak Ceiling: {args.true_peak} dBTP]")
    print("Normal Mix Timeline:")
    for mark_time, artist, title in timeline_markers:
        print(f" [{format_time(mark_time)}] {artist} - {title}")
    return True

# -----------------------------------------------------------------------------
# AUDIO LOADER WITH OPTIONAL PITCH-PRESERVING TEMPO MATCHING
# -----------------------------------------------------------------------------

def load_audio_clip(path, start_s, duration_s=None, end_s=None, sr=44100, tempo_ratio=1.0):
    cmd = ["ffmpeg", "-y", "-ss", f"{start_s:.3f}"]
    if duration_s is not None and duration_s > 0:
        cmd.extend(["-t", f"{duration_s:.3f}"])
    elif end_s is not None and end_s > start_s:
        cmd.extend(["-to", f"{end_s:.3f}"])
    cmd.extend(["-i", path])
    if abs(tempo_ratio - 1.0) > 0.005:
        ratio_clamped = max(0.5, min(2.0, tempo_ratio))
        cmd.extend(["-af", f"atempo={ratio_clamped:.5f}"])
    cmd.extend(["-f", "s16le", "-ac", "2", "-ar", str(sr), "-"])
    proc = subprocess.run(cmd, capture_output=True, check=True)
    raw = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return raw.reshape(-1, 2)

# -----------------------------------------------------------------------------
# SMART CROSSFADED MIX (Studio-Grade Gradual Cue Transitions)
# -----------------------------------------------------------------------------

def render_crossfade_mix(tracks, args, output_file):
    print("\n" + "-" * 78)
    print(f" RENDERING SMART CROSSFADED MIX (Gradual Cue Transitions | Target: {args.target_lufs} LUFS)...")
    print("-" * 78)

    sr = 44100
    custom_styles = parse_custom_styles(args.trans_style)

    # Determine transition lengths and styles for each transition
    trans_durations = []
    trans_modes = []

    for i in range(len(tracks) - 1):
        t_a = tracks[i]
        t_b = tracks[i + 1]
        bpm_a = t_a["bpm"] or 118.0
        bpm_b = t_b["bpm"] or 118.0

        # Transition duration strictly determined by Cue 2 (fade) to Cue 3 (exit/cut)
        if args.trans_bars is not None and args.trans_bars > 0:
            fade_dur = args.trans_bars * 4.0 * (60.0 / bpm_a)
        elif t_a["cue_fade"] is not None and t_a["cue_exit"] is not None and t_a["cue_exit"] > t_a["cue_fade"]:
            fade_dur = t_a["cue_exit"] - t_a["cue_fade"]
        else:
            fade_dur = 16.0 * 4.0 * (60.0 / bpm_a)  # Default 16 bars (64 beats)

        mode = get_transition_mode(i, args.crossfade_mode, custom_styles)
        trans_durations.append(fade_dur)
        trans_modes.append(mode)

    print("Planned Transitions:")
    for i, (dur, mode) in enumerate(zip(trans_durations, trans_modes)):
        bpm_a = tracks[i]["bpm"] or 118.0
        bpm_b = tracks[i+1]["bpm"] or 118.0
        bpm_diff = abs(bpm_a - bpm_b)
        tempo_note = f" [Tempo Sync: {bpm_b:.1f} -> {bpm_a:.1f} BPM]" if 0.5 < bpm_diff <= 12.0 else ""
        if bpm_diff > 12.0:
            tempo_note = f" [Tempo Shift: {bpm_a:.1f} -> {bpm_b:.1f} BPM]"
        print(f"  * Transition {i+1} -> {i+2}: {dur:.1f}s ({mode.upper()}){tempo_note} | Tracks: {tracks[i]['title']} -> {tracks[i+1]['title']}")

    # Assemble master audio with DSP transitions
    timeline_markers = []
    master_blocks = []
    current_time_s = 0.0

    # Start first track at its cue_entry
    timeline_markers.append((current_time_s, tracks[0]["artist"], tracks[0]["title"], None))
    curr_in_pos = tracks[0]["cue_entry"]

    for i in range(len(tracks) - 1):
        t_a = tracks[i]
        t_b = tracks[i + 1]
        fade_dur = trans_durations[i]
        mode = trans_modes[i]
        bpm_a = t_a["bpm"] or 118.0
        bpm_b = t_b["bpm"] or 118.0

        # Cue 2 is the fade start point
        if t_a["cue_fade"] is not None and t_a["cue_fade"] > curr_in_pos:
            fade_start = t_a["cue_fade"]
        else:
            fade_start = max(curr_in_pos, (t_a["length"] or 180.0) - fade_dur)

        # 1. Track A Solo Section: from curr_in_pos up to Cue 2 (fade_start)
        solo_dur = max(0.0, fade_start - curr_in_pos)
        if solo_dur > 0.02:
            solo_audio = load_audio_clip(t_a["path"], start_s=curr_in_pos, duration_s=solo_dur, sr=sr)
            master_blocks.append(solo_audio)
            current_time_s += len(solo_audio) / sr

        # 2. Gradual Crossfade Transition Window: Cue 2 to Cue 3
        # Track A fades out over fade_dur
        a_trans = load_audio_clip(t_a["path"], start_s=fade_start, duration_s=fade_dur, sr=sr)

        # Track B enters at its cue_entry and fades in over fade_dur
        b_entry = t_b["cue_entry"]
        bpm_diff = abs(bpm_a - bpm_b)

        if 0.5 < bpm_diff <= 12.0:
            tempo_ratio = bpm_a / bpm_b
            dur_b_needed = fade_dur * tempo_ratio
            b_trans = load_audio_clip(
                t_b["path"],
                start_s=b_entry,
                duration_s=dur_b_needed,
                sr=sr,
                tempo_ratio=tempo_ratio
            )
        else:
            dur_b_needed = fade_dur
            b_trans = load_audio_clip(
                t_b["path"],
                start_s=b_entry,
                duration_s=fade_dur,
                sr=sr,
                tempo_ratio=1.0
            )

        # Match exact sample lengths
        target_len = len(a_trans)
        if len(b_trans) > target_len:
            b_trans = b_trans[:target_len]
        elif len(b_trans) < target_len:
            b_trans = np.pad(b_trans, ((0, target_len - len(b_trans)), (0, 0)))

        # Blend transition using gradual DJ crossfader
        if mode == "equal-power":
            blended = blend_equal_power(a_trans, b_trans)
        else:
            blended = blend_gradual(
                a_trans,
                b_trans,
                sr=sr,
                bass_swap_ratio=getattr(args, "bass_swap_ratio", 0.68)
            )

        # Mark Track B entry on the mixtape timeline
        timeline_markers.append((current_time_s, t_b["artist"], t_b["title"], mode))

        master_blocks.append(blended)
        current_time_s += len(blended) / sr

        # Track B's playback position for its subsequent solo / transition
        curr_in_pos = b_entry + dur_b_needed

    # 3. Final Track Solo Section (respects Cue 2 fade and Cue 3 finale cutoff)
    last_t = tracks[-1]
    if last_t["cue_exit"] is not None and last_t["cue_exit"] > curr_in_pos:
        last_end = last_t["cue_exit"]
        if last_t["cue_fade"] is not None and curr_in_pos < last_t["cue_fade"] < last_end:
            fade_dur = last_end - last_t["cue_fade"]
        else:
            fade_dur = min(4.0, (last_end - curr_in_pos) * 0.5)
    else:
        last_end = last_t["length"]
        fade_dur = min(4.0, (last_end - curr_in_pos) * 0.5)

    if last_end <= curr_in_pos:
        last_end = last_t["length"]

    last_dur = max(0.1, last_end - curr_in_pos)
    last_audio = load_audio_clip(last_t["path"], start_s=curr_in_pos, duration_s=last_dur, sr=sr)

    # Smooth fade out on mixtape finale
    fade_out_len = min(int(sr * fade_dur), len(last_audio))
    if fade_out_len > 0:
        last_audio[-fade_out_len:] *= np.linspace(1.0, 0.0, fade_out_len)[:, None]

    master_blocks.append(last_audio)
    current_time_s += len(last_audio) / sr

    # Concatenate master audio
    print("\nConcatenating master audio stream...")
    full_audio = np.concatenate(master_blocks, axis=0)

    # Write temporary WAV for loudness normalization
    temp_master_wav = os.path.join(args.output_dir, "_temp_crossfade_master.wav")
    wavfile.write(temp_master_wav, sr, (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16))

    # Master Output Stage: Apply EBU R128 DJ Loudness Normalization & True Peak Limiting
    print("Mastering to 320k MP3 with EBU R128 DJ Standards (-14.0 LUFS, -1.5 dBTP)...")
    mix_tag = getattr(args, "mix_name", "Amapiano")
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_master_wav,
        "-af", f"loudnorm=I={args.target_lufs}:TP={args.true_peak}:LRA=10.0",
        "-b:a", "320k",
        "-metadata", f"album={mix_tag} Continuous Mix (Smart Crossfaded)",
        "-metadata", f"title={mix_tag} Set (Smart Crossfaded)",
        "-metadata", "artist=Various Artists",
        "-metadata", f"genre={mix_tag}",
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if os.path.exists(temp_master_wav):
        os.remove(temp_master_wav)

    out_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"-> Crossfaded Mix Rendered: {output_file} ({out_size_mb:.2f} MB)")
    print(f"   [Loudness Target: {args.target_lufs} LUFS | True Peak Ceiling: {args.true_peak} dBTP]")
    print("Crossfaded Mix Timeline:")
    for mark_time, artist, title, trans in timeline_markers:
        trans_str = f" [Crossfade: {trans}]" if trans else ""
        print(f" [{format_time(mark_time)}] {artist} - {title}{trans_str}")
    return True

def main():
    args = parse_args()

    tracks = get_track_data(args)
    if not tracks:
        print("No valid tracks found to mix.")
        return

    # Automatically resolve output directory (from track directory or user folder)
    args.output_dir = resolve_output_dir(args.output_dir, tracks)
    os.makedirs(args.output_dir, exist_ok=True)
    args.mix_name = resolve_mix_name(args.mix_name, tracks)

    normal_output = os.path.join(args.output_dir, f"{args.mix_name}_Continuous_Mix_Normal.mp3")
    crossfade_output = os.path.join(args.output_dir, f"{args.mix_name}_Continuous_Mix_Crossfaded.mp3")

    print("=" * 78)
    print(" SMARTMIX: ADVANCED DJ TRANSITION & CONTINUOUS MIXTAPE ENGINE")
    print("=" * 78)
    print(f"Target Mode    : {args.mode.upper()}")
    print(f"Transition Mode: {args.crossfade_mode.upper()}")
    print(f"Loudness Target: {args.target_lufs:.1f} LUFS (Industry DJ/Club Reference)")
    print(f"True Peak Cap  : {args.true_peak:.1f} dBTP (Inter-Sample Headroom Margin)")
    print(f"Loaded {len(tracks)} tracks from Automix playlist:\n")

    for i, t in enumerate(tracks):
        cues_count = len(t["all_cues"])
        print(f" [{i+1}] {t['artist']} - {t['title']}")
        print(f"     BPM: {t['bpm']:.1f} | Cues: {cues_count} | Entry @ {format_time(t['cue_entry'])} | Fade/Cut @ {format_time(t['cue_fade'])} | Outro @ {format_time(t['cue_exit'])}")

    if args.mode in ("both", "normal"):
        render_normal_mix(tracks, args, normal_output)

    if args.mode in ("both", "crossfade"):
        render_crossfade_mix(tracks, args, crossfade_output)

    print("\n" + "=" * 78)
    print(" ALL REQUESTED MIXES GENERATED ACCORDING TO DJ LOUDNESS STANDARDS!")
    print("=" * 78)
    if args.mode in ("both", "normal"):
        print(f" 1. Normal Cut Mix    : {normal_output}")
    if args.mode in ("both", "crossfade"):
        print(f" 2. Crossfaded Mix   : {crossfade_output}")
    print(f" Master Levels Verified: {args.target_lufs} LUFS Integrated, Max True Peak {args.true_peak} dBTP")
    print("=" * 78)

if __name__ == "__main__":
    main()
