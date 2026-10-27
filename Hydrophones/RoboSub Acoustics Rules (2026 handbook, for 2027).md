---
date: 2026-10-27
tags: [hydrophone, robosub, rules, pinger]
source: RoboSub 2026 Team Handbook (GitBook, updated 2026-06-11)
---
# RoboSub acoustics rules (2026 handbook, for 2027)

> [!warning] 2027 rules aren't out yet
> RoboSub 2027 is **10–15 Aug 2027**, Woollett Aquatics Center, Irvine CA. The 2027 Team Handbook is still marked "coming soon", and registration opens **1 Dec 2026**. RoboNation calls 2027 a pilot of "the next evolution of RoboSub", so the tasks may change. Everything below comes from the **2026 handbook**. Re-check it once the 2027 version is published.

## Pingers (handbook 5.4.3)
- Model: **Teledyne Benthos ALP-365**. These are out of production and RoboNation is looking for a replacement, so the pinger hardware may change for 2027.
- Frequency: chosen from **25–40 kHz in 0.5 kHz steps**
- Pulse rate: **0.5–2 Hz** (several settings are available)
- Ping duration and source level are not in the handbook. Check the [Benthos locator spec sheet](https://robonation.org/app/uploads/sites/2/2021/06/Teledyne-Benthos-Locator-RobotX2022.pdf).
- The pool has 4 course sections (A–D) with at least one pinger in each. **Only one pinger per section pings at a time.**
- Active pingers are **at least 2 kHz apart** and pulse **in sequence across courses**. Example: A 30, B 40, C 25, D 35 kHz.
- Frequencies and pulse rates **can change daily** and are given to teams on site.

## Tasks that use the pinger (3.2, 4.2.1)
Two navigation pingers. Each sits "very close to the task", either next to it or in the centre. You get no points just for finding a pinger.

| Task | Where the pinger is | Points |
|---|---|---|
| **Restore (Octagon)** | On the floor near the centre of the 9 ft (2.7 m) floating octagon | Surface in area 800; facing image 200/400/700; surface with object 400 each; drop object 200 each; basket 500 any / 700 correct each; basket count 500 (±1) / 1000 (correct) |
| **Deploy (Torpedoes)** | At the torpedo task | Any opening 600 per torpedo (max 2); correct sequence 1400; far 200 / farther 400 per torpedo |

- **Random pinger bonus:** 500 points for the first task, 1500 for the second.
- The team lead can ask for a specific pinger and switch it as often as they like during a run.

## Rules that affect the vehicle (5.3)
- **5.3.2:** acoustic frequencies inside the pinger band can never be used for sub-to-sub communication.
- **5.3.1:** no communication with people or off-board computers during a run. All acoustic processing has to run on board.
- No rules on passive-only hydrophones or active sonar turned up in the sections read.

## What this means for our hydrophone chain
- **The analog band is right.** The redesigned bandpass ([[Bandpass Filter Redesign - Simulation]]) is flat at ±0.2 dB from 20.0 to 44.4 kHz, which covers 25–40 kHz with margin. The current board (−3 dB at 32.4–42.8 kHz) loses about 16 dB at 25 kHz, so a section-C pinger at 25 kHz would come in very weak.
- **The analog filter can't pick the pinger.** Every pinger is inside the passband, so selecting one (≥2 kHz apart, set on the day) has to happen **digitally**, with a narrow band or FFT bin on the FPGA/MCU around a frequency set at runtime. The frequency has to be **configurable without reflashing**, because it can change daily.
- **Timing:** pinging in sequence at 0.5–2 Hz means up to ~2 s between pings. The software needs to gate on ping detection, not assume a continuous tone.
- **Channel matching matters**, because direction comes from arrival-time differences (TDOA). The Monte Carlo result (1% R + 1% C0G caps → ~0.5 µs worst pair at 30 kHz) supports the C0G choice.
- **Close-range overload:** near the octagon the pinger is very loud. The preamp clips above ~30 mV pk at U4, so the PGA (LTC6910) gain has to step down as the sub gets closer.

## Club hydrophone repos (for reference)
- [Cascade_hydrophones](https://github.com/Okanagan-Marine-Robotics/Cascade_hydrophones): processing system on a Zynq SoC, with Verilog HDL (Vivado 2024.2), C firmware (Vitis) and MATLAB test programs. The README says both HDL and firmware are a "working prototype, 90% done".
- [HydroZynqDriver](https://github.com/Okanagan-Marine-Robotics/HydroZynqDriver): a single Jupyter notebook (`HydroZynq.ipynb`)

## Sources
- [robosub.org/programs/2027](https://robosub.org/programs/2027/)
- [RoboSub 2026 handbook (GitBook)](https://robonation.gitbook.io/robosub-resources): 1.1, 3.2.5/3.2.6/3.2.9, 4.2.1, 5.3.1/5.3.2, 5.4.3
- [2026 handbook PDF](https://robonation.org/app/uploads/sites/4/2026/07/RoboSub-2026_Team-Handbook_20260711-compressed.pdf)
