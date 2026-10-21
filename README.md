# SmartMix & VirtualDJ Cue-Based Mixtape Engine

An automated, studio-grade DJ continuous mix generator and cue-transition engine integrated with **VirtualDJ**. 

Instead of relying on real-time software crossfaders that can suffer from volume dips, buffer underruns, or rigid timer limits, this project reads your VirtualDJ playlist order and Hotcues to render a mathematically flawless, phrase-aligned, equal-power continuous mix into a single high-fidelity audio master.

---

## Key Features

- **Direct VirtualDJ Playlist Sync:** Automatically parses your active Automix queue (`automix.vdjfolder`) in its exact playback sequence.
- **Flexible Cue-Driven Transitions:**
  - **Mix In Drop:** Starts each incoming track cleanly at **Cue 1** (or any cue named `Start`, `In`, `Drop`), bypassing silence.
  - **Fade Out Start:** Initiates the transition window at **Cue 2** (or any cue named `Fade Out`, `Fade`, `Mix Out`).
  - **Cutoff / Exit:** Concludes the blend and stops the outgoing track at **Cue 3** (or any cue named `Cut`, `Exit`, `End`).
  - **Performance Cue Freedom:** Tracks can have 4, 6, or 8+ performance cues (for vocals, drops, or scratching)—the mix engine selectively targets transition points while leaving performance cues untouched.
- **Equal-Power Crossfades ($\cos / \sin$):**
  - Standard linear crossfaders drop volume by $-3\text{ dB}$ in the middle of a blend.
  - SmartMix utilizes **Quarter-Sine Equal-Power Curves** ($\cos^2\theta + \sin^2\theta = 1$) to ensure perceived acoustic loudness remains rock-solid at $100\%$ ($0\text{ dB}$).
- **Intelligent BPM & Tempo Matching (RubberBand Engine):**
  - Automatically compares BPMs between consecutive tracks.
  - If a tempo disparity exists ($> 0.3\text{ BPM}$), it applies pitch-preserving time-stretching (**RubberBand / WSOLA**) across the transition window so beatgrids remain locked in phase.
- **32-Bit Float Mastering:**
  - Overlapping audio streams are mixed in 32-bit floating-point PCM before being encoded into pristine $320\text{ kbps}$ MP3 with complete ID3 album metadata and tracklists.
- **C++ DSP Plugin & VirtualDJ Skin Components:**
  - Includes source code and compiled binaries for the native VirtualDJ C++ DSP engine (`smartmix_engine.cpp` / `SmartMix64.dll`) and skin integration panels.

---

## Transition Architecture & Phrasing

The engine splits consecutive track pairs (**Track A** $\rightarrow$ **Track B**) into solo and transition zones based on your cues:

```text
Track A (Outgoing):
[ Cue 1 ] =============== Solo Play =============== [ Cue 2 ] -------- 16-Bar Fade Out -------- [ Cue 3 ] (Stops)
                                                                \                                /
                                                                 \     TRANSITION WINDOW (T)    /
                                                                  \     ~32.5s (64 beats)      /
Track B (Incoming):                                                \                          /
                                                               [ Cue 1 ] ------ 16-Bar Fade In ------ [ Full Solo Play ] ===>
```

### The 16-Bar Amapiano / House Phrase Window
At standard tempos like **$118\text{ BPM}$**:
- $1\text{ beat} \approx 0.5085\text{ s}$
- $1\text{ bar} = 4\text{ beats} \approx 2.034\text{ s}$
- **$16\text{ bars} = 64\text{ beats} \approx 32.54\text{ s}$**

Setting your Cue 2 and Cue 3 across a 16-bar phrase ensures drops, percussion breaks, and vocal entries layer harmoniously.

---

## Installation & Prerequisites

1. **Python 3.10+** (Python 3.14 recommended)
2. **FFmpeg** with `librubberband` and `libmp3lame` installed and added to your system `PATH`.
3. **VirtualDJ** (2021, 2023, 2024, or 2026+).

---

## Usage Guide

### 1. Basic Generation
Run the script to build a mixtape using the tracks and cues from your active VirtualDJ Automix playlist:

```bash
python generate_mixtape.py
```

### 2. Custom Cue Selection
If your tracks use different cue numbers for transitions (e.g. Cue 1 for intro, Cue 4 for fade start, Cue 5 for cutoff):

```bash
python generate_mixtape.py --entry-cue 1 --fade-cue 4 --exit-cue 5
```

### 3. Multi-Cue Auto Mode (`--use-last-cues`)
If your songs contain numerous performance hotcues and you want the script to automatically designate the **last two cues** as the fade-out window:

```bash
python generate_mixtape.py --use-last-cues
```

### 4. Custom Output Destination
Specify a custom destination for your rendered continuous mix:

```bash
python generate_mixtape.py --output "C:\Users\username\Music\My_DJ_Mix.mp3"
```

---

## CLI Options

| Argument | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--entry-cue` | `int` | `1` | Cue number for track entry / mix-in |
| `--fade-cue` | `int` | `2` | Cue number where fade-out begins |
| `--exit-cue` | `int` | `3` | Cue number where outgoing track cuts off |
| `--use-last-cues` | `flag` | `False` | Automatically uses the final 2 cues for fade-out |
| `--output` | `str` | *Default MP3* | Destination path for the exported master file |

---

## Repository Structure

```text
├── generate_mixtape.py               # Core offline mix generator & cue crossfade engine
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
