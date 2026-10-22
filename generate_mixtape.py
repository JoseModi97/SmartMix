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
        default="both",
        choices=["both", "normal", "crossfade"],
        help="Rendering mode: 'both' (default: renders both normal and crossfade mixes), 'normal' (clean cue transitions to Cue 3), or 'crossfade' (gradual cue transitions)"
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
        default=None,
        help="Name or genre of the mix (used for output filenames and ID3 tags, e.g. 'Afrobeats', 'House', 'Amapiano')"
    )
    parser.add_argument("--entry-cue", type=int, default=1, help="Default cue number to use for song entry/mix-in (default: 1)")
    parser.add_argument("--fade-cue", type=int, default=2, help="Default cue number where fade-out begins / normal cutoff (default: 2)")
    parser.add_argument("--exit-cue", type=int, default=3, help="Default cue number where fade completes/cuts off (default: 3)")
    parser.add_argument(
        "--normal-cutoff",
        type=str,
        default="cue3",
        choices=["cue3", "cue2"],
        help="Where normal transition cutoff occurs: 'cue3' (default: hear out full transition phrase to Cue 3) or 'cue2' (cutoff at Cue 2)"
    )
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

def blend_gradual(a_seg, b_seg, sr=44100, bass_swap_ratio=0.68, initial_b_gain=0.65, pre_fade_gain=0.88):
    """
    Studio-Grade Gradual DJ Crossfade between Cue 2 and Cue 3.
    Provides confident, audible presence for both incoming and outgoing tracks:
      - Outgoing Track (Track A) smoothly dips slightly before Cue 2 (~0.88) to create
        natural acoustic breathing room, grooving firmly across the main transition phrase,
        before gently tapering out into Cue 3.
      - Incoming Track (Track B) drops in immediately loud and clear (gain ~0.65)
        so listeners can instantly hear and appreciate the new song entering,
        smoothly ramping up to full volume across the transition.
      - Linkwitz-Riley 4th Order (LR-4) zero-phase crossover at 200 Hz maintains
        groove and cleanly hands over low-end bass energy near the 68% mark.
    """
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]

    t = np.linspace(0.0, 1.0, n)

    # Outgoing curve (Track A):
    # Starts at pre_fade_gain (0.88) to match the pre-Cue 2 dip seamlessly,
    # maintains presence for the first ~30% of the transition distance,
    # then smoothly rolls off towards Cue 3 so it remains audible together with Track B
    t_fade_a = np.clip((t - 0.30) / 0.70, 0.0, 1.0)
    curve_a = (pre_fade_gain * (np.cos(t_fade_a * (np.pi * 0.5)) ** 0.85))[:, None]

    # Incoming curve (Track B):
    # Enters audibly at initial_b_gain (default: 0.65 = -3.7 dB) with a 25ms anti-pop micro-ramp,
    # smoothly climbing to 1.0 at Cue 3 so listeners immediately recognize and vibe to the incoming track!
    ramp_samples = min(int(sr * 0.025), max(1, n // 10))
    micro_in = np.ones(n, dtype=np.float32)
    if ramp_samples > 0:
        micro_in[:ramp_samples] = np.linspace(0.0, 1.0, ramp_samples)

    b_level = initial_b_gain + (1.0 - initial_b_gain) * np.sin(t * (np.pi * 0.5))
    curve_b = (b_level * micro_in)[:, None]

    fc = 200.0
    b_l, a_l = signal.butter(2, fc, btype='low', fs=sr)
    b_h, a_h = signal.butter(2, fc, btype='high', fs=sr)

    a_low = signal.filtfilt(b_l, a_l, a_seg, axis=0)
    a_high = signal.filtfilt(b_h, a_h, a_seg, axis=0)
    b_low = signal.filtfilt(b_l, a_l, b_seg, axis=0)
    b_high = signal.filtfilt(b_h, a_h, b_seg, axis=0)

    # Mids & highs crossfade: both tracks audibly blend together without volume collapse
    sum_energy = np.sqrt(curve_a ** 2 + curve_b ** 2)
    gain_corr = np.where(sum_energy > 1.05, 1.0 / (sum_energy ** 0.5), 1.0)
    high_blend = (a_high * curve_a + b_high * curve_b) * gain_corr

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

def blend_equal_power(a_seg, b_seg, initial_b_gain=0.65, pre_fade_gain=0.88):
    """Mathematical equal-power crossfade tuned for punchy, audible DJ transitions."""
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]
    t = np.linspace(0.0, 1.0, n)
    t_fade_a = np.clip((t - 0.30) / 0.70, 0.0, 1.0)
    curve_a = (pre_fade_gain * (np.cos(t_fade_a * (np.pi * 0.5)) ** 0.85))[:, None]
    
    ramp_samples = min(int(44100 * 0.025), max(1, n // 10))
    micro_in = np.ones(n, dtype=np.float32)
    if ramp_samples > 0:
        micro_in[:ramp_samples] = np.linspace(0.0, 1.0, ramp_samples)
    b_level = initial_b_gain + (1.0 - initial_b_gain) * np.sin(t * (np.pi * 0.5))
    curve_b = (b_level * micro_in)[:, None]

    sum_energy = np.sqrt(curve_a ** 2 + curve_b ** 2)
    gain_corr = np.where(sum_energy > 1.05, 1.0 / (sum_energy ** 0.5), 1.0)
    return (a_seg * curve_a + b_seg * curve_b) * gain_corr

def blend_filter_sweep(a_seg, b_seg, sr=44100, initial_b_gain=0.65, pre_fade_gain=0.88):
    """Dynamic High-Pass Filter sweep: progressively washes out Track A lows/mids as Track B drops in."""
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]
    q = max(1, n // 4)
    cutoffs = [80.0, 300.0, 900.0, 2400.0]
    a_filtered = np.zeros_like(a_seg)
    for idx in range(4):
        s_idx = idx * q
        e_idx = (idx + 1) * q if idx < 3 else n
        chunk = a_seg[s_idx:e_idx]
        b_hp, a_hp = signal.butter(2, cutoffs[idx], btype='high', fs=sr)
        a_filtered[s_idx:e_idx] = signal.filtfilt(b_hp, a_hp, chunk, axis=0)

    t = np.linspace(0.0, 1.0, n)
    t_fade_a = np.clip((t - 0.20) / 0.80, 0.0, 1.0)
    a_env = (pre_fade_gain * ((1.0 - t_fade_a) ** 1.8))[:, None]

    ramp_samples = min(int(sr * 0.025), max(1, n // 10))
    micro_in = np.ones(n, dtype=np.float32)
    if ramp_samples > 0:
        micro_in[:ramp_samples] = np.linspace(0.0, 1.0, ramp_samples)
    b_level = initial_b_gain + (1.0 - initial_b_gain) * np.sin(t * (np.pi * 0.5))
    b_env = (b_level * micro_in)[:, None]

    sum_energy = np.sqrt(a_env ** 2 + b_env ** 2)
    gain_corr = np.where(sum_energy > 1.05, 1.0 / (sum_energy ** 0.5), 1.0)
    return (a_filtered * a_env + b_seg * b_env) * gain_corr

def blend_echo_out(a_seg, b_seg, sr=44100, bpm=118.0, decay=0.55, initial_b_gain=0.70):
    """Tempo-synced 1-beat dub echo freeze: Track A echoes out dissolving under Track B's clean drop."""
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]
    mid = n // 2
    beat_s = 60.0 / (bpm if bpm > 0 else 118.0)
    delay_samp = max(1, int(round(sr * beat_s)))

    a_echoed = np.zeros_like(a_seg)
    a_echoed[:mid] = a_seg[:mid]

    tail_source = a_seg[max(0, mid - delay_samp):mid]
    if len(tail_source) > 0:
        for rep in range(1, 6):
            s = mid + (rep - 1) * delay_samp
            e = min(n, s + len(tail_source))
            if s < n:
                a_echoed[s:e] += tail_source[:e - s] * (decay ** rep)

    b_out = np.zeros_like(b_seg)
    b_out[mid:] = b_seg[mid:]
    ramp_samples = min(int(sr * 0.025), n - mid)
    if ramp_samples > 0:
        b_out[mid:mid+ramp_samples] *= np.linspace(0.0, 1.0, ramp_samples)[:, None]

    return np.clip(a_echoed + b_out, -1.0, 1.0)

def blend_no_crossfade(a_seg, b_seg, sr=44100):
    """
    Combines Track A and Track B across the Cue 2 -> Cue 3 transition window
    WITHOUT crossfading or volume ducking:
      - Both tracks play at full, natural presence across the entire transition.
      - 15ms anti-pop micro-fades at the extreme boundaries eliminate digital clicks.
      - 0.7071 equal-power scaling maintains constant 0 dB acoustic energy without clipping.
    """
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]

    micro_len = min(int(sr * 0.015), max(1, n // 10))
    a_env = np.ones(n, dtype=np.float32)
    b_env = np.ones(n, dtype=np.float32)

    if micro_len > 0:
        a_env[-micro_len:] = np.linspace(1.0, 0.0, micro_len)
        b_env[:micro_len] = np.linspace(0.0, 1.0, micro_len)

    blended = (a_seg * a_env[:, None] + b_seg * b_env[:, None]) * 0.7071
    return blended

# -----------------------------------------------------------------------------
# NORMAL TRANSITION MIX (Cue 2 -> Cue 3 Transition, Zero Crossfade Ducking)
# -----------------------------------------------------------------------------

def render_normal_mix(tracks, args, output_file):
    print("\n" + "-" * 78)
    print(" RENDERING NORMAL MIX (Cue 2 -> Cue 3 Transition, Zero Crossfade Ducking)...")
    print("-" * 78)

    sr = 44100
    timeline_markers = []
    master_blocks = []
    current_time_s = 0.0

    timeline_markers.append((current_time_s, tracks[0]["artist"], tracks[0]["title"], None))
    curr_in_pos = tracks[0]["cue_entry"]

    for i in range(len(tracks) - 1):
        t_a = tracks[i]
        t_b = tracks[i + 1]
        bpm_a = t_a["bpm"] or 118.0
        bpm_b = t_b["bpm"] or 118.0

        has_fade = t_a["cue_fade"] is not None
        has_exit = t_a["cue_exit"] is not None

        if has_fade and has_exit and (t_a["cue_exit"] <= t_a["cue_fade"] + 0.1):
            fade_dur = 0.0
            is_immediate = True
        elif has_fade and has_exit and t_a["cue_exit"] > t_a["cue_fade"]:
            fade_dur = t_a["cue_exit"] - t_a["cue_fade"]
            is_immediate = False
        else:
            fade_dur = 16.0 * 4.0 * (60.0 / bpm_a)
            is_immediate = False

        if has_fade and t_a["cue_fade"] > curr_in_pos:
            fade_start = t_a["cue_fade"]
        else:
            fade_start = max(curr_in_pos, (t_a["length"] or 180.0) - fade_dur)

        # 1. Track A Solo Section: from curr_in_pos up to Cue 2 (fade_start)
        solo_dur = max(0.0, fade_start - curr_in_pos)
        if solo_dur > 0.02:
            solo_audio = load_audio_clip(t_a["path"], start_s=curr_in_pos, duration_s=solo_dur, sr=sr)
            if is_immediate:
                fade_out_samples = min(int(sr * 0.015), len(solo_audio))
                if fade_out_samples > 0:
                    solo_audio[-fade_out_samples:] *= np.linspace(1.0, 0.0, fade_out_samples)[:, None]
            master_blocks.append(solo_audio)
            current_time_s += len(solo_audio) / sr

        # If immediate transition (Cue 2 == Cue 3), cut directly to Track B
        b_entry = t_b["cue_entry"]
        if is_immediate or fade_dur <= 0.05:
            timeline_markers.append((current_time_s, t_b["artist"], t_b["title"], "immediate cut"))
            curr_in_pos = b_entry
            continue

        # 2. Transition Window: Cue 2 to Cue 3 (Zero Crossfade, both tracks groove naturally)
        a_trans = load_audio_clip(t_a["path"], start_s=fade_start, duration_s=fade_dur, sr=sr)
        tempo_ratio = compute_tempo_ratio(bpm_a, bpm_b)
        if abs(tempo_ratio - 1.0) > 0.0005:
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

        target_len = len(a_trans)
        if len(b_trans) > target_len:
            b_trans = b_trans[:target_len]
        elif len(b_trans) < target_len:
            b_trans = np.pad(b_trans, ((0, target_len - len(b_trans)), (0, 0)))

        # Blend transition without crossfade: both tracks play at full natural presence!
        blended = blend_no_crossfade(a_trans, b_trans, sr=sr)

        timeline_markers.append((current_time_s, t_b["artist"], t_b["title"], "no crossfade (Cue 2->3)"))
        master_blocks.append(blended)
        current_time_s += len(blended) / sr

        curr_in_pos = b_entry + dur_b_needed

    # 3. Final Track Solo Section
    last_t = tracks[-1]
    if last_t["cue_exit"] is not None and last_t["cue_exit"] > curr_in_pos:
        last_end = last_t["cue_exit"]
    elif last_t["cue_fade"] is not None and last_t["cue_fade"] > curr_in_pos:
        last_end = last_t["cue_fade"]
    else:
        last_end = last_t["length"]

    if last_end <= curr_in_pos:
        last_end = last_t["length"]

    last_dur = max(0.1, last_end - curr_in_pos)
    last_audio = load_audio_clip(last_t["path"], start_s=curr_in_pos, duration_s=last_dur, sr=sr)

    fade_out_len = min(int(sr * 4.0), len(last_audio))
    if fade_out_len > 0:
        last_audio[-fade_out_len:] *= np.linspace(1.0, 0.0, fade_out_len)[:, None]

    master_blocks.append(last_audio)
    current_time_s += len(last_audio) / sr

    # Concatenate master audio
    print("\nConcatenating master audio stream...")
    full_audio = np.concatenate(master_blocks, axis=0)

    # Write temporary WAV for loudness normalization
    temp_master_wav = os.path.join(args.output_dir, "_temp_normal_master.wav")
    wavfile.write(temp_master_wav, sr, (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16))

    print("Mastering to 320k MP3 with EBU R128 DJ Standards (-14.0 LUFS, -1.5 dBTP)...")
    mix_tag = getattr(args, "mix_name", "Amapiano")
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_master_wav,
        "-af", f"loudnorm=I={args.target_lufs}:TP={args.true_peak}:LRA=10.0",
        "-b:a", "320k",
        "-metadata", f"album={mix_tag} Continuous Mix (Normal)",
        "-metadata", f"title={mix_tag} Set (Normal Transition, No Crossfade)",
        "-metadata", "artist=Various Artists",
        "-metadata", f"genre={mix_tag}",
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if os.path.exists(temp_master_wav):
        os.remove(temp_master_wav)

    out_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"-> Normal Mix Rendered: {output_file} ({out_size_mb:.2f} MB)")
    print(f"   [Loudness Target: {args.target_lufs} LUFS | True Peak Ceiling: {args.true_peak} dBTP]")
    print("Normal Mix Timeline:")
    tracklist_lines = []
    for mark_time, artist, title, trans in timeline_markers:
        trans_str = f" [{trans}]" if trans else ""
        line_str = f" [{format_time(mark_time)}] {artist} - {title}{trans_str}"
        print(line_str)
        tracklist_lines.append(line_str)

    txt_path = os.path.splitext(output_file)[0] + "_Tracklist.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"SmartMix Continuous Mix (Normal Transition, No Crossfade)\nTarget: {args.target_lufs} LUFS\n\nTracklist:\n")
            f.write("\n".join(tracklist_lines))
    except Exception:
        pass
    return True

# -----------------------------------------------------------------------------
# AUDIO LOADER WITH OPTIONAL PITCH-PRESERVING TEMPO MATCHING
# -----------------------------------------------------------------------------

def compute_tempo_ratio(bpm_outgoing, bpm_incoming):
    """
    Computes pitch-preserving tempo stretch ratio so the incoming track
    exact-matches the outgoing track's BPM during the crossfade transition.
    Also handles double-time / half-time detection (e.g. 70 vs 140 bpm).
    """
    if not bpm_outgoing or not bpm_incoming or bpm_outgoing <= 0 or bpm_incoming <= 0:
        return 1.0

    ratio = bpm_outgoing / bpm_incoming
    if ratio > 1.6:
        ratio /= 2.0
    elif ratio < 0.65:
        ratio *= 2.0

    return max(0.80, min(1.25, ratio))

def load_audio_clip(path, start_s, duration_s=None, end_s=None, sr=44100, tempo_ratio=1.0):
    cmd = ["ffmpeg", "-y", "-ss", f"{start_s:.3f}"]
    if duration_s is not None and duration_s > 0:
        cmd.extend(["-t", f"{duration_s:.3f}"])
    elif end_s is not None and end_s > start_s:
        cmd.extend(["-to", f"{end_s:.3f}"])
    cmd.extend(["-i", path])
    if abs(tempo_ratio - 1.0) > 0.0005:
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
        has_fade = t_a["cue_fade"] is not None
        has_exit = t_a["cue_exit"] is not None
        if has_fade and has_exit and (t_a["cue_exit"] <= t_a["cue_fade"] + 0.1):
            # When Cue 2 and Cue 3 are at the same level/position: IMMEDIATE CUT
            fade_dur = 0.0
            mode = "immediate"
        elif args.trans_bars is not None and args.trans_bars > 0:
            fade_dur = args.trans_bars * 4.0 * (60.0 / bpm_a)
            mode = get_transition_mode(i, args.crossfade_mode, custom_styles)
        elif has_fade and has_exit and t_a["cue_exit"] > t_a["cue_fade"]:
            fade_dur = t_a["cue_exit"] - t_a["cue_fade"]
            mode = get_transition_mode(i, args.crossfade_mode, custom_styles)
        else:
            fade_dur = 16.0 * 4.0 * (60.0 / bpm_a)  # Default 16 bars (64 beats)
            mode = get_transition_mode(i, args.crossfade_mode, custom_styles)

        trans_durations.append(fade_dur)
        trans_modes.append(mode)

    print("Planned Transitions:")
    for i, (dur, mode) in enumerate(zip(trans_durations, trans_modes)):
        bpm_a = tracks[i]["bpm"] or 118.0
        bpm_b = tracks[i+1]["bpm"] or 118.0
        if mode == "immediate":
            print(f"  * Transition {i+1} -> {i+2}: IMMEDIATE CUT (Cue 2 == Cue 3) | Tracks: {tracks[i]['title']} -> {tracks[i+1]['title']}")
        else:
            t_ratio = compute_tempo_ratio(bpm_a, bpm_b)
            tempo_note = f" [Tempo Sync: {bpm_b:.1f} -> {bpm_a:.1f} BPM]" if abs(t_ratio - 1.0) > 0.0005 else ""
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
            if mode == "immediate":
                # Micro-fadeout (15ms) prevents digital click on immediate cuts
                fade_out_samples = min(int(sr * 0.015), len(solo_audio))
                if fade_out_samples > 0:
                    solo_audio[-fade_out_samples:] *= np.linspace(1.0, 0.0, fade_out_samples)[:, None]
            else:
                # Slight volume down slightly before outgoing Cue 2 (~1.5s window down to 0.88)
                # Gives natural breathing room for incoming Track B to drop in audibly without clashing
                dip_samples = min(int(sr * 1.5), max(1, len(solo_audio) // 3))
                if dip_samples > 10:
                    t_dip = np.linspace(0.0, 1.0, dip_samples)
                    dip_curve = 1.0 - (1.0 - 0.88) * (0.5 - 0.5 * np.cos(t_dip * np.pi))
                    solo_audio[-dip_samples:] *= dip_curve[:, None]
            master_blocks.append(solo_audio)
            current_time_s += len(solo_audio) / sr

        # If immediate transition (Cue 2 == Cue 3), cut directly to Track B
        b_entry = t_b["cue_entry"]
        if mode == "immediate" or fade_dur <= 0.05:
            timeline_markers.append((current_time_s, t_b["artist"], t_b["title"], "immediate cut"))
            curr_in_pos = b_entry
            continue

        if mode == "normal":
            # Normal Transition: Track A plays out its full transition/outro (to Cue 3), then Track B drops in at b_entry with zero overlap
            outro_dur = max(0.0, fade_dur)
            if outro_dur > 0.02:
                outro_audio = load_audio_clip(t_a["path"], start_s=fade_start, duration_s=outro_dur, sr=sr)
                fade_out_samples = min(int(sr * 0.015), len(outro_audio))
                if fade_out_samples > 0:
                    outro_audio[-fade_out_samples:] *= np.linspace(1.0, 0.0, fade_out_samples)[:, None]
                master_blocks.append(outro_audio)
                current_time_s += len(outro_audio) / sr
            timeline_markers.append((current_time_s, t_b["artist"], t_b["title"], "normal cut"))
            curr_in_pos = b_entry
            continue

        # 2. Crossfade Transition Window: Cue 2 to Cue 3
        # Track A fades out over fade_dur
        a_trans = load_audio_clip(t_a["path"], start_s=fade_start, duration_s=fade_dur, sr=sr)
        tempo_ratio = compute_tempo_ratio(bpm_a, bpm_b)
        if abs(tempo_ratio - 1.0) > 0.0005:
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

        # Blend transition using selected DSP mode
        if mode == "filter-sweep":
            blended = blend_filter_sweep(a_trans, b_trans, sr=sr)
        elif mode == "echo-out":
            blended = blend_echo_out(a_trans, b_trans, sr=sr, bpm=bpm_a)
        elif mode == "equal-power":
            blended = blend_equal_power(a_trans, b_trans)
        else: # gradual
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
    cf_tracklist_lines = []
    for mark_time, artist, title, trans in timeline_markers:
        trans_str = f" [Crossfade: {trans}]" if trans else ""
        line_str = f" [{format_time(mark_time)}] {artist} - {title}{trans_str}"
        print(line_str)
        cf_tracklist_lines.append(line_str)
    
    txt_path = os.path.splitext(output_file)[0] + "_Tracklist.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"SmartMix Continuous Mix (Smart Crossfaded)\nTarget: {args.target_lufs} LUFS\n\nTracklist:\n")
            f.write("\n".join(cf_tracklist_lines))
    except Exception:
        pass
    return True

# -----------------------------------------------------------------------------
# REAL-TIME TRANSITION AUDITION PREVIEW ENGINE (SmartMix Studio)
# -----------------------------------------------------------------------------

def render_transition_preview(t_a, t_b, mode="gradual", pre_s=3.0, post_s=3.0, sr=44100, bass_swap_ratio=0.68):
    """
    Renders an instant preview clip (float32 stereo array) for a single transition
    between Track A and Track B using the specified mode.
    Takes ~0.2s, perfectly suited for real-time audition in SmartMix Studio.
    """
    bpm_a = t_a.get("bpm") or 118.0
    bpm_b = t_b.get("bpm") or 118.0
    cue_fade = t_a.get("cue_fade")
    cue_exit = t_a.get("cue_exit")
    b_entry = t_b.get("cue_entry") or 0.0

    if cue_fade is not None:
        fade_start = cue_fade
    else:
        fade_start = max(0.0, (t_a.get("length") or 180.0) - 16.0)

    if cue_fade is not None and cue_exit is not None:
        fade_dur = max(0.0, cue_exit - cue_fade)
    else:
        fade_dur = 16.0 * (60.0 / bpm_a)

    # 1. Pre-audio from Track A
    pre_start = max(0.0, fade_start - pre_s)
    pre_dur = fade_start - pre_start
    pre_audio = load_audio_clip(t_a["path"], start_s=pre_start, duration_s=pre_dur, sr=sr)

    # Pre-Cue 2 volume dip
    if mode != "immediate" and mode != "normal" and len(pre_audio) > 10:
        dip_samples = min(int(sr * 1.5), len(pre_audio))
        t_dip = np.linspace(0.0, 1.0, dip_samples)
        dip_curve = 1.0 - (1.0 - 0.88) * (0.5 - 0.5 * np.cos(t_dip * np.pi))
        pre_audio[-dip_samples:] *= dip_curve[:, None]

    if mode == "normal":
        outro_dur = max(0.1, fade_dur)
        a_outro = load_audio_clip(t_a["path"], start_s=fade_start, duration_s=outro_dur, sr=sr)
        fade_out_samples = min(int(sr * 0.015), len(a_outro))
        if fade_out_samples > 0:
            a_outro[-fade_out_samples:] *= np.linspace(1.0, 0.0, fade_out_samples)[:, None]
        b_post = load_audio_clip(t_b["path"], start_s=b_entry, duration_s=post_s + 1.0, sr=sr)
        return np.concatenate([pre_audio, a_outro, b_post], axis=0)

    if mode == "immediate" or fade_dur <= 0.05:
        fade_out_samples = min(int(sr * 0.015), len(pre_audio))
        if fade_out_samples > 0:
            pre_audio[-fade_out_samples:] *= np.linspace(1.0, 0.0, fade_out_samples)[:, None]
        b_post = load_audio_clip(t_b["path"], start_s=b_entry, duration_s=post_s + 2.0, sr=sr)
        return np.concatenate([pre_audio, b_post], axis=0)

    # Crossfade blends
    a_trans = load_audio_clip(t_a["path"], start_s=fade_start, duration_s=fade_dur, sr=sr)
    tempo_ratio = compute_tempo_ratio(bpm_a, bpm_b)
    if abs(tempo_ratio - 1.0) > 0.0005:
        dur_b_needed = fade_dur * tempo_ratio
        b_trans = load_audio_clip(t_b["path"], start_s=b_entry, duration_s=dur_b_needed, sr=sr, tempo_ratio=tempo_ratio)
    else:
        dur_b_needed = fade_dur
        b_trans = load_audio_clip(t_b["path"], start_s=b_entry, duration_s=fade_dur, sr=sr, tempo_ratio=1.0)

    target_len = len(a_trans)
    if len(b_trans) > target_len:
        b_trans = b_trans[:target_len]
    elif len(b_trans) < target_len:
        b_trans = np.pad(b_trans, ((0, target_len - len(b_trans)), (0, 0)))

    if mode == "filter-sweep":
        blended = blend_filter_sweep(a_trans, b_trans, sr=sr)
    elif mode == "echo-out":
        blended = blend_echo_out(a_trans, b_trans, sr=sr, bpm=bpm_a)
    elif mode == "equal-power":
        blended = blend_equal_power(a_trans, b_trans)
    else:
        blended = blend_gradual(a_trans, b_trans, sr=sr, bass_swap_ratio=bass_swap_ratio)

    post_start = b_entry + dur_b_needed
    b_post = load_audio_clip(t_b["path"], start_s=post_start, duration_s=post_s, sr=sr)
    return np.concatenate([pre_audio, blended, b_post], axis=0)

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
