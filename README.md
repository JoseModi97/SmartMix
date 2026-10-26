# SmartMix: All-In-One VirtualDJ Cue-Based Continuous Mixtape Engine

An automated, studio-grade DJ continuous mix compiler and cue-transition engine integrated with **VirtualDJ**.

Instead of relying on real-time software crossfaders that suffer from volume dips, buffer underruns, or rigid timer limits, SmartMix reads your VirtualDJ playlist order and Hotcues to render mathematically flawless, phrase-aligned continuous mixes into high-fidelity audio masters.

---

## 🖥️ SmartMix Studio (Desktop Graphical User Interface)

You can run SmartMix using a sleek, modern dark-themed desktop interface:

### How to Launch:
* **Option 1 (Double-Click):** Double-click `SmartMix_Studio.bat` in Windows File Explorer.
* **Option 2 (Terminal):**
  ```bash
  python smartmix_gui.py
  ```

### Key Features of the User Interface:
1. **Custom Export Name:** Easily set the title or genre for your mix (e.g. `Afrobeats`, `Amapiano`, `Y2K`, `Deep House`). Output files are automatically named accordingly.
2. **Custom Destination Directory:** Click **"📂 Browse..."** to select any folder or drive on your PC. It displays a live preview of the target file path.
3. **Live VirtualDJ Automix Queue Table:** Displays all queued tracks, BPMs, Cue 1 (In), Cue 2 (Fade Out), Cue 3 (Cut Out), and durations.
4. **VirtualDJ Cue Optimizer ("⚡ Optimize Cues (VDJ)"):** Automatically aligns playlist Hotcues to 8-bar musical phrase boundaries and song beat drops, creating a safety backup of `database.xml`.
5. **Instant Playlist Reload ("🔄 Reload VirtualDJ"):** Click to immediately reload track information if you modify the playlist in VirtualDJ.
6. **Interactive Transition Director:** Audition and select custom transitions per song pair (VirtualDJ Flanger, Reverb Wash, End-Filter sweeps, Echo-Out, Vinyl Brake, Immediate Cut).
7. **Natural Phrase Alignment Checkbox:** Automatically snaps transitions to 8-bar / 4-bar downbeat drops and repairs defective cues during mix compilation.
8. **Mastering Controls:** Select target loudness (`-14.0 LUFS` DJ/Club standard) and true-peak ceiling (`-1.5 dBTP`).
9. **Live Compilation Terminal:** Streams real-time progress, time-stretching, DSP transitions, and EBU R128 mastering logs.
10. **1-Click Completion Actions:** Instantly click **"📂 Open Export Folder"** or **"▶ Play Mix in Audio Player"** when done.

---

## 🎵 Natural Phrasing & VirtualDJ Cue Adjustment

### Why Transitions Sometimes Sound Unnatural in VirtualDJ
In DJ mixing, transitions sound jarring or awkward when:
1. **0-Second Chops:** Cue 2 and Cue 3 are placed at the exact same timestamp (e.g. `144.78s -> 144.78s`), causing an instantaneous cut instead of a transition.
2. **Micro-Fades:** Cue 2 is placed only 1–2 seconds before Cue 3 (less than 1 musical bar), sounding clipped.
3. **Silent / Spoken Intros (Beat Clashes):** Cue 1 is placed at `00:00` while the song has 10–18 seconds of speech, hypeman banter, or silence before the drums drop. Track A fades out, leaving no beat before the drums suddenly kick in mid-song.
4. **Phrase Misalignment:** Transitions do not start and end on 4-bar (16-beat) or 8-bar (32-beat) musical boundaries.

### How SmartMix Solves This:
1. **Automatic In-Memory Phrase Quantization (`--natural-cues`, Default On):**
   SmartMix automatically inspects the automix beatgrid (`cutStart`, `cutEnd`, `Phase`) for every song. If broken cues or spoken intros are detected, SmartMix automatically snaps the entry point to the actual beat drop and spaces Cue 2 to Cue 3 by a natural 8-bar (32-beat) window.
2. **Direct VirtualDJ Database Optimization (`--optimize-vdj-cues`):**
   You can permanently write phrase-aligned cues back to VirtualDJ's `database.xml`:
   ```bash
   python smartmix.py --optimize-vdj-cues
   ```
   *(Or click **"⚡ Optimize Cues (VDJ)"** in SmartMix Studio).*
   A timestamped safety backup is automatically created (e.g. `database.xml.bak_20261026_091625`).

---

## ⚡ The 1-Click Master Pipeline (Command-Line / Batch)

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
2. **Extracts Exact Hotcues:** Pulls Cue 1 (entry), Cue 2 (fade start), and Cue 3 (fade end / cut) from VirtualDJ's `database.xml`.
3. **Renders Master Smart Crossfaded Continuous Mix:** Mathematical, gradual crossfade according to Cue 2 and Cue 3 with zero-phase Linkwitz-Riley LR-4 Bass crossover (**100% scratch-free, zero abrupt cuts, zero echo freezes**) (`Amapiano_Continuous_Mix_Crossfaded.mp3`).
4. **EBU R128 Studio Mastering:** Normalizes the master continuous mix to `-14.0 LUFS` with a `-1.5 dBTP` true-peak ceiling (zero clipping, punchy log drums).
5. **Prints Tracklist & Timestamps:** Gives you a timestamped cue sheet ready for YouTube/Mixcloud descriptions and chapter markers.

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

### Standard Output File:

| Output File | Description | Style / Transitions |
| :--- | :--- | :--- |
| **`<MixName>_Continuous_Mix_Crossfaded.mp3`** | Master Continuous Mix | Gradual Cue 2 $\to$ Cue 3 Crossfade (LR-4 Bass Crossover, Zero Scratches) |

*(Note: If you ever want a standalone DJ scratch performance routine on the lead track, simply pass `--with-scratch-preview` to generate `<MixName>_DJ_Scratch_Preview.mp3`).*

---

## 💻 Environment Setup & Requirements (Install Guide)

Before running SmartMix for the first time, your computer needs the following 3 tools:

### 1. Python 3.10+
- Download and install Python from [python.org](https://www.python.org/downloads/) (or via Windows Package Manager: `winget install Python.Python.3.12`).
- **Important:** Make sure to check **"Add Python to PATH"** during installation.

### 2. FFmpeg (Audio DSP & Mastering Engine)
FFmpeg is used for 32-bit floating-point audio decoding, pitch-preserving tempo stretching, and EBU R128 mastering.
- **Easiest install (PowerShell):**
  ```powershell
  winget install Gyan.FFmpeg
  ```
  *(Close and reopen your terminal after installation so `ffmpeg` is loaded into your PATH).*
- Alternatively, download the full build from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) and add its `bin` folder to your Windows system Environment Variables.

### 3. Python Audio Libraries (NumPy & SciPy)
SmartMix relies on `numpy` (audio arrays) and `scipy` (Linkwitz-Riley crossover filters). Install them in one command:
```bash
pip install -r requirements.txt
```

### 4. VirtualDJ
- Install **VirtualDJ** (2021, 2023, 2024, or 2026+). SmartMix automatically reads playlists and hotcues from `%LOCALAPPDATA%\VirtualDJ`.

### 5. Verify Your Setup in 1 Second!
Run the built-in diagnostic doctor to verify that everything is configured properly:
```bash
python check_setup.py
```
If all items show `[OK]`, your computer is 100% ready to compile mixtapes!

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

## 🎛️ Continuous DJ Mix Engine (VirtualDJ FX & End-Filter Transitions)

SmartMix replaces traditional volume-ducking crossfaders with a studio-grade **Continuous DJ Mix Engine**:
- Both tracks maintain **full continuous presence and groove** across the transition phrase with zero volume dips or weak energy.
- Over long transitions (e.g. 8 bars / 32 beats, $12\text{–}20\text{s}$), SmartMix utilizes the signature **VirtualDJ Deck FX** (highlighted in VirtualDJ's effects menu):
  - **🎛️ VirtualDJ Flanger:** Modulated comb-filter jet sweep that builds intense energy and movement across the transition phrase.
  - **🌌 VirtualDJ Space Reverb Wash:** Expands the outgoing track into a wide, lush spatial ambient cloud before Cue 3.
  - **🔁 VirtualDJ Echo-Out:** Tempo-synced dub delay freeze catching the final phrase and decaying gracefully into Track B.
  - **🛑 VirtualDJ Vinyl Brake:** Turntable motor stop deceleration on sudden cuts and drops.

### 🎛️ How the End-Filter Sweep Works:
1. **Filter Appears Towards the End:**
   - Instead of draining the song prematurely, the resonant High-Pass Filter engages **towards the end** of the transition phrase (at the $\approx 58\%$ mark).
   - In the first half ($0\text{–}58\%$), both tracks groove together with full fidelity, bass, and presence.
   - Across the final $42\%$ leading into Cue 3, the resonant HPF sweeps up from **25 Hz to 3,200 Hz**, completely eradicating Track A's kick drum and bass before Cue 3.
2. **Zero Kick & Bass Clashing:**
   - By the time Track B reaches full dominance, Track A's kick drum is attenuated by over **$-45\text{ dB}$**, eliminating any double-kick galloping or phase cancellation.
3. **Preserves Airy Vocal Tail:**
   - Track A's vocals, snares, and flanged/reverbed highs float smoothly above Track B before dissolving into total silence as Cue 3 hits.
4. **Universal Across Any Playlist & Genre:**
   - Works universally on any playlist loaded in VirtualDJ.
   - Automatically analyzes transition phrase lengths (immediate cuts, short drops, or long 8-bar flanger/reverb builds).
   - Master output is a single unified Continuous Mix: `<MixName>_Continuous_Mix.mp3`.

---

## 🎛️ DJ Transitions According to Cue 2 & Cue 3

SmartMix transitions are built strictly around your VirtualDJ Hotcues:
- **Cue 1 (`In` / `Entry`):** Where the track starts playing.
- **Cue 2 (`Fade Out` / `Mix Out`):** The exact beat where the transition window starts. Both tracks groove continuously.
- **Cue 3 (`Cut` / `Exit`):** The exact beat where the transition completes. Track A reaches 0% volume and stops completely; Track B takes over solo.

### Transition Modes Available:
- **`auto` (Default):** Smart playlist analysis: automatically applies **Flanger + End-Filter** or **Reverb Wash + End-Filter** on long transitions (>12s), and clean End-Filter sweeps on short transitions.
- **`flanger`:** VirtualDJ Flanger jet comb-filter build + End-Filter sweep.
- **`reverb`:** VirtualDJ Space Reverb ambient wash + End-Filter sweep.
- **`filter`:** VirtualDJ Color FX Filter sweep towards the end.
- **`echo-out`:** Tempo-synced dub delay freeze.
- **`brake`:** Turntable vinyl brake stop.
- **`immediate`:** Clean on-beat cut at Cue 3 (for tracks marked Cue 2 == Cue 3).

---

## 🚀 Universal Song & Speed Support (Any Songs, Any Speeds, Any Genre)

SmartMix is **not restricted to a fixed playlist, tempo, or genre**:

### 1. Any Songs & Audio Formats
Whatever audio files you drag into VirtualDJ Automix (MP3, WAV, FLAC, M4A, AAC) from any folder or drive are loaded dynamically. SmartMix reads each track's individual length, BPM, and cue points from VirtualDJ's database.

### 2. How Different Speeds (BPMs) Are Handled:
- **Same / Similar Tempo ($\Delta\text{BPM} \le 0.5$ BPM):** Seamless phrase blending across Cue 2 to Cue 3.
- **Tempo Differences ($0.5 < \Delta\text{BPM} \le 12.0$ BPM):** SmartMix automatically applies pitch-preserving time-stretching (`atempo`) across the Cue 2 $\to$ Cue 3 transition window so incoming Track B locks 1:1 in phase with Track A! Once Cue 3 is reached and Track A finishes, Track B continues playing solo at its native BPM.

### 3. Custom Mix Name & Genre (`--mix-name`)
You can compile mixes for any genre:
```bash
python smartmix.py --mix-name "Afrobeats"
python smartmix.py --mix-name "House"
python smartmix.py --mix-name "Dancehall"
```
This automatically tags ID3 metadata and names output files accordingly (e.g. `Afrobeats_Continuous_Mix_Crossfaded.mp3`). If omitted, it defaults to `Amapiano`.

### 4. Summary Capability Matrix

| Feature | Behavior with Other Songs & Speeds |
| :--- | :--- |
| **Track List** | Completely dynamic (whatever songs are in VirtualDJ Automix) |
| **Song Lengths** | Completely dynamic (uses each track's individual duration & cues) |
| **BPM / Speed** | Auto-detected per song; tempo-matched during crossfades |
| **Crossfade Transitions** | Gradual Cue 2 $\to$ Cue 3 transition with pitch-preserving beat-lock |
| **Output Location** | Auto-detects where your songs live and saves mixes alongside them |
| **Loudness Standards** | Integrated EBU R128 mastering (`-14.0 LUFS`, `-1.5 dBTP`) on any style of music |

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
| `--mix-name` | `Amapiano` | Name or genre of the mix (used for output filenames and ID3 tags, e.g. `'Afrobeats'`, `'House'`) |
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

### Q1: Is this script tailored only for a specific set of songs, or will it work with other songs and different speeds?
- **It works for ANY songs and ANY speeds!** SmartMix is not hardcoded to any artist, genre, or speed:
  - **Different Speeds in Normal Cut Mode (`--mode normal`):** 100% speed-agnostic. You can mix 80 BPM into 130 BPM with zero clash because each song plays at its natural tempo and drops on beat 1 without overlap.
  - **Different Speeds in Crossfade Mode (`--mode crossfade`):** Within DJ mixable pitch range ($\le 12$ BPM difference), SmartMix automatically time-stretches incoming tracks during the 16-bar blend window using pitch-neutral `atempo` so kicks lock 1:1 in phase. If there is a massive tempo jump ($> 12$ BPM), it automatically routes to an **Echo-Out Drop** transition.
  - **Different Genres:** Pass `--mix-name "Afrobeats"`, `--mix-name "House"`, etc., to customize tags and filenames.

### Q2: What if my songs are not in `C:\Users\odhis\Downloads\Amapiano\`?
- SmartMix automatically detects the folder where your audio files live and outputs the mixes there! If your tracks are in `D:\DJ_Music\` or `C:\Users\YourName\Music\`, your mixes will automatically be placed there. You can also specify any custom folder with `--output-dir "D:\MyMixes"`.

### Q3: Why are there no scratches in the continuous mixes?
- Continuous DJ mixtapes are designed for seamless musical blends. Scratches were removed from the mix transitions to ensure smooth, uninterrupted listening with Linkwitz-Riley bass swaps, filter sweeps, and echo outs. If you want a standalone scratch performance routine, pass `--with-scratch-preview`.

### Q4: What if a song does not have Cue 2 or Cue 3 set?
- Don't worry! If Cue 2 or Cue 3 are missing, SmartMix automatically calculates an intelligent 16-bar fade window based on the song's BPM before the end of the track.

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
├── check_setup.py                    # Environment & dependency verification doctor
├── requirements.txt                  # Python dependencies (numpy, scipy)
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
