---
tags: [hydrophone, analog, preamp, reference]
created: 2026-10-04
parts: [AD8605ARTZ-REEL, 1N4148WSF-7, TE 5227699-2]
---
# Hydrophone Preamp: Labelled Diagram

![[hydrophone_preamp_reference.png]]

> [!summary] In one line
> Piezo charge → **U5 charge amp** (charge to voltage) → **C20/R15 high-pass** (strip drift, re-centre on V<sub>REF</sub>) → **U4 ×52 gain** → filter [1B].
> Overall: **×52 (34.3 dB)**, flat from **≈166 Hz to ≈119 kHz** (−3 dB). A 25–40 kHz pinger band sits within 0.5 dB of the peak.

## Parts

| Ref | Value | Block | Job |
|---|---|---|---|
| J1 | TE 5227699-2 | 1 | Coax connector for the hydrophone (piezo element, makes charge *Q*) |
| C19 | 1 nF | 1 | Couples the AC signal in. Blocks DC so the hydrophone sits at 0 V while U5's input sits at V<sub>REF</sub> |
| D1 | 1N4148WS | 1 | Clamps the input node to ≤ 3.3 V + ~0.6 V (spike → supply rail) |
| D2 | 1N4148WS | 1 | Clamps the input node to ≥ −0.6 V (spike → ground) |
| U5 | AD8605 | 2 | Charge amplifier. − input held at V<sub>REF</sub> (virtual ground) |
| C18 | 1 nF | 2 | Feedback capacitor. Incoming charge lands here, so V = Q / C18 |
| R13 | 1 MΩ | 2 | DC path that slowly bleeds C18. Sets the low cut at 1/(2π·R13·C18) = **159 Hz** |
| C20 | 220 nF | 3 | Inter-stage coupling. Passes the signal, blocks DC offset and drift |
| R15 | 22 kΩ | 3 | Re-biases U4's + input to V<sub>REF</sub>. With C20: corner **33 Hz** |
| U4 | AD8605 | 4 | Non-inverting amplifier |
| R14 | 51 kΩ | 4 | Feedback resistor: gain = 1 + R14/R16 = **52** |
| R16 | 1 kΩ | 4 | Gain-setting resistor, returned to V<sub>REF</sub> (not ground) so the DC gain only applies around 1.65 V |
| C17 | 10 pF | 4 | Rolls the gain back toward 1 above 1/(2π·R14·C17) = **312 kHz**. Limits noise bandwidth and helps stability |
| C21, C22 | 100 nF | supply | Local decoupling on each op-amp's 3.3 V pin |

AD8605 pins (SOT-23-5): 1 = OUT, 2 = V−, 3 = +IN, 4 = −IN, 5 = V+.

## Key numbers

| Quantity | Formula | Value |
|---|---|---|
| Stage-1 charge gain | 1 / C18 | 1 mV per pC (inverted) |
| Stage-1 low cut | 1/(2π·R13·C18) | 159 Hz |
| Coupling high-pass | 1/(2π·R15·C20) | 32.9 Hz |
| Stage-2 gain | 1 + R14/R16 | 52 V/V = 34.3 dB |
| Stage-2 feedback pole | 1/(2π·R14·C17) | 312 kHz |
| U4 bandwidth limit | GBW / 52 = 10 MHz / 52 | ≈192 kHz |
| Overall −3 dB band | (simulated, see below) | ≈166 Hz to ≈119 kHz |

The overall response comes from a small-signal model: ideal parts plus a 10 MHz single-pole op-amp, with the hydrophone capacitance assumed ≫ 1 nF. The upper edge (119 kHz) is lower than either 312 kHz or 192 kHz alone because the two poles stack.

## DC operating point
- Single 3.3 V supply, so every signal node idles at **V<sub>REF</sub> ≈ 1.65 V** (assumed mid-supply; check the real V<sub>REF</sub> source).
- The hydrophone side of C19 sits at 0 V. C19 holds the 1.65 V difference.
- Preamp out = V<sub>REF</sub> + 52 × (signal). Swing headroom is about ±1.6 V, so the largest clean input at U4 is about ±30 mV.

See [[Hydrophone Preamp - How It Works]] for the full walkthrough.
