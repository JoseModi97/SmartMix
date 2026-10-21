# SmartMix Native VirtualDJ Extension (v1.0)

SmartMix is an offline-capable, native VirtualDJ extension that provides exact Hot Cue-based automated transitions with absolute cutoff protection. It coexists with VirtualDJ's native Automix without modifying proprietary binaries or breaking existing features.

---

## Browser Tab Placement

SmartMix integrates directly into the browser's SideView tab bar in your preferred position:

```
Sidelist | Remixes | Sampler | Automix | SmartMix | Karaoke
```

Clicking **Automix** accesses VirtualDJ's built-in Automix as usual.  
Clicking **SmartMix** reveals the dedicated cue-based arranger.

---

## Key Features

1. **Exact Cue-Based Transitions:**
   - **Song A Trigger Cue:** The exact cue where incoming playback is commanded.
   - **Song B Start Cue:** The incoming track immediately starts from this Hot Cue (with BPM lock) without waiting for the next beat or phrase.
   - **Song A Cutoff Cue:** Outgoing playback stops and is silenced immediately at this cue.
2. **Absolute Audio Cutoff (Non-Destructive):**
   - Unused audio past the Cutoff Cue is never played.
   - The original music file is never trimmed, modified, or overwritten.
3. **Multi-Curve Transition Automation:**
   - Real-time 60 Hz volume automation (*Smooth*, *Linear*, *Equal Power*, *Sharp Cut*).
   - Frequency-aware 3-band EQ crossover (low-end bass swap prevents phase cancellation).
4. **Local Playlist Persistence:**
   - Full SQLite storage (`smartmix.db`) saves custom arrangements, cue selections, and curve parameters independently from VirtualDJ's database.
5. **100% Offline Independence:**
   - Operates completely offline without accounts, remote APIs, or cloud subscriptions.

---

## Installation

### Method 1: Automatic (One-Click)
1. Close VirtualDJ.
2. Open PowerShell in this folder and run:
   ```powershell
   .\install.ps1
   ```
3. Launch VirtualDJ, open **Settings -> Interface**, and select **SmartMix**.

### Method 2: Manual
1. Copy `SmartMix64.dll` to:
   `%LOCALAPPDATA%\VirtualDJ\Plugins64\AutoStart\`
2. Copy `SmartMix.zip` to:
   `%LOCALAPPDATA%\VirtualDJ\Skins\`
3. Copy `smartmix.db` to:
   `%LOCALAPPDATA%\VirtualDJ\`
4. Launch VirtualDJ and select the `SmartMix` skin under **Settings -> Interface**.

---

## Uninstallation

Run PowerShell in this folder and execute:
```powershell
.\uninstall.ps1
```
This restores VirtualDJ cleanly to its default state while keeping your music library, hot cues, and settings intact.
