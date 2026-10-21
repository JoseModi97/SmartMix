"""
==============================================================================
 SMARTMIX: ALL-IN-ONE MASTER DJ MIXTAPE COMPILATION PIPELINE
==============================================================================
Runs the entire SmartMix compilation workflow in a SINGLE, UNIFIED PROCESS:
  1. Syncs active Automix queue and Cue points from VirtualDJ
  2. Compiles the Smart Crossfaded Continuous Mix (Gradual Cue 2 to Cue 3 DJ Crossfade)
  3. Applies EBU R128 DJ/Club Loudness Normalization (-14.0 LUFS, -1.5 dBTP)
  4. Generates full tracklist reports and timestamp markers
  (Optional: standalone scratch preview only when --with-scratch-preview is passed)

Usage:
  python smartmix.py
  (or simply double-click run_smartmix.bat)
==============================================================================
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Import internal compilation modules
import generate_mixtape as gm

def parse_args():
    parser = argparse.ArgumentParser(
        description="SmartMix: All-In-One Unified DJ Mixtape Compiler"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Destination directory for all compiled MP3 files (default: auto-detected from source tracks or ~/Downloads/Amapiano)"
    )
    parser.add_argument(
        "--mix-name",
        type=str,
        default="Amapiano",
        help="Name or genre of the mix (used for output filenames and ID3 tags, e.g. 'Afrobeats', 'House', 'Amapiano')"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="normal",
        choices=["normal", "crossfade", "both"],
        help="Transition mode: 'normal' (default: clean cue-drop cut transition, zero crossfade), 'crossfade' (gradual crossfade), or 'both'"
    )
    parser.add_argument(
        "--normal-cutoff",
        type=str,
        default="cue2",
        choices=["cue2", "cue3"],
        help="Where normal cut transition occurs: 'cue2' (radio cutoff) or 'cue3' (full phrase)"
    )
    parser.add_argument(
        "--crossfade-mode",
        type=str,
        default="gradual",
        choices=["gradual", "equal-power"],
        help="Global crossfade transition style (default: gradual, smooth Cue 2 to Cue 3 crossfade with LR-4 bass crossover)"
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
        help="Force transition length in bars (e.g. 8, 16, 32 bars). If omitted, uses cue markers."
    )
    parser.add_argument(
        "--bass-swap-ratio",
        type=float,
        default=0.5,
        help="Ratio within transition where low-end swaps (default: 0.5 = midpoint)"
    )
    parser.add_argument(
        "--target-lufs",
        type=float,
        default=-14.0,
        help="Target integrated loudness in LUFS (default: -14.0 LUFS)"
    )
    parser.add_argument(
        "--true-peak",
        type=float,
        default=-1.5,
        help="Maximum True Peak ceiling in dBTP (default: -1.5 dBTP)"
    )
    parser.add_argument(
        "--with-scratch-preview",
        action="store_true",
        help="Optional: also render a standalone DJ scratch routine on track 1 (default: False, no scratches)"
    )
    parser.add_argument(
        "--entry-cue",
        type=int,
        default=1,
        help="Default cue number to use for song entry/mix-in (default: 1)"
    )
    parser.add_argument(
        "--fade-cue",
        type=int,
        default=2,
        help="Default cue number where fade-out begins / normal cutoff (default: 2)"
    )
    parser.add_argument(
        "--exit-cue",
        type=int,
        default=3,
        help="Default cue number where fade completes/cuts off (default: 3)"
    )
    parser.add_argument(
        "--use-last-cues",
        action="store_true",
        help="If track has 4+ cues, automatically use the final 2 cues for the fade-out window"
    )
    return parser.parse_args()

def run_all_in_one():
    args = parse_args()

    print("=" * 78)
    print(" SMARTMIX: UNIFIED ALL-IN-ONE DJ COMPILATION MASTER PIPELINE")
    print("=" * 78)
    print(f"Loudness Target  : {args.target_lufs:.1f} LUFS (Industry DJ/Club Reference)")
    print(f"True Peak Ceiling: {args.true_peak:.1f} dBTP (Inter-Sample Headroom Margin)")
    print(f"Compilation Mode : {args.mode.upper()} ({'Clean Cue-Drop Transitions (Zero Crossfade)' if args.mode == 'normal' else 'Gradual Cue 2 -> Cue 3 Crossfade' if args.mode == 'crossfade' else 'Both Normal & Crossfaded Sets'})")
    print("-" * 78)

    # -------------------------------------------------------------------------
    # STEP 1: LOAD & VALIDATE PLAYLIST FROM VIRTUALDJ
    # -------------------------------------------------------------------------
    print(f"\n[Step 1] Reading VirtualDJ Automix Queue & Cue Database...")
    tracks = gm.get_track_data(args)
    if not tracks:
        print("ERROR: No valid tracks found in VirtualDJ Automix queue!")
        return False

    # Automatically resolve output directory (dynamic: track location, downloads, or custom)
    args.output_dir = gm.resolve_output_dir(args.output_dir, tracks)
    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Destination Dir  : {args.output_dir}")

    print(f"-> Successfully loaded {len(tracks)} tracks from Automix playlist:\n")
    for i, t in enumerate(tracks):
        cues_count = len(t["all_cues"])
        print(f"  [{i+1}] {t['artist']} - {t['title']}")
        print(f"      BPM: {t['bpm']:.1f} | Cues: {cues_count} | Entry: {gm.format_time(t['cue_entry'])} | Fade/Cut: {gm.format_time(t['cue_fade'])} | Outro: {gm.format_time(t['cue_exit'])}")

    normal_out = os.path.join(args.output_dir, f"{args.mix_name}_Continuous_Mix_Normal.mp3")
    crossfade_out = os.path.join(args.output_dir, f"{args.mix_name}_Continuous_Mix_Crossfaded.mp3")
    scratch_out = os.path.join(args.output_dir, f"{args.mix_name}_DJ_Scratch_Preview.mp3")

    # -------------------------------------------------------------------------
    # STEP 2: COMPILE NORMAL CUT MIX (ZERO CROSSFADE) IF REQUESTED
    # -------------------------------------------------------------------------
    if args.mode in ("normal", "both"):
        print("\n" + "=" * 78)
        print(" COMPILING NORMAL CONTINUOUS MIX (CLEAN CUE DROPS, ZERO CROSSFADE)")
        print("=" * 78)
        success_nm = gm.render_normal_mix(tracks, args, normal_out)
        if not success_nm:
            print("ERROR: Normal cut mix compilation failed!")
            return False

    # -------------------------------------------------------------------------
    # STEP 3: COMPILE SMART CROSSFADED MIX (GRADUAL BLEND) IF REQUESTED
    # -------------------------------------------------------------------------
    if args.mode in ("crossfade", "both"):
        print("\n" + "=" * 78)
        print(" COMPILING SMART CROSSFADED CONTINUOUS MIX (GRADUAL DJ TRANSITIONS)")
        print("=" * 78)
        success_cf = gm.render_crossfade_mix(tracks, args, crossfade_out)
        if not success_cf:
            print("ERROR: Crossfaded mix compilation failed!")
            return False

    # -------------------------------------------------------------------------
    # STEP 4: (OPTIONAL) STANDALONE SCRATCH PREVIEW
    # -------------------------------------------------------------------------
    if args.with_scratch_preview:
        print("\n" + "=" * 78)
        print(" COMPILING OPTIONAL STANDALONE SCRATCH PREVIEW")
        print("=" * 78)
        first_track = tracks[0]
        try:
            cmd_scratch = [
                sys.executable,
                os.path.join(os.path.dirname(__file__), "generate_scratch_preview.py"),
                "--track", first_track["path"],
                "--output", scratch_out,
                "--bpm", str(first_track["bpm"] or 118.0),
                "--cue", str(first_track["cue_entry"] or 0.122),
                "--duration", "65",
                "--intensity", "0.92"
            ]
            res_sc = subprocess.run(cmd_scratch, capture_output=True, text=True)
            if res_sc.returncode == 0:
                print(f"-> Optional Scratch Preview Rendered: {scratch_out}")
        except Exception as e:
            print(f"Notice on scratch preview: {e}")

    # -------------------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print(" SMARTMIX CONTINUOUS MIX SUCCESSFULLY COMPILED!")
    print("=" * 78)
    if args.mode in ("normal", "both") and os.path.exists(normal_out):
        nm_mb = os.path.getsize(normal_out) / (1024 * 1024)
        print(" 1. Normal Cut Mix (Zero Overlap): " + normal_out + f" ({nm_mb:.2f} MB)")
    if args.mode in ("crossfade", "both") and os.path.exists(crossfade_out):
        cf_mb = os.path.getsize(crossfade_out) / (1024 * 1024)
        print(" 2. Crossfaded Mix (Gradual Blend): " + crossfade_out + f" ({cf_mb:.2f} MB)")
    if args.with_scratch_preview and os.path.exists(scratch_out):
        sc_mb = os.path.getsize(scratch_out) / (1024 * 1024)
        print(" 3. DJ Scratch Preview           : " + scratch_out + f" ({sc_mb:.2f} MB)")
    print(f"\n Master Audio Standards  : {args.target_lufs:.1f} LUFS Integrated, Max True Peak {args.true_peak:.1f} dBTP")
    print(f" Transition Profile      : {'Clean On-Beat Cue Drops (Zero Overlapping Crossfade)' if args.mode == 'normal' else 'Gradual Cue 2 -> Cue 3 DJ Crossfade'}")
    print("=" * 78)
    return True

if __name__ == "__main__":
    run_all_in_one()
