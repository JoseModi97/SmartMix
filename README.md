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
1. **Custom Export Name:** Easily set the title or genre for your mix (e.g. `Afrobeats`, `Amapiano`, `Deep House 2026`). Output files are automatically named accordingly.
2. **Custom Destination Directory:** Click **"📂 Browse..."** to select any folder or drive on your PC. It displays a live preview of the target file path.
3. **Live VirtualDJ Automix Queue Table:** Displays all queued tracks, BPMs, Cue 1 (In), Cue 2 (Fade Out), Cue 3 (Cut Out), and durations.
4. **Instant Playlist Reload ("🔄 Reload from VirtualDJ"):** Click to immediately reload track information if you modify the playlist in VirtualDJ.
5. **Transition & Loudness Controls:** Select transition style (`Gradual Cue 2 -> Cue 3 Crossfade` or `Equal-Power`), loudness target (`-14.0 LUFS`), and true-peak limiter.
6. **Live Compilation Terminal:** Streams real-time progress, time-stretching, DSP transitions, and EBU R128 mastering logs.
7. **1-Click Completion Actions:** Instantly click **"📂 Open Export Folder"** or **"▶ Play Mix in Audio Player"** when done.

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

## 🎛️ Universal DJ Filter (Anti-Beat Clash Transition Engine)

When transitioning between two songs, overlapping kick drums and 808 sub-bass can create **beat collision**, muddy low-end buildup, phase cancellation, or distracting "double-kick galloping". 

SmartMix implements the **VirtualDJ hardware Color FX FILTER knob** (the circled filter knobs on Deck A and Deck B) universally across all mixes and playlists:

### How the DJ Filter Sweep Works:
1. **Continuous Resonant High-Pass Filter (HPF):**
   - At Cue 2, as incoming Track B drops in, Track A's filter cutoff smoothly sweeps upward from **25 Hz to 3,000 Hz** using zero-phase STFT frequency-domain processing.
   - An authentic analog resonance peak ($Q \approx 1.12$, $+1.2\text{ dB}$ at the cutoff frequency) provides the signature club mixer filter sweep texture found on Pioneer DJM and Allen & Heath hardware.
2. **Eliminates Kick Drum & Bass Clashing:**
   - Within the first 30–40% of the transition window, Track A's sub-bass and kick drums (<100 Hz) are attenuated by over **$-30\text{ to } -45\text{ dB}$**.
   - Track B's kick drum drops into an uncluttered, pristine low-end acoustic space with 100% impact!
3. **Preserves Airy Vocals & Melodic Highs:**
   - Track A's vocals, snares, and high-hats remain audible in the upper spectrum, morphing into an airy shimmer that floats musically above Track B before dissolving cleanly at Cue 3.
4. **Universal Across Any Playlist & Genre:**
   - Works universally on any playlist loaded in VirtualDJ (Amapiano, Hip-Hop, R&B, House, Pop, Afrobeats).
   - Available in both the **SmartMix Studio GUI** and the CLI (`--crossfade-mode filter` and `--use-filter`, enabled by default).

---

## 🎛️ Gradual Transition Engine (According to Cue 2 & Cue 3)

SmartMix transitions are built strictly around your VirtualDJ Hotcues:
- **Cue 1 (`In` / `Entry`):** Where the track starts playing.
- **Cue 2 (`Fade Out` / `Mix Out`):** The exact beat where the crossfade starts. Track A is at 100% volume; Track B starts fading in at 0% volume.
- **Cue 3 (`Cut` / `Exit`):** The exact beat where the crossfade completes. Track A reaches 0% volume and stops completely; Track B reaches 100% volume.

### How the Gradual Transition Works:
1. **Mathematical Equal-Power Crossfade:** Outgoing Track A follows $\cos(t \cdot \pi / 2)$ down to 0%, while incoming Track B follows $\sin(t \cdot \pi / 2)$ up to 100%. Total acoustic power remains steady throughout the transition with zero volume dips or sudden spikes.
2. **Linkwitz-Riley LR-4 Bass Crossover (Zero Low-End Mud):** Low frequencies (<220 Hz) smoothly hand over across the midpoint. Vocals, synths, and high hats blend gradually across the entire duration between Cue 2 and Cue 3, while kicks and sub-bass swap cleanly without clashing or phasing.
3. **Zero Scratches & Zero Echo Freezes:** No scratch sound effects, no delay loops, and no abrupt cuts. Pure, seamless DJ blending.

### Transition Modes Available:
- **`filter` (Default):** VirtualDJ Color FX Filter sweep (Anti-Beat Clash) that eliminates kick collisions and sweeps Track A into an airy vocal shimmer.
- **`gradual`:** Studio-grade gradual crossfade between Cue 2 and Cue 3 with LR-4 zero-phase low-end crossover and dynamic anti-clash low filter.
- **`normal`:** Clean on-beat cut at Cue 3 with zero crossfade volume ducking.
- **`equal-power`:** Mathematical equal-power crossfade across all frequencies.

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
