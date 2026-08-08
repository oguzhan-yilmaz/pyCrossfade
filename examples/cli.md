# CLI crossfade examples

All commands assume the Docker alias from the main README, or:

```bash
docker run --rm -v "$PWD/audios:/app/audios" \
  -e BASE_AUDIO_DIRECTORY=/app/audios/ \
  ghcr.io/oguzhan-yilmaz/pycrossfade:latest \
  crossfade ...
```

File paths are **relative to `BASE_AUDIO_DIRECTORY`** (typically your `audios/` folder).

---

## Basic two-song crossfade

```bash
# master_filepath — outgoing track (time-stretched to match the incoming track)
# slave_filepath  — incoming track
# Defaults: 8-bar time-stretch (-t), 8-bar crossfade (-c), equal_power fade profile
pycrossfade crossfade master.mp3 slave.mp3
```

Output is written to `crossfade-{master}---{slave}.wav` in the audio directory unless `-o` is set.

---

## Crossfade length and time-stretch length

```bash
# -t / --len-time-stretch — bars to gradually time-stretch the master before the blend
# -c / --len-crossfade     — bars where master fades out and slave fades in (EQ + volume)
pycrossfade crossfade master.mp3 slave.mp3 \
  --len-time-stretch 4 \
  --len-crossfade 16
```

- **`--len-time-stretch` / `-t`** — how many bars the master is gradually stretched so its tempo aligns with the slave. Use `0` to skip gradual stretch (jump straight to the crossfade region).
- **`--len-crossfade` / `-c`** — overlap length in **bars** (downbeats). Must be ≥ 1.

---

## Fade profile (volume curve)

```bash
# --fade-profile — volume ramp during the crossfade section
#   linear       — straight gain ramp; loudest at the crossover point
#   cosine       — cos/sin curve; smoother perceived blend
#   equal_power  — default; constant perceived loudness through the overlap
pycrossfade crossfade master.mp3 slave.mp3 --fade-profile linear
```

EQ filtering is unchanged; `--fade-profile` only affects the gain curve.

---

## Loudness offsets (replay-gain style)

```bash
# --master-gain — dB offset applied to the master before blending
# --slave-gain  — dB offset applied to the slave before blending
pycrossfade crossfade master.mp3 slave.mp3 \
  --master-gain -2.0 \
  --slave-gain 1.5
```

Use when one track is noticeably louder after Essentia replay-gain analysis, or to nudge the balance by ear.

---

## Sample rate override

```bash
# --sample-rate — resample both tracks to this rate for processing and output
# (omit to keep each file's native sample rate)
pycrossfade crossfade master.mp3 slave.mp3 --sample-rate 48000
```

---

## Mark transition points (debug / alignment)

```bash
# --mark-transitions — beeps at time-stretch start, crossfade start, and crossfade end
pycrossfade crossfade master.mp3 slave.mp3 \
  --mark-transitions \
  -o marked_mix.wav
```

Beeps are placed at:

1. **Time-stretch start** — where gradual master stretching begins  
2. **Crossfade start** — where EQ + volume blending begins  
3. **Crossfade end** — where the slave takes over fully  

Pair with `--verbose` to print the same indices in seconds.

---

## Verbose output and custom output path

```bash
# --verbose / -v — print transition indices, bar lengths, saved path
# --output / -o  — explicit output filename (under audios/)
pycrossfade crossfade master.mp3 slave.mp3 \
  --verbose \
  --output my_mix.wav \
  --len-time-stretch 8 \
  --len-crossfade 8
```

---

## Full recipe (all crossfade tunables)

```bash
pycrossfade crossfade master.mp3 slave.mp3 \
  --len-time-stretch 8 \
  --len-crossfade 8 \
  --fade-profile equal_power \
  --master-gain 0 \
  --slave-gain 0 \
  --sample-rate 44100 \
  --mark-transitions \
  --verbose \
  --output full_recipe.wav
```

| Flag | Meaning |
|------|---------|
| `-t` / `--len-time-stretch` | Bars of gradual master time-stretch |
| `-c` / `--len-crossfade` | Bars of EQ + volume overlap |
| `--fade-profile` | `linear`, `cosine`, or `equal_power` |
| `--master-gain` / `--slave-gain` | Loudness offset in dB |
| `--sample-rate` | Optional output/processing rate (Hz) |
| `--mark-transitions` | Beep at stretch start, crossfade start, crossfade end |
| `-v` / `--verbose` | Print timing table |
| `-o` / `--output` | Output filename |

---

## Three or more songs (`crossfade-many`)

```bash
# At least three filepaths, processed in order (A→B, then B→C, …)
pycrossfade crossfade-many track_a.mp3 track_b.mp3 track_c.mp3 \
  --len-time-stretch 8 \
  --len-crossfade 8 \
  --fade-profile cosine \
  --mark-transitions \
  --verbose \
  --output set_mix.wav
```

Supports `--len-time-stretch`, `--len-crossfade`, `--fade-profile`, `--mark-transitions`, `--verbose`, `-o`.

Does **not** expose `--master-gain`, `--slave-gain`, or `--sample-rate` on this subcommand (use the [SDK](./sdk.py) for per-transition gain).

---

## Related commands (prep before crossfading)

```bash
# Inspect downbeats / duration
pycrossfade song master.mp3

# Cut both tracks to the same bar range, then crossfade the cuts
pycrossfade cut-song master.mp3 35 65 -o master-cut.wav
pycrossfade cut-song slave.mp3  35 65 -o slave-cut.wav
pycrossfade crossfade master-cut.wav slave-cut.wav -o mix.wav
```
