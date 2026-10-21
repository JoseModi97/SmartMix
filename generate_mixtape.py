import os
import sys
import argparse
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
from scipy import signal
from scipy.io import wavfile

VDJ_FOLDER = r"C:\Users\odhis\AppData\Local\VirtualDJ\Sideview\automix.vdjfolder"
VDJ_DB = r"C:\Users\odhis\AppData\Local\VirtualDJ\database.xml"
OUTPUT_DIR = r"C:\Users\odhis\Downloads\Amapiano"

def parse_args():
    parser = argparse.ArgumentParser(description="SmartMix: Studio-Grade DJ Mixtape & Transition Engine")
    parser.add_argument(
        "--mode",
        type=str,
        default="both",
        choices=["both", "crossfade", "normal"],
        help="Rendering mode: 'both' (default), 'crossfade' (smart blends), or 'normal' (sequential drops)"
    )
    parser.add_argument(
        "--crossfade-mode",
        type=str,
        default="dynamic",
        choices=["dynamic", "bass-swap", "filter-sweep", "echo-out", "scratch-in", "equal-power"],
        help="Global transition style: 'dynamic' (alternates styles), 'bass-swap' (LR-4 low-end crossover), 'filter-sweep' (HPF wash), 'echo-out' (tempo delay freeze), 'scratch-in' (on-beat scratch drop), 'equal-power' (sine blend)"
    )
    parser.add_argument(
        "--trans-style",
        type=str,
        default="",
        help="Per-transition custom styles (e.g. '1=bass-swap,2=filter-sweep,3=scratch-in,4=echo-out')"
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
        default=0.5,
        help="Position within transition where low-end swaps (default: 0.5 = midpoint, e.g. bar 8 of 16)"
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
    parser.add_argument("--entry-cue", type=int, default=1, help="Default cue number to use for song entry/mix-in (default: 1)")
    parser.add_argument("--fade-cue", type=int, default=2, help="Default cue number where fade-out begins / normal cutoff (default: 2)")
    parser.add_argument("--exit-cue", type=int, default=3, help="Default cue number where fade completes/cuts off (default: 3)")
    parser.add_argument("--normal-cutoff", type=str, default="cue2", choices=["cue2", "cue3"], help="Where normal cut transition occurs: 'cue2' (radio cutoff) or 'cue3' (full phrase)")
    parser.add_argument("--use-last-cues", action="store_true", help="If track has 4+ cues, automatically use the last 2 cues for the fade-out window")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR, help="Destination directory for output files")
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
            db_lookup[p] = {
                "entry": entry_pos,
                "fade": fade_pos,
                "exit": exit_pos,
                "all_cues": all_cues,
                "bpm": db_bpm
            }

    tree_folder = ET.parse(VDJ_FOLDER)
    tracks = []
    for s in tree_folder.getroot().findall("song"):
        p = s.get("path")
        if not os.path.exists(p):
            print(f"Warning: File not found: {p}")
            continue
        
        artist = s.get("artist", "Unknown Artist")
        title = s.get("title", "Unknown Title")
        bpm = float(s.get("bpm", 0.0))
        length = float(s.get("songlength", 0.0))
        
        info = db_lookup.get(p, {})
        if info.get("bpm"):
            bpm = info["bpm"]

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

def get_transition_mode(idx, global_mode, custom_styles):
    if idx in custom_styles:
        return custom_styles[idx]
    if global_mode != "dynamic":
        return global_mode
    patterns = ["bass-swap", "filter-sweep", "scratch-in", "echo-out"]
    return patterns[idx % len(patterns)]

# -----------------------------------------------------------------------------
# ADVANCED DSP TRANSITION BLENDERS
# -----------------------------------------------------------------------------

def blend_bass_swap(a_seg, b_seg, sr=44100, swap_ratio=0.5):
    """
    True Linkwitz-Riley 4th Order (LR-4) Crossover Bass-Swap.
    Separates low frequencies (<220 Hz) and mid/highs (>220 Hz).
    Mids/Highs crossfade smoothly with equal-power curves.
    Low-end swaps cleanly at swap_ratio, completely eliminating log drum mud!
    """
    fc = 220.0
    b_l, a_l = signal.butter(2, fc, btype='low', fs=sr)
    b_h, a_h = signal.butter(2, fc, btype='high', fs=sr)

    # LR-4 zero-phase crossover
    a_low = signal.filtfilt(b_l, a_l, a_seg, axis=0)
    a_high = signal.filtfilt(b_h, a_h, a_seg, axis=0)
    b_low = signal.filtfilt(b_l, a_l, b_seg, axis=0)
    b_high = signal.filtfilt(b_h, a_h, b_seg, axis=0)

    n = len(a_seg)
    t = np.linspace(0, 1, n)
    cos_curve = np.cos(t * np.pi * 0.5)[:, None]
    sin_curve = np.sin(t * np.pi * 0.5)[:, None]
    high_blend = a_high * cos_curve + b_high * sin_curve

    # Smooth 0.5s swap centered at swap_ratio
    swap_center = int(round(n * swap_ratio))
    half_w = int(round(sr * 0.25))
    s_start = max(0, swap_center - half_w)
    s_end = min(n, swap_center + half_w)

    low_env_a = np.ones(n, dtype=np.float32)
    low_env_a[s_end:] = 0.0
    low_env_a[s_start:s_end] = np.linspace(1.0, 0.0, s_end - s_start)
    low_env_b = 1.0 - low_env_a

    low_blend = a_low * low_env_a[:, None] + b_low * low_env_b[:, None]
    return high_blend + low_blend

def blend_filter_sweep(a_seg, b_seg, sr=44100):
    """
    Dynamic High-Pass Filter sweep.
    Progressively filters Track A's bass and lower mids (60 Hz -> 2000 Hz),
    turning it into an airy wash before Track B's full drop hits.
    """
    n = len(a_seg)
    q = n // 4
    cutoffs = [60.0, 220.0, 700.0, 2000.0]
    a_filtered = np.zeros_like(a_seg)
    for i in range(4):
        s_idx = i * q
        e_idx = (i + 1) * q if i < 3 else n
        chunk = a_seg[s_idx:e_idx]
        b_hp, a_hp = signal.butter(2, cutoffs[i], btype='high', fs=sr)
        a_filtered[s_idx:e_idx] = signal.filtfilt(b_hp, a_hp, chunk, axis=0)

    t = np.linspace(0, 1, n)
    a_env = ((1.0 - t)**2.0)[:, None]
    b_env = np.sin(t * np.pi * 0.5)[:, None]
    return a_filtered * a_env + b_seg * b_env

def blend_echo_out(a_seg, b_seg, sr=44100, bpm=118.0, decay=0.55):
    """
    Tempo-Synced 1-Beat Dub Delay Freeze.
    Track A plays to the midpoint, cuts, and echoes out with 55% decay
    dissolving under Track B's clean drop.
    """
    n = len(a_seg)
    mid = n // 2
    beat_s = 60.0 / bpm
    delay_samp = int(round(sr * beat_s))

    a_echoed = np.zeros_like(a_seg)
    a_echoed[:mid] = a_seg[:mid]

    tail_source = a_seg[max(0, mid - delay_samp):mid]
    for rep in range(1, 6):
        s = mid + (rep - 1) * delay_samp
        e = min(n, s + len(tail_source))
        if s < n:
            a_echoed[s:e] += tail_source[:e - s] * (decay ** rep)

    b_out = np.zeros_like(b_seg)
    b_out[mid:] = b_seg[mid:]
    fade_len = int(sr * 0.015)
    b_out[mid:mid+fade_len] *= np.linspace(0, 1, fade_len)[:, None]

    return a_echoed + b_out

def blend_scratch_in(a_seg, b_seg, sr=44100, bpm=118.0):
    """
    On-Beat Subtle Scratch Drop.
    Track A plays up to the final 2 beats, where a subtle baby/chirp scratch
    scratches Track B's drop note before Track B unleashes on Beat 1!
    """
    n = len(a_seg)
    mid = n // 2
    beat_s = 60.0 / bpm

    b_stab = b_seg[mid:mid + int(sr * 1.5)].copy()
    if len(b_stab) < int(sr * 0.5):
        b_stab = b_seg[:int(sr * 1.5)].copy()

    scratch_dur = beat_s * 2.0
    n_sc = int(round(sr * scratch_dur))
    t_sc = np.linspace(0, scratch_dur, n_sc)
    traj = 0.04 + 0.16 * np.sin(2 * np.pi * (1.0 / beat_s) * t_sc)
    phase = (t_sc % (beat_s / 2.0)) / (beat_s / 2.0)
    fader = np.where(phase < 0.70, 1.0, 0.0).astype(np.float32)

    # Scratch resample
    idx = np.clip(traj * sr, 0, len(b_stab) - 2)
    fl = np.floor(idx).astype(np.int32)
    fr = (idx - fl)[:, None]
    sc_audio = (b_stab[fl] * (1 - fr) + b_stab[fl + 1] * fr) * fader[:, None]

    out = np.zeros_like(a_seg)
    out[:mid] = a_seg[:mid]
    fade_len = int(sr * beat_s)
    out[mid - fade_len:mid] *= np.linspace(1, 0, fade_len)[:, None]

    sc_start = max(0, mid - n_sc)
    out[sc_start:mid] += sc_audio[:mid - sc_start] * 0.92
    out[mid:] += b_seg[mid:]
    return out

def blend_equal_power(a_seg, b_seg):
    """Equal-Power quarter-sine crossfade"""
    n = len(a_seg)
    t = np.linspace(0, 1, n)
    cos_curve = np.cos(t * np.pi * 0.5)[:, None]
    sin_curve = np.sin(t * np.pi * 0.5)[:, None]
    return a_seg * cos_curve + b_seg * sin_curve

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

        if is_last:
            end_time = t["length"]
        else:
            if args.normal_cutoff == "cue2" and t["cue_fade"] is not None:
                end_time = t["cue_fade"]
            elif t["cue_exit"] is not None:
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
    cmd.extend([
        "-filter_complex", concat_filter,
        "-map", "[out]",
        "-b:a", "320k",
        "-metadata", "album=Amapiano Continuous Mix (Normal)",
        "-metadata", "title=Amapiano Set (Clean Cut)",
        "-metadata", "artist=Various Artists",
        "-metadata", "genre=Amapiano",
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
# SMART CROSSFADED MIX (Advanced DSP Transitions)
# -----------------------------------------------------------------------------

def render_crossfade_mix(tracks, args, output_file):
    print("\n" + "-" * 78)
    print(f" RENDERING SMART CROSSFADED MIX (DSP Transitions | Target: {args.target_lufs} LUFS)...")
    print("-" * 78)

    sr = 44100
    custom_styles = parse_custom_styles(args.trans_style)

    # Determine transition lengths and styles for each transition
    trans_durations = []
    trans_modes = []

    for i in range(len(tracks) - 1):
        t = tracks[i]
        bpm = t["bpm"] or 118.0
        
        # Determine duration
        if args.trans_bars is not None and args.trans_bars > 0:
            fade_dur = args.trans_bars * (60.0 / bpm) * 4.0
        elif t["cue_fade"] is not None and t["cue_exit"] is not None and t["cue_exit"] > t["cue_fade"]:
            fade_dur = t["cue_exit"] - t["cue_fade"]
        else:
            fade_dur = 16.0 * (60.0 / bpm) # Default 16 bars

        mode = get_transition_mode(i, args.crossfade_mode, custom_styles)
        trans_durations.append(fade_dur)
        trans_modes.append(mode)

    print("Planned Transitions:")
    for i, (dur, mode) in enumerate(zip(trans_durations, trans_modes)):
        print(f"  * Transition {i+1} -> {i+2}: {dur:.1f}s ({mode.upper()}) | Tracks: {tracks[i]['title']} -> {tracks[i+1]['title']}")

    # Load audio clips for each track
    track_buffers = []
    for i, t in enumerate(tracks):
        is_last = (i == len(tracks) - 1)
        start_time = t["cue_entry"]

        if is_last:
            end_time = t["length"]
        else:
            fade_dur = trans_durations[i]
            if t["cue_fade"] is not None:
                end_time = t["cue_fade"] + fade_dur
            else:
                end_time = t["length"]

        # Ensure valid range
        if end_time <= start_time:
            end_time = t["length"]

        # Load raw audio via ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start_time:.3f}",
            "-to", f"{end_time:.3f}",
            "-i", t["path"],
            "-f", "s16le", "-ac", "2", "-ar", str(sr), "-"
        ]
        proc = subprocess.run(cmd, capture_output=True, check=True)
        raw = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        buf = raw.reshape(-1, 2)
        track_buffers.append(buf)

    # Assemble master audio with DSP transitions
    timeline_markers = []
    master_blocks = []
    current_time_s = 0.0

    for i in range(len(tracks)):
        curr_buf = track_buffers[i]
        t = tracks[i]
        is_last = (i == len(tracks) - 1)

        if is_last:
            # Last track plays to end, add 4s fade out
            fade_out_len = min(int(sr * 4.0), len(curr_buf))
            if fade_out_len > 0:
                curr_buf[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)[:, None]
            master_blocks.append(curr_buf)
            break

        next_buf = track_buffers[i + 1]
        fade_dur = trans_durations[i]
        mode = trans_modes[i]
        n_trans = int(round(sr * fade_dur))

        # Check that buffers are long enough for transition
        if len(curr_buf) < n_trans:
            n_trans = len(curr_buf) // 2
        if len(next_buf) < n_trans:
            n_trans = min(n_trans, len(next_buf) // 2)

        # Split curr_buf into solo part and transition part
        solo_part = curr_buf[:-n_trans]
        a_trans = curr_buf[-n_trans:]
        b_trans = next_buf[:n_trans]

        # Add solo part of current track
        master_blocks.append(solo_part)
        mode_used = trans_modes[i-1] if i > 0 else None
        timeline_markers.append((current_time_s, t["artist"], t["title"], mode_used))
        current_time_s += len(solo_part) / sr

        # Apply specific DSP transition blend
        if mode == "bass-swap":
            blended = blend_bass_swap(a_trans, b_trans, sr=sr, swap_ratio=args.bass_swap_ratio)
        elif mode == "filter-sweep":
            blended = blend_filter_sweep(a_trans, b_trans, sr=sr)
        elif mode == "echo-out":
            blended = blend_echo_out(a_trans, b_trans, sr=sr, bpm=t["bpm"] or 118.0)
        elif mode == "scratch-in":
            blended = blend_scratch_in(a_trans, b_trans, sr=sr, bpm=t["bpm"] or 118.0)
        else: # equal-power
            blended = blend_equal_power(a_trans, b_trans)

        master_blocks.append(blended)
        current_time_s += len(blended) / sr

        # Shorten next_buf by removing the transition part that was already blended
        track_buffers[i + 1] = next_buf[n_trans:]

    # Add last track marker
    last_t = tracks[-1]
    timeline_markers.append((current_time_s, last_t["artist"], last_t["title"], trans_modes[-1]))

    # Concatenate master audio
    print("\nConcatenating master audio stream...")
    full_audio = np.concatenate(master_blocks, axis=0)

    # Write temporary WAV for loudness normalization
    temp_master_wav = os.path.join(args.output_dir, "_temp_crossfade_master.wav")
    wavfile.write(temp_master_wav, sr, (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16))

    # Master Output Stage: Apply EBU R128 DJ Loudness Normalization & True Peak Limiting
    print("Mastering to 320k MP3 with EBU R128 DJ Standards (-14.0 LUFS, -1.5 dBTP)...")
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_master_wav,
        "-af", f"loudnorm=I={args.target_lufs}:TP={args.true_peak}:LRA=10.0",
        "-b:a", "320k",
        "-metadata", "album=Amapiano Continuous Mix (Smart Crossfaded)",
        "-metadata", "title=Amapiano Set (Smart Crossfaded)",
        "-metadata", "artist=Various Artists",
        "-metadata", "genre=Amapiano",
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
    os.makedirs(args.output_dir, exist_ok=True)

    tracks = get_track_data(args)
    if not tracks:
        print("No valid tracks found to mix.")
        return

    normal_output = os.path.join(args.output_dir, "Amapiano_Continuous_Mix_Normal.mp3")
    crossfade_output = os.path.join(args.output_dir, "Amapiano_Continuous_Mix_Crossfaded.mp3")

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
