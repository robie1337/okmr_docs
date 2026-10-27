"""10th-order Butterworth bandpass (30 kHz centre, 30 kHz -3 dB bandwidth) built from
five MFB (Deliyannis-Friend) stages.

1. Reproduces the Filter Wizard design from "Updated 8th Order Filter Design  (2).json"
2. Explains its lopsided response (stage f0/Q errors from E12 caps + E24 resistors)
3. Re-designs it with capacitors that JLCPCB/LCSC actually stock (C0G, E6 values)
   and E24 1% resistors, choosing the resistor triple per stage that hits f0 and Q
   (letting each stage's gain float)
4. Monte Carlo with realistic tolerances: gain shape + channel-to-channel phase

Run:  python bp10_design.py      (needs numpy + matplotlib)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

F0, BW, ORDER = 30e3, 30e3, 10
f = np.logspace(np.log10(2e3), np.log10(300e3), 3000)
w = 2 * np.pi * f
FMARK = [25e3, 30e3, 35e3, 40e3]


# ---------- MFB stage -------------------------------------------------------
def mfb(R1, R2, R5, Ca, Cb, s):
    """Inverting MFB bandpass, ideal op amp. R1 in, R2 node->VREF (None = absent),
    R5 feedback, Ca node->out, Cb node->inverting input."""
    G = 1 / R1 + (0 if R2 is None else 1 / R2)
    return -(s * Cb * R5 / R1) / (G + s * (Ca + Cb) + s**2 * Ca * Cb * R5)


def f0_q(R1, R2, R5, Ca, Cb):
    G = 1 / R1 + (0 if R2 is None else 1 / R2)
    w0 = np.sqrt(G / (R5 * Ca * Cb))
    return w0 / 2 / np.pi, w0 * R5 * Ca * Cb / (Ca + Cb)


def chain(stages, s=1j * w):
    h = np.ones_like(s)
    for st in stages:
        h = h * mfb(*st, s)
    return h


# ---------- ideal Butterworth target ---------------------------------------
def butter_bp_sections(order=ORDER, f0=F0, bw=BW):
    n = order // 2
    k = np.arange(n)
    p_lp = np.exp(1j * np.pi * (2 * k + n + 1) / (2 * n))  # LP poles, unit circle
    w0, b = 2 * np.pi * f0, 2 * np.pi * bw
    poles = []
    for p in p_lp:
        disc = np.sqrt((p * b) ** 2 - 4 * w0**2 + 0j)
        poles += [(p * b + disc) / 2, (p * b - disc) / 2]
    secs = sorted({(round(abs(p) / 2 / np.pi, 3), round(abs(p) / (-2 * p.real), 4))
                   for p in poles if p.imag > 0})
    return secs  # (f0, Q) per biquad


TARGET = butter_bp_sections()


def ideal(s=1j * w, gain=10.0):
    """Ideal Butterworth, scaled to `gain` V/V at the 30 kHz centre."""
    def raw(s):
        h = np.ones_like(s)
        for fk, qk in TARGET:
            wk = 2 * np.pi * fk
            h = h * (s * wk / qk) / (s**2 + s * wk / qk + wk**2)
        return h
    return gain * raw(s) / abs(raw(np.array([2j * np.pi * F0]))[0])


# ---------- Filter Wizard design (JSON (2), read from the Wizard 2026-10-27) -
# order in the chain: D, A, C, B, E.  (R1, R2-to-VREF, R5, Ca, Cb)
WIZ = {
    "D": (360, None, 2.4e3, 3.9e-9, 4.7e-9),
    "A": (300, None, 1.5e3, 4.7e-9, 12e-9),
    "C": (1e3, 160, 7.5e3, 8.2e-9, 8.2e-9),
    "B": (1e3, 160, 7.5e3, 3.3e-9, 3.3e-9),
    "E": (1e3, 620, 2.4e3, 8.2e-9, 8.2e-9),
}

# ---------- re-design with stocked parts ----------------------------------
E24 = np.array([1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
                3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1])
E96 = np.round(10 ** (np.arange(96) / 96), 2)
# C0G/NP0 +-5% 0603 values (Yageo CC0603JRNPO9BN... at JLCPCB/LCSC, e.g. 4.7 nF = C576818)
CAPS = [1e-9, 2.2e-9, 4.7e-9]
# Per-stage gain at its OWN f0. The off-centre stages only give part of that at 30 kHz,
# so the product has to be ~216 for 10 V/V (20 dB) at 30 kHz -- same as the Wizard's.
# Equal-C MFB limit is gain < 2Q^2 (2 for Q=1, 3.4 for Q=1.3, 25 for Q=3.6).
STAGE_GAIN = {0: 3.65, 1: 3.0, 2: 1.8, 3: 3.0, 4: 3.65}


def series(base, lo=100, hi=200e3):
    v = np.concatenate([base * 10**d for d in range(1, 6)])
    return v[(v >= lo) & (v <= hi)]


def design_stage(f0, q, gain, rser):
    """Equal-C 3-resistor MFB:  R5 = 2Q/(w0 C),  R1 = R5/(2 gain),  R1||R2 = 1/(2 Q w0 C).
    Try every stocked cap and the nearest series values of R5, R1, R2; keep the
    combination with the smallest f0 + Q error (gain error weighted lightly)."""
    best = None
    w0 = 2 * np.pi * f0
    for C in CAPS:
        R5x = 2 * q / (w0 * C)
        Rpx = 1 / (2 * q * w0 * C)
        R1x = R5x / (2 * gain)
        if not (1e3 <= R5x <= 100e3 and Rpx >= 250 and R1x > Rpx):  # sane impedances
            continue
        near = lambda x, k: rser[np.argsort(abs(np.log(rser / x)))[:k]]
        for R5 in near(R5x, 6):
            for R1 in near(R1x, 6):
                g2x = 1 / Rpx - 1 / R1
                if g2x <= 0:
                    continue
                for R2 in near(1 / g2x, 6):
                    fe, qe = f0_q(R1, R2, R5, C, C)
                    err = (abs(np.log(fe / f0)) + 0.5 * abs(np.log(qe / q))
                           + 0.05 * abs(np.log(R5 / (2 * R1) / gain)))
                    if best is None or err < best[0]:
                        best = (err, (R1, R2, R5, C, C))
    return best[1]


def redesign(rser):
    st = {f"S{i+1}": design_stage(fk, qk, STAGE_GAIN[i], rser) for i, (fk, qk) in enumerate(TARGET)}
    # chain order: lowest Q first, highest-Q (most peaky) stages last
    return {k: st[k] for k in ["S3", "S2", "S4", "S1", "S5"]}


# ---------- Monte Carlo ----------------------------------------------------
def monte_carlo(stages, tol_r, tol_c, n=500, seed=1):
    rng = np.random.default_rng(seed)
    sm = 1j * 2 * np.pi * np.array(FMARK)
    out_full, out_mark = [], []
    for _ in range(n):
        st2 = []
        for (R1, R2, R5, Ca, Cb) in stages:
            r = 1 + rng.normal(0, tol_r / 3, 3)
            c = 1 + rng.normal(0, tol_c / 3, 2)
            st2.append((R1 * r[0], None if R2 is None else R2 * r[1], R5 * r[2], Ca * c[0], Cb * c[1]))
        out_full.append(chain(st2))
        out_mark.append(chain(st2, sm))
    return np.array(out_full), np.array(out_mark)


def summarize(name, h):
    db = 20 * np.log10(abs(h))
    pk = db.max()
    band = f[db >= pk - 3]
    m = {fm: db[np.argmin(abs(f - fm))] - pk for fm in [20e3, 25e3, 30e3, 35e3, 40e3, 45e3]}
    print(f"{name:28s} peak {pk:5.1f} dB @ {f[db.argmax()]/1e3:5.1f} kHz | -3 dB {band[0]/1e3:5.1f}-{band[-1]/1e3:5.1f} kHz | "
          + " ".join(f"{k/1e3:.0f}k:{v:+5.1f}" for k, v in m.items()))


if __name__ == "__main__":
    print("Ideal Butterworth biquads (f0 Hz, Q):", TARGET)
    print("\nWizard stages: f0 / Q   vs ideal")
    for k, st in WIZ.items():
        fe, qe = f0_q(*st)
        fi, qi = min(TARGET, key=lambda t: abs(np.log(t[0] / fe)) + abs(np.log(t[1] / qe)))
        print(f"  {k}: {fe/1e3:6.2f} kHz Q {qe:4.2f}   ideal {fi/1e3:6.2f} kHz Q {qi:4.2f}   f0 err {100*(fe/fi-1):+5.1f}%  Q err {100*(qe/qi-1):+5.1f}%")

    h_id = ideal()  # 20 dB
    h_wiz = chain(WIZ.values())
    new24 = redesign(series(E24))
    new96 = redesign(series(E96))
    h24, h96 = chain(new24.values()), chain(new96.values())

    print()
    summarize("Ideal Butterworth", h_id)
    summarize("Wizard (E12 C, E24 R)", h_wiz)
    summarize("Redesign, E24 R + E6 C0G", h24)
    summarize("Redesign, E96 R + E6 C0G", h96)

    for tag, des in [("E24", new24), ("E96", new96)]:
        print(f"\nRedesign {tag} resistors (R1 in, R2 to VREF, R5 feedback, C both):")
        for k, (R1, R2, R5, C, _) in des.items():
            fe, qe = f0_q(R1, R2, R5, C, C)
            print(f"  {k}: R1 {R1:8.0f}  R2 {R2:7.0f}  R5 {R5:8.0f}  C {C*1e9:4.1f} nF   f0 {fe/1e3:6.2f} kHz  Q {qe:4.2f}  gain {R5/2/R1:5.2f}")
        print(f"  total mid-band gain {20*np.log10(abs(chain(des.values(), np.array([2j*np.pi*F0]))[0])):.1f} dB")

    print("\nMonte Carlo (500 runs, normal, tol = 3 sigma). Phase = worst pair among 4 channels, 95th percentile.")
    mc_cases = [("Wizard, 1% R / 10% C", list(WIZ.values()), 0.01, 0.10),
                ("Redesign E24, 1% R / 10% C", list(new24.values()), 0.01, 0.10),
                ("Redesign E24, 1% R / 5% C0G", list(new24.values()), 0.01, 0.05),
                ("Redesign E24, 1% R / 2% C0G", list(new24.values()), 0.01, 0.02),
                ("Redesign E96, 1% R / 5% C0G", list(new96.values()), 0.01, 0.05)]
    mc_results = {}
    for name, st, tr, tc in mc_cases:
        full, mark = monte_carlo(st, tr, tc)
        mc_results[name] = full
        ph = np.degrees(np.unwrap(np.angle(mark), axis=0))
        rng = np.random.default_rng(7)
        spreads = np.array([np.ptp(ph[rng.choice(len(ph), 4, replace=False)], axis=0) for _ in range(400)])
        p95 = np.percentile(spreads, 95, axis=0)
        dbm = 20 * np.log10(abs(mark))
        tilt = dbm[:, 0] - dbm[:, 3]  # 25k minus 40k
        print(f"  {name:30s} 25k-40k tilt {tilt.mean():+5.2f} ± {tilt.std():4.2f} dB | "
              + " ".join(f"{fm/1e3:.0f}k {p:4.1f}° ({p/360/fm*1e6:4.2f} µs)" for fm, p in zip(FMARK, p95)))

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    for h, lab, sty in [(h_id, "Ideal Butterworth", "k--"), (h_wiz, "Wizard (E12 C, E24 R)", "r-"),
                        (h96, "Redesign (C0G 1n/4.7n, E96 R)", "b-")]:
        ax[0].semilogx(f / 1e3, abs(h), sty, label=lab)
        ax[1].plot(f / 1e3, abs(h), sty, label=lab)
    for a in ax:
        a.set_xlabel("Frequency (kHz)"); a.set_ylabel("Gain (V/V)"); a.grid(True, which="both", alpha=.3)
        a.axvspan(25, 40, color="g", alpha=.08, label="pinger band")
    ax[0].set_xlim(5, 150); ax[0].set_title("Log frequency axis"); ax[0].legend(fontsize=8)
    ax[1].set_xlim(0, 100); ax[1].set_title("Linear frequency axis")
    fig.tight_layout(); fig.savefig("bp10_nominal.png", dpi=130)

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    for a, name in zip(ax, ["Wizard, 1% R / 10% C", "Redesign E96, 1% R / 5% C0G"]):
        for h in mc_results[name][:150]:
            a.semilogx(f / 1e3, abs(h), color="tab:blue", alpha=.08)
        a.semilogx(f / 1e3, abs(h_id), "k--", label="ideal")
        a.axvspan(25, 40, color="g", alpha=.08)
        a.set_xlim(5, 150); a.set_title(name + " (150 runs)"); a.set_xlabel("Frequency (kHz)"); a.grid(True, which="both", alpha=.3)
    ax[0].set_ylabel("Gain (V/V)")
    fig.tight_layout(); fig.savefig("bp10_montecarlo.png", dpi=130)
    print("\nSaved bp10_nominal.png, bp10_montecarlo.png")
