"""Song-derived, beat-locked scratch performance. Requires numpy, scipy, FFmpeg."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from scipy import signal
from scipy.interpolate import PchipInterpolator
from scipy.io import wavfile

SR = 44100
DEFAULT_TRACK = Path.home() / "Downloads" / "Amapiano" / "Heavy-K, DJ Buckz, Nonny D - No Bad Vibes (SPOTISAVER).mp3"
if not DEFAULT_TRACK.exists():
    DEFAULT_TRACK = Path(r"C:\Users\odhis\Downloads\Amapiano\Heavy-K, DJ Buckz, Nonny D - No Bad Vibes (SPOTISAVER).mp3")


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *map(str, args)],
                          capture_output=True, check=True)


def edge_fade(audio, milliseconds=3):
    audio = audio.copy()
    n = min(round(SR * milliseconds / 1000), len(audio) // 2)
    if n:
        ramp = np.sin(np.linspace(0, np.pi / 2, n)) ** 2
        audio[:n] *= ramp[:, None]
        audio[-n:] *= ramp[::-1, None]
    return audio


def render_gesture(source, beats, beat, kind, rng):
    """Continuous hand trajectory; fader closes around deliberate reversals."""
    n = max(16, round(beats * beat * SR))
    u = np.arange(n) / n
    # Fader events and hand reversals share one musical clock.
    apex = .5
    travel = rng.uniform(.115, .175)
    if kind == "stab":
        knots, positions = [0, .45, .55, 1], [0, 1, 1, 0]
    elif kind == "tear":
        knots = [0, .20, .28, .48, .71, 1]
        positions = [0, .38, .40, 1, .58, 0]
    else:
        knots, positions = [0, apex, 1], [0, 1, 0]
    trajectory = .008 + travel * PchipInterpolator(knots, positions)(u)
    velocity = np.abs(np.gradient(trajectory) * SR)
    # Prefilter before accelerated playback to control aliasing and brittle highs.
    cutoff = min(12500, 17500 / max(1, float(velocity.max())))
    sos = signal.butter(4, [220, max(600, cutoff)], btype="bandpass", fs=SR, output="sos")
    source = signal.sosfiltfilt(sos, source, axis=0)
    indices = np.clip(trajectory * SR, 0, len(source) - 2)
    lo = indices.astype(np.int64)
    frac = (indices - lo)[:, None]
    audio = source[lo] * (1 - frac) + source[lo + 1] * frac
    gate = np.ones(n)
    if kind == "stab":
        # Hear the forward hit; hide the hand returning to the cue.
        gate[u >= .43] = 0
    elif kind == "chirp":
        gate[(u > .37) & (u < .63)] = 0
    elif kind == "flare":
        for center in (.125, .375, .625, .875):
            gate[np.abs(u - center) < .034] = 0
    elif kind == "transform":
        gate = (((u * max(1, round(beats * 4))) % 1) < .60).astype(float)
    # A median filter does not soften a square fader edge; an actual raised-cosine
    # convolution does. Keep cuts short and percussive without digital clicks.
    kernel = np.hanning(max(5, round(SR * .0015) | 1))
    gate = signal.convolve(gate, kernel / kernel.sum(), mode="same")
    # Silence near a stopped platter instead of sustaining a frozen sample value.
    gate *= np.minimum(1, velocity / .12)
    audio *= gate[:, None]
    audio = edge_fade(audio).astype(np.float32)
    rms = np.sqrt(np.mean(audio ** 2) + 1e-12)
    audio *= min(4, .21 / rms)
    return audio


def phrase_pickup(song, start, beat):
    """A nearby midrange attack, retaining the phrase that follows it.

    This is an onset selector, not a vocal or syllable recognizer.
    """
    start = max(0, min(start, len(song) - round(beat * 4 * SR)))
    search = song[start:start + round(beat * .5 * SR)]
    mid = signal.sosfilt(signal.butter(2, [400, 4500], btype="bandpass",
                                      fs=SR, output="sos"), search, axis=0)
    hop = 220
    count = len(mid) // hop
    energy = np.sqrt(np.mean(mid[:count * hop].reshape(count, hop, 2) ** 2,
                             axis=(1, 2)) + 1e-12)
    attack = np.maximum(0, np.diff(energy, prepend=energy[0]))
    offset = max(0, int(np.argmax(attack)) * hop - round(.008 * SR))
    return start + offset


def sample_bank(song, beat):
    """Choose several strong midrange attacks from the actual song."""
    mid = signal.sosfilt(signal.butter(3, [350, 5000], btype="bandpass",
                                     fs=SR, output="sos"), song, axis=0)
    hop = 441
    count = len(mid) // hop
    energy = np.sqrt(np.mean(mid[:count * hop].reshape(count, hop, 2) ** 2,
                             axis=(1, 2)) + 1e-12)
    onset = np.maximum(0, energy - np.roll(energy, 3))
    peaks, _ = signal.find_peaks(onset, distance=max(1, round(beat * 100)))
    peaks = sorted(peaks, key=lambda p: onset[p], reverse=True)
    picks = []
    for p in peaks:
        start = max(0, p * hop - round(.012 * SR))
        if start + SR > len(song):
            continue
        if any(abs(start - old) < beat * SR for old in picks):
            continue
        picks.append(start)
        if len(picks) == 5:
            break
    if not picks:
        picks = [0]
    bank = []
    for start in picks:
        sample = song[start:start + SR].copy()
        rms = np.sqrt(np.mean(sample ** 2) + 1e-12)
        sample *= min(3, .16 / rms)
        bank.append(sample)
    return bank, [round(p / SR, 3) for p in picks]


def make_scratch_preview():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", type=Path, default=DEFAULT_TRACK)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bpm", type=float, default=118)
    parser.add_argument("--cue", type=float, default=.122)
    parser.add_argument("--duration", type=float, default=65)
    parser.add_argument("--intensity", type=float, default=1.25, help="Scratch level, 0 to 1.5")
    parser.add_argument("--beat-offset", type=float, default=-.022,
                        help="Beat-grid offset in seconds relative to cue")
    parser.add_argument("--seed", type=int, default=27)
    args = parser.parse_args()
    if not 40 <= args.bpm <= 240 or args.duration < 8 or args.cue < 0:
        parser.error("Use BPM 40..240, duration >= 8 seconds, and cue >= 0")
    if not 0 <= args.intensity <= 1.5:
        parser.error("Intensity must be between 0 and 1.5")
    output = args.output or args.track.with_name("Heavy-K_No_Bad_Vibes_Kenyan_Scratch_Preview.mp3")
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = ffmpeg("-ss", args.cue, "-i", args.track, "-t", args.duration,
                 "-f", "f32le", "-ac", 2, "-ar", SR, "-").stdout
    song = np.frombuffer(raw, dtype="<f4").reshape(-1, 2).copy()
    if len(song) < SR * 8:
        raise ValueError("At least eight seconds of audio are required after the cue")
    beat = 60 / args.bpm
    pickups = []
    rng = np.random.default_rng(args.seed)
    scratch = np.zeros_like(song)
    duck = np.ones(len(song), dtype=np.float32)
    events = []
    patterns = [
        [(0, .5, "stab"), (.5, .5, "stab"), (1, 1, "chirp")],
        [(0, 1, "tear"), (1, .5, "chirp"), (1.5, .5, "stab")],
        [(0, .5, "chirp"), (.5, .5, "chirp"), (1, 1, "transform")],
        [(0, 1, "tear"), (1, .5, "flare"), (1.5, .5, "stab")],
    ]
    routines = [(p, patterns[i % len(patterns)])
                for i, p in enumerate(range(4, int(len(song) / SR / beat) - 6, 8))]

    def place(block, beat_number, kind, source_seconds=None):
        start = round((beat_number * beat + args.beat_offset) * SR)
        if start < 0 or start >= len(song):
            return
        block = block[:len(song) - start]
        scratch[start:start + len(block)] += block * args.intensity
        depth = 1 - .88 * min(1, args.intensity)
        envelope = np.full(len(block), depth, dtype=np.float32)
        ramp = min(round(.004 * SR), len(block) // 2)
        envelope[:ramp] = np.linspace(1, depth, ramp)
        envelope[-ramp:] = np.linspace(depth, 1, ramp)
        duck[start:start + len(block)] = np.minimum(duck[start:start + len(block)], envelope)
        events.append({"seconds": start / SR, "beat": beat_number, "gesture": kind,
                       "source_seconds": source_seconds})

    for phrase, gestures in routines:
        # Work the current phrase, rather than an unrelated loud hit elsewhere.
        pickup = phrase_pickup(song, round((phrase * beat + args.beat_offset) * SR), beat)
        pickups.append(pickup / SR)
        source = song[pickup:pickup + round(4 * beat * SR)].copy()
        for j, (offset, length, kind) in enumerate(gestures):
            place(render_gesture(source, length, beat, kind, rng), phrase + offset, kind, pickup / SR)
        # Repeat the same pickup used by the scratches, then move forward through
        # the phrase. Alternate a longer reply with a quicker turnaround.
        cursor = pickup
        repeats_plan = ([(2, .5, 2), (3, .25, 4)] if phrase % 16 == 4
                        else [(2, .25, 4), (3, .5, 2)])
        for offset, division, repeats in repeats_plan:
            size = round(division * beat * SR)
            unit = song[cursor:cursor + size].copy()
            if len(unit) != size:
                break
            unit = edge_fade(unit, 2)
            rms = np.sqrt(np.mean(unit ** 2) + 1e-12)
            unit *= min(3, .21 / rms)
            for repeat in range(repeats):
                place(unit, phrase + offset + repeat * division, "repeat", cursor / SR)
            cursor += size
        # Release at normal pitch from exactly the next source position, on beat.
        release = edge_fade(song[cursor:cursor + round(2 * beat * SR)], 3)
        rms = np.sqrt(np.mean(release ** 2) + 1e-12)
        release *= min(2, .21 / rms)
        place(release, phrase + 4, "release", cursor / SR)
    # Keep a steady low-end bed while giving the phrase deck space in the mids.
    bass = signal.sosfilt(signal.butter(4, 170, fs=SR, output="sos"), song, axis=0)
    bass_gain = .82 + .18 * duck
    master = bass * bass_gain[:, None] + (song - bass) * duck[:, None] + scratch
    # Float WAV preserves peaks above 0 dBFS until mastering: never pre-clip.
    master = edge_fade(master, 15)
    with tempfile.TemporaryDirectory(prefix="smartmix_", dir=output.parent) as temp:
        wav = Path(temp) / "mix.wav"
        wavfile.write(wav, SR, master.astype(np.float32))
        measured = ffmpeg("-i", wav, "-af", "loudnorm=I=-14:TP=-2:LRA=10:print_format=json",
                          "-f", "null", "-").stderr.decode()
        stats = json.loads(measured[measured.rfind("{"):measured.rfind("}") + 1])
        norm = ("loudnorm=I=-14:TP=-2:LRA=10:linear=true:"
                f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
                f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
                f"offset={stats['target_offset']}")
        ffmpeg("-y", "-i", wav, "-af", norm, "-ar", SR, "-c:a", "libmp3lame", "-b:a", "320k",
               "-metadata", "title=No Bad Vibes (Kenyan Scratch Preview)", output)
    meter = ffmpeg("-i", output, "-af", "loudnorm=I=-14:TP=-2:LRA=10:print_format=json",
                   "-f", "null", "-").stderr.decode()
    verified = json.loads(meter[meter.rfind("{"):meter.rfind("}") + 1])
    report = {"output": str(output), "bpm": args.bpm, "cue": args.cue,
              "beat_offset": args.beat_offset, "intensity": args.intensity,
              "duration": len(song) / SR, "sample_pickups_seconds_after_cue": pickups,
              "events": events, "decoded_mp3_lufs": verified["input_i"],
              "decoded_mp3_true_peak_db": verified["input_tp"]}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    make_scratch_preview()
