# SmartMix: All-In-One VirtualDJ Cue-Based Continuous Mixtape Engine

An automated, studio-grade DJ continuous mix compiler and cue-transition engine integrated with **VirtualDJ**.

Instead of relying on real-time software crossfaders that suffer from volume dips, buffer underruns, or rigid timer limits, SmartMix reads your VirtualDJ playlist order and Hotcues to render mathematically flawless, phrase-aligned continuous mixes into high-fidelity audio masters.

---

## ⚡ The 1-Click Master Pipeline (How to Run Everything at Once)

You can run the **entire mixtape compilation in ONE single step**:

### Method 1: Double-Click (Easiest)
In Windows File Explorer, simply double-click:
```text
run_smartmix.bat
```

### Method 2: Command Line
Open your terminal in the repository folder and run:
```bash
python smartmix.py
```

### What Happens in This Single Run:
1. **Reads VirtualDJ Automix Queue:** Automatically syncs the song order directly from VirtualDJ (`Sideview\automix.vdjfolder`).
2. **Extracts Exact Hotcues:** Pulls Cue 1, Cue 2, and Cue 3 from VirtualDJ's `database.xml`.
3. **Renders Option 1 — Smart Crossfaded Continuous Mix:** Seamless 16-bar phrase blends with Linkwitz-Riley LR-4 Bass-Swaps, Filter-Sweeps, Echo-Outs, and Equal-Power blends (**100% scratch-free**) (`Amapiano_Continuous_Mix_Crossfaded.mp3`).
4. **Renders Option 2 — Normal Cut Continuous Mix:** Clean, on-beat sequential cue drops with zero overlap, micro-faded to prevent digital clicks (`Amapiano_Continuous_Mix_Normal.mp3`).
5. **EBU R128 Studio Mastering:** Normalizes all outputs to `-14.0 LUFS` with a `-1.5 dBTP` true-peak ceiling (zero clipping, punchy log drums).
6. **Prints Tracklist & Timestamps:** Gives you a timestamped cue sheet ready for tracklist descriptions and chapter markers.

---

## 📍 Output Directory & File Locations (Smart Auto-Detection)

### What if you don't have `C:\Users\odhis\Downloads\Amapiano\` in the future?
You do **not** need that folder! SmartMix dynamically determines the best output folder with zero manual configuration:

1. **Auto-Detect from Your Tracks (Default):** SmartMix automatically identifies the folder where your playlist songs are stored (e.g. `D:\Music\Afrobeats\` or `C:\Users\YourUser\Music\...`) and saves your compiled mixes directly alongside your music files!
2. **Custom Folder (`--output-dir`):** You can specify any destination directory:
   ```bash
   python smartmix.py --output-dir "D:\MyMixes"
   ```
3. **Universal Fallback:** If neither applies, SmartMix automatically creates and outputs to `~/Downloads/SmartMix/` or `~/Downloads/Amapiano/`.
4. **Zero Crashing:** The directory is automatically created (`os.makedirs`) if it does not exist.

### Standard Output Files:

| Output File | Description | Style / Transitions |
| :--- | :--- | :--- |
| **`Amapiano_Continuous_Mix_Crossfaded.mp3`** | Full Continuous Mix (Smart Overlaps) | Seamless 16-bar transitions: LR-4 Bass-Swaps, Filter-Sweeps, Echo-Outs |
| **`Amapiano_Continuous_Mix_Normal.mp3`** | Full Continuous Mix (Clean Sequential Cuts) | Radio / live showcase cue-drop cuts (Zero overlap) |

*(Note: If you ever want a standalone DJ scratch performance routine on the lead track, simply pass `--with-scratch-preview` to generate `Heavy-K_No_Bad_Vibes_DJ_Scratch_Preview.mp3`).*

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

## 🎛️ Transition Styles & DSP Modes (Zero Scratches in Continuous Mixes)

SmartMix includes studio-grade transition algorithms designed specifically for rhythmically intense genres like Amapiano, Afro House, and Dancehall. Continuous mixes are **100% free of scratch sound effects**:

### 1. Dynamic Mode (`--crossfade-mode dynamic`) — *Default*
Intelligently alternates musical transition styles across consecutive tracks so every transition feels fresh, seamless, and professional:
- **Transition A $\to$ B:** Linkwitz-Riley Bass-Swap
- **Transition B $\to$ C:** High-Pass Filter Sweep
- **Transition C $\to$ D:** Echo-Out Dub Delay Freeze

### 2. Linkwitz-Riley Bass-Swap (`--crossfade-mode bass-swap`)
Uses a true 4th-order (LR-4) zero-phase frequency crossover at **220 Hz**. Mid and high frequencies blend smoothly over 16 bars, while the sub and log drum frequencies swap cleanly at the midpoint (ratio 0.5). **Result:** Zero log-drum clashing or low-end distortion.

### 3. High-Pass Filter Sweep (`--crossfade-mode filter-sweep`)
Applies a 4-stage resonant high-pass filter ($60\text{ Hz} \to 2000\text{ Hz}$) with quadratic decay on the outgoing track, turning it into an airy wash right before the incoming track's log drum drops.

### 4. Echo-Out Freeze (`--crossfade-mode echo-out`)
A tempo-synced 1-beat (508ms) stereo dub delay freeze with 55% decay on the outgoing track that dissolves underneath the incoming track's intro.

### 5. Equal-Power Blend (`--crossfade-mode equal-power`)
A mathematical quarter-sine equal-power crossfade curve ensuring total sound energy never dips or peaks during transitions.

### Custom Per-Transition Styling
You can specify exact transition styles for specific song changes using `--trans-style`:
```bash
python smartmix.py --trans-style "1=bass-swap,2=filter-sweep,3=echo-out,4=bass-swap"
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
| `--output-dir` | *Auto-detected* | Folder where compiled MP3s will be saved (defaults to track directory or `~/Downloads/Amapiano`) |
| `--crossfade-mode` | `dynamic` | Transition style: `dynamic`, `bass-swap`, `filter-sweep`, `echo-out`, `equal-power` |
| `--trans-style` | `""` | Per-transition map (e.g. `'1=bass-swap,2=filter-sweep,3=echo-out'`) |
| `--trans-bars` | *Cue markers* | Force transition length in bars (e.g. `8`, `16`, `32`) |
| `--bass-swap-ratio`| `0.5` | Point in transition where low frequencies swap (`0.5` = midpoint) |
| `--target-lufs` | `-14.0` | Integrated loudness target in LUFS (Club/DJ standard) |
| `--true-peak` | `-1.5` | Maximum true peak ceiling in dBTP |
| `--with-scratch-preview` | `False` | Optional: also render a standalone DJ scratch routine on track 1 |
| `--entry-cue` | `1` | Cue number for track entry / mix-in |
| `--fade-cue` | `2` | Cue number where fade starts or normal cut occurs |
| `--exit-cue` | `3` | Cue number where outgoing track stops |
| `--normal-cutoff` | `cue2` | Where normal cut transition occurs: `cue2` (radio cut) or `cue3` (full phrase) |
| `--use-last-cues` | `False` | Automatically uses the last 2 cues for tracks with many performance cues |

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q1: What if my songs are not in `C:\Users\odhis\Downloads\Amapiano\`?
- SmartMix automatically detects the folder where your audio files live and outputs the mixes there! If your tracks are in `D:\DJ_Music\` or `C:\Users\YourName\Music\`, your mixes will automatically be placed there. You can also specify any custom folder with `--output-dir "D:\MyMixes"`.

### Q2: Why are there no scratches in the continuous mixes?
- Continuous DJ mixtapes are designed for seamless musical blends. Scratches were removed from the mix transitions to ensure smooth, uninterrupted listening with Linkwitz-Riley bass swaps, filter sweeps, and echo outs. If you want a standalone scratch performance routine, pass `--with-scratch-preview`.

### Q3: What if a song does not have Cue 2 or Cue 3 set?
- Don't worry! If Cue 2 or Cue 3 are missing, SmartMix automatically calculates an intelligent 16-bar fade window based on the song's BPM before the end of the track.

### Q4: What if my songs have different tempos (BPM)?
- SmartMix has a built-in pitch-neutral time-stretching engine (**RubberBand / WSOLA**). If two consecutive tracks differ in tempo by more than 0.3 BPM, it automatically time-stretches the transition window so beats stay locked in phase without altering pitch.

### Q5: How do I render ONLY the crossfaded mix or ONLY the normal mix?
- If you only want one specific mix, use `generate_mixtape.py`:
  ```bash
  python generate_mixtape.py --mode crossfade
  ```
  or
  ```bash
  python generate_mixtape.py --mode normal
  ```

---

## 📁 Repository Structure

```text
├── smartmix.py                       # Master unified 1-click compiler (All-in-One)
├── run_smartmix.bat                  # 1-Click Windows batch launcher
├── generate_mixtape.py               # Core offline mix generator (Crossfade & Normal Cut)
├── generate_scratch_preview.py       # Standalone DJ scratch preview generator
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
