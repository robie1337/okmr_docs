---
date: 2026-10-27
tags: [hydrophone, filter, ltspice, jlcpcb]
---
# 10th-order filter: why it came out lopsided, and the fix

Design under test: `filter_sim/filter_wizard_10th_order.json`. Despite the file name, it is a **10th-order Butterworth bandpass** with 5 MFB stages on LT6233, 20 dB gain, a 30 kHz centre and a 30 kHz −3 dB bandwidth (18.5–48.5 kHz). Its caps are 10% E12 and its resistors are 1% E24.

![[bp10_nominal.png]]

## Why it's lopsided
A 10th-order bandpass is five 2nd-order stages, each tuned to its own centre frequency f₀ and Q. The flat top only appears when all five land exactly where the Butterworth maths puts them, so that each stage's bump fills the dip next to it.

| Stage | Should be | Wizard's values give | Error |
|---|---|---|---|
| E | 21.93 kHz, Q 1.30 | 20.25 kHz, Q 1.25 | **f₀ −7.7%** |
| A | 30.00 kHz, Q 1.00 | 31.59 kHz, Q 1.01 | **f₀ +5.3%** |
| D | 41.04 kHz, Q 1.30 | 39.99 kHz, Q 1.29 | f₀ −2.6% |
| C | 18.87 kHz, Q 3.59 | 19.08 kHz, Q 3.69 | +1.1%, Q +2.7% |
| B | 47.69 kHz, Q 3.59 | 47.42 kHz, Q 3.69 | −0.6%, Q +2.7% |

1. **Rounding to E12 caps and E24 resistors moves the stages.** E12 caps step about 20% apart and E24 resistors about 10%, so the Wizard can't land each f₀. Stage E slides 7.7% low, which puts a hump at ~21 kHz. Stage A slides 5% high, which leaves a dip at ~25–30 kHz. LTspice with the real LT6233 model gives a peak of 19.95 dB at 21.1 kHz and 19.53 dB at 25–30 kHz.
2. **A V/V plot exaggerates it.** That 0.4 dB of ripple is only about 5% in V/V, but on a linear gain axis the hump and dip look like a lopsided top.
3. **10% caps then make each board different.** Each high-Q edge stage (Q 3.6) moves ±5% with its caps, so on a real board one edge randomly grows a peak (up to 13 V/V instead of 10, left plot below).
4. **The rest of the asymmetry is geometry, not a fault.** A Butterworth bandpass is symmetric in *log* frequency: 18.5 × 48.5 = 30². On a *linear* frequency axis the high side always looks stretched, because it sits 18.5 kHz above centre while the low side sits only 11.5 kHz below.

## The fix: let the resistors absorb the rounding
Pick the caps from the few values that are actually stocked, then tune each stage with its three resistors. In a 3-resistor MFB stage with equal caps C:
- R5 = 2Q / (ω₀C)
- R1 = R5 / (2·gain)
- R1 ∥ R2 = 1 / (2Qω₀C)

Three resistors give three knobs: f₀, Q and gain. The script tries the nearest E96 values for each resistor and keeps the combination that hits f₀ and Q best.

**Design (chain order = lowest Q first; all caps C0G/NP0 ±5% 0603, all resistors 1%):**

| Stage | f₀ / Q (target) | R1 (in) | R2 (to VREF) | R5 (feedback) | C (both) | Gain @ f₀ |
|---|---|---|---|---|---|---|
| 1 | 30.0 kHz / 1.00 | 634 | 5.11k | 2.26k | 4.7 nF | 1.78 |
| 2 | 21.9 kHz / 1.30 | 665 | 5.49k | 4.02k | 4.7 nF | 3.02 |
| 3 | 41.0 kHz / 1.30 | 357 | 2.80k | 2.15k | 4.7 nF | 3.01 |
| 4 | 18.9 kHz / 3.59 | 8.25k | 1.37k | 60.4k | 1 nF | 3.66 |
| 5 | 47.7 kHz / 3.59 | 3.24k | 549 | 23.7k | 1 nF | 3.66 |

Every stage lands within 0.4% on f₀ and 1% on Q. **Only two capacitor values are needed (4.7 nF and 1 nF)**, which means only two extended parts at JLCPCB.

**LTspice (LT6233 model, `filter_sim/bp10_compare.cir`):**

| | Wizard (JSON 2) | Redesign |
|---|---|---|
| 25 / 30 / 35 / 40 kHz | 19.53 / 19.53 / 19.73 / 19.83 dB | **20.07 / 20.08 / 20.08 / 20.05 dB** |
| Peak | 19.95 dB @ 21.1 kHz | 20.08 dB (flat) |
| −3 dB band | 18.4–48.2 kHz | 18.6–48.4 kHz |
| 10 kHz / 90 kHz | −22.1 / −23.2 dB | −22.6 / −22.7 dB |

On the AD8608 (10 MHz quad, cheaper) the same values give 20.1–20.4 dB across 25–40 kHz, which is still fine.

> [!warning] Headroom inside the chain
> The stage-4 output peaks at **25.1 dB (18 V/V)** around 19 kHz, which is 5 dB above the final output. With ±1.6 V of swing around VREF, inputs above ~90 mV pk near 19 kHz clip inside the filter. The final output is clean up to ~160 mV pk input. The preamp can put out up to ±1.6 V, so either move the PGA in front of the filter or drop the preamp gain for close-range pings.

## Capacitors you can actually get (JLCPCB, checked 2026-10-27)
- **JLC "Basic" caps in this range are X7R ±10%** (e.g. 1 nF C1523, 4.7 nF C1538). These are where the "10%" comes from. **Don't use X7R in a filter.** It drifts about ±15% over temperature, loses capacitance under DC bias, and it's piezoelectric: on a sub full of thruster vibration it turns knocks into signal, inside the hydrophone chain.
- **C0G/NP0 ±5% is easy to get as an extended part.** For example, Yageo **CC0603JRNPO9BN472** (4.7 nF, 50 V, 0603) is **C576818**, with about 260k in stock at about $0.03. The FH 0402CG102J500NT (1 nF C0G ±5% 0402) is also stocked (~232k). Check the 1 nF part in 0603 from the same Yageo series (CC0603JRNPO9BN102) before ordering. Each unique extended part adds a small setup fee per order, and this design has only two.
- **±1% and ±2% C0G do exist at JLC, but only in 0805/1206, at low stock and 5–10× the price.** For example, CC0805FKNPO9BN472 (4.7 nF ±1%) is C541577 with ~8.5k in stock at ~$0.23. That's usable for a few boards if needed.
- PCBWay sources from distributors such as Digi-Key or Mouser or takes customer-supplied parts, so tolerance there is whatever you order.

## What 5% caps cost in channel matching (Monte Carlo, 500 runs)
Worst channel pair across a 4-hydrophone array, 95th percentile:

| Caps | Passband tilt 25→40 kHz | Phase / time mismatch at 30 kHz |
|---|---|---|
| Wizard design, 10% | ±0.66 dB | 15.8° / 1.46 µs |
| Redesign, 10% | ±0.60 dB | 16.8° / 1.56 µs |
| **Redesign, 5% C0G** | **±0.31 dB** | **8.7° / 0.80 µs** |
| Redesign, 2% C0G | ±0.14 dB | 3.6° / 0.34 µs |

![[bp10_montecarlo.png]]

**Fixing the mismatch in software instead of buying 1% caps:** C0G doesn't drift, so each channel's phase offset is fixed once the board is built. Calibrate it out once: feed the same signal (or a pinger at a known bearing) into all channels, measure each channel's delay at 25–40 kHz, and subtract it in the TDOA code. That turns 0.8 µs of hardware mismatch into a constant offset you remove for free. Note: 0.8 µs × 1500 m/s ≈ 1.2 mm of path difference. For a 2 cm hydrophone spacing that's about 3.4° of bearing error if left uncalibrated.

## Files
- `filter_sim/bp10_design.py`: the full analysis (stage errors, redesign search, Monte Carlo, plots). Its printed output is saved in `filter_sim/bp10_design_output.txt`.
- `filter_sim/bp10_compare.cir`: LTspice netlist for the Wizard design vs the redesign (LT6233 and AD8608). Run it with `LTspice.exe -b bp10_compare.cir`.
- `filter_sim/bp10_nominal.png`, `filter_sim/bp10_montecarlo.png`

See also [[Bandpass Filter Redesign - Simulation]] for the earlier 8th-order version.
