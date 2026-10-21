import os
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy import signal

def make_scratch_preview():
    track_path = r"C:\Users\odhis\Downloads\Amapiano\Heavy-K, DJ Buckz, Nonny D - No Bad Vibes (SPOTISAVER).mp3"
    output_mp3 = r"C:\Users\odhis\Downloads\Amapiano\Heavy-K_No_Bad_Vibes_DJ_Scratch_Preview.mp3"
    temp_wav = r"C:\Users\odhis\Downloads\Amapiano\_temp_scratch.wav"

    sr = 44100
    bpm = 118.0
    beat_s = 60.0 / bpm         # ~0.50847s per beat
    bar_s = beat_s * 4.0        # ~2.0339s per bar
    cue1_s = 0.122              # Cue 1 start time in the song

    print("=" * 78)
    print(" SMARTMIX: ADVANCED HUMANIZED DJ SCRATCH ENGINE (ACID / DJ STONE STYLE)")
    print("=" * 78)
    print(f"Track       : Heavy-K, DJ Buckz, Nonny D - No Bad Vibes")
    print(f"BPM         : {bpm} (1 Beat = {beat_s*1000:.1f}ms | 1 Bar = {bar_s:.2f}s)")

    # 1. Load 75 seconds of pristine song audio starting at Cue 1
    print("\n[1/6] Loading source audio...")
    cmd = [
        "ffmpeg", "-y", "-ss", str(cue1_s), "-t", "75",
        "-i", track_path,
        "-f", "s16le", "-ac", "2", "-ar", str(sr), "-"
    ]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    raw_audio = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    song_audio = raw_audio.reshape(-1, 2)

    # Scratch sample: anchored right at the sharp transient attack (sample 350 onwards)
    transient_offset = int(sr * 0.008) # 8ms in gives the punchiest initial attack
    scratch_sample = song_audio[transient_offset:transient_offset + int(sr * 1.8)].copy()

    # -------------------------------------------------------------------------
    # DSP: Resampling with Platter Physics, Inertia & Phono Emulation
    # -------------------------------------------------------------------------
    def render_scratch(source, time_traj_sec, fader_env):
        sample_indices = time_traj_sec * sr
        sample_indices = np.clip(sample_indices, 0, len(source) - 2)
        idx_floor = np.floor(sample_indices).astype(np.int32)
        frac = (sample_indices - idx_floor)[:, None]

        s0 = source[idx_floor]
        s1 = source[idx_floor + 1]
        scratched = s0 * (1.0 - frac) + s1 * frac

        # Platter velocity (pitch derivative)
        dt = 1.0 / sr
        vel = np.gradient(time_traj_sec, dt)
        speed = np.abs(vel)

        # Phono cartridge response: high-frequency boost on fast forward flicks, warm bass on slow pulls
        scratched *= np.clip(0.65 + 0.35 * speed[:, None], 0.4, 1.4)

        # Smooth fader cuts (1.5ms edge to prevent clicks while keeping cuts razor sharp)
        kernel = max(3, int(sr * 0.0015) | 1)
        smoothed_fader = signal.medfilt(fader_env, kernel_size=kernel) if len(fader_env) > kernel else fader_env
        scratched *= smoothed_fader[:, None]
        return scratched

    # -------------------------------------------------------------------------
    # Scratch Gesture Generators (Humanized S-Curves & Fader Timing)
    # -------------------------------------------------------------------------
    def baby_scratch(duration_s, amp_s=0.16, n_strokes=1):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        stroke_dur = duration_s / (2 * n_strokes)
        traj = np.zeros(n, dtype=np.float32)
        for i in range(2 * n_strokes):
            t_s = i * stroke_dur
            t_e = (i + 1) * stroke_dur
            mask = (t >= t_s) & (t < t_e)
            u = (t[mask] - t_s) / stroke_dur
            # Cubic Hermite S-curve (natural human hand deceleration)
            curve = u**2 * (3.0 - 2.0 * u)
            if i % 2 == 0:
                traj[mask] = curve * amp_s
            else:
                traj[mask] = (1.0 - curve) * amp_s
        fader = np.ones(n, dtype=np.float32)
        return traj, fader

    def chirp_scratch(duration_s, amp_s=0.18, n_chirps=1):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        chirp_dur = duration_s / n_chirps
        traj = np.zeros(n, dtype=np.float32)
        fader = np.zeros(n, dtype=np.float32)
        for i in range(n_chirps):
            t_s = i * chirp_dur
            t_e = (i + 1) * chirp_dur
            mask = (t >= t_s) & (t < t_e)
            u = (t[mask] - t_s) / chirp_dur
            # Forward push first 45%, backstroke next 55%
            push_mask = u < 0.45
            u_push = u[push_mask] / 0.45
            u_pull = (u[~push_mask] - 0.45) / 0.55
            
            stroke_traj = np.zeros(len(u), dtype=np.float32)
            stroke_traj[push_mask] = (u_push**2 * (3 - 2 * u_push)) * amp_s
            stroke_traj[~push_mask] = ((1.0 - u_pull)**2 * (3 - 2 * (1.0 - u_pull))) * amp_s
            traj[mask] = stroke_traj

            # Fader open during forward push, cuts instantly on turnaround/pull, opens at end
            stroke_fader = np.zeros(len(u), dtype=np.float32)
            stroke_fader[push_mask] = 1.0
            stroke_fader[~push_mask] = np.where(u_pull > 0.85, 1.0, 0.0)
            fader[mask] = stroke_fader
        return traj, fader

    def tear_scratch(duration_s, amp_s=0.20):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        # Two-speed forward stroke (slow drag 0->35%, quick flick 35%->60%, pull back 60%->100%)
        traj = np.where(
            u < 0.35,
            (u / 0.35) * (amp_s * 0.4),
            np.where(
                u < 0.60,
                (amp_s * 0.4) + ((u - 0.35) / 0.25) * (amp_s * 0.6),
                amp_s * (1.0 - (u - 0.60) / 0.40)
            )
        ).astype(np.float32)
        fader = np.ones(n, dtype=np.float32)
        return traj, fader

    def transformer_scratch(duration_s, amp_s=0.25, cuts_per_beat=4):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        # Smooth forward-reverse platter movement
        traj = (0.5 - 0.5 * np.cos(2 * np.pi * u)) * amp_s
        # Rhythmic fader chops
        cut_period = beat_s / cuts_per_beat
        phase = (t % cut_period) / cut_period
        fader = np.where(phase < 0.65, 1.0, 0.0).astype(np.float32)
        return traj.astype(np.float32), fader

    def flare_scratch(duration_s, amp_s=0.22):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        # Forward stroke 0->0.5, backward 0.5->1.0
        traj = np.where(u < 0.5, (u / 0.5) * amp_s, (1.0 - (u - 0.5) / 0.5) * amp_s).astype(np.float32)
        # Flare: click fader closed twice mid-stroke
        fader = np.ones(n, dtype=np.float32)
        # Click 1 at u=0.25, Click 2 at u=0.75
        mask_click1 = (u >= 0.22) & (u <= 0.28)
        mask_click2 = (u >= 0.72) & (u <= 0.78)
        fader[mask_click1] = 0.0
        fader[mask_click2] = 0.0
        return traj, fader

    def stutter_roll(slice_audio, div_beats, duration_beats, crescendo=False):
        div_s = beat_s * div_beats
        n_div = int(round(sr * div_s))
        repeats = int(round(duration_beats / div_beats))
        win_len = min(len(slice_audio), n_div)
        unit = np.zeros((n_div, 2), dtype=np.float32)
        fade_len = min(int(sr * 0.003), win_len // 4)
        c = slice_audio[:win_len].copy()
        if fade_len > 0:
            c[-fade_len:] *= np.linspace(1, 0, fade_len)[:, None]
        unit[:win_len] = c
        block = np.tile(unit, (repeats, 1))
        if crescendo:
            block *= np.linspace(0.7, 1.25, len(block))[:, None]
        return block

    def vinyl_brake(source, duration_s):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n)
        # v(t) = (1 - t/T)^2 -> p(t) = t - t^2/T + t^3/(3*T^2)
        p = (t - (t**2)/duration_s + (t**3)/(3 * duration_s**2)) * 0.35
        fader = (1.0 - (t / duration_s)**1.8).astype(np.float32)
        return render_scratch(source, p, fader)

    # -------------------------------------------------------------------------
    # [2/6] BUILD THE PERFECT ON-BEAT INTRO (Exactly 3 Bars = 12 Beats)
    # -------------------------------------------------------------------------
    print("\n[2/6] Building Perfect On-Beat Intro (ACID / DJ Stone Style)...")
    intro_parts = []

    # Bar 1 (Beats 1 - 4): Rhythmic Baby & Chirp Stabs
    # Beat 1: Forward stab + pull
    t1, f1 = baby_scratch(beat_s, amp_s=0.18, n_strokes=1)
    # Beat 2: Forward stab + pull
    t2, f2 = baby_scratch(beat_s, amp_s=0.18, n_strokes=1)
    # Beat 3: Double baby scratch
    t3, f3 = baby_scratch(beat_s, amp_s=0.14, n_strokes=2)
    # Beat 4: Sharp chirp + fader snap
    t4, f4 = chirp_scratch(beat_s, amp_s=0.20, n_chirps=1)
    bar1 = np.concatenate([
        render_scratch(scratch_sample, t1, f1),
        render_scratch(scratch_sample, t2, f2),
        render_scratch(scratch_sample, t3, f3),
        render_scratch(scratch_sample, t4, f4)
    ], axis=0)
    intro_parts.append(bar1)

    # Bar 2 (Beats 5 - 8): Tear, Flare & Transformer Chops
    # Beat 5: Tear scratch
    t5, f5 = tear_scratch(beat_s, amp_s=0.22)
    # Beat 6: Flare scratch (double click)
    t6, f6 = flare_scratch(beat_s, amp_s=0.20)
    # Beat 7: Transformer chops (1/16th cuts)
    t7, f7 = transformer_scratch(beat_s, amp_s=0.24, cuts_per_beat=4)
    # Beat 8: Sharp pull into the build
    t8, f8 = chirp_scratch(beat_s, amp_s=0.22, n_chirps=2)
    bar2 = np.concatenate([
        render_scratch(scratch_sample, t5, f5),
        render_scratch(scratch_sample, t6, f6),
        render_scratch(scratch_sample, t7, f7),
        render_scratch(scratch_sample, t8, f8)
    ], axis=0)
    intro_parts.append(bar2)

    # Bar 3 (Beats 9 - 12): The Signature ACID Stutter Roll & Turntable Brake
    # Beat 9: 1/8 note chops
    r_1_8 = stutter_roll(scratch_sample, 0.5, 1.0)
    # Beat 10: 1/16 note chops
    r_1_16 = stutter_roll(scratch_sample, 0.25, 1.0)
    # Beat 11: 1/32 note machine-gun roll with crescendo
    r_1_32 = stutter_roll(scratch_sample, 0.125, 1.0, crescendo=True)
    # Beat 12: Vinyl tape stop / motor power down (slows down to 0) + 40ms silence
    brake_dur = beat_s * 0.82
    brake_audio = vinyl_brake(scratch_sample, brake_dur)
    silence_dur = beat_s - brake_dur
    silence = np.zeros((int(round(sr * silence_dur)), 2), dtype=np.float32)
    bar3 = np.concatenate([r_1_8, r_1_16, r_1_32, brake_audio, silence], axis=0)
    intro_parts.append(bar3)

    intro_audio = np.concatenate(intro_parts, axis=0)
    print(f"  -> Intro Scratch Routine: {len(intro_audio)/sr:.2f}s (Exactly 3 Bars / 12 Beats on-grid)")

    # -------------------------------------------------------------------------
    # [3/6] ASSEMBLE FULL MIX WITH CONTINUOUS ON-BEAT SCRATCHES ACROSS AUDIO
    # -------------------------------------------------------------------------
    print("\n[3/6] Weaving Scratches Across the Audio Phrasing...")

    # Helper: Slice of the song from bar start to bar end
    def get_song_bars(start_bar, end_bar):
        s = int(round(start_bar * bar_s * sr))
        e = int(round(end_bar * bar_s * sr))
        return song_audio[s:e].copy()

    mix_segments = []

    # Intro Routine (0.0s -> 6.1s)
    mix_segments.append(intro_audio)

    # --- DROP 1 (Beat 1 of Song): Bars 0 to 3.5 (Rolling Amapiano Groove) ---
    print("  * [06.1s] DROP 1: Song drops on Beat 1 (Groove rolling for 3.5 bars)")
    mix_segments.append(get_song_bars(0, 3.5))

    # --- SCRATCH 1 (Bar 4, Beats 3 & 4): Phrase Turnaround ---
    # Fast Double-Chirp & Baby Scratch fill
    print("  * [13.2s] Scratch 1: Phrase Turnaround Fill (Double Chirp + Baby)")
    tc1, fc1 = chirp_scratch(beat_s, amp_s=0.22, n_chirps=2)
    tc2, fc2 = baby_scratch(beat_s, amp_s=0.16, n_strokes=2)
    fill1 = np.concatenate([render_scratch(scratch_sample, tc1, fc1), render_scratch(scratch_sample, tc2, fc2)], axis=0)
    mix_segments.append(fill1)

    # --- GROOVE: Bars 4 to 7.0 ---
    mix_segments.append(get_song_bars(4, 7.0))

    # --- SCRATCH 2 (Bar 8, Beats 2, 3, 4): In-Song Slip Scratch Solo ---
    print("  * [20.3s] Scratch 2: In-Song Slip Scratch Solo (Transformer + Flare)")
    tf1, ff1 = transformer_scratch(beat_s * 1.5, amp_s=0.25, cuts_per_beat=4)
    tf2, ff2 = flare_scratch(beat_s * 1.5, amp_s=0.22)
    fill2 = np.concatenate([render_scratch(scratch_sample, tf1, ff1), render_scratch(scratch_sample, tf2, ff2)], axis=0)
    mix_segments.append(fill2)

    # --- GROOVE: Bars 8 to 11.5 ---
    mix_segments.append(get_song_bars(8, 11.5))

    # --- SCRATCH 3 (Bar 12, Beats 3 & 4): Stutter Loop-Roll Accent ---
    print("  * [29.5s] Scratch 3: 1/32 Stutter Roll Accent into Pre-Drop")
    roll_accent = stutter_roll(scratch_sample, 0.125, 2.0, crescendo=True)
    mix_segments.append(roll_accent)

    # --- PRE-DROP GROOVE: Bars 12 to 15.0 ---
    mix_segments.append(get_song_bars(12, 15.0))

    # --- SCRATCH 4 (Bar 16, Beats 1 - 4): Massive Pre-Drop Scratch Solo ---
    # Just before the major vocal & log drum explosion at Bar 17
    print("  * [36.6s] Scratch 4: Big Pre-Drop Scratch Solo (Chirp + Tear + Brake)")
    t_pd1, f_pd1 = chirp_scratch(beat_s, amp_s=0.24, n_chirps=2)
    t_pd2, f_pd2 = tear_scratch(beat_s, amp_s=0.22)
    t_pd3, f_pd3 = baby_scratch(beat_s, amp_s=0.18, n_strokes=2)
    pd_brake = vinyl_brake(scratch_sample, beat_s * 0.85)
    pd_silence = np.zeros((int(round(sr * (beat_s * 0.15))), 2), dtype=np.float32)
    fill4 = np.concatenate([
        render_scratch(scratch_sample, t_pd1, f_pd1),
        render_scratch(scratch_sample, t_pd2, f_pd2),
        render_scratch(scratch_sample, t_pd3, f_pd3),
        pd_brake,
        pd_silence
    ], axis=0)
    mix_segments.append(fill4)

    # --- THE MAJOR DROP: Bar 16 to 19.5 (Heavy Vocal & Bassline Drop) ---
    print("  * [38.6s] MAJOR DROP: Full Vocal & Log Drum Explosion")
    mix_segments.append(get_song_bars(16, 19.5))

    # --- SCRATCH 5 (Bar 20, Beats 3 & 4): Vocal Pocket Slip Scratch ---
    print("  * [45.7s] Scratch 5: Vocal Pocket Slip Scratch (Double Chirp)")
    t_vp, f_vp = chirp_scratch(beat_s * 2.0, amp_s=0.25, n_chirps=3)
    fill5 = render_scratch(scratch_sample, t_vp, f_vp)
    mix_segments.append(fill5)

    # --- GROOVE: Bars 20 to 23.0 ---
    mix_segments.append(get_song_bars(20, 23.0))

    # --- SCRATCH 6 (Bar 24, Beats 2, 3, 4): Fast Flare & Transformer ---
    print("  * [52.8s] Scratch 6: Fast Flare & Transformer Combo")
    t_fl, f_fl = flare_scratch(beat_s * 1.5, amp_s=0.22)
    t_tr, f_tr = transformer_scratch(beat_s * 1.5, amp_s=0.24, cuts_per_beat=4)
    fill6 = np.concatenate([render_scratch(scratch_sample, t_fl, f_fl), render_scratch(scratch_sample, t_tr, f_tr)], axis=0)
    mix_segments.append(fill6)

    # --- GROOVE: Bars 24 to 28.0 ---
    mix_segments.append(get_song_bars(24, 28.0))

    # --- OUTRO: High-Speed Turntable Backspin & Vinyl Power Down ---
    print("  * [63.0s] OUTRO: Turntable Rewind Backspin & Brake")
    spin_dur = bar_s * 1.5
    n_spin = int(round(sr * spin_dur))
    t_spin = np.linspace(0, spin_dur, n_spin)
    traj_spin = 0.9 * np.exp(-3.5 * t_spin / spin_dur)
    fader_spin = (1.0 - t_spin / spin_dur).astype(np.float32)
    outro_spin = render_scratch(scratch_sample, traj_spin, fader_spin)
    mix_segments.append(outro_spin)

    # Concatenate complete mix
    full_audio = np.concatenate(mix_segments, axis=0)
    total_duration_s = len(full_audio) / sr
    print(f"\n[4/6] Assembly Complete! Total Preview Duration: {total_duration_s:.2f} seconds")

    # Step 4: Write intermediate WAV
    wavfile.write(temp_wav, sr, (np.clip(full_audio, -1.0, 1.0) * 32767).astype(np.int16))

    # Step 5: Master with EBU R128 DJ Loudness Normalization (-14 LUFS, -1.5 dBTP)
    print("\n[5/6] Mastering to 320k MP3 with EBU R128 DJ Standards...")
    master_cmd = [
        "ffmpeg", "-y",
        "-i", temp_wav,
        "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=10.0",
        "-b:a", "320k",
        "-metadata", "title=No Bad Vibes (DJ Scratch Master Preview)",
        "-metadata", "artist=Heavy-K, DJ Buckz, Nonny D",
        "-metadata", "album=SmartMix Professional DJ Series",
        "-metadata", "comment=ACID & VirtualDJ Humanized Scratch Performance",
        output_mp3
    ]
    subprocess.run(master_cmd, check=True)

    if os.path.exists(temp_wav):
        os.remove(temp_wav)

    # Step 6: Loudness Verification
    print("\n[6/6] Verifying Master Loudness...")
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
    print(" ADVANCED DJ SCRATCH PREVIEW GENERATED SUCCESSFULLY!")
    print("=" * 78)
    print(f"File   : {output_mp3} ({out_mb:.2f} MB)")
    print(f"Length : {total_duration_s:.2f} seconds")
    print(f"Loudness:")
    for sl in summary_lines[-3:]:
        print(f"  {sl.strip()}")
    print("=" * 78)

if __name__ == "__main__":
    make_scratch_preview()
