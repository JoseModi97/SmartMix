# SmartMix & VirtualDJ Cue-Based Mixtape Engine

An automated, studio-grade DJ continuous mix generator and cue-transition engine integrated with **VirtualDJ**.

Instead of relying on real-time software crossfaders that can suffer from volume dips, buffer underruns, or rigid timer limits, this project reads your VirtualDJ playlist order and Hotcues to render mathematically flawless, phrase-aligned continuous mixes into high-fidelity audio masters.

---

## Output Options (Dual-Mode Engine)

SmartMix provides **two distinct mixing styles**:

1. **Option 1: Smart Crossfaded Mix (`--mode crossfade`)**
   - Seamless 16-bar overlaps between **Cue 2** and **Cue 3**.
   - Quarter-sine equal-power curves ($\cos / \sin$) ensuring perceived loudness remains rock-solid at $100\%$ ($0\text{ dB}$).
   - VirtualDJ-inspired on-beat crossfading:
     - **Dynamic Mode (`--crossfade-mode dynamic`):** Tastefully alternates styles across the set.
     - **EQ Bass-Swap (`--crossfade-mode bass-swap`):** Midpoint low-end crossover preventing log drum mud.
     - **High-Pass Filter Sweep (`--crossfade-mode filter-sweep`):** Natural exponential decay on outgoing tracks.
   - Generates: `Amapiano_Continuous_Mix_Crossfaded.mp3`

2. **Option 2: Normal Cut Mix (`--mode normal`)**
   - Clean, on-beat sequential transitions with **no crossfade overlap**.
   - Track A plays from Cue 1 to Cue 2 (or Cue 3), cleanly cuts on beat 4, and Track B drops on beat 1 of its Cue 1 with sample-perfect timing.
   - Micro-faded at boundaries (15ms) to eliminate digital clicks/pops.
   - Ideal for radio-style cuts, live performance showcases, or fast-paced sets.
   - Generates: `Amapiano_Continuous_Mix_Normal.mp3`

3. **Both Options Simultaneously (`--mode both`)**
   - Renders both the Normal and Crossfaded mixes in a single command.

---

## Key Features

- **Direct VirtualDJ Playlist Sync:** Automatically parses your active Automix queue (`automix.vdjfolder`) in its exact playback sequence.
- **Flexible Cue-Driven Transitions:**
  - **Mix In Drop:** Starts each incoming track cleanly at **Cue 1** (or any cue named `Start`, `In`, `Drop`), bypassing silence.
  - **Fade Out Start / Normal Cutoff:** Initiates the transition window or cuts at **Cue 2** (or any cue named `Fade Out`, `Fade`, `Mix Out`).
  - **Cutoff / Exit:** Concludes the blend and stops the outgoing track at **Cue 3** (or any cue named `Cut`, `Exit`, `End`).
  - **Performance Cue Freedom:** Tracks can have 4, 6, or 8+ performance cues (for vocals, drops, or scratching)—the mix engine selectively targets transition points while leaving performance cues untouched.
- **Intelligent BPM & Tempo Matching (RubberBand Engine):**
  - Automatically compares BPMs between consecutive tracks.
  - If a tempo disparity exists ($> 0.3\text{ BPM}$), it applies pitch-preserving time-stretching (**RubberBand / WSOLA**) across the transition window so beatgrids remain locked in phase.
- **32-Bit Float Mastering:**
  - Audio streams are processed in 32-bit floating-point PCM before being encoded into pristine $320\text{ kbps}$ MP3 with complete ID3 album metadata and tracklists.
- **C++ DSP Plugin & VirtualDJ Skin Components:**
  - Includes source code and compiled binaries for the native VirtualDJ C++ DSP engine (`smartmix_engine.cpp` / `SmartMix64.dll`) and skin integration panels.

---

## Installation & Prerequisites

1. **Python 3.10+** (Python 3.14 recommended)
2. **FFmpeg** with `librubberband` and `libmp3lame` installed and added to your system `PATH`.
3. **VirtualDJ** (2021, 2023, 2024, or 2026+).

---

## Usage Guide

### 1. Render Both Options (Default)
Generates both the Normal Cut MP3 and the Smart Crossfaded MP3:

```bash
python generate_mixtape.py --mode both
```

### 2. Render Only the Smart Crossfaded Mix
```bash
python generate_mixtape.py --mode crossfade --crossfade-mode dynamic
```

### 3. Render Only the Normal Cut Mix
```bash
python generate_mixtape.py --mode normal
```

### 4. Custom Cue Selection
If your tracks use different cue numbers for transitions (e.g. Cue 1 for intro, Cue 4 for fade start, Cue 5 for cutoff):

```bash
python generate_mixtape.py --entry-cue 1 --fade-cue 4 --exit-cue 5
```

### 5. Multi-Cue Auto Mode (`--use-last-cues`)
If your songs contain numerous performance hotcues and you want the script to automatically designate the **last two cues** as the fade-out window:

```bash
python generate_mixtape.py --use-last-cues
```

---

## CLI Options

| Argument | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--mode` | `str` | `both` | `both`, `crossfade`, `normal` |
| `--crossfade-mode` | `str` | `dynamic` | `dynamic`, `bass-swap`, `filter-sweep`, `equal-power` |
| `--normal-cutoff` | `str` | `cue2` | `cue2` (radio cut) or `cue3` (full phrase cut) |
| `--entry-cue` | `int` | `1` | Cue number for track entry / mix-in |
| `--fade-cue` | `int` | `2` | Cue number where fade-out begins / normal cut |
| `--exit-cue` | `int` | `3` | Cue number where outgoing track cuts off |
| `--use-last-cues` | `flag` | `False` | Automatically uses the final 2 cues for fade-out |
| `--output-dir` | `str` | *Default Dir* | Destination directory for exported MP3s |

---

## Repository Structure

```text
├── generate_mixtape.py               # Core offline mix generator (Dual-Mode: Normal & Crossfade)
├── smartmix_engine.cpp               # Native VirtualDJ C++ DSP Plugin source code
├── SmartMix64.dll                    # Compiled 64-bit VirtualDJ DSP Plugin binary
├── vdjPlugin8.h / vdjDsp8.h          # VirtualDJ Plugin API header definitions
├── apply_smartmix_cue_engine.py      # VirtualDJ database & skin injector script
├── insert_smartmix_xml.py            # XML skin panel injector
├── make_smartmix_default.py          # Script to set SmartMix skin layout
├── build_dll.bat                     # MSVC build script for SmartMix64.dll
├── default_skin_extracted/           # Unpacked VirtualDJ skin definitions & layouts
├── backup/                           # Configuration and database recovery backups
└── README.md                         # Comprehensive documentation
```

---

## License

This project is licensed under the MIT License.
