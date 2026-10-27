---
tags: [hydrophone, analog, preamp, explainer]
created: 2026-10-04
---
# Hydrophone Preamp: How It Works

> [!info] Explainer video
> There is also a narrated Manim explainer of this circuit, about 7 minutes long. It is not committed here because it is 42 MB, so ask Mahmoud for a copy.

*Video visual code: **wire brightness = voltage**, **yellow dots = current**, **red + / blue − = charge on capacitor plates**, **yellow traces = the signal**.*

Reference sheet: [[Hydrophone Preamp - Labelled Diagram]] · Original schematic: ![[hydrophone_preamp_original_schematic.png]]

---

## 0. What the hydrophone gives you
A hydrophone is a piezoelectric ceramic. Each pressure wave squeezes it and puts **charge** on its electrodes, + on one face and − on the other. From a distant pinger that charge is only a few picocoulombs. It is far too small to digitise directly, and the cable and connector capacitance would swamp a plain voltage reading. The preamp's job is to turn that charge into a large voltage that is centred and clean.

## 1. Quiet state: DC bias
- Everything runs from **one 3.3 V supply**, so a signal can't go below 0 V.
- Every signal node therefore idles at **V<sub>REF</sub> ≈ 1.65 V**, halfway up, with room to swing both ways.
- Capacitors block DC. **C19** lets the hydrophone sit at 0 V while U5's input sits at 1.65 V. **C20** lets each stage keep its own resting point.

## 2. Block 1: input and protection (C19, D1, D2)
- C19 (1 nF) carries the AC signal in.
- D1 and D2 are guards that stay off for normal signals.
- If a spike (ESD, a knock on the hydrophone, hot-plugging the cable) pushes the node above **3.3 V + 0.6 V**, D1 conducts and dumps the surge into the 3.3 V rail.
- Below **−0.6 V**, D2 conducts and pulls current up from ground.
- U5's input never sees much beyond its supply rails.

## 3. Block 2: charge amplifier (U5, C18, R13)
Two op-amp rules make it work:
1. U5 moves its output however it must to keep **− input = + input = V<sub>REF</sub>** (a *virtual ground*).
2. Its inputs draw almost no current (pA range), so charge can't get into U5.

So charge that arrives through C19 has only one place to go: **onto C18**. To keep the − input at V<sub>REF</sub>, U5's output pulls an equal and opposite charge onto C18's far plate:

$$V_\text{out} = V_\text{REF} - \frac{Q}{C_{18}} \quad\Rightarrow\quad 1\ \text{pC} \rightarrow 1\ \text{mV (inverted)}$$

**R13 (1 MΩ)** slowly bleeds C18's charge, which gives the stage a DC path and stops it drifting into a rail. Slow changes fade out:

$$f_{L1} = \frac{1}{2\pi R_{13} C_{18}} = \frac{1}{2\pi \cdot 1\,\text{M}\Omega \cdot 1\,\text{nF}} \approx 159\ \text{Hz}$$

> [!note] The real stage-1 gain depends on the hydrophone
> The *Q* in the formula is the charge that actually crosses C19. If you model the hydrophone as a source $V_s$ in series with its capacitance $C_h$ (cable included), then mid-band:
> $$\frac{V_\text{out}}{V_s} = -\frac{C_{eq}}{C_{18}}, \qquad C_{eq} = \frac{C_h C_{19}}{C_h + C_{19}}$$
> If $C_h \gg 1$ nF the gain is ≈ −1 (the Bode plot assumes this). With $C_h$ = 3 nF it is about −0.75. In charge terms, only $C_{19}/(C_h + C_{19})$ of the hydrophone's charge reaches C18, so C19 trades some sensitivity for DC isolation. **Look up the hydrophone's capacitance** to pin this down.

## 4. Block 3: high-pass coupling (C20, R15)
- A **slow drift** gives C20 time to charge up and follow it, so the far side barely moves. R15 holds that side at V<sub>REF</sub>. Slow drift is blocked.
- A **fast signal** is too quick for C20 to follow, so it passes straight through.
- Corner: $f = 1/(2\pi \cdot 22\,\text{k}\Omega \cdot 220\,\text{nF}) \approx 33$ Hz.
- Result: U5's DC offset, cable thumps and low-frequency rumble are removed, and the signal is freshly centred on V<sub>REF</sub> for U4.

## 5. Block 4: gain stage (U4, R14, R16, C17)
- Non-inverting amplifier. R14 and R16 split the output swing **51 : 1**, and only the R16 slice reaches the − input.
- For that 1/52 slice to equal the input, the output must swing 52× bigger:

$$G = 1 + \frac{R_{14}}{R_{16}} = 1 + \frac{51\,\text{k}\Omega}{1\,\text{k}\Omega} = 52 \;(34.3\ \text{dB})$$

- R16 returns to **V<sub>REF</sub>**, not ground, so the ×52 applies only to the signal around 1.65 V and the output still idles at 1.65 V.
- **C17 (10 pF)** acts like a short across R14 at high frequency, so the gain sinks back toward 1 above ~312 kHz. Together with U4's 10 MHz gain-bandwidth (10 MHz / 52 ≈ 192 kHz), the band ends near **119 kHz**. This limits noise and keeps the stage stable.

## 6. Whole chain: frequency response
In decibels, cascaded stages simply **add**:

| Block | Response |
|---|---|
| Charge amp | 0 dB mid-band, high-pass at 159 Hz |
| C20/R15 | 0 dB mid-band, high-pass at 33 Hz |
| Gain stage | 34.3 dB, rolls off above ~120–190 kHz |
| **Total** | **34.3 dB (×52) from ≈166 Hz to ≈119 kHz** |

Typical AUV pingers (25–40 kHz, e.g. RoboSub-style) land on the flat top: full gain, with less than 0.5 dB variation across the band.

## 7. Practical checks
- [ ] Confirm V<sub>REF</sub> (divider + buffer? its own decoupling?). R15 and R16 both return to V<sub>REF</sub>, so V<sub>REF</sub> noise mostly cancels in U4 (+52 through R15, −51 through R16, net ≈ 1). That only holds if both really connect to the same well-decoupled node.
- [ ] Hydrophone + cable capacitance → real stage-1 gain (see the note above).
- [ ] Output headroom: about ±1.6 V around V<sub>REF</sub>, so input at U4 above ~30 mV<sub>pk</sub> will clip. Close pingers may need gain switching or the filter [1B] stage to handle overload.
- [ ] Probe tip: measure at C20's far side (R15 node) to see the clean stage-1 output already centred on V<sub>REF</sub>.
