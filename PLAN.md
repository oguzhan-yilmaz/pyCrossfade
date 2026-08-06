# pyCrossfade — Improvement Plan

> Status: **Draft for review**
> Scope: core functions, audio settings, crossfade filtering, CLI, packaging, testing.

---

## 1. Executive Summary

pyCrossfade's algorithm is actually sound (downbeat-based beat-matching + gradual
time-stretch + EQ crossfade is a legitimately good idea). The problems are all in
**engineering quality**: the code was written fast, with no types, no tests, no
config, hardcoded constants, destructive global state, and a broken package layout.
The biggest *audio-quality* problems are that **everything is forced to mono** and
**all tuning values are hardcoded magic numbers**.

Goal: refactor into a clean, configurable, testable package while **keeping the
core algorithm identical** at first, then improving the DSP (EQ, volume, fades).

---

## 2. Current Architecture (as-is)

| File | Responsibility | Key issues |
|------|---------------|------------|
| `config.py` | 2 env vars only (`ANNOTATIONS_DIRECTORY`, `BASE_AUDIO_DIRECTORY`) | No tuning config, no sample-rate config |
| `song.py` | `Song` class: load audio, madmom beats/downbeats, attributes, extract | Hardcoded 44100, mono-only, fragile name parsing, recursive `load_beats`, no error handling |
| `utils.py` | IO, time-stretch, fades, EQ filters, beeps, essentia extractor | `from utils import *` targets; `linear_fade_filter` mutates yodel internals; destructive `add_beep`; hardcoded EQ params |
| `transition.py` | `crossfade`, `crossfade_multiple`, `crop_audio_and_dbeats`, `beatmatch_to_slave` | Massive duplication, dict-as-return-type, hardcoded fades/EQ, float `np.arange` bug, 44100 hardcoded |
| `cli.py` | Typer CLI commands | Broken package imports, `crossfade_many --verbose` incomplete, no validation |
| `__init__.py` | Public API | **Absolute imports** (`from song import Song`) → package install broken |
| `results.json` | Essentia artifact | Committed by accident — should not be in repo |

### Data flow today

```
CLI → Song(filepath)
   → MonoLoader (mono!) → audio (np.float32 1-D)
   → madmom RNNDownBeatProcessor → beats (2-col) → downbeats (sample idx)
   → transition.crossfade(master, slave, len_crossfade, len_time_stretch)
        → time-stretch master on downbeats via pyrubberband
        → beatmatch master-fadeout to slave-fadein per-bar (time-stretch)
        → EQ + volume fades (yodel shelves) → sum → concat → save (MonoWriter)
```

---

## 3. Core Problems (ranked by severity)

### P0 — Will break / wrong results
1. **`__init__.py`, `cli.py`, `transition.py` use non-relative imports**
   (`from song import Song`, `from utils import *`). The package only works when
   run from inside the `pycrossfade/` dir. `pip install` / `import pycrossfade`
   fails. → Fix with relative imports.
2. **`time_stretch_gradually_in_downbeats` uses `np.arange(1.0, final_factor, step)[1:]`**
   Float steps are unreliable: the last factor may never be reached and length can
   drift, so the time-stretch section may not actually end at `final_factor`.
   → Build factors from `np.linspace` (or exact `i*step`) and validate endpoint.
3. **`beatmatch_to_slave` duplicated "last part" block** — the tail handling is a
   near-verbatim copy of the loop body. Any fix must be applied twice. → Extract helper.
4. **`add_beep_to_audio` mutates its input in place** (`audio[...] += beep`).
   Callers share arrays (e.g. result dict `audio`), so repeated calls and reuse
   have hidden side effects. → Return a copy; document non-mutation.
5. **`linear_fade_filter` reaches into `bquad_filter._b_coeffs/_a_coeffs` and
   manually sets `a[0] = 1.0`.** Fragile against yodel internals; gain is
   quantized with `int(26*(1.0-profile))`; `MID_CENTER` unused; no filter-state
   handling at step boundaries → audible zipper noise.

### P1 — Audio quality
6. **Stereo is destroyed**: `MonoLoader` downmixes and `MonoWriter` writes mono.
   For a DJ tool this is unacceptable. → `AudioLoader` / `AudioWriter` with
   channel support (`essentia.standard.AudioLoader` + `AudioWriter`), keep a
   `num_channels`/`sample_rate` on `Song`, and make all DSP channel-aware.
7. **Hardcoded `44100` everywhere** instead of the file's real sample rate.
   → `song.sample_rate` propagated through utils/transition (no defaults).
8. **No click/pop prevention** at splice points (concat boundaries) and the beep
   sine has no fade envelope → clicks. → Short fade-in/out at splice edges; envelope the beep.
9. **No volume balancing via ReplayGain** — README lists it as a goal; not done.
   → Apply loudness normalization / replay-gain offsets before crossfade.

### P2 — Crossfade / EQ quality
10. **EQ is a crude linear shelf fade** (`low_shelf` + `high_shelf` 0.9→0.0 /
    0.0→1.0). No **mid-frequency dip** — the classic DJ crossfade trick to avoid
    muddy overlap. → Add configurable 3-band (low/mid/high) crossover with a mid dip.
11. **Fade profiles are linear-in-gain (`np.linspace` then `np.sqrt`)** — no
    equal-power / cosine profile for a smooth perceived level. → Make fades
    configurable (linear / equal-power / cosine).
12. **All EQ/volume/fade constants are magic numbers** (0.9, 0.1, 26, 70Hz,
    1000Hz, 13000Hz, 20 steps). → Move to a `CrossfadeSettings` dataclass.

### P3 — Architecture / DX
13. `crossfade` returns a bare `dict` mixing audio arrays + indices + seconds.
    → Return a typed `Transition` dataclass (audio, master_initial, ts_audio,
    crossfade_part, slave_remaining, and index/seconds fields).
14. `Song` mixes concerns (IO, madmom, presentation). → Split: `Song` = data,
    `AudioIO`, `BeatTracker`/`annotations`, keep `Song` as a clean container.
15. `crossfade_multiple`'s `mark_indices` closure is O(n²) and confusing; the
    CLI `--verbose` branch is incomplete/broken (empty dict, dead asserts).
16. No type hints, no tests, `print()` instead of logging, no `__version__`.
17. `config.py` only env vars; no settings hierarchy. → dataclasses + env overrides.
18. `results.json` committed; stale deps pinned to python 3.8 era.

---

## 4. Improvement Plan (phased)

### Phase 1 — Make it a real package (no behavior change)
**Goal:** `import pycrossfade` works; code is importable from anywhere.
- [x] Convert all internal imports to relative (`from .song import Song`, `.utils`, `.config`).
- [x] Add `pyproject.toml` (proper metadata, `__version__`, console-script `pycrossfade`).
- [x] Remove `results.json` from repo; add to `.gitignore`.
- [x] Replace `from utils import *` with explicit imports.
- [x] Keep CLI entry point working (`pycrossfade ...`) — `main()` added; Docker entrypoint unaffected.

> Phase 1 landed. Verification was syntax/compile-level only; full import requires the
> heavy deps (numpy/essentia/madmom) which live in the Docker container (python 3.7).
> Docker entrypoint `python3 pycrossfade/cli.py` still works because it runs from `/app`.

### Phase 2 — Hardcode → Config
**Goal:** every tunable is a setting, no magic numbers.
- [ ] Add dataclasses in `config.py`:
  - `AudioSettings` (`sample_rate=None` → read from file, `num_channels`, `bit_rate`)
  - `BeatSettings` (`beats_per_bar`, `fps`, annotation dir)
  - `FadeSettings` (`profile: 'equal_power'|'linear'|'cosine'`, `start/end volumes`)
  - `EQSettings` (`low_cutoff`, `mid_center`, `high_cutoff`, `q`, `gain_db`,
    `bands: ['low','mid','high']`, `mid_dip_db`, `num_steps`)
  - `CrossfadeSettings` (`len_crossfade`, `len_time_stretch`, `mark_transitions`)
- [ ] Thread settings through `Song`, `transition`, `utils`; env vars override defaults.

### Phase 3 — Fix core correctness bugs
- [ ] `time_stretch_gradually_in_downbeats`: replace `np.arange` with exact factors;
      assert output length ≈ expected; handle `final_factor == 1` early-return cleanly.
- [ ] Extract `time_stretch_beatmatch_fragment(...)` helper; de-duplicate
      `beatmatch_to_slave` loop + tail.
- [ ] `add_beep_to_audio` → non-mutating; add envelope; return new array.
- [ ] `Song.get_song_name_and_format` → `pathlib`/`os.path`; robust to dots/Windows;
      raise on missing file; guard `load_beats` recursion.
- [ ] `linear_fade_filter` → rewrite with `scipy`/`yodel` cleanly:
      - build one filter per step with proper state carry (`zi`),
      - no manual `_a_coeffs[0]=1.0` hack,
      - continuous (non-quantized) gain mapping.

### Phase 4 — Audio quality & stereo
- [ ] `AudioLoader`/`AudioWriter` supporting mono + stereo (`AudioLoader` + `AudioWriter`).
- [ ] `Song` carries `sample_rate`, `num_channels`, `duration_seconds` correctly
      (`audio.shape[0] / sample_rate` for mono, or shape-aware).
- [ ] Remove all hardcoded `44100`; propagate real sample rate.
- [ ] Splice click protection: short (2–5 ms) fade-in/out at every concat boundary.
- [ ] ReplayGain/loudness normalization option (store `replay_gain` on `Song`,
      apply offset before summing).

### Phase 5 — Crossfade filtering (the "good stuff")
- [ ] Replace single shelf-pair with **3-band EQ**:
      low (< low_cutoff), mid (around mid_center), high (> high_cutoff).
- [ ] Implement the **mid-dip crossfade**: master fades out low+high, slave fades in
      low+high, while *both* get a mid dip at the overlap center for clarity.
- [ ] Equal-power fades: master `cos(t)`-ish fade-out, slave `sin(t)`-ish fade-in
      so summed power stays ~constant (replace `np.linspace`+`sqrt`).
- [ ] Make EQ curves **non-linear/smoothed** across steps (interp, more steps,
      or per-sample coefficient interpolation) to kill zipper noise.
- [ ] Optionally: EQ the master-fadeout and slave-fadein with *slightly different*
      curves for a musical blend (kick vs. vocals).

### Phase 6 — Typed API + cleaner CLI
- [ ] `Transition` dataclass with fields: `audio`, `master_initial_audio`,
      `time_stretch_audio`, `crossfade_part_audio`, `slave_remaining_audio`,
      and `time_stretch_start_idx/sec`, `crossfade_start_idx/sec`,
      `slave_start_idx/sec`, `slave_fadein_end_idx/sec`.
- [ ] `crossfade_multiple` returns `MultiTransition(full_transition, transition_indices)`.
- [ ] Rewrite `crossfade_many --verbose` (fix empty dict / dead code) or drop it.
- [ ] Add CLI input validation (`len_crossfade >= 1`, `len_time_stretch >= 0`,
      downbeat bounds, file existence).
- [ ] Add `--sample-rate`, `--eq-profile`, `--fade-profile`, `--gain` options
      mapped to settings dataclasses.

### Phase 7 — Tests, docs, DX
- [ ] Unit tests:
  - `time_stretch` factors reach endpoint & length preserved.
  - `beatmatch_to_slave` output lengths equal; no `np.concatenate` shape errors.
  - `linear_fade_volume/filter` output shape == input; stereo-aware.
  - `crop_audio_and_dbeats` negative-index bounds.
  - `crossfade` result lengths: `len(audio)` == master_initial + ts + crossfade + slave_remaining.
  - `add_beep` returns copy, doesn't mutate input.
- [ ] Test with tiny synthesized mono + stereo fixtures (no real mp3 needed).
- [ ] CI: run pytest + a smoke `pycrossfade --help` (extend `.github/workflows`).
- [ ] Update README with new settings/CLI options.
- [ ] Modernize deps if feasible (note madmom/essentia python-version constraints).

---

## 5. Future feature ideas (after plan lands)
- MIDI/beat-grid export; waveform visualization for transition QA.
- `--output` directory handling + auto mkdir.
- Loudness-matched crossfades (EBU R128 via Essentia `lowlevel.loudness_ebu128`).
- Caching of Essentia `extract()` per song (avoid full re-analysis).
- Key detection → harmonic mixing suggestions (`extract` already returns keys).
- A `preview` command that plays just the crossfade segment.

---

## 6. Definition of Done (per phase)
- Phase 1–3: `import pycrossfade` + CLI work from any cwd; existing output is
  byte-identical or audibly equivalent; all tests green.
- Phase 4–5: stereo preserved end-to-end; EQ/fades configurable; no zipper/click
  artifacts; equal-power crossfade in place.
- Phase 6–7: typed return values; validated CLI; `pytest` + CI green; docs updated.

---

## 7. Open questions for the author
1. **Stereo support priority?** Mono-only made the algorithm simpler. Confirm we want
   full stereo DSP everywhere (bigger lift).
2. **EQ target sound**: classic EDM mid-dip crossfade, or preserve original EQ
   with only volume crossfade? Pick a default.
3. **Volume balance**: auto ReplayGain normalization, or expose manual gain per song?
4. **Backward compat**: keep old `crossfade()` dict return for the deprecated
   scripted API, or break it with the new `Transition` object?
5. **Dependency modernization** budget — madmom pins to old Python; do we containerize
   and bump, or keep the frozen stack?
