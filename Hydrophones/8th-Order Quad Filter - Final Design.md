---
date: 2026-10-27
tags: [hydrophone, filter, ltspice, jlcpcb]
---
# 8th-order quad filter: final design

The same spec as the 10th-order version ([[10th-Order Filter - Lopsided Response Fix]]): **Butterworth bandpass, 30 kHz centre, 30 kHz −3 dB bandwidth (18.5–48.5 kHz), 20 dB gain**. It now uses **four MFB stages, so one quad op amp per channel** fits the quad board.

![[bp8_design.png]]

## Schematic values (one channel)
Every capacitor is the same part: **2.2 nF C0G**. Every resistor is 1% E96. Each stage is the 3-resistor MFB (Deliyannis-Friend) already on the board: R1 input → node, R2 node → VREF, one C node → output, one C node → inverting input, R5 inverting input → output, + input on VREF.

| Op amp | f₀ / Q | R1 (in) | R2 (to VREF) | R5 (feedback) | C (both) | Gain @ f₀ |
|---|---|---|---|---|---|---|
| A | 37.1 kHz / 1.11 | 1.05k | 5.49k | 4.32k | 2.2 nF | 2.06 |
| B | 24.2 kHz / 1.11 | 1.58k | 8.87k | 6.65k | 2.2 nF | 2.10 |
| C | 47.2 kHz / 2.89 | 909 | 374 | 8.87k | 2.2 nF | 4.88 |
| D | 19.0 kHz / 2.91 | 2.32k | 909 | 22.1k | 2.2 nF | 4.76 |

Every stage lands within 0.12% of its target f₀ and within 0.8% of its target Q. The chain order (lower-Q stages first) keeps every internal node at or below the output level (peaks 2.1 / 3.5 / 10.6 / 9.8 V/V), so nothing clips early.

## Capacitor: one part, and ±1% is available
JLCPCB stock checked 2026-10-27, all Yageo C0G/NP0 50 V 0603:

| Tolerance | Part | LCSC # | Stock | Price |
|---|---|---|---|---|
| **±1%** | CC0603FRNPO9BN222 | **C576780** | ~11.9k | ~$0.047 |
| ±2% | CC0603GRNPO9BN222 | C576798 | ~9.7k | ~$0.026 |
| ±5% | CC0603JRNPO9BN222 | C107043 | ~41.7k | ~$0.017 |

A 4-channel board uses 32 of them, so the ±1% part costs about **$1.50 total**. It's one extended part (one setup fee). The ±1% caps are cheap here because 2.2 nF happens to be stocked at that tolerance. Avoid the X7R "basic" parts.

## LTspice (`filter_sim/bp8_quad.cir`)

| Op amp | 25 / 30 / 35 / 40 kHz | −3 dB band | Verdict |
|---|---|---|---|
| **AD8608** (10 MHz quad) | 19.80 / 19.86 / 19.93 / 19.96 dB | 18.5–48.0 kHz | ✅ flat to 0.16 dB |
| LT6233 (60 MHz, reference) | 19.78 / 19.77 / 19.76 / 19.71 dB | n/a | ✅ |
| 1 MHz quad (MCP6L04 class) | 19.44 / 20.05 / n/a / 20.49 dB | 18.7–43.4 kHz | ❌ tilts 1 dB and cuts the top of the band |

**Use a ≥10 MHz quad in the standard quad pinout.** The AD8608 is a drop-in for the MCP6L04 footprint (SOIC-14 / TSSOP-14, same pins). The LT6235 (quad LT6233) is SSOP-16 with a different pinout, so it isn't a drop-in. Check AD8608 stock at JLC before committing.

## Rejection vs the 10th-order version
Relative to the 20 dB passband:

| | 5 kHz | 10 kHz | 80 kHz | 90 kHz |
|---|---|---|---|---|
| 8th order (this) | −61 dB | −34 dB | −29 dB | −34 dB |
| 10th order | −77 dB | −43 dB | −36 dB | −43 dB |

Going to 8th order costs about 8 dB of stopband. Thruster noise (mostly below 5–10 kHz) is still cut 34–61 dB. Digital filtering after the ADC narrows things further anyway, because the pinger is selected digitally.

## Channel matching (Monte Carlo, 500 runs, 1% resistors)
Worst channel pair in a 4-hydrophone array, 95th percentile:

| Caps | Tilt 25→40 kHz | Mismatch at 30 kHz |
|---|---|---|
| 10% | ±0.52 dB | 15.1° / 1.40 µs |
| 5% C0G | ±0.27 dB | 7.6° / 0.70 µs |
| 2% C0G | ±0.12 dB | 3.2° / 0.29 µs |
| **1% C0G (C576780)** | **±0.08 dB** | **1.9° / 0.18 µs** |

With the 1% part the channels match to about 0.2 µs (≈0.3 mm of acoustic path). A one-time software calibration is still worth doing, but it's no longer critical.

## Gain staging note
Total gain is 19.8 dB (9.8 V/V). With ±1.6 V of swing around VREF, the filter output clips above about 160 mV pk at its input. The preamp can put out up to ±1.6 V on a close ping, so keep the PGA ahead of the filter, or reduce the gain for the octagon approach.

## Files
- `filter_sim/bp8_design.py` (uses `bp10_design.py`): stage synthesis, rejection, Monte Carlo, plot. Output saved in `filter_sim/bp8_design_output.txt`.
- `filter_sim/bp8_quad.cir`: LTspice netlist. Run it with `LTspice.exe -b bp8_quad.cir`.
- `filter_sim/bp8_design.png`
