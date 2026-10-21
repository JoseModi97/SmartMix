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
    total_duration_s = 65.0     # Preview duration

    print("=" * 78)
    print(" SMARTMIX: MULTITRACK LIVE DJ SCRATCH ENGINE (CONTINUOUS SONG PLAYBACK)")
    print("=" * 78)
    print(f"Track       : Heavy-K, DJ Buckz, Nonny D - No Bad Vibes")
    print(f"BPM         : {bpm} (1 Beat = {beat_s*1000:.1f}ms | 1 Bar = {bar_s:.2f}s)")
    print(f"Mode        : Continuous Song Deck + Overlay Scratch Deck (ACID / Slip Style)")

    # 1. Load continuous song audio starting at Cue 1
    print("\n[1/5] Extracting continuous song track...")
    cmd = [
        "ffmpeg", "-y", "-ss", str(cue1_s), "-t", str(total_duration_s + 2.0),
        "-i", track_path,
        "-f", "s16le", "-ac", "2", "-ar", str(sr), "-"
    ]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    raw_audio = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    song_audio = raw_audio.reshape(-1, 2)

    n_total = int(round(sr * total_duration_s))
    song_track = song_audio[:n_total].copy()
    scratch_track = np.zeros_like(song_track)
    ducking_envelope = np.ones((n_total, 1), dtype=np.float32)

    # Scratch sample: anchored right at the punchiest 8ms attack peak
    transient_offset = int(sr * 0.008)
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

        dt = 1.0 / sr
        vel = np.gradient(time_traj_sec, dt)
        speed = np.abs(vel)

        # Phono cartridge response
        scratched *= np.clip(0.65 + 0.35 * speed[:, None], 0.4, 1.4)

        # Smooth fader cuts (1.5ms edge to prevent digital clicks)
        kernel = max(3, int(sr * 0.0015) | 1)
        smoothed_fader = signal.medfilt(fader_env, kernel_size=kernel) if len(fader_env) > kernel else fader_env
        scratched *= smoothed_fader[:, None]
        return scratched

    # -------------------------------------------------------------------------
    # Scratch Gesture Generators
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
            push_mask = u < 0.45
            u_push = u[push_mask] / 0.45
            u_pull = (u[~push_mask] - 0.45) / 0.55
            
            stroke_traj = np.zeros(len(u), dtype=np.float32)
            stroke_traj[push_mask] = (u_push**2 * (3 - 2 * u_push)) * amp_s
            stroke_traj[~push_mask] = ((1.0 - u_pull)**2 * (3 - 2 * (1.0 - u_pull))) * amp_s
            traj[mask] = stroke_traj

            stroke_fader = np.zeros(len(u), dtype=np.float32)
            stroke_fader[push_mask] = 1.0
            stroke_fader[~push_mask] = np.where(u_pull > 0.85, 1.0, 0.0)
            fader[mask] = stroke_fader
        return traj, fader

    def tear_scratch(duration_s, amp_s=0.20):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
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
        traj = (0.5 - 0.5 * np.cos(2 * np.pi * u)) * amp_s
        cut_period = beat_s / cuts_per_beat
        phase = (t % cut_period) / cut_period
        fader = np.where(phase < 0.65, 1.0, 0.0).astype(np.float32)
        return traj.astype(np.float32), fader

    def flare_scratch(duration_s, amp_s=0.22):
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        traj = np.where(u < 0.5, (u / 0.5) * amp_s, (1.0 - (u - 0.5) / 0.5) * amp_s).astype(np.float32)
        fader = np.ones(n, dtype=np.float32)
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
        p = (t - (t**2)/duration_s + (t**3)/(3 * duration_s**2)) * 0.35
        fader = (1.0 - (t / duration_s)**1.8).astype(np.float32)
        return render_scratch(source, p, fader)

    # -------------------------------------------------------------------------
    # Helper: Add Scratch Overlay with Soft Sidechain Ducking
    # -------------------------------------------------------------------------
    def add_scratch_event(start_time_s, audio_block, duck_amount=0.72, boost=1.20):
        start_samp = int(round(start_time_s * sr))
        end_samp = start_samp + len(audio_block)
        if start_samp >= n_total:
            return
        if end_samp > n_total:
            audio_block = audio_block[:n_total - start_samp]
            end_samp = n_total
        
        # Overlay scratch audio onto scratch deck
        scratch_track[start_samp:end_samp] += audio_block * boost

        # Soft sidechain ducking envelope on song deck so scratch cuts through cleanly
        duck_len = end_samp - start_samp
        duck_env = np.ones(duck_len, dtype=np.float32) * duck_amount
        ramp_len = min(int(sr * 0.008), duck_len // 4) # 8ms soft crossfade
        if ramp_len > 0:
            duck_env[:ramp_len] = np.linspace(1.0, duck_amount, ramp_len)
            duck_env[-ramp_len:] = np.linspace(duck_amount, 1.0, ramp_len)
        ducking_envelope[start_samp:end_samp, 0] = np.minimum(ducking_envelope[start_samp:end_samp, 0], duck_env)

    print("\n[2/5] Weaving Scratches ON TOP of the Continuous Playing Song...")

    # =========================================================================
    # INTRO SECTION: The song plays its intro while DJ scratches live on top!
    # =========================================================================
    # Bar 1 (0.0s - 2.03s): Song starts playing, baby stabs overlaid
    print("  * [00.0s - 02.0s] Bar 1: Song intro plays with Baby Stabs overlaid")
    t1, f1 = baby_scratch(beat_s, amp_s=0.18, n_strokes=1)
    t2, f2 = baby_scratch(beat_s, amp_s=0.18, n_strokes=1)
    t3, f3 = baby_scratch(beat_s, amp_s=0.14, n_strokes=2)
    t4, f4 = chirp_scratch(beat_s, amp_s=0.20, n_chirps=1)
    intro_scratches_1 = np.concatenate([
        render_scratch(scratch_sample, t1, f1),
        render_scratch(scratch_sample, t2, f2),
        render_scratch(scratch_sample, t3, f3),
        render_scratch(scratch_sample, t4, f4)
    ], axis=0)
    add_scratch_event(0.0, intro_scratches_1, duck_amount=0.65)

    # Bar 2 (2.03s - 4.07s): Song intro continues, tear & transformer overlaid
    print("  * [02.0s - 04.1s] Bar 2: Song intro continues with Tear & Transformer chops")
    t5, f5 = tear_scratch(beat_s, amp_s=0.22)
    t6, f6 = flare_scratch(beat_s, amp_s=0.20)
    t7, f7 = transformer_scratch(beat_s, amp_s=0.24, cuts_per_beat=4)
    t8, f8 = chirp_scratch(beat_s, amp_s=0.22, n_chirps=2)
    intro_scratches_2 = np.concatenate([
        render_scratch(scratch_sample, t5, f5),
        render_scratch(scratch_sample, t6, f6),
        render_scratch(scratch_sample, t7, f7),
        render_scratch(scratch_sample, t8, f8)
    ], axis=0)
    add_scratch_event(bar_s, intro_scratches_2, duck_amount=0.65)

    # Bar 3 (4.07s - 6.10s): The ACID Stutter Roll & Pre-Drop Brake
    print("  * [04.1s - 06.1s] Bar 3: ACID 1/8 -> 1/16 -> 1/32 Stutter Roll & Brake")
    r_1_8 = stutter_roll(scratch_sample, 0.5, 1.0)
    r_1_16 = stutter_roll(scratch_sample, 0.25, 1.0)
    r_1_32 = stutter_roll(scratch_sample, 0.125, 1.0, crescendo=True)
    brake_dur = beat_s * 0.85
    brake_audio = vinyl_brake(scratch_sample, brake_dur)
    intro_roll = np.concatenate([r_1_8, r_1_16, r_1_32, brake_audio], axis=0)
    add_scratch_event(bar_s * 2.0, intro_roll, duck_amount=0.55)

    # At Beat 12 (5.59s to 6.10s): Quick half-beat tape stop mute on the song right before THE DROP
    brake_start_samp = int(round((bar_s * 2.0 + beat_s * 3.0) * sr))
    brake_len = int(round(beat_s * sr))
    ducking_envelope[brake_start_samp:brake_start_samp + brake_len, 0] *= np.linspace(1.0, 0.0, brake_len)**2

    print("  * [06.1s] DROP 1: Song hits full groove and NEVER STOPS PLAYING!")

    # =========================================================================
    # IN-SONG SCRATCHES (Song plays continuously, scratches dance over top!)
    # =========================================================================
    # Scratch 1: Bar 4, Beats 3 & 4 (Phrase Turnaround Double Chirp)
    print("  * [07.1s] Scratch 1: Turnaround Double Chirp + Baby over rolling beat")
    tc1, fc1 = chirp_scratch(beat_s, amp_s=0.22, n_chirps=2)
    tc2, fc2 = baby_scratch(beat_s, amp_s=0.16, n_strokes=2)
    s1 = np.concatenate([render_scratch(scratch_sample, tc1, fc1), render_scratch(scratch_sample, tc2, fc2)], axis=0)
    add_scratch_event(bar_s * 3.5, s1, duck_amount=0.75)

    # Scratch 2: Bar 8, Beats 2, 3, 4 (Transformer + Flare Slip Scratch)
    print("  * [14.7s] Scratch 2: In-Song Slip Scratch Solo (Transformer + Flare)")
    tf1, ff1 = transformer_scratch(beat_s * 1.5, amp_s=0.25, cuts_per_beat=4)
    tf2, ff2 = flare_scratch(beat_s * 1.5, amp_s=0.22)
    s2 = np.concatenate([render_scratch(scratch_sample, tf1, ff1), render_scratch(scratch_sample, tf2, ff2)], axis=0)
    add_scratch_event(bar_s * 7.25, s2, duck_amount=0.72)

    # Scratch 3: Bar 12, Beats 3 & 4 (1/32 Stutter Roll Accent)
    print("  * [23.4s] Scratch 3: 1/32 Stutter Roll Accent over groove")
    s3 = stutter_roll(scratch_sample, 0.125, 2.0, crescendo=True)
    add_scratch_event(bar_s * 11.5, s3, duck_amount=0.75)

    # Scratch 4: Bar 16, Beats 1 to 4 (Pre-Drop Scratch Routine over build-up)
    print("  * [30.5s] Scratch 4: Pre-Drop Scratch Solo leading into Major Drop")
    t_pd1, f_pd1 = chirp_scratch(beat_s, amp_s=0.24, n_chirps=2)
    t_pd2, f_pd2 = tear_scratch(beat_s, amp_s=0.22)
    t_pd3, f_pd3 = baby_scratch(beat_s, amp_s=0.18, n_strokes=2)
    pd_brake = vinyl_brake(scratch_sample, beat_s * 0.85)
    s4 = np.concatenate([
        render_scratch(scratch_sample, t_pd1, f_pd1),
        render_scratch(scratch_sample, t_pd2, f_pd2),
        render_scratch(scratch_sample, t_pd3, f_pd3),
        pd_brake
    ], axis=0)
    add_scratch_event(bar_s * 15.0, s4, duck_amount=0.68)

    print("  * [32.5s] MAJOR DROP: Heavy Vocal & Log Drum Explosion!")

    # Scratch 5: Bar 20, Beats 3 & 4 (Vocal Pocket Chirp Scratch)
    print("  * [39.7s] Scratch 5: Vocal Pocket Chirp Scratch over vocal break")
    t_vp, f_vp = chirp_scratch(beat_s * 2.0, amp_s=0.25, n_chirps=3)
    s5 = render_scratch(scratch_sample, t_vp, f_vp)
    add_scratch_event(bar_s * 19.5, s5, duck_amount=0.75)

    # Scratch 6: Bar 24, Beats 2, 3, 4 (Fast Flare & Transformer Combo)
    print("  * [47.3s] Scratch 6: Fast Flare & Transformer Combo over rolling beat")
    t_fl, f_fl = flare_scratch(beat_s * 1.5, amp_s=0.22)
    t_tr, f_tr = transformer_scratch(beat_s * 1.5, amp_s=0.24, cuts_per_beat=4)
    s6 = np.concatenate([render_scratch(scratch_sample, t_fl, f_fl), render_scratch(scratch_sample, t_tr, f_tr)], axis=0)
    add_scratch_event(bar_s * 23.25, s6, duck_amount=0.72)

    # Scratch 7: Bar 28, Beats 3 & 4 (Double Chirp into Outro)
    print("  * [55.4s] Scratch 7: Double Chirp into Outro Climax")
    t_oc, f_oc = chirp_scratch(beat_s * 2.0, amp_s=0.24, n_chirps=3)
    s7 = render_scratch(scratch_sample, t_oc, f_oc)
    add_scratch_event(bar_s * 27.25, s7, duck_amount=0.75)

    # Outro: Bar 31 (Turntable Rewind Backspin & Motor Power Down)
    print("  * [61.0s] OUTRO: Turntable Backspin Rewind & Vinyl Brake")
    spin_dur = bar_s * 1.5
    n_spin = int(round(sr * spin_dur))
    t_spin = np.linspace(0, spin_dur, n_spin)
    traj_spin = 0.9 * np.exp(-3.5 * t_spin / spin_dur)
    fader_spin = (1.0 - t_spin / spin_dur).astype(np.float32)
    outro_spin = render_scratch(scratch_sample, traj_spin, fader_spin)
    add_scratch_event(total_duration_s - spin_dur, outro_spin, duck_amount=0.4)

    # Fade out song at the very end (last 1.5 seconds)
    fade_end_len = int(sr * 1.5)
    ducking_envelope[-fade_end_len:, 0] *= np.linspace(1.0, 0.0, fade_end_len)

    # =========================================================================
    # MULTITRACK MIXDOWN: Song Deck + Scratch Deck
    # =========================================================================
    print("\n[3/5] Mixing Multitrack (Continuous Song + Overlay Scratches)...")
    multitrack_master = song_track * ducking_envelope + scratch_track

    # Step 4: Write intermediate WAV
    wavfile.write(temp_wav, sr, (np.clip(multitrack_master, -1.0, 1.0) * 32767).astype(np.int16))

    # Step 5: Master with EBU R128 DJ Loudness Normalization (-14 LUFS, -1.5 dBTP)
    print("\n[4/5] Mastering to 320k MP3 with EBU R128 DJ Standards...")
    master_cmd = [
        "ffmpeg", "-y",
        "-i", temp_wav,
        "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=10.0",
        "-b:a", "320k",
        "-metadata", "title=No Bad Vibes (Continuous Multitrack DJ Scratch Master)",
        "-metadata", "artist=Heavy-K, DJ Buckz, Nonny D",
        "-metadata", "album=SmartMix Professional DJ Series",
        "-metadata", "comment=Multitrack Continuous Playback with ACID & VirtualDJ Scratches",
        output_mp3
    ]
    subprocess.run(master_cmd, check=True)

    if os.path.exists(temp_wav):
        os.remove(temp_wav)

    # Step 6: Loudness Verification
    print("\n[5/5] Verifying Master Loudness...")
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
    print(" MULTITRACK DJ SCRATCH MASTER GENERATED SUCCESSFULLY!")
    print("=" * 78)
    print(f"File     : {output_mp3} ({out_mb:.2f} MB)")
    print(f"Length   : {total_duration_s:.2f} seconds")
    print(f"Playback : Song plays CONTINUOUSLY with scratches overlaid on top")
    print(f"Loudness :")
    for sl in summary_lines[-3:]:
        print(f"  {sl.strip()}")
    print("=" * 78)

if __name__ == "__main__":
    make_scratch_preview()
