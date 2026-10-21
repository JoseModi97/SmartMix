# SmartMix: All-In-One VirtualDJ Cue-Based Continuous Mixtape & Scratch Engine

An automated, studio-grade DJ continuous mix compiler and cue-transition engine integrated with **VirtualDJ**.

Instead of relying on real-time software crossfaders that suffer from volume dips, buffer underruns, or rigid timer limits, SmartMix reads your VirtualDJ playlist order and Hotcues to render mathematically flawless, phrase-aligned continuous mixes into high-fidelity audio masters.

---

## ⚡ The 1-Click Master Pipeline (How to Run Everything at Once)

You can run the **entire mixtape and scratch compilation in ONE single step**:

### Method 1: Double-Click (Easiest)
Simply double-click the Windows batch launcher:
```text
run_smartmix.bat
```

### Method 2: Command Line
Open your terminal inside the repository folder and run:
```bash
python smartmix.py
```

### What Happens in This Single Run:
1. **Reads VirtualDJ Automix Queue:** Automatically syncs the song order directly from VirtualDJ (`Sideview\automix.vdjfolder`).
2. **Extracts Exact Hotcues:** Pulls Cue 1, Cue 2, and Cue 3 from VirtualDJ's `database.xml`.
3. **Renders Option 1 — Smart Crossfaded Continuous Mix:** Seamless 16-bar phrase blends with Linkwitz-Riley LR-4 Bass-Swaps, Filter-Sweeps, Echo-Outs, and Scratch-Ins (`Amapiano_Continuous_Mix_Crossfaded.mp3`).
4. **Renders Option 2 — Normal Cut Continuous Mix:** Clean, on-beat sequential cue drops with zero overlap, micro-faded to prevent digital clicks (`Amapiano_Continuous_Mix_Normal.mp3`).
5. **Renders Option 3 — DJ Scratch Performance Preview:** Acid / Kenyan street tape style live scratch showcase on the lead track (`Heavy-K_No_Bad_Vibes_DJ_Scratch_Preview.mp3`).
6. **EBU R128 Studio Mastering:** Normalizes all outputs to `-14.0 LUFS` with a `-1.5 dBTP` true-peak ceiling (zero clipping, punchy log drums).
7. **Prints Tracklist & Timestamps:** Gives you a timestamped cue sheet ready for tracklist descriptions and chapter markers.

---

## 📍 Output Files & Locations

All compiled audio files are saved directly to your destination folder (default: `C:\Users\odhis\Downloads\Amapiano\`):

| Output File | Description | Duration / Style |
| :--- | :--- | :--- |
| **`Amapiano_Continuous_Mix_Crossfaded.mp3`** | Full Continuous Mix (Smart Overlaps) | Seamless 16-bar transitions, zero log-drum collision |
| **`Amapiano_Continuous_Mix_Normal.mp3`** | Full Continuous Mix (Clean Sequential Cuts) | Radio / live showcase cue-drop cuts |
| **`Heavy-K_No_Bad_Vibes_DJ_Scratch_Preview.mp3`** | DJ Scratch Performance Preview | Acid / Street-tape scratch performance routine |

---

## 🎧 Step-by-Step Guide: How to Add Songs & Never Get Stuck

Follow these simple steps whenever you want to compile a new mixtape:

### Step 1: Arrange Songs in VirtualDJ Automix
1. Open **VirtualDJ**.
2. In the right-hand browser panel, go to **Sideview** $\to$ **Automix**.
3. Drag and drop the songs you want in your mix into the Automix list.
4. Drag tracks up or down to arrange them in your desired playback order.

### Step 2: Set Your Cue Points on Each Track
Load each song onto a deck and set up to 3 transition hotcues (you can also have other performance cues):
- **Cue 1 (`In` / `Drop` / `Start`):** Where the track starts playing (skips long silent intros).
- **Cue 2 (`Fade Out` / `Fade` / `Mix Out`):** 
  - In *Crossfade Mode*: The exact beat where the next track begins fading in.
  - In *Normal Mode*: The beat where this track cuts off.
- **Cue 3 (`Cut` / `Exit` / `End`):**
  - In *Crossfade Mode*: The beat where this outgoing track finishes fading and stops completely.
- *(Note: If you have additional hotcues like Cue 4, 5, 6 for live performance or vocals, SmartMix safely ignores them and only targets your transition cues).*

### Step 3: Run the All-In-One Script
Double-click `run_smartmix.bat` or run:
```bash
python smartmix.py
```
Wait a few moments for audio rendering and mastering to finish. That's it!

---

## 🎛️ Transition Styles & DSP Modes

SmartMix includes professional DJ transition algorithms designed specifically for rhythmically intense genres like Amapiano, Afro House, and Dancehall:

### 1. Dynamic Mode (`--crossfade-mode dynamic`) — *Default*
Intelligently alternates transition styles across consecutive tracks so every transition feels unique and professional.

### 2. Linkwitz-Riley Bass-Swap (`--crossfade-mode bass-swap`)
Uses a true 4th-order (LR-4) zero-phase frequency crossover at **220 Hz**. Mid and high frequencies blend smoothly over 16 bars, while the sub and log drum frequencies swap cleanly at the midpoint (ratio 0.5). **Result:** Zero log-drum clashing or low-end distortion.

### 3. High-Pass Filter Sweep (`--crossfade-mode filter-sweep`)
Applies a 4-stage resonant high-pass filter ($60\text{ Hz} \to 2000\text{ Hz}$) with quadratic decay on the outgoing track, turning it into an airy wash right before the incoming track's log drum drops.

### 4. Echo-Out Freeze (`--crossfade-mode echo-out`)
A tempo-synced 1-beat (508ms) stereo dub delay freeze with 55% decay on the outgoing track that dissolves underneath the incoming track's intro.

### 5. Scratch-In Drop (`--crossfade-mode scratch-in`)
An energetic 2-beat on-beat scratch routine cutting the incoming track's drop into the mix.

### Custom Per-Transition Styling
You can specify exact transition styles for specific song changes using `--trans-style`:
```bash
python smartmix.py --trans-style "1=bass-swap,2=filter-sweep,3=scratch-in,4=echo-out"
```

---

## 🔊 Audio Standards & Mastering Engine

Commercial tracks are mastered hot (often peaking near 0 dBFS). Simply blending two tracks during a crossfade would cause up to $+4.9\text{ dBFS}$ clipping and muddy distortion.

SmartMix applies broadcast-grade mastering:
- **ITU-R BS.1770-4 / EBU R128 Loudness Normalization:**
  - Integrated Loudness Target: `-14.0 LUFS` (The universal DJ/club reference level matching VirtualDJ AutoGain 89 dB SPL, Rekordbox, Apple Music, YouTube, and Spotify).
  - True Peak Ceiling: `-1.5 dBTP` (Prevents inter-sample peak distortion during MP3 encoding).
  - Dynamic Range Target: `10.0 LU` (Preserves transient punch of kicks and log drums).
- **32-Bit Float Processing:**
  - All mixing, filtering, and time-stretching are executed in 32-bit floating-point PCM before encoding to high-fidelity $320\text{ kbps}$ MP3.

---

## ⚙️ Command-Line Options Reference

| Argument | Default | Description |
| :--- | :---: | :--- |
| `--output-dir` | `C:\Users\odhis\Downloads\Amapiano\` | Folder where compiled MP3s will be saved |
| `--crossfade-mode` | `dynamic` | Transition style: `dynamic`, `bass-swap`, `filter-sweep`, `echo-out`, `scratch-in`, `equal-power` |
| `--trans-style` | `""` | Per-transition map (e.g. `'1=bass-swap,2=filter-sweep,3=scratch-in'`) |
| `--trans-bars` | *Cue markers* | Force transition length in bars (e.g. `8`, `16`, `32`) |
| `--bass-swap-ratio`| `0.5` | Point in transition where low frequencies swap (`0.5` = midpoint) |
| `--target-lufs` | `-14.0` | Integrated loudness target in LUFS |
| `--true-peak` | `-1.5` | Maximum true peak ceiling in dBTP |
| `--skip-scratch` | `False` | Skip rendering the standalone scratch preview |
| `--entry-cue` | `1` | Cue number for track entry / mix-in |
| `--fade-cue` | `2` | Cue number where fade starts or normal cut occurs |
| `--exit-cue` | `3` | Cue number where outgoing track stops |
| `--normal-cutoff` | `cue2` | Where normal cut transition occurs: `cue2` (radio cut) or `cue3` (full phrase) |
| `--use-last-cues` | `False` | Automatically uses the last 2 cues for tracks with many performance cues |

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q1: I added new songs to the Automix list, but SmartMix didn't pick them up?
- VirtualDJ writes playlist changes to disk when you switch focus or exit. In VirtualDJ, make sure your playlist is in the **Sideview $\to$ Automix** panel.

### Q2: What if a song does not have Cue 2 or Cue 3 set?
- Don't worry! If Cue 2 or Cue 3 are missing, SmartMix automatically calculates an intelligent 16-bar fade window based on the song's BPM before the end of the track.

### Q3: What if my songs have different tempos (BPM)?
- SmartMix has a built-in pitch-neutral time-stretching engine (**RubberBand / WSOLA**). If two consecutive tracks differ in tempo by more than 0.3 BPM, it automatically time-stretches the transition window so beats stay locked in phase without altering pitch.

### Q4: How do I render ONLY the crossfaded mix or ONLY the normal mix?
- If you only want one specific mix, use `generate_mixtape.py`:
  ```bash
  python generate_mixtape.py --mode crossfade
  ```
  or
  ```bash
  python generate_mixtape.py --mode normal
  ```

### Q5: How do I change the output folder?
- Pass the `--output-dir` argument:
  ```bash
  python smartmix.py --output-dir "D:\MyMixes"
  ```

---

## 📁 Repository Structure

```text
├── smartmix.py                       # Master unified 1-click compiler (All-in-One)
├── run_smartmix.bat                  # 1-Click Windows batch launcher
├── generate_mixtape.py               # Core offline mix generator (Crossfade & Normal Cut)
├── generate_scratch_preview.py       # Kenyan / Acid style DJ scratch preview generator
├── smartmix_engine.cpp               # Native VirtualDJ C++ DSP Plugin source code
├── SmartMix64.dll                    # Compiled 64-bit VirtualDJ DSP Plugin binary
├── vdjPlugin8.h / vdjDsp8.h          # VirtualDJ Plugin API header definitions
├── apply_smartmix_cue_engine.py      # VirtualDJ database & skin injector script
├── insert_smartmix_xml.py            # XML skin panel injector
├── make_smartmix_default.py          # Script to set SmartMix skin layout
├── build_dll.bat                     # MSVC build script for SmartMix64.dll
├── default_skin_extracted/           # Unpacked VirtualDJ skin definitions & layouts
├── backup/                           # Configuration and database recovery backups
└── README.md                         # Complete user guide and documentation
```

---

## 📄 License

This project is open-source and licensed under the MIT License.
