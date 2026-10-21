import os
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy import signal

def build_scratch_preview():
    track_path = r"C:\Users\odhis\Downloads\Amapiano\Heavy-K, DJ Buckz, Nonny D - No Bad Vibes (SPOTISAVER).mp3"
    output_mp3 = r"C:\Users\odhis\Downloads\Amapiano\Heavy-K_No_Bad_Vibes_DJ_Scratch_Preview.mp3"
    temp_wav = r"C:\Users\odhis\Downloads\Amapiano\_temp_scratch.wav"

    sr = 44100
    bpm = 118.0
    beat_s = 60.0 / bpm         # ~0.50847s per beat
    bar_s = beat_s * 4.0        # ~2.0339s per bar
    cue1_s = 0.122              # Cue 1 start time in the song

    print("=" * 78)
    print(" GENERATING PROFESSIONAL DJ SCRATCH PREVIEW (ACID / DJ STONE STYLE)")
    print("=" * 78)
    print(f"Track       : Heavy-K, DJ Buckz, Nonny D - No Bad Vibes")
    print(f"Tempo       : {bpm} BPM (1 Beat = {beat_s*1000:.1f}ms | 1 Bar = {bar_s:.2f}s)")
    print(f"Cue 1 Entry : {cue1_s:.3f}s")

    # Step 1: Load the first 65 seconds of the song as 32-bit float stereo audio
    print("\n[1/5] Extracting song audio...")
    cmd = [
        "ffmpeg", "-y", "-ss", str(cue1_s), "-t", "70",
        "-i", track_path,
        "-f", "s16le", "-ac", "2", "-ar", str(sr), "-"
    ]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    raw_audio = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    song_audio = raw_audio.reshape(-1, 2)

    # Step 2: Grab the opening sound slice (first 1.5 seconds) for scratching
    scratch_sample = song_audio[:int(sr * 1.5)].copy()

    # Scratch Resampling Engine with Linear Interpolation & Fader Envelope
    def scratch_resample(source_audio, time_trajectory_sec, fader_env):
        sample_indices = time_trajectory_sec * sr
        sample_indices = np.clip(sample_indices, 0, len(source_audio) - 2)
        idx_floor = np.floor(sample_indices).astype(np.int32)
        frac = (sample_indices - idx_floor)[:, None]
        
        # 2-channel interpolation
        s0 = source_audio[idx_floor]
        s1 = source_audio[idx_floor + 1]
        scratched = s0 * (1.0 - frac) + s1 * frac
        
        # Smooth fader to prevent clicks
        smoothed_fader = signal.medfilt(fader_env, kernel_size=5) if len(fader_env) > 5 else fader_env
        scratched *= smoothed_fader[:, None]
        return scratched

    print("[2/5] Synthesizing Turntable & ACID-Style Scratch Routine...")

    # -------------------------------------------------------------------------
    # PART A: INTRO ROUTINE (4 Bars = 16 Beats before the main drop)
    # -------------------------------------------------------------------------
    intro_blocks = []

    # Bar 0 (Lead-in): Turntable needle drop and warm vinyl crackle (2 beats)
    n_leadin = int(sr * beat_s * 2)
    t_leadin = np.linspace(0, beat_s * 2, n_leadin)
    # Subtle analog surface noise and needle touch
    needle_noise = np.random.normal(0, 0.006, (n_leadin, 2)).astype(np.float32)
    # Low frequency rumble (30 Hz)
    rumble = 0.015 * np.sin(2 * np.pi * 33 * t_leadin)[:, None]
    needle_drop = needle_noise + rumble
    # Needle contact pop at t = 0.2s
    pop_idx = int(sr * 0.2)
    if pop_idx < n_leadin:
        needle_drop[pop_idx:pop_idx+100] += np.hanning(100)[:, None] * 0.08
    intro_blocks.append(needle_drop)

    # Bar 1: Classic Baby Scratch (4 beats)
    # Moves forward and backward in smooth rhythmic sine waves
    n_b1 = int(sr * bar_s)
    t_b1 = np.linspace(0, bar_s, n_b1)
    # 4 baby scratches (1 per beat)
    traj_b1 = 0.05 + 0.18 * (0.5 - 0.5 * np.cos(2 * np.pi * (1.0 / beat_s) * t_b1))
    fader_b1 = np.ones(n_b1, dtype=np.float32)
    # Slight micro-fade at turnaround to emulate vinyl friction
    intro_blocks.append(scratch_resample(scratch_sample, traj_b1, fader_b1))

    # Bar 2: Chirp & Tear Scratch (4 beats)
    # Beat 1 & 2: Double chirp (forward with fader open, backward muted)
    # Beat 3 & 4: Tear scratch (two-speed forward push, quick pull back)
    n_b2 = int(sr * bar_s)
    t_b2 = np.linspace(0, bar_s, n_b2)
    traj_b2 = np.zeros(n_b2, dtype=np.float32)
    fader_b2 = np.ones(n_b2, dtype=np.float32)

    half_b2 = n_b2 // 2
    # First half (Chirps): 2 chirps over 2 beats
    t_chirp = np.linspace(0, beat_s * 2, half_b2)
    # Chirp trajectory
    chirp_cycle = (t_chirp % beat_s) / beat_s
    traj_b2[:half_b2] = 0.03 + 0.22 * np.sin(np.pi * chirp_cycle)
    # Fader cuts on the return stroke (second half of each beat)
    fader_chirp = np.where(chirp_cycle > 0.55, 0.0, 1.0).astype(np.float32)
    fader_b2[:half_b2] = fader_chirp

    # Second half (Tears): 2 tears over 2 beats
    t_tear = np.linspace(0, beat_s * 2, n_b2 - half_b2)
    tear_cycle = (t_tear % beat_s) / beat_s
    # Two-speed curve: slow push first 30%, fast burst next 30%, pull back last 40%
    tear_pos = np.where(
        tear_cycle < 0.3,
        tear_cycle * 0.4,
        np.where(tear_cycle < 0.6, 0.12 + (tear_cycle - 0.3) * 0.8, 0.36 * (1.0 - (tear_cycle - 0.6) / 0.4))
    )
    traj_b2[half_b2:] = 0.04 + tear_pos * 0.3
    intro_blocks.append(scratch_resample(scratch_sample, traj_b2, fader_b2))

    # Bar 3: Fast Transformer Scratch (4 beats)
    # Smooth forward and backward sweep while crossfader chops at 1/16th note divisions
    n_b3 = int(sr * bar_s)
    t_b3 = np.linspace(0, bar_s, n_b3)
    traj_b3 = 0.05 + 0.35 * (0.5 - 0.5 * np.cos(2 * np.pi * (0.5 / beat_s) * t_b3)) # 2 full sweeps
    # 16th note fader chops
    sixteenth_s = beat_s / 4.0
    chop_phase = (t_b3 % sixteenth_s) / sixteenth_s
    fader_b3 = np.where(chop_phase < 0.65, 1.0, 0.0).astype(np.float32)
    intro_blocks.append(scratch_resample(scratch_sample, traj_b3, fader_b3))

    # Bar 4: The Signature ACID Pro Stutter Roll & Turntable Brake
    # Beat 1: 1/8 note chops (2 chops)
    # Beat 2: 1/16 note chops (4 chops)
    # Beat 3: 1/32 note machine-gun roll (8 chops with volume crescendo)
    # Beat 4: Vinyl Tape-Stop / Power-Down Brake + 50ms silence before THE DROP!
    stutter_slice = scratch_sample[int(sr * 0.05):int(sr * 0.18)].copy() # 130ms attack transient

    def generate_stutter_div(slice_audio, div_fraction, duration_beats):
        div_duration = beat_s * div_fraction
        n_div = int(round(sr * div_duration))
        repeats = int(round(duration_beats / div_fraction))
        win_len = min(len(slice_audio), n_div)
        unit = np.zeros((n_div, 2), dtype=np.float32)
        # Apply 3ms soft envelope to prevent clicks
        env_cut = slice_audio[:win_len].copy()
        fade_out = min(int(sr * 0.003), win_len // 4)
        if fade_out > 0:
            env_cut[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
        unit[:win_len] = env_cut
        return np.tile(unit, (repeats, 1))

    # 1/8 chops (Beat 1)
    roll_1_8 = generate_stutter_div(stutter_slice, 0.5, 1.0)
    # 1/16 chops (Beat 2)
    roll_1_16 = generate_stutter_div(stutter_slice, 0.25, 1.0)
    # 1/32 chops (Beat 3) with crescendo
    roll_1_32 = generate_stutter_div(stutter_slice, 0.125, 1.0)
    crescendo = np.linspace(0.7, 1.15, len(roll_1_32))[:, None]
    roll_1_32 *= crescendo

    # Beat 4: Turntable Power-Down Brake (Tape Stop)
    brake_duration = beat_s * 0.85
    n_brake = int(sr * brake_duration)
    t_brake = np.linspace(0, brake_duration, n_brake)
    # Speed decays quadratically from 1 to 0: v(t) = (1 - t/T)^2
    # Position p(t) = t - t^2/T + t^3/(3*T^2)
    p_brake = 0.08 + (t_brake - (t_brake**2)/brake_duration + (t_brake**3)/(3 * brake_duration**2)) * 0.3
    fader_brake = (1.0 - (t_brake / brake_duration)**1.5).astype(np.float32)
    brake_audio = scratch_resample(scratch_sample, p_brake, fader_brake)

    # 60ms silence before beat 1 drops
    silence_gap = np.zeros((int(sr * (beat_s - brake_duration)), 2), dtype=np.float32)

    bar4_audio = np.concatenate([roll_1_8, roll_1_16, roll_1_32, brake_audio, silence_gap], axis=0)
    intro_blocks.append(bar4_audio)

    # Combine Part A (The Complete Intro Scratch Routine)
    intro_audio = np.concatenate(intro_blocks, axis=0)
    print(f"  * Intro Scratch Routine length: {len(intro_audio)/sr:.2f}s")

    # -------------------------------------------------------------------------
    # PART B: THE MAIN GROOVE & IN-SONG SLIP SCRATCH PERFORMANCE
    # -------------------------------------------------------------------------
    print("[3/5] Assembling Full Track Playback with Live In-Song Slip Scratching...")

    # Song plays from Cue 1 for 16 bars (~32.5 seconds)
    # At Bar 8 (beat 3 & 4), the DJ performs a Live Slip Scratch Fill!
    n_groove_1 = int(sr * bar_s * 7.5) # 7.5 bars of solid rolling groove
    groove_part1 = song_audio[:n_groove_1].copy()

    # In-Song Scratch Fill: 2 beats (1 second) of rapid Flare & Chirp
    n_fill = int(sr * beat_s * 2.0)
    t_fill = np.linspace(0, beat_s * 2.0, n_fill)
    traj_fill = 0.10 + 0.28 * np.sin(2 * np.pi * (1.0 / beat_s) * t_fill)
    fill_cycle = (t_fill % (beat_s / 2.0)) / (beat_s / 2.0)
    fader_fill = np.where(fill_cycle < 0.7, 1.0, 0.0).astype(np.float32)
    scratch_fill = scratch_resample(scratch_sample, traj_fill, fader_fill)

    # The song seamlessly resumes in phrase (Slip Mode) from Bar 8 Beat 1
    # up to Bar 24 (~32 more seconds of high energy Amapiano groove)
    resume_start = int(sr * bar_s * 8.0)
    resume_len = int(sr * bar_s * 16.0)
    groove_part2 = song_audio[resume_start:resume_start + resume_len].copy()

    # -------------------------------------------------------------------------
    # PART C: OUTRO VINYL BACKSPIN & BRAKE
    # -------------------------------------------------------------------------
    # Quick 1-bar turntable backspin rewind and stop
    n_spin = int(sr * bar_s * 1.5)
    t_spin = np.linspace(0, bar_s * 1.5, n_spin)
    # Violent rewind: high negative speed decaying exponentially
    traj_spin = 0.8 * np.exp(-3.5 * t_spin / (bar_s * 1.5))
    fader_spin = (1.0 - t_spin / (bar_s * 1.5)).astype(np.float32)
    spin_audio = scratch_resample(scratch_sample, traj_spin, fader_spin)

    # Final Assembly:
    # [Intro Scratch Routine] -> [Drop / Groove Part 1] -> [Slip Scratch Fill] -> [Groove Part 2] -> [Outro Backspin]
    full_mix = np.concatenate([
        intro_audio,
        groove_part1,
        scratch_fill,
        groove_part2,
        spin_audio
    ], axis=0)

    print(f"  * Total Scratched Preview Duration: {len(full_mix)/sr:.2f} seconds")

    # Step 3: Write to intermediate uncompressed WAV
    wavfile.write(temp_wav, sr, (np.clip(full_mix, -1.0, 1.0) * 32767).astype(np.int16))

    # Step 4: Encode to 320 kbps MP3 with EBU R128 DJ Loudness Normalization (-14 LUFS, -1.5 dBTP)
    print("\n[4/5] Applying EBU R128 DJ Loudness Normalization & Encoding 320k MP3...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", temp_wav,
        "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=10.0",
        "-b:a", "320k",
        "-metadata", "title=No Bad Vibes (DJ Scratch Intro & Performance Preview)",
        "-metadata", "artist=Heavy-K, DJ Buckz, Nonny D",
        "-metadata", "album=SmartMix DJ Scratch Series",
        "-metadata", "comment=ACID & VirtualDJ Scratch DNA Emulation",
        output_mp3
    ]
    subprocess.run(ffmpeg_cmd, check=True)

    # Clean up intermediate wav
    if os.path.exists(temp_wav):
        os.remove(temp_wav)

    # Step 5: Verification & Loudness Measurement
    print("\n[5/5] Measuring Output Loudness...")
    meter_cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", output_mp3,
        "-af", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    meter_res = subprocess.run(meter_cmd, capture_output=True, text=True)
    summary_lines = [l for l in meter_res.stderr.split("\n") if "I:" in l or "Peak:" in l or "LRA:" in l]

    out_mb = os.path.getsize(output_mp3) / (1024 * 1024)
    print("\n" + "=" * 78)
    print(" DJ SCRATCH PREVIEW GENERATED SUCCESSFULLY!")
    print("=" * 78)
    print(f"Output File : {output_mp3} ({out_mb:.2f} MB)")
    print(f"Loudness Metrics:")
    for sl in summary_lines[-3:]:
        print(f"  {sl.strip()}")
    print("=" * 78)

if __name__ == "__main__":
    build_scratch_preview()
