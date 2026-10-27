---
date: 2026-10-26
tags: [hydrophone, filter, ltspice]
---
# Bandpass filter redesign: simulation

Sheet **[1B → 2B]** is an 8th-order bandpass: four multiple-feedback (Deliyannis-Friend) stages on one MCP6L04 quad, all caps 1 nF, biased at V<sub>REF</sub>.

Goal: widen the passband to cover the 25–40 kHz pinger band flat, and reject thruster/motor noise below ~10 kHz.

Filter Wizard spec (saved as `filter_sim/filter_wizard_spec.json`): bandpass, 20 dB gain, 30 kHz centre, 25 kHz −3 dB bandwidth, −40 dB at 80 kHz stopband bandwidth, Butterworth. The JSON stores settings only, not component values, so the values below were synthesised from the same spec.

## Stage values (E96, C = 1 nF, lowest Q first)

| Stage | f₀ | Q | R1 (in) | R3 (to VREF) | R2 (feedback) |
|---|---|---|---|---|---|
| 1 | 25.3 kHz | 1.32 | 2.67k | 23.7k | 16.5k |
| 2 | 35.6 kHz | 1.32 | 1.87k | 16.5k | 11.8k |
| 3 | 20.5 kHz | 3.37 | 8.45k | 1.33k | 52.3k |
| 4 | 43.9 kHz | 3.37 | 3.92k | 619 | 24.3k |

Each stage has a gain of 3.12 at its own f₀.

## LTspice results (op amp GBW = 10 MHz)

| | Current board | New design |
|---|---|---|
| Peak gain | 19.8 dB @ 35.7 kHz | 19.8 dB, flat |
| −3 dB band | 32.4–42.8 kHz | **20.0–44.8 kHz** |
| 25 / 30 / 40 kHz | 3.4 / 12.6 / 18.0 dB | 19.6 / 19.7 / 19.6 dB |
| 10 kHz (relative to peak) | −54 dB | −40 dB |
| 5 kHz (relative to peak) | −80 dB | −68 dB |
| 90 kHz (relative to peak) | −22 dB | −41 dB |

**With the MCP6L04 (1 MHz GBW)**, the current board's peak moves down to 31.6 kHz. The new design is pushed out of shape too: its −3 dB band shrinks to 20.2–40.2 kHz with 1 dB of ripple. Use a ≥10 MHz quad such as the AD8608, which is the quad version of the preamp's AD8605.

## Channel matching (Monte Carlo, 100 runs)

| Tolerances | Worst channel-pair phase at 30 kHz | Same, as time | Gain spread (σ) |
|---|---|---|---|
| 1% R, 5% C | 21.9° | 2.0 µs | 0.70 dB |
| 1% R, **1% C0G** | 5.9° | 0.55 µs | 0.20 dB |

Use 1% C0G capacitors if the pinger is located from arrival-time differences between channels. Lower stage Q alone did not improve matching.

## Filter Wizard design (final candidate)

Settings: `filter_sim/filter_wizard_final.json`. That's 3.3 V / 0 V supply, VREF 1.65 V, AD8608, 1% R (E96) and 1% C (E24), with RC sizing at 61/69/63/67. The values were read from the Wizard after loading that JSON on 2026-10-26.

| Stage | R1 (in) | R3 (to VREF) | R2 (feedback) | C (both) |
|---|---|---|---|---|
| A | 10.9k | 1.74k | 67.8k | 360 pF |
| B | 11.1k | 1.78k | 69.6k | 750 pF |
| C | 4.39k | 39.2k | 27.4k | 430 pF |
| D | 4.29k | 38.3k | 26.8k | 620 pF |

The Wizard also draws a VREF buffer (AD8031 + 10k/10k divider). The board already has a VREF net, so that buffer is only needed if VREF isn't already buffered.

LTspice simulation with the real AD8608 model:

| | Result |
|---|---|
| −3 dB band | **20.0–44.4 kHz**, peak 20.2 dB, ±0.2 dB ripple across 25–40 kHz |
| 10 kHz / 90 kHz | −40 dB / −41 dB relative to peak |
| Same design on a 1 MHz op amp (MCP6L04) | band shrinks to 20–40 kHz, 45 kHz drops to 10 dB, 1 dB peaking |
| Internal stage peaks | +9.9 / +5.0 / +14.2 dB, so no early-stage clipping |
| Max clean input at 30 kHz | ~140 mV pk (1.4 V pk out); 200 mV pk clips at the rails |
| Output noise 20–45 kHz | 165 µV rms (input-referred 104 nV/√Hz at 30 kHz) |
| Monte Carlo, 1% R / 1% C | gain σ 0.26 dB; worst channel pair 5° (0.46 µs) at 30 kHz |

LTspice schematics (open and press Run): `filter_sim/Original_Filter_1B.asc`, `filter_sim/Wizard_Filter_Redesign.asc`, and `filter_sim/Compare_Original_vs_Wizard.asc` (both filters on one input; the plot opens with V(out_orig) and V(out_wiz) overlaid).

Files: `filter_sim/wizard_*.cir`, `filter_sim/filter_compare.cir`, `filter_sim/filter_montecarlo*.cir`. Run them with `LTspice.exe -b <file>`; results land in the `.log`.
