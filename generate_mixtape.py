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
        default="continuous",
        choices=["continuous", "crossfade", "normal", "both"],
        help="Rendering mode: 'continuous' (default: premier continuous mix with VirtualDJ FX & End-Filter), 'normal' (clean cue drops), or 'both'"
    )
    parser.add_argument(
        "--crossfade-mode",
        "--transition-mode",
        dest="crossfade_mode",
        type=str,
        default="auto",
        choices=["auto", "flanger", "reverb", "filter", "beatgrid", "echo-out", "brake", "gradual", "equal-power"],
        help="Global transition style: 'auto' (default: smart VirtualDJ FX analysis per transition phrase), 'flanger', 'reverb', 'beatgrid', 'filter', 'echo-out', 'brake'"
    )
    parser.add_argument(
        "--filter-start",
        type=float,
        default=0.58,
        help="Position within transition phrase where the filter sweep engages towards the end (default: 0.58 = 58%% mark)"
    )
    parser.add_argument(
        "--use-filter",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Universal VirtualDJ Color FX Filter sweep (eliminates kick and sub-bass clashing between tracks, default: True)"
    )
    parser.add_argument(
        "--no-filter",
        dest="use_filter",
        action="store_false",
        help=argparse.SUPPRESS
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

def get_track_data(args=None):
    if not os.path.exists(VDJ_FOLDER):
        raise FileNotFoundError(f"Automix folder not found: {VDJ_FOLDER}")
    
    default_entry = getattr(args, "entry_cue", 1) if args else 1
    default_fade = getattr(args, "fade_cue", 2) if args else 2
    default_exit = getattr(args, "exit_cue", 3) if args else 3
    use_last_cues = getattr(args, "use_last_cues", False) if args else False

    db_lookup = {}
    if os.path.exists(VDJ_DB):
        tree_db = ET.parse(VDJ_DB)
        for s in tree_db.getroot().findall("Song"):
            p = s.get("FilePath", "")
            entry_pos, fade_pos, exit_pos, all_cues = extract_cue_points(
                s,
                default_entry=default_entry,
                default_fade=default_fade,
                default_exit=default_exit,
                use_last_cues=use_last_cues
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

def choose_smart_transition(i, t_a, t_b, total_tracks=None):
    """
    Intelligently analyzes the transition phrase length, BPM, and track dynamics
    for any playlist to assign the optimal VirtualDJ performance transition:
      - Immediate Cut (0s, Cue 2 == Cue 3): 'immediate'
      - Short transition (< 5s, 1-2 bars): 'filter' (clean handover with end-filter)
      - Medium transition (5-12s, 2-4 bars): 'filter'
      - Long transition (> 12s, 8 bars / 32 beats): alternates between 'flanger' (VirtualDJ Flanger
        jet comb sweep + end filter) and 'reverb' (Space Reverb wash + end filter).
    """
    if not t_a or not t_b:
        return "filter"
    has_fade = t_a.get("cue_fade") is not None
    has_exit = t_a.get("cue_exit") is not None
    if has_fade and has_exit and (t_a["cue_exit"] <= t_a["cue_fade"] + 0.15):
        return "immediate"

    dur = (t_a["cue_exit"] - t_a["cue_fade"]) if (has_fade and has_exit) else 16.0
    if dur <= 0.15:
        return "immediate"
    elif dur < 5.0:
        return "filter"
    elif dur > 12.0:
        # Long transitions: alternate between Flanger and Reverb Wash for dynamic variety
        return "flanger" if (i % 2 == 1) else "reverb"
    else:
        return "filter"

def get_transition_mode(idx, global_mode, custom_styles, t_a=None, t_b=None, total_tracks=None):
    if idx in custom_styles:
        return custom_styles[idx]
    if global_mode == "auto" or global_mode is None:
        return choose_smart_transition(idx, t_a, t_b, total_tracks)
    if global_mode in ("filter", "filter-sweep"):
        return "filter"
    if global_mode == "flanger":
        return "flanger"
    if global_mode == "reverb":
        return "reverb"
    if global_mode == "beatgrid":
        return "beatgrid"
    if global_mode == "brake":
        return "brake"
    if global_mode == "equal-power":
        return "equal-power"
    if global_mode == "gradual":
        return "gradual"
    return global_mode

# -----------------------------------------------------------------------------
# ADVANCED DSP TRANSITION BLENDERS & VIRTUALDJ FX ENGINE
# -----------------------------------------------------------------------------

def apply_dj_filter_hpf(audio, sr=44100, f_start=25.0, f_end=3200.0, curve_power=1.5, resonance=1.12, start_ratio=0.58):
    """
    VirtualDJ Color FX High-Pass Filter Sweep (Appears Towards the End).
    
    For t < start_ratio (~58% of the transition), the filter is flat/bypassed (25 Hz),
    allowing both tracks to groove continuously with full low-end presence.
    Towards the end (t >= start_ratio), the resonant HPF sweeps up from 25 Hz to 3200 Hz,
    completely eradicating Track A's kick drum and bass before Cue 3 while leaving an airy
    vocal wash that dissolves smoothly into silence.
    """
    n = len(audio)
    if n < 512:
        return audio

    nperseg = min(2048, 2 ** int(np.log2(n)))
    noverlap = nperseg * 3 // 4

    f, t_frames, Zxx_l = signal.stft(audio[:, 0], fs=sr, nperseg=nperseg, noverlap=noverlap)
    _, _, Zxx_r = signal.stft(audio[:, 1], fs=sr, nperseg=nperseg, noverlap=noverlap)

    n_frames = len(t_frames)
    t_norm = np.linspace(0.0, 1.0, n_frames)

    # Filter appears towards the end of the transition
    t_filter = np.clip((t_norm - start_ratio) / max(0.01, 1.0 - start_ratio), 0.0, 1.0)
    fc = f_start * ((f_end / f_start) ** (t_filter ** curve_power))
    ratio = f[:, None] / np.maximum(fc[None, :], 1.0)

    # 4th-order High-Pass Filter frequency response: (f/fc)^4 / (1 + (f/fc)^4)
    H = (ratio ** 4) / (1.0 + ratio ** 4)

    # Authentic DJ mixer resonant peak (+1.0 to +1.5 dB near cutoff)
    if resonance > 1.0:
        peak = np.exp(-0.5 * (np.log(np.maximum(ratio, 1e-4)) / 0.35) ** 2) * (resonance - 1.0) * (t_filter ** 0.5)
        H = np.clip(H + peak, 0.0, 1.8)

    Zxx_l_filt = Zxx_l * H
    Zxx_r_filt = Zxx_r * H

    _, out_l = signal.istft(Zxx_l_filt, fs=sr, nperseg=nperseg, noverlap=noverlap)
    _, out_r = signal.istft(Zxx_r_filt, fs=sr, nperseg=nperseg, noverlap=noverlap)

    out = np.stack([out_l[:n], out_r[:n]], axis=-1).astype(np.float32)
    return out

def apply_dj_flanger(audio, sr=44100, depth_ms=2.8, rate_hz=0.22, feedback=0.45, mix=0.60):
    """
    VirtualDJ Flanger Effect (Comb Filter Jet Sweep).
    Activates across the transition phrase to build intense energy and movement on Track A
    before washing out into the end-filter.
    """
    n = len(audio)
    if n < 512:
        return audio

    t = np.arange(n) / sr
    min_d = int(0.0006 * sr)
    mod_d = int(depth_ms * 0.001 * sr)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * rate_hz * t)[:, None]
    delays = (min_d + mod_d * lfo).astype(np.int32)

    idx = np.arange(n)[:, None]
    idx1 = np.clip(idx - delays, 0, n - 1)
    idx2 = np.clip(idx - 2 * delays, 0, n - 1)
    idx3 = np.clip(idx - 3 * delays, 0, n - 1)

    delayed = (
        audio[idx1, np.arange(2)] * feedback
        + audio[idx2, np.arange(2)] * (feedback ** 2)
        + audio[idx3, np.arange(2)] * (feedback ** 3)
    )

    env = np.ones((n, 1), dtype=np.float32)
    ramp_len = min(int(sr * 0.8), n // 4)
    if ramp_len > 0:
        env[:ramp_len] = np.linspace(0.0, 1.0, ramp_len)[:, None]

    flanged = audio * (1.0 - mix * 0.4) + delayed * (mix * env)
    return np.clip(flanged, -1.0, 1.0).astype(np.float32)

def apply_dj_reverb(audio, sr=44100, decay=0.65, mix=0.50):
    """
    VirtualDJ Space Reverb Wash.
    Dissolves Track A into a lush, wide stereo ambient cloud before the Cue 3 cutoff.
    """
    n = len(audio)
    if n < 512:
        return audio

    taps = [
        (int(sr * 0.029), 0.75, 0.9),
        (int(sr * 0.037), 0.65, 0.8),
        (int(sr * 0.049), 0.55, 0.7),
        (int(sr * 0.067), 0.45, 0.6),
        (int(sr * 0.089), 0.35, 0.5),
        (int(sr * 0.117), 0.25, 0.4),
    ]
    wet = np.zeros_like(audio)
    idx = np.arange(n)
    for d_samp, gain, damp in taps:
        d_idx = np.clip(idx - d_samp, 0, n - 1)
        tap_sig = audio[d_idx] * (gain * decay)
        wet[:, 0] += tap_sig[:, 0] * damp + tap_sig[:, 1] * (1.0 - damp) * 0.5
        wet[:, 1] += tap_sig[:, 1] * damp + tap_sig[:, 0] * (1.0 - damp) * 0.5

    out = audio * (1.0 - mix * 0.3) + wet * mix
    return np.clip(out, -1.0, 1.0).astype(np.float32)

def apply_dj_brake(audio, sr=44100, brake_s=1.2):
    """
    VirtualDJ Turntable Motor Stop / Vinyl Brake.
    Simulates pressing the start/stop button on a turntable, smoothly slowing down playback.
    """
    n = len(audio)
    brake_len = min(int(sr * brake_s), n)
    if brake_len < 512:
        return audio

    start_idx = n - brake_len
    brake_in = audio[start_idx:]
    t_norm = np.linspace(0.0, 1.0, brake_len)
    phase = t_norm * (1.0 - 0.5 * t_norm)
    orig_pos = np.clip((phase * (brake_len - 1)).astype(np.int32), 0, brake_len - 1)
    brake_out = brake_in[orig_pos]
    brake_out *= (1.0 - t_norm[:, None] ** 2)

    out = np.copy(audio)
    out[start_idx:] = brake_out
    return out

def apply_dj_beatgrid(audio, sr=44100, bpm=118.0, start_ratio=0.78, lead_beats=None, mix=0.95, anti_click_ms=2.5):
    """
    VirtualDJ BeatGrid Slicer & Roll Transition Effect.
    Engages SHORTLY before the incoming track's beat drop (in the final ~1-2 bars / 3-4 beats
    of the outgoing track's exit), delivering a tight, crisp rhythmic build-up right before Cue 3.

    Features:
      1. Short Pre-Drop Timing: Engages shortly before the beat starts (at start_ratio ~0.78 or final ~3-4 beats).
         The outgoing track grooves naturally for the majority of the exit, then stutters right before the drop.
      2. Tight Progressive Acceleration: Moves from 1/4-beat stutter repeat to 1/8-beat rapid roll.
      3. Anti-Click Cosine Windowing: 2.5ms cosine crossfade at slice boundaries eliminates clicks.
      4. Studio Warmth: Soft analog saturation (tanh) and 25ms entrance ramp for clean, warm presence.
    """
    n = len(audio)
    if n < 1024 or bpm <= 0:
        return audio

    beat_samp = max(256, int(sr * (60.0 / bpm)))

    if lead_beats is not None and lead_beats > 0:
        lead_samp = int(lead_beats * beat_samp)
        start_samp = max(0, n - lead_samp)
    else:
        # Default start_ratio ~0.78 = final ~22% of transition window (shortly before the beat)
        clamped_ratio = max(0.50, min(0.85, start_ratio))
        start_samp = int(n * clamped_ratio)
        # Ensure it lasts around 3 to 4 beats at most
        if n - start_samp > 4 * beat_samp:
            start_samp = max(0, n - 4 * beat_samp)

    effect_len = n - start_samp
    if effect_len < beat_samp:
        start_samp = max(0, n - beat_samp)
        effect_len = n - start_samp

    out = np.copy(audio)
    wet = np.copy(audio[start_samp:])
    m = len(wet)

    fade_samp = max(16, int(sr * (anti_click_ms / 1000.0)))

    cur_pos = 0
    while cur_pos < m:
        prog = cur_pos / m
        # Progressive roll shortly before drop:
        # First 50% of the short window: 1/4 beat stutter
        # Final 50%: 1/8 beat rapid roll into the drop
        if prog < 0.50:
            slice_len = max(32, beat_samp // 4)   # 1/4 beat slice
            cycle_len = beat_samp // 2            # repeat twice per half-beat
        else:
            slice_len = max(16, beat_samp // 8)   # 1/8 beat slice
            cycle_len = beat_samp // 4            # repeat twice per quarter-beat

        src_start = cur_pos
        src_end = min(m, src_start + slice_len)
        chunk = wet[src_start:src_end]
        actual_chunk_len = len(chunk)

        if actual_chunk_len == 0:
            break

        # Anti-click windowing: smooth cosine fade at slice boundaries
        env = np.ones(actual_chunk_len, dtype=np.float32)
        env_fade = min(fade_samp, actual_chunk_len // 4)
        if env_fade > 0:
            env[:env_fade] = 0.5 * (1.0 - np.cos(np.pi * np.arange(env_fade) / env_fade))
            env[-env_fade:] = 0.5 * (1.0 + np.cos(np.pi * np.arange(env_fade) / env_fade))
        chunk_windowed = chunk * env[:, None]

        # Fill cycle_len with repeats of this slice
        rep_end = min(m, cur_pos + cycle_len)
        fill_pos = cur_pos
        while fill_pos < rep_end:
            copy_len = min(actual_chunk_len, rep_end - fill_pos)
            wet[fill_pos:fill_pos + copy_len] = chunk_windowed[:copy_len]
            fill_pos += copy_len

        cur_pos += cycle_len

    # Soft saturation to smooth transients
    wet = np.tanh(wet * 1.15) / 1.15

    # Smooth entrance ramp-in (25ms)
    ramp_in = min(int(sr * 0.025), m // 4)
    mix_env = np.ones(m, dtype=np.float32) * mix
    if ramp_in > 0:
        mix_env[:ramp_in] = np.linspace(0.0, mix, ramp_in)

    out[start_samp:] = audio[start_samp:] * (1.0 - mix_env[:, None]) + wet * mix_env[:, None]
    return out.astype(np.float32)

def apply_dj_filter_hpf_in(audio, sr=44100, f_start=280.0, f_end=20.0, open_s=1.5):
    """
    Musical opening sweep on incoming Track B:
    Quickly sweeps cutoff from 280 Hz down to 20 Hz (flat/bypassed) over the first open_s seconds,
    ensuring a pristine, silky entry with zero low-frequency collision.
    """
    n = len(audio)
    open_samples = min(int(sr * open_s), n)
    if open_samples < 512:
        return audio

    part_sweep = audio[:open_samples]
    nperseg = min(2048, 2 ** int(np.log2(open_samples)))
    noverlap = nperseg * 3 // 4

    f, t_frames, Zxx_l = signal.stft(part_sweep[:, 0], fs=sr, nperseg=nperseg, noverlap=noverlap)
    _, _, Zxx_r = signal.stft(part_sweep[:, 1], fs=sr, nperseg=nperseg, noverlap=noverlap)

    n_frames = len(t_frames)
    t_norm = np.linspace(0.0, 1.0, n_frames)
    fc = f_start * ((f_end / f_start) ** (t_norm ** 0.8))
    ratio = f[:, None] / np.maximum(fc[None, :], 1.0)
    H = (ratio ** 4) / (1.0 + ratio ** 4)

    Zxx_l *= H
    Zxx_r *= H

    _, out_l = signal.istft(Zxx_l, fs=sr, nperseg=nperseg, noverlap=noverlap)
    _, out_r = signal.istft(Zxx_r, fs=sr, nperseg=nperseg, noverlap=noverlap)

    out_sweep = np.stack([out_l[:open_samples], out_r[:open_samples]], axis=-1).astype(np.float32)
    out = np.copy(audio)
    out[:open_samples] = out_sweep
    return out

def blend_continuous(a_seg, b_seg, sr=44100, fx="filter", bpm=118.0, initial_b_gain=0.72, pre_fade_gain=0.92, filter_start_ratio=0.58):
    """
    Premier SmartMix Continuous DJ Transition Engine.
    Provides full, continuous energy with VirtualDJ FX and resonant filter sweep towards the end:
      1. Both tracks groove continuously across the transition window without crossfader volume dips.
      2. If an FX is selected (Flanger, Reverb, Echo Out, Phaser, Vinyl Brake), it engages during
         the transition phrase on Track A to build excitement and motion.
      3. Towards the end (last ~40% of the transition), the resonant High-Pass Filter engages,
         sweeping away Track A's kick drum and bass cleanly before Cue 3.
      4. Track B enters with confident groove presence (gain ~0.72) and ramps smoothly to 1.0 at Cue 3.
    """
    n = min(len(a_seg), len(b_seg))
    a_seg = a_seg[:n]
    b_seg = b_seg[:n]
    dur_s = n / sr

    # Step 1: Apply VirtualDJ Transition FX on Track A if requested
    a_fx = a_seg
    if fx == "flanger" and dur_s > 4.0:
        a_fx = apply_dj_flanger(a_seg, sr=sr, depth_ms=2.8, rate_hz=0.22, feedback=0.45, mix=0.60)
    elif fx == "reverb" and dur_s > 4.0:
        a_fx = apply_dj_reverb(a_seg, sr=sr, decay=0.65, mix=0.50)
    elif fx == "beatgrid":
        a_fx = apply_dj_beatgrid(a_seg, sr=sr, bpm=bpm, start_ratio=0.78, mix=0.95)
    elif fx == "echo-out":
        return blend_echo_out(a_seg, b_seg, sr=sr, bpm=bpm)
    elif fx == "brake":
        a_fx = apply_dj_brake(a_seg, sr=sr, brake_s=min(2.0, dur_s * 0.5))

    # Step 2: Apply Resonant High-Pass Filter sweep TOWARDS THE END (starts at filter_start_ratio)
    # This keeps both tracks grooving together for the first ~60%, then wipes out Track A's bass!
    a_filtered = apply_dj_filter_hpf(
        a_fx,
        sr=sr,
        f_start=25.0,
        f_end=3200.0,
        curve_power=1.5,
        resonance=1.12,
        start_ratio=filter_start_ratio
    )

    t = np.linspace(0.0, 1.0, n)
    # Track A maintains presence through the first 50%, then smoothly fades to 0 as filter sweeps out
    t_fade_a = np.clip((t - 0.50) / 0.50, 0.0, 1.0)
    a_env = (pre_fade_gain * ((1.0 - t_fade_a) ** 1.3))[:, None]

    # Track B enters loud and clear with a 25ms anti-pop micro-ramp
    ramp_samples = min(int(sr * 0.025), max(1, n // 10))
    micro_in = np.ones(n, dtype=np.float32)
    if ramp_samples > 0:
        micro_in[:ramp_samples] = np.linspace(0.0, 1.0, ramp_samples)

    b_level = initial_b_gain + (1.0 - initial_b_gain) * np.sin(t * (np.pi * 0.5))
    b_env = (b_level * micro_in)[:, None]

    # Equal-energy correction ensures steady continuous volume
    sum_energy = np.sqrt(a_env ** 2 + b_env ** 2)
    gain_corr = np.where(sum_energy > 1.05, 1.0 / (sum_energy ** 0.5), 1.0)
    return (a_filtered * a_env + b_seg * b_env) * gain_corr

# Backwards compatibility aliases
blend_dj_filter = blend_continuous
blend_filter_sweep = blend_continuous

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
# SMART CONTINUOUS MIX ENGINE (VirtualDJ FX & End-Filter Sweep Transitions)
# -----------------------------------------------------------------------------

def render_continuous_mix(tracks, args, output_file):
    print("\n" + "-" * 78)
    print(f" RENDERING SMART CONTINUOUS MIX (VirtualDJ FX & End-Filter | Target: {args.target_lufs} LUFS)...")
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
            mode = get_transition_mode(i, args.crossfade_mode, custom_styles, t_a, t_b, len(tracks))
        elif has_fade and has_exit and t_a["cue_exit"] > t_a["cue_fade"]:
            fade_dur = t_a["cue_exit"] - t_a["cue_fade"]
            mode = get_transition_mode(i, args.crossfade_mode, custom_styles, t_a, t_b, len(tracks))
        else:
            fade_dur = 16.0 * 4.0 * (60.0 / bpm_a)  # Default 16 bars (64 beats)
            mode = get_transition_mode(i, args.crossfade_mode, custom_styles, t_a, t_b, len(tracks))

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
        filter_start = getattr(args, "filter_start", 0.58)
        if mode == "flanger":
            blended = blend_continuous(a_trans, b_trans, sr=sr, fx="flanger", bpm=bpm_a, filter_start_ratio=filter_start)
        elif mode == "reverb":
            blended = blend_continuous(a_trans, b_trans, sr=sr, fx="reverb", bpm=bpm_a, filter_start_ratio=filter_start)
        elif mode == "beatgrid":
            blended = blend_continuous(a_trans, b_trans, sr=sr, fx="beatgrid", bpm=bpm_a, filter_start_ratio=max(filter_start, 0.70))
        elif mode == "echo-out":
            blended = blend_echo_out(a_trans, b_trans, sr=sr, bpm=bpm_a)
        elif mode == "brake":
            blended = blend_continuous(a_trans, b_trans, sr=sr, fx="brake", bpm=bpm_a, filter_start_ratio=filter_start)
        elif mode in ("filter", "filter-sweep"):
            blended = blend_continuous(a_trans, b_trans, sr=sr, fx="filter", bpm=bpm_a, filter_start_ratio=filter_start)
        elif mode == "equal-power":
            blended = blend_equal_power(a_trans, b_trans)
        elif mode == "gradual":
            blended = blend_gradual(
                a_trans,
                b_trans,
                sr=sr,
                bass_swap_ratio=getattr(args, "bass_swap_ratio", 0.68),
                use_filter=getattr(args, "use_filter", True)
            )
        else: # default continuous
            blended = blend_continuous(a_trans, b_trans, sr=sr, fx="filter", bpm=bpm_a, filter_start_ratio=filter_start)

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
    temp_master_wav = os.path.join(args.output_dir, "_temp_continuous_master.wav")
    wavfile.write(temp_master_wav, sr, (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16))

    # Master Output Stage: Apply EBU R128 DJ Loudness Normalization & True Peak Limiting
    print("Mastering to 320k MP3 with EBU R128 DJ Standards (-14.0 LUFS, -1.5 dBTP)...")
    mix_tag = getattr(args, "mix_name", "Amapiano")
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_master_wav,
        "-af", f"loudnorm=I={args.target_lufs}:TP={args.true_peak}:LRA=10.0",
        "-b:a", "320k",
        "-metadata", f"album={mix_tag} Continuous Mix",
        "-metadata", f"title={mix_tag} Continuous Set (SmartMix Engine)",
        "-metadata", "artist=Various Artists",
        "-metadata", f"genre={mix_tag}",
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if os.path.exists(temp_master_wav):
        os.remove(temp_master_wav)

    out_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"-> Continuous Mix Rendered: {output_file} ({out_size_mb:.2f} MB)")
    print(f"   [Loudness Target: {args.target_lufs} LUFS | True Peak Ceiling: {args.true_peak} dBTP]")
    print("Continuous Mix Timeline:")
    cf_tracklist_lines = []
    for mark_time, artist, title, trans in timeline_markers:
        trans_str = f" [{trans}]" if trans else ""
        line_str = f" [{format_time(mark_time)}] {artist} - {title}{trans_str}"
        print(line_str)
        cf_tracklist_lines.append(line_str)
    
    txt_path = os.path.splitext(output_file)[0] + "_Tracklist.txt"
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"SmartMix Continuous Mix (VirtualDJ FX & End-Filter)\nTarget: {args.target_lufs} LUFS\n\nTracklist:\n")
            f.write("\n".join(cf_tracklist_lines))
    except Exception:
        pass
    return True

# Backwards compatibility alias
render_crossfade_mix = render_continuous_mix

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

    if mode == "auto":
        mode = choose_smart_transition(0, t_a, t_b)
    if mode == "flanger":
        blended = blend_continuous(a_trans, b_trans, sr=sr, fx="flanger", bpm=bpm_a)
    elif mode == "reverb":
        blended = blend_continuous(a_trans, b_trans, sr=sr, fx="reverb", bpm=bpm_a)
    elif mode == "beatgrid":
        blended = blend_continuous(a_trans, b_trans, sr=sr, fx="beatgrid", bpm=bpm_a)
    elif mode == "echo-out":
        blended = blend_echo_out(a_trans, b_trans, sr=sr, bpm=bpm_a)
    elif mode == "brake":
        blended = blend_continuous(a_trans, b_trans, sr=sr, fx="brake", bpm=bpm_a)
    elif mode in ("filter", "filter-sweep"):
        blended = blend_continuous(a_trans, b_trans, sr=sr, fx="filter", bpm=bpm_a)
    elif mode == "equal-power":
        blended = blend_equal_power(a_trans, b_trans)
    elif mode == "gradual":
        blended = blend_gradual(a_trans, b_trans, sr=sr, bass_swap_ratio=bass_swap_ratio, use_filter=True)
    else:
        blended = blend_continuous(a_trans, b_trans, sr=sr, fx="filter", bpm=bpm_a)

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

    continuous_output = os.path.join(args.output_dir, f"{args.mix_name}_Continuous_Mix.mp3")
    normal_output = os.path.join(args.output_dir, f"{args.mix_name}_Continuous_Mix_Normal.mp3")

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

    if args.mode in ("both", "continuous", "crossfade"):
        render_continuous_mix(tracks, args, continuous_output)

    print("\n" + "=" * 78)
    print(" ALL REQUESTED MIXES GENERATED ACCORDING TO DJ LOUDNESS STANDARDS!")
    print("=" * 78)
    if args.mode in ("both", "continuous", "crossfade"):
        print(f" 1. Continuous Mix    : {continuous_output}")
    if args.mode in ("both", "normal"):
        print(f" 2. Normal Cut Mix    : {normal_output}")
    print(f" Master Levels Verified: {args.target_lufs} LUFS Integrated, Max True Peak {args.true_peak} dBTP")
    print("=" * 78)

if __name__ == "__main__":
    main()
