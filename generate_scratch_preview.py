import os
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy import signal

def make_wizard_scratch_preview():
    track_path = r"C:\Users\odhis\Downloads\Amapiano\Heavy-K, DJ Buckz, Nonny D - No Bad Vibes (SPOTISAVER).mp3"
    output_mp3 = r"C:\Users\odhis\Downloads\Amapiano\Heavy-K_No_Bad_Vibes_DJ_Scratch_Preview.mp3"
    temp_wav = r"C:\Users\odhis\Downloads\Amapiano\_temp_scratch.wav"

    sr = 44100
    bpm = 118.0
    beat_s = 60.0 / bpm         # ~0.50847s per beat
    bar_s = beat_s * 4.0        # ~2.0339s per bar
    cue1_s = 0.122              # Cue 1 start time in the song
    total_duration_s = 68.0     # Preview duration

    print("=" * 78)
    print(" SMARTMIX: FUNKMASTER FLEX & WIZARD-LEVEL TURNTABLISM ENGINE")
    print("=" * 78)
    print(f"Track       : Heavy-K, DJ Buckz, Nonny D - No Bad Vibes")
    print(f"BPM         : {bpm} (1 Beat = {beat_s*1000:.1f}ms | 1 Bar = {bar_s:.2f}s)")
    print(f"Style       : Funkmaster Flex Tease-Rewinds & DMC Wizard Fast-Cut Turntablism")

    # 1. Load continuous song audio starting at Cue 1
    print("\n[1/6] Extracting continuous song track...")
    cmd = [
        "ffmpeg", "-y", "-ss", str(cue1_s), "-t", str(total_duration_s + 4.0),
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

    # 2. Extract Song Attack Transient Sample
    transient_offset = int(sr * 0.008)
    song_stab = song_audio[transient_offset:transient_offset + int(sr * 1.5)].copy()

    # 3. Synthesize the Legendary Turntablist "AHHHH" Vocal Battle Sample
    print("[2/6] Synthesizing Iconic Turntablist 'AHHHH' Vocal Sample...")
    n_ah = int(sr * 1.8)
    t_ah = np.linspace(0, 1.8, n_ah)
    # Rich sawtooth fundamental at 138 Hz
    saw = signal.sawtooth(2 * np.pi * 138.0 * t_ah)
    # 4 vocal formants for open "AH": F1=750Hz, F2=1250Hz, F3=2400Hz, F4=3400Hz
    b1, a1 = signal.iirpeak(750, 6, sr)
    b2, a2 = signal.iirpeak(1250, 7, sr)
    b3, a3 = signal.iirpeak(2400, 8, sr)
    b4, a4 = signal.iirpeak(3400, 10, sr)
    f_ah = (
        signal.lfilter(b1, a1, saw) * 1.8 +
        signal.lfilter(b2, a2, saw) * 1.5 +
        signal.lfilter(b3, a3, saw) * 1.0 +
        signal.lfilter(b4, a4, saw) * 0.5
    )
    # Tube/phono saturation
    f_ah = np.tanh(f_ah * 1.7)
    env_ah = np.clip(t_ah / 0.010, 0, 1) * np.exp(-t_ah / 1.2)
    f_ah = (f_ah * env_ah / np.max(np.abs(f_ah))).astype(np.float32)
    ah_sample = np.stack([f_ah, f_ah], axis=1)

    # -------------------------------------------------------------------------
    # DSP: Resampling with Platter Physics, Velocity Boost & Fader Curves
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

        # Turntable stylus phono cartridge dynamics: screaming highs on fast whips, heavy bass on slow grinds
        phono_boost = np.clip(0.60 + 0.40 * speed[:, None], 0.35, 2.2)
        scratched *= phono_boost

        # 1.2ms ultra-fast fader cut (Innofader style)
        kernel = max(3, int(sr * 0.0012) | 1)
        smoothed_fader = signal.medfilt(fader_env, kernel_size=kernel) if len(fader_env) > kernel else fader_env
        scratched *= smoothed_fader[:, None]
        return scratched

    # -------------------------------------------------------------------------
    # WIZARD-LEVEL SCRATCH GESTURES
    # -------------------------------------------------------------------------
    def crab_scratch(source, duration_s, cuts_per_beat=16, amp_s=0.28):
        """Blistering 4-finger crab scratch (16 cuts per beat = 64th notes)"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        # Fast forward glide with subtle inertia curve
        traj = 0.04 + amp_s * (t / duration_s)**1.1
        # Crab fader clicks
        cut_period = beat_s / cuts_per_beat
        phase = (t % cut_period) / cut_period
        # 60% open, 40% sharp cut
        fader = np.where(phase < 0.60, 1.0, 0.0).astype(np.float32)
        return render_scratch(source, traj, fader)

    def scribble_scratch(source, duration_s, freq_hz=36.0, amp_s=0.04):
        """High-speed wrist shimmer (36 Hz) producing the screaming zipper scratch"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        traj = 0.08 + amp_s * np.sin(2 * np.pi * freq_hz * t)
        fader = np.ones(n, dtype=np.float32)
        return render_scratch(source, traj, fader)

    def two_click_flare(source, duration_s, amp_s=0.24):
        """2-Click Flare / Orbit (2 fader clicks forward, 2 backward = 8 notes/beat)"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        # Forward stroke 0->0.5, backward 0.5->1.0
        traj = np.where(u < 0.5, (u / 0.5) * amp_s, (1.0 - (u - 0.5) / 0.5) * amp_s).astype(np.float32)
        fader = np.ones(n, dtype=np.float32)
        # Click 1: u in [0.15, 0.22], Click 2: u in [0.35, 0.42]
        # Click 3: u in [0.62, 0.69], Click 4: u in [0.82, 0.89]
        fader[(u >= 0.15) & (u <= 0.22)] = 0.0
        fader[(u >= 0.35) & (u <= 0.42)] = 0.0
        fader[(u >= 0.62) & (u <= 0.69)] = 0.0
        fader[(u >= 0.82) & (u <= 0.89)] = 0.0
        return render_scratch(source, traj, fader)

    def chirp_tear_combo(source, duration_s, amp_s=0.22):
        """High-speed chirp followed by a rapid two-phase tear"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        traj = np.zeros(n, dtype=np.float32)
        fader = np.ones(n, dtype=np.float32)
        # Chirp in first 40%
        c_mask = u < 0.40
        u_c = u[c_mask] / 0.40
        traj[c_mask] = (np.sin(np.pi * u_c) * amp_s)
        fader[c_mask] = np.where(u_c > 0.55, 0.0, 1.0)
        # Tear in remaining 60%
        t_mask = ~c_mask
        u_t = (u[t_mask] - 0.40) / 0.60
        traj[t_mask] = np.where(u_t < 0.35, u_t * (amp_s * 0.5), amp_s * (1.0 - (u_t - 0.35) / 0.65))
        return render_scratch(source, traj, fader)

    def transformer_barrage(source, duration_s, cuts_per_beat=8):
        """Rapid 1/32-note transformer cutting across a sweeping arc"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n, endpoint=False)
        u = t / duration_s
        traj = (0.5 - 0.5 * np.cos(2 * np.pi * u)) * 0.30
        cut_p = beat_s / cuts_per_beat
        phase = (t % cut_p) / cut_p
        fader = np.where(phase < 0.65, 1.0, 0.0).astype(np.float32)
        return render_scratch(source, traj, fader)

    def flex_rewind_audio(source, duration_s):
        """Violent Funkmaster Flex turntable pull-back / rewind"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n)
        traj = 0.55 * np.exp(-5.5 * t / duration_s)
        fader = np.clip(1.0 - (t / duration_s)**2, 0, 1).astype(np.float32)
        return render_scratch(source, traj, fader)

    def flex_bomb_drop(duration_s):
        """Classic Hot 97 sub-bass bomb drop / whistle explosion"""
        n = int(round(sr * duration_s))
        t = np.linspace(0, duration_s, n)
        # Pitch diving sub-sine from 150 Hz -> 35 Hz
        f_sub = 150.0 * np.exp(-3.5 * t / duration_s) + 35.0
        phase = 2 * np.pi * np.cumsum(f_sub) / sr
        sub = np.sin(phase) * (1.0 - t / duration_s)**1.2
        # White noise burst on the hit
        noise = np.random.normal(0, 0.08, n) * np.exp(-t / 0.08)
        bomb = (sub * 0.7 + noise * 0.3)
        return np.stack([bomb, bomb], axis=1).astype(np.float32)

    def stutter_roll(source, div_beats, duration_beats):
        div_s = beat_s * div_beats
        n_div = int(round(sr * div_s))
        repeats = int(round(duration_beats / div_beats))
        win_len = min(len(source), n_div)
        unit = np.zeros((n_div, 2), dtype=np.float32)
        fade_len = min(int(sr * 0.003), win_len // 4)
        c = source[:win_len].copy()
        if fade_len > 0:
            c[-fade_len:] *= np.linspace(1, 0, fade_len)[:, None]
        unit[:win_len] = c
        block = np.tile(unit, (repeats, 1))
        block *= np.linspace(0.8, 1.35, len(block))[:, None]
        return block

    # -------------------------------------------------------------------------
    # Helper: Add Scratch Overlay with Soft Sidechain Ducking
    # -------------------------------------------------------------------------
    def add_scratch_event(start_time_s, audio_block, duck_amount=0.68, boost=1.35):
        start_samp = int(round(start_time_s * sr))
        end_samp = start_samp + len(audio_block)
        if start_samp >= n_total:
            return
        if end_samp > n_total:
            audio_block = audio_block[:n_total - start_samp]
            end_samp = n_total
        
        scratch_track[start_samp:end_samp] += audio_block * boost

        duck_len = end_samp - start_samp
        duck_env = np.ones(duck_len, dtype=np.float32) * duck_amount
        ramp_len = min(int(sr * 0.006), duck_len // 4)
        if ramp_len > 0:
            duck_env[:ramp_len] = np.linspace(1.0, duck_amount, ramp_len)
            duck_env[-ramp_len:] = np.linspace(duck_amount, 1.0, ramp_len)
        ducking_envelope[start_samp:end_samp, 0] = np.minimum(ducking_envelope[start_samp:end_samp, 0], duck_env)

    print("\n[3/6] Programming Funkmaster Flex Rewind Teases & Wizard Scratch Solos...")

    # =========================================================================
    # PART 1: THE FUNKMASTER FLEX INTRO TEASE & BOMB ROUTINE (0:00 - 0:08)
    # =========================================================================
    # Tease 1: Beat drops on beat 1 -> VIOLENT REWIND after 1 beat!
    print("  * [00.0s] FLEX TEASE 1: Beat 1 drops -> AGGRESSIVE RECORD PULL-BACK!")
    rewind_1 = flex_rewind_audio(song_stab, beat_s * 1.0)
    add_scratch_event(beat_s * 0.8, rewind_1, duck_amount=0.2, boost=1.6)

    # Tease 2: Screaming 36 Hz Scribble + 16-cut Crab Scratch on 'AHHH'
    print("  * [01.5s] WIZARD TEASE 2: 36 Hz Scribble & 16-cut Crab on 'AHHH' -> BOMB DROP")
    scribble_tease = scribble_scratch(ah_sample, beat_s * 0.8, freq_hz=36.0)
    crab_tease = crab_scratch(ah_sample, beat_s * 1.2, cuts_per_beat=16)
    add_scratch_event(beat_s * 2.0, scribble_tease, duck_amount=0.5, boost=1.5)
    add_scratch_event(beat_s * 2.8, crab_tease, duck_amount=0.4, boost=1.6)

    # Flex Rewind 2 + Bomb explosion
    rewind_2 = flex_rewind_audio(ah_sample, beat_s * 1.2)
    bomb_1 = flex_bomb_drop(beat_s * 2.5)
    add_scratch_event(beat_s * 4.0, rewind_2, duck_amount=0.15, boost=1.7)
    add_scratch_event(beat_s * 4.8, bomb_1, duck_amount=0.7, boost=1.1)

    # Tease 3 (Bar 2): Blistering 2-Click Flare Orbit + 1/32 Stutter Barrage
    print("  * [03.5s] WIZARD CLIMAX: 2-Click Flare Orbit -> 1/32 Stutter Barrage -> Tape Stop")
    flare_tease = two_click_flare(ah_sample, beat_s * 1.5)
    stutter_tease = stutter_roll(song_stab, 0.125, 1.5)
    add_scratch_event(beat_s * 5.0, flare_tease, duck_amount=0.5, boost=1.5)
    add_scratch_event(beat_s * 6.5, stutter_tease, duck_amount=0.4, boost=1.6)

    # Quick vinyl tape stop right before the full groove drops!
    tape_stop = flex_rewind_audio(song_stab, beat_s * 0.8)
    add_scratch_event(beat_s * 7.2, tape_stop, duck_amount=0.2, boost=1.6)
    # Duck the song completely for half a beat right before the drop
    pre_drop_samp = int(round(beat_s * 7.4 * sr))
    pre_drop_len = int(round(beat_s * 0.6 * sr))
    ducking_envelope[pre_drop_samp:pre_drop_samp + pre_drop_len, 0] = 0.0

    print("  * [04.1s] THE DROP: Track slams in full blast on Beat 1 (Groove rolls unbroken)!")

    # =========================================================================
    # PART 2: WIZARD TURNTABLISM ROUTINES OVER THE CONTINUOUS ROLLING BEAT
    # =========================================================================
    # Solo 1: Bar 4 (Turnaround Crab & Chirp-Tear Combo on 'AHHH')
    print("  * [08.1s] WIZARD SOLO 1: 16-Cut Crab & Chirp-Tear Combo over rolling beat")
    crab_s1 = crab_scratch(ah_sample, beat_s * 1.0, cuts_per_beat=16)
    chirp_tear_s1 = chirp_tear_combo(song_stab, beat_s * 1.0)
    add_scratch_event(bar_s * 3.5, crab_s1, duck_amount=0.65, boost=1.5)
    add_scratch_event(bar_s * 3.75, chirp_tear_s1, duck_amount=0.65, boost=1.4)

    # Solo 2: Bar 8 (The Master Showcase: 36 Hz Scribble -> Flare -> 16th Transformer)
    print("  * [15.2s] WIZARD SOLO 2: 36 Hz Scribble -> 2-Click Flare -> Transformer Barrage")
    scribble_s2 = scribble_scratch(ah_sample, beat_s * 1.0, freq_hz=38.0)
    flare_s2 = two_click_flare(ah_sample, beat_s * 1.0)
    trans_s2 = transformer_barrage(song_stab, beat_s * 1.5, cuts_per_beat=8)
    add_scratch_event(bar_s * 7.0, scribble_s2, duck_amount=0.60, boost=1.5)
    add_scratch_event(bar_s * 7.25, flare_s2, duck_amount=0.60, boost=1.5)
    add_scratch_event(bar_s * 7.50, trans_s2, duck_amount=0.60, boost=1.5)

    # Solo 3: Bar 12 (Blistering 1/32 Stutter Roll & Flare Accent)
    print("  * [23.4s] WIZARD SOLO 3: 1/32 Machine-Gun Stutter & Flare Accent")
    stutter_s3 = stutter_roll(song_stab, 0.125, 1.5)
    flare_s3 = two_click_flare(ah_sample, beat_s * 1.0)
    add_scratch_event(bar_s * 11.25, stutter_s3, duck_amount=0.65, boost=1.4)
    add_scratch_event(bar_s * 11.60, flare_s3, duck_amount=0.65, boost=1.5)

    # Solo 4: Bar 16 (PRE-DROP MAYHEM: Flex Rewind -> 16-Cut Crab -> Bomb Explosion)
    print("  * [31.5s] PRE-DROP MAYHEM: Flex Rewind -> 16-Cut Crab -> Bomb Drop into Major Drop!")
    rewind_pd = flex_rewind_audio(ah_sample, beat_s * 1.0)
    crab_pd = crab_scratch(ah_sample, beat_s * 1.0, cuts_per_beat=16)
    bomb_pd = flex_bomb_drop(beat_s * 2.5)
    add_scratch_event(bar_s * 15.0, rewind_pd, duck_amount=0.3, boost=1.6)
    add_scratch_event(bar_s * 15.25, crab_pd, duck_amount=0.5, boost=1.5)
    add_scratch_event(bar_s * 15.50, bomb_pd, duck_amount=0.7, boost=1.1)

    print("  * [32.5s] MAJOR DROP: Heavy Vocal & Amapiano Log Drums Explosion!")

    # Solo 5: Bar 20 (Vocal Pocket Twiddle & Scribble Solo)
    print("  * [39.7s] WIZARD SOLO 5: Vocal Pocket Screaming Scribble & Crab Barrage")
    scribble_s5 = scribble_scratch(ah_sample, beat_s * 1.0, freq_hz=35.0)
    crab_s5 = crab_scratch(ah_sample, beat_s * 1.5, cuts_per_beat=16)
    add_scratch_event(bar_s * 19.25, scribble_s5, duck_amount=0.65, boost=1.5)
    add_scratch_event(bar_s * 19.50, crab_s5, duck_amount=0.60, boost=1.5)

    # Solo 6: Bar 24 (2-Click Flare & Chirp-Tear Rhythmic Juggling)
    print("  * [47.8s] WIZARD SOLO 6: 2-Click Flare & Chirp-Tear Rhythmic Juggling")
    flare_s6 = two_click_flare(ah_sample, beat_s * 1.5)
    ct_s6 = chirp_tear_combo(song_stab, beat_s * 1.5)
    add_scratch_event(bar_s * 23.0, flare_s6, duck_amount=0.65, boost=1.5)
    add_scratch_event(bar_s * 23.35, ct_s6, duck_amount=0.65, boost=1.4)

    # Solo 7: Bar 28 (Climax: 16-Cut Crab into Screaming Scribble)
    print("  * [55.9s] WIZARD SOLO 7: 16-Cut Crab into Screaming High-Frequency Scribble")
    crab_s7 = crab_scratch(ah_sample, beat_s * 1.5, cuts_per_beat=16)
    scrib_s7 = scribble_scratch(ah_sample, beat_s * 1.5, freq_hz=38.0)
    add_scratch_event(bar_s * 27.0, crab_s7, duck_amount=0.60, boost=1.5)
    add_scratch_event(bar_s * 27.35, scrib_s7, duck_amount=0.60, boost=1.5)

    # OUTRO: Bar 31 (Funkmaster Flex Grand Finale Spin-Back & Needle Drag)
    print("  * [63.0s] OUTRO FINALE: Massive Funkmaster Flex Platter Rewind & Power-Off")
    spin_dur = bar_s * 2.0
    rewind_outro = flex_rewind_audio(ah_sample, spin_dur)
    add_scratch_event(total_duration_s - spin_dur, rewind_outro, duck_amount=0.15, boost=1.7)

    # Fade out song at the very end (last 1.5 seconds)
    fade_end_len = int(sr * 1.5)
    ducking_envelope[-fade_end_len:, 0] *= np.linspace(1.0, 0.0, fade_end_len)

    # =========================================================================
    # MULTITRACK MIXDOWN: Song Deck + Turntablist Scratch Deck
    # =========================================================================
    print("\n[4/6] Summing Multitrack Master (Continuous Song + Wizard Scratches)...")
    multitrack_master = song_track * ducking_envelope + scratch_track

    # Step 4: Write intermediate WAV
    wavfile.write(temp_wav, sr, (np.clip(multitrack_master, -1.0, 1.0) * 32767).astype(np.int16))

    # Step 5: Master with EBU R128 DJ Loudness Normalization (-14 LUFS, -1.5 dBTP)
    print("\n[5/6] Mastering to 320k MP3 with EBU R128 DJ Standards...")
    master_cmd = [
        "ffmpeg", "-y",
        "-i", temp_wav,
        "-af", "loudnorm=I=-14.0:TP=-1.5:LRA=10.0",
        "-b:a", "320k",
        "-metadata", "title=No Bad Vibes (Funkmaster Flex & Wizard Turntablism Master)",
        "-metadata", "artist=Heavy-K, DJ Buckz, Nonny D",
        "-metadata", "album=SmartMix Wizard Turntablism Series",
        "-metadata", "comment=Funkmaster Flex Tease-Rewinds & DMC Wizard Fast-Cut Scratches",
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
    print(" FUNKMASTER FLEX & WIZARD-LEVEL MASTER GENERATED SUCCESSFULLY!")
    print("=" * 78)
    print(f"File     : {output_mp3} ({out_mb:.2f} MB)")
    print(f"Length   : {total_duration_s:.2f} seconds")
    print(f"Loudness :")
    for sl in summary_lines[-3:]:
        print(f"  {sl.strip()}")
    print("=" * 78)

if __name__ == "__main__":
    make_wizard_scratch_preview()
