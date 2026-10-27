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

## Mouser Canada BOM (stock checked 2026-10-27)
Per channel: 1 op-amp section, 8 caps, 12 resistors. A 4-channel board needs 1 AD8608, 32 caps, and 4 of each resistor.

| Part | Use | Mouser # | Stock | Note |
|---|---|---|---|---|
| **AD8608ARZ** (SOIC-14) | quad op amp | 584-AD8608ARZ | 445 | CA$10.54 (CA$8.11 @10). Mouser only lists SOIC-14, not TSSOP. Check the board footprint |
| **Murata GCM1885C1H222FA16J** | 2.2 nF ±1% C0G 0603, 50 V | 81-GCM1885C1H222FA6J | ~9.2k | ~CA$0.18 @50 |
| alt: Vishay VJ0603A222FXJCW1BC | 2.2 nF ±1% C0G 0603, 16 V | 77-VJ0603A222FXJCBC | ~9.8k | CA$0.24 @100 |
| ~~Yageo CC0603FRNPO9BN222~~ | (the JLC part) | 603-CC0603FRNPO9BN22 | **0** | backordered to 2027-03-30 |
| Yageo RC0603FR-071K05L | 1.05k | | 391k | |
| Yageo RC0603FR-071K58L | 1.58k | | 24k | |
| Yageo RC0603FR-072K32L | 2.32k | | 25k | |
| Yageo RC0603FR-07909RL | 909 Ω | | 2.1k | |
| Yageo RC0603FR-076K65L | 6.65k | | 871k | |
| **Panasonic ERJ-3EKF5491V** | 5.49k | 667-ERJ-3EKF5491V | 49k | Yageo 5.49k out of stock |
| Panasonic ERJ-3EKF4321V | 4.32k | | 46.5k | |
| Panasonic ERJ-3EKF8871V | 8.87k | | 25k | |
| Panasonic ERJ-3EKF2212V | 22.1k | | 78k | |
| Panasonic ERJ-3EKF3740V | 374 Ω | | 5.5k | |

All resistors are 0603 1% 100 ppm thick film. Yageo RC and Panasonic ERJ-3EKF parts are interchangeable.

## Seeing it in the ADI Filter Wizard
Load `filter_sim/filter_wizard_8th_order_quad.json`, or enter the settings by hand:
- Band Pass
- Gain 20 dB
- Passband −3 dB at **30k** (this is the bandwidth)
- Stopband −40 dB at **100k** (95k–139k gives 8th order; 80k forces 10th)
- Centre 30k
- Butterworth (slider in the middle)
- 3.3 V / 0 V, VREF 1.65 V
- Every stage Multiple Feedback (Deliyannis-Friend) on **AD8608**
- Tolerances 1% / 1%, series E6 caps / E96 resistors

The Wizard draws the same four stages (19.0 / 24.2 / 37.1 / 47.2 kHz), so its plot matches. It picks its own component values, though, not 2.2 nF everywhere. The exact circuit is in `bp8_quad.cir`.

> [!warning] Why the Wizard's Components/Tolerances V/V plot looks lopsided
> Checked 2026-10-27 by reading the Wizard's plotted curve data:
> - The ideal plot on the Specifications tab is a symmetric 8th-order Butterworth.
> - The plots on the Components and Tolerances tabs ramp from **3.0 V/V at 20 kHz** to **8.9 V/V at 45 kHz**.
> - That ramp is the same no matter which parts the Wizard picks (E6 or E96 caps, AD8608 or AD8515). So the plot isn't actually simulating the listed parts.
> - LTspice with the real AD8608 and the Wizard's own listed parts gives **8.0 → 10 V/V**, close to flat.
> - The Wizard's curve matches the listed circuit exactly if its **two-resistor stages (C and D, unequal caps 2.2n/3.3n) are treated as if both caps were the smaller value**. The same thing turns the old 10th-order design (stages A and D had 3.9/4.7n and 4.7/12n) into 2.9 → 7.2 V/V on the plot, while LTspice gives it a flat 9.5 V/V.
> - **Don't sign off on the Wizard's real-parts V/V plot when it uses two-resistor MFB stages. Check in LTspice.** Our design uses only three-resistor, equal-cap stages, so it isn't affected.

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
