# Hydrophones

Acoustic pinger localisation for the AUV: the analog front end (preamp → 8th-order bandpass → PGA → ADC), filter simulations, and the RoboSub pinger rules that drive the design.

## Notes
- [[RoboSub Acoustics Rules (2026 handbook, for 2027)]]: pinger specs (25–40 kHz, 0.5 kHz steps, 0.5–2 Hz), which tasks use them, points, and what that means for the hardware and software
- [[Hydrophone Preamp - Labelled Diagram]]: one-page reference for the preamp. Every part and key number (×52, 34.3 dB, ≈166 Hz–119 kHz)
- [[Hydrophone Preamp - How It Works]]: block-by-block walkthrough of the charge amp, high-pass and gain stage
- [[Bandpass Filter Redesign - Simulation]]: redesign of the [1B] filter to a flat 20–45 kHz Butterworth, LTspice results and channel-matching Monte Carlo

## Files
- `Attachments/`: original preamp schematic and the labelled reference diagram
- `filter_sim/`: LTspice schematics (`.asc`, open and press Run), batch netlists (`.cir`, run with `LTspice.exe -b <file>`), result plots, and the Analog Devices Filter Wizard settings (`filter_wizard_spec.json`, `filter_wizard_final.json`)

## Key takeaways
1. The current board's bandpass is 32.4–42.8 kHz at −3 dB, so a 25 kHz pinger arrives about 16 dB down. The redesign is flat (±0.2 dB) from 20 to 44 kHz.
2. The filter needs a ≥10 MHz GBW quad op amp (AD8608). On the MCP6L04 (1 MHz) the response distorts.
3. Use 1% C0G capacitors in the filter so channel-to-channel phase stays matched for TDOA (~0.5 µs worst pair at 30 kHz).
4. Every RoboSub pinger is inside the analog passband, so selecting the pinger has to happen digitally, at a frequency set at runtime (it can change daily).

## Related repos
- [Cascade_hydrophones](https://github.com/Okanagan-Marine-Robotics/Cascade_hydrophones): Zynq processing HDL + firmware
- [HydroZynqDriver](https://github.com/Okanagan-Marine-Robotics/HydroZynqDriver)

## Open questions
- The real V<sub>REF</sub> source (the notes assume 1.65 V)
- Hydrophone + cable capacitance, which sets the true stage-1 gain
- The 2027 handbook isn't published yet, so re-check the pinger specs when it is
