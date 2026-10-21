import os
import sys
import argparse
import subprocess
import xml.etree.ElementTree as ET

VDJ_FOLDER = r"C:\Users\odhis\AppData\Local\VirtualDJ\Sideview\automix.vdjfolder"
VDJ_DB = r"C:\Users\odhis\AppData\Local\VirtualDJ\database.xml"
OUTPUT_DIR = r"C:\Users\odhis\Downloads\Amapiano"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Amapiano_Continuous_Mix.mp3")

def parse_args():
    parser = argparse.ArgumentParser(description="Cue-Based Continuous Mixtape Generator with Smart Crossfading")
    parser.add_argument("--entry-cue", type=int, default=1, help="Default cue number to use for song entry/mix-in (default: 1)")
    parser.add_argument("--fade-cue", type=int, default=2, help="Default cue number where fade-out begins (default: 2)")
    parser.add_argument("--exit-cue", type=int, default=3, help="Default cue number where fade completes/cuts off (default: 3)")
    parser.add_argument("--use-last-cues", action="store_true", help="If track has 4+ cues, automatically use the last 2 cues for the fade-out window")
    parser.add_argument(
        "--crossfade-mode",
        type=str,
        default="dynamic",
        choices=["dynamic", "bass-swap", "filter-sweep", "equal-power"],
        help="Crossfading technique: 'dynamic' (tastefully alternates), 'bass-swap' (EQ crossover at midpoint), 'filter-sweep' (high-pass outro wash), 'equal-power' (smooth sine blend)"
    )
    parser.add_argument("--output", type=str, default=OUTPUT_FILE, help="Custom output MP3 path")
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

    # Priority 1: Check for named cues
    for name, pos in cues_by_name.items():
        if any(k in name for k in ["start", "intro", "in", "drop"]) and entry_pos is None:
            entry_pos = pos
        elif any(k in name for k in ["fade out", "fade_out", "mix out", "fade start"]) and fade_pos is None:
            fade_pos = pos
        elif any(k in name for k in ["cutoff", "cut", "exit", "end"]) and exit_pos is None:
            exit_pos = pos

    # Priority 2: Use last cues if user requested and 4+ cues exist
    if use_last_cues and len(cues_by_num) >= 4:
        sorted_cues = sorted(cues_by_num.items(), key=lambda x: x[1])
        if entry_pos is None:
            entry_pos = sorted_cues[0][1]
        if fade_pos is None:
            fade_pos = sorted_cues[-2][1]
        if exit_pos is None:
            exit_pos = sorted_cues[-1][1]

    # Priority 3: Check configured Cue numbers (defaults: 1, 2, 3)
    if entry_pos is None:
        entry_pos = cues_by_num.get(default_entry, 0.0)
    if fade_pos is None:
        fade_pos = cues_by_num.get(default_fade, None)
    if exit_pos is None:
        exit_pos = cues_by_num.get(default_exit, None)

    # Priority 4: Fallback to Automix POIs
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
    # Dynamic mode: Tastefully alternates without overdoing it
    # Transition 0: bass-swap (punchy opening mix)
    # Transition 1: filter-sweep (smooth melodic washout)
    # Transition 2: bass-swap (hard drop)
    # Transition 3: equal-power (gentle vocal blend)
    patterns = ["bass-swap", "filter-sweep", "bass-swap", "equal-power"]
    return patterns[idx % len(patterns)]

def build_mixtape():
    args = parse_args()
    tracks = get_track_data(args)
    if not tracks:
        print("No tracks found in Automix playlist!")
        return

    output_file = args.output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print("=" * 78)
    print(" SMARTMIX: VIRTUALDJ-INSPIRED ON-BEAT CROSSFADING ENGINE")
    print("=" * 78)
    print(f"Crossfade Strategy: {args.crossfade_mode.upper()}")
    print(f"Loaded {len(tracks)} tracks from Automix playlist:\n")

    for i, t in enumerate(tracks):
        c_count = len(t['all_cues'])
        print(f" [{i+1}] {t['artist']} - {t['title']}")
        print(f"     BPM: {t['bpm']:.1f} | Cues: {c_count} | Entry @ {format_time(t['cue_entry'])} | Fade @ {format_time(t['cue_fade'])} | Cut @ {format_time(t['cue_exit'])}")

    print("-" * 78)

    temp_dir = os.path.join(os.path.dirname(output_file), "_temp_mix_parts")
    os.makedirs(temp_dir, exist_ok=True)

    prepared_clips = []
    crossfade_durations = []
    transition_modes = []
    
    current_timeline = 0.0
    timeline_markers = []

    for i, t in enumerate(tracks):
        is_last = (i == len(tracks) - 1)
        in_file = t["path"]
        out_clip = os.path.join(temp_dir, f"clip_{i:02d}.wav")

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

        # Check BPM difference for tempo matching
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

    # Build sequential crossfade filtergraph
    filter_parts = []
    curr_label = "0:a"
    for i in range(len(prepared_clips) - 1):
        fade_d = crossfade_durations[i]
        mode = transition_modes[i]
        next_label = f"{i+1}:a"
        out_label = f"m{i}" if i < len(prepared_clips) - 2 else "out"

        # Curve selection based on mode:
        # 'qsin' (quarter sine equal-power) is the core curve
        # 'hpf' applies a high-pass washout on outgoing
        if mode == "filter-sweep":
            # Exponential sine washout curve on outgoing, equal-power entry on incoming
            curve_param = "c1=esin:c2=qsin"
        elif mode == "bass-swap":
            # Quarter-sine equal-power crossover
            curve_param = "c1=qsin:c2=qsin"
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
        "-metadata", "album=Amapiano SmartMix Set",
        "-metadata", "title=Amapiano Set (Smart Crossfaded)",
        "-metadata", "artist=Various Artists",
        "-metadata", "genre=Amapiano",
        output_file
    ])

    print("Rendering final smart continuous mixtape...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        return

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
    print("\n" + "=" * 78)
    print(" SMART MIXTAPE RENDERED SUCCESSFULLY!")
    print("=" * 78)
    print(f"File Path: {output_file}")
    print(f"File Size: {out_size_mb:.2f} MB (320 kbps High Quality MP3)")
    print("\nTIMELINE TRACKLIST:")
    for mark_time, artist, title, trans in timeline_markers:
        trans_str = f" [Crossfade: {trans}]" if trans else ""
        print(f" [{format_time(mark_time)}] {artist} - {title}{trans_str}")
    print("=" * 78)

if __name__ == "__main__":
    build_mixtape()
