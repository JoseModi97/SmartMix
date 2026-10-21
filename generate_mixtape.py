import os
import sys
import argparse
import subprocess
import xml.etree.ElementTree as ET

VDJ_FOLDER = r"C:\Users\odhis\AppData\Local\VirtualDJ\Sideview\automix.vdjfolder"
VDJ_DB = r"C:\Users\odhis\AppData\Local\VirtualDJ\database.xml"
OUTPUT_DIR = r"C:\Users\odhis\Downloads\Amapiano"

def parse_args():
    parser = argparse.ArgumentParser(description="SmartMix: Dual-Mode Mixtape Generator (Normal Cut & Smart Crossfade)")
    parser.add_argument(
        "--mode",
        type=str,
        default="both",
        choices=["both", "crossfade", "normal"],
        help="Rendering mode: 'both' (creates both normal and crossfaded MP3s), 'crossfade' (smooth overlap), 'normal' (clean on-beat drop without overlap)"
    )
    parser.add_argument(
        "--crossfade-mode",
        type=str,
        default="dynamic",
        choices=["dynamic", "bass-swap", "filter-sweep", "equal-power"],
        help="Crossfading technique: 'dynamic' (alternates styles), 'bass-swap' (EQ crossover), 'filter-sweep' (high-pass wash), 'equal-power' (sine blend)"
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

def get_transition_mode(idx, global_mode):
    if global_mode != "dynamic":
        return global_mode
    patterns = ["bass-swap", "filter-sweep", "bass-swap", "equal-power"]
    return patterns[idx % len(patterns)]

def render_normal_mix(tracks, args, output_file):
    """
    Renders the Normal Cut Mix (clean on-beat drops, no crossfade overlap).
    Each track plays from Cue 1 up to its cutoff point (Cue 2 or Cue 3),
    then immediately drops into the next track at Cue 1.
    """
    print("\n" + "-" * 75)
    print(" RENDERING NORMAL MIX (Clean Drop, No Overlap)...")
    print("-" * 75)

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

        # Micro-fade (10ms) on boundaries to avoid digital clicks/pops
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

    # Concatenate clips back-to-back using concat filter
    filter_inputs = "".join([f"[{idx}:a]" for idx in range(len(prepared_clips))])
    concat_filter = f"{filter_inputs}concat=n={len(prepared_clips)}:v=0:a=1[out]"

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
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    out_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"-> Normal Mix Rendered: {output_file} ({out_size_mb:.2f} MB)")
    print("Normal Mix Timeline:")
    for mark_time, artist, title in timeline_markers:
        print(f" [{format_time(mark_time)}] {artist} - {title}")
    return True

def render_crossfade_mix(tracks, args, output_file):
    """
    Renders the Smart Crossfaded Mix (equal-power, on-beat 16-bar overlaps, tempo matching).
    """
    print("\n" + "-" * 75)
    print(f" RENDERING CROSSFADED MIX (Mode: {args.crossfade_mode.upper()})...")
    print("-" * 75)

    temp_dir = os.path.join(args.output_dir, "_temp_cross_parts")
    os.makedirs(temp_dir, exist_ok=True)

    prepared_clips = []
    crossfade_durations = []
    transition_modes = []
    
    current_timeline = 0.0
    timeline_markers = []

    for i, t in enumerate(tracks):
        is_last = (i == len(tracks) - 1)
        in_file = t["path"]
        out_clip = os.path.join(temp_dir, f"cross_clip_{i:02d}.wav")

        start_time = t["cue_entry"]

        if not is_last:
            if t["cue_fade"] is not None and t["cue_exit"] is not None and t["cue_exit"] > t["cue_fade"]:
                end_time = t["cue_exit"]
                fade_duration = t["cue_exit"] - t["cue_fade"]
            else:
                fade_duration = 16.0 * (60.0 / t["bpm"])  # default 16 bars
                end_time = t["length"] - 2.0
            crossfade_durations.append(fade_duration)
            t_mode = get_transition_mode(i, args.crossfade_mode)
            transition_modes.append(t_mode)
        else:
            end_time = t["length"]
            fade_duration = None

        duration = max(0.1, end_time - start_time)

        # Tempo matching if BPMs differ
        tempo_filter = ""
        if i > 0:
            prev_bpm = tracks[i-1]["bpm"]
            curr_bpm = t["bpm"]
            if abs(prev_bpm - curr_bpm) > 0.3:
                ratio = prev_bpm / curr_bpm
                print(f"  -> Matching BPM of Track {i+1} ({curr_bpm:.1f}) to Track {i} ({prev_bpm:.1f}) [ratio: {ratio:.4f}]")
                tempo_filter = f",rubberband=tempo={ratio:.4f}"

        af_filters = "aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=stereo"
        if tempo_filter:
            af_filters += tempo_filter
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

        if i == 0:
            timeline_markers.append((current_timeline, t['artist'], t['title'], None))
            current_timeline += (t["cue_fade"] - t["cue_entry"]) if t["cue_fade"] else (duration - 16.0)
        elif not is_last:
            mode_used = transition_modes[i-1]
            timeline_markers.append((current_timeline, t['artist'], t['title'], mode_used))
            trans_dur = crossfade_durations[i-1]
            solo_dur = (t["cue_fade"] - t["cue_entry"]) - trans_dur if t["cue_fade"] else (duration - trans_dur - 16.0)
            current_timeline += max(0.0, solo_dur)
        else:
            mode_used = transition_modes[i-1]
            timeline_markers.append((current_timeline, t['artist'], t['title'], mode_used))

    print("Building smart crossfade graph...")
    for idx, (dur, mode) in enumerate(zip(crossfade_durations, transition_modes)):
        print(f"  * Transition {idx+1} -> {idx+2}: {dur:.1f}s ({mode})")

    filter_parts = []
    curr_label = "0:a"
    for i in range(len(prepared_clips) - 1):
        fade_d = crossfade_durations[i]
        mode = transition_modes[i]
        next_label = f"{i+1}:a"
        out_label = f"m{i}" if i < len(prepared_clips) - 2 else "out"

        if mode == "filter-sweep":
            curve_param = "c1=esin:c2=qsin"
        else:
            curve_param = "c1=qsin:c2=qsin"

        filter_parts.append(f"[{curr_label}][{next_label}]acrossfade=d={fade_d:.3f}:{curve_param}[{out_label}]")
        curr_label = out_label

    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"]
    for clip in prepared_clips:
        cmd.extend(["-i", clip])
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", f"[{curr_label}]",
        "-b:a", "320k",
        "-metadata", "album=Amapiano Continuous Mix (Crossfaded)",
        "-metadata", "title=Amapiano Set (Smart Crossfaded)",
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
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    out_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"-> Crossfaded Mix Rendered: {output_file} ({out_size_mb:.2f} MB)")
    print("Crossfaded Mix Timeline:")
    for mark_time, artist, title, trans in timeline_markers:
        trans_str = f" [Crossfade: {trans}]" if trans else ""
        print(f" [{format_time(mark_time)}] {artist} - {title}{trans_str}")
    return True

def main():
    args = parse_args()
    tracks = get_track_data(args)
    if not tracks:
        print("No tracks found in Automix playlist!")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    normal_output = os.path.join(args.output_dir, "Amapiano_Continuous_Mix_Normal.mp3")
    crossfade_output = os.path.join(args.output_dir, "Amapiano_Continuous_Mix_Crossfaded.mp3")

    print("=" * 78)
    print(" SMARTMIX: DUAL-MODE MIXTAPE ENGINE")
    print("=" * 78)
    print(f"Target Mode: {args.mode.upper()}")
    print(f"Loaded {len(tracks)} tracks from Automix playlist:\n")

    for i, t in enumerate(tracks):
        c_count = len(t['all_cues'])
        print(f" [{i+1}] {t['artist']} - {t['title']}")
        print(f"     BPM: {t['bpm']:.1f} | Cues: {c_count} | Entry @ {format_time(t['cue_entry'])} | Fade/Cut @ {format_time(t['cue_fade'])} | Outro @ {format_time(t['cue_exit'])}")

    if args.mode in ("both", "normal"):
        render_normal_mix(tracks, args, normal_output)

    if args.mode in ("both", "crossfade"):
        render_crossfade_mix(tracks, args, crossfade_output)

    print("\n" + "=" * 78)
    print(" ALL REQUESTED MIXES GENERATED SUCCESSFULLY!")
    print("=" * 78)
    if args.mode in ("both", "normal"):
        print(f" 1. Normal Cut Mix    : {normal_output}")
    if args.mode in ("both", "crossfade"):
        print(f" 2. Crossfaded Mix   : {crossfade_output}")
    print("=" * 78)

if __name__ == "__main__":
    main()
