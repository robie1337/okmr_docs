"""8th-order version of bp10_design.py: four MFB stages so the filter fits one quad op amp.
Same spec (Butterworth, 30 kHz centre, 30 kHz -3 dB bandwidth, 20 dB), same stocked
C0G caps (1 / 2.2 / 4.7 nF) and 1% E96 resistors.

Run:  python bp8_design.py      (needs numpy + matplotlib, and bp10_design.py next to it)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import bp10_design as bp

bp.TARGET = bp.butter_bp_sections(order=8)
# one cap value for every stage: 2.2 nF C0G, stocked at JLCPCB in +-1% 0603
# (Yageo CC0603FRNPO9BN222 = C576780), +-2% (C576798) and +-5% (C107043)
bp.CAPS = [2.2e-9]
TARGET10 = bp.butter_bp_sections(order=10)


def stage_gains(target, total=10.0, margin=0.85):
    """Per-stage gain at its own f0. Water-fill: every stage gets the same gain x,
    capped at margin*2Q^2 (equal-C MFB limit), with x chosen so the chain gives
    `total` V/V at the centre frequency."""
    s = 2j * np.pi * bp.F0
    shape = 1.0
    for fk, qk in target:
        wk = 2 * np.pi * fk
        shape *= abs((s * wk / qk) / (s**2 + s * wk / qk + wk**2))
    need = total / shape
    caps = np.array([margin * 2 * q**2 for _, q in target])
    lo, hi = 1.0, need
    for _ in range(100):
        x = np.sqrt(lo * hi)
        if np.prod(np.minimum(caps, x)) < need:
            lo = x
        else:
            hi = x
    return np.minimum(caps, x)


def stage_peaks(stages):
    """Largest |gain| at each stage output (internal headroom check)."""
    h = np.ones_like(bp.w, dtype=complex)
    out = []
    for st in stages:
        h = h * bp.mfb(*st, 1j * bp.w)
        out.append(abs(h).max())
    return out


if __name__ == "__main__":
    print("8th-order Butterworth biquads (f0 Hz, Q):", bp.TARGET)
    gains = stage_gains(bp.TARGET)
    rser = bp.series(bp.E96)
    des = {}
    for i, ((fk, qk), g) in enumerate(zip(bp.TARGET, gains)):
        des[f"S{i+1}"] = bp.design_stage(fk, qk, g, rser)
    # chain order: lowest Q first
    order = sorted(des, key=lambda k: bp.f0_q(*des[k])[1])
    des = {k: des[k] for k in order}

    print("\nStages in chain order (R1 in, R2 to VREF, R5 feedback, C both):")
    for k, (R1, R2, R5, C, _) in des.items():
        fe, qe = bp.f0_q(R1, R2, R5, C, C)
        fi, qi = min(bp.TARGET, key=lambda t: abs(np.log(t[0] / fe)) + abs(np.log(t[1] / qe)))
        print(f"  {k}: R1 {R1:7.0f}  R2 {R2:7.0f}  R5 {R5:7.0f}  C {C*1e9:3.1f} nF | f0 {fe/1e3:6.2f} kHz ({100*(fe/fi-1):+.2f}%)  "
              f"Q {qe:4.2f} ({100*(qe/qi-1):+.1f}%)  gain {R5/2/R1:4.2f}")

    h8 = bp.chain(des.values())
    h8i = bp.ideal()
    bp.TARGET = TARGET10
    h10i = bp.ideal()
    bp.TARGET = bp.butter_bp_sections(order=8)
    print()
    bp.summarize("Ideal 8th-order", h8i)
    bp.summarize("Redesign 8th-order", h8)
    bp.summarize("Ideal 10th-order (ref)", h10i)
    for fx in [5e3, 10e3, 80e3, 90e3]:
        i = np.argmin(abs(bp.f - fx))
        print(f"  rejection at {fx/1e3:4.0f} kHz: 8th {20*np.log10(abs(h8[i])/10):6.1f} dB   10th {20*np.log10(abs(h10i[i])/10):6.1f} dB  (rel. to 20 dB passband)")
    print("  internal stage peaks (V/V):", " ".join(f"{p:.1f}" for p in stage_peaks(list(des.values()))))

    print("\nMonte Carlo (500 runs, 1% R, tol = 3 sigma). Phase = worst pair among 4 channels, 95th pct.")
    mc = {}
    for name, tc in [("8th, 10% C", 0.10), ("8th, 5% C0G", 0.05), ("8th, 2% C0G", 0.02), ("8th, 1% C0G", 0.01)]:
        full, mark = bp.monte_carlo(list(des.values()), 0.01, tc)
        mc[name] = full
        ph = np.degrees(np.unwrap(np.angle(mark), axis=0))
        rng = np.random.default_rng(7)
        spreads = np.array([np.ptp(ph[rng.choice(len(ph), 4, replace=False)], axis=0) for _ in range(400)])
        p95 = np.percentile(spreads, 95, axis=0)
        dbm = 20 * np.log10(abs(mark))
        tilt = dbm[:, 0] - dbm[:, 3]
        print(f"  {name:14s} 25k-40k tilt {tilt.mean():+5.2f} ± {tilt.std():4.2f} dB | "
              + " ".join(f"{fm/1e3:.0f}k {p:4.1f}° ({p/360/fm*1e6:4.2f} µs)" for fm, p in zip(bp.FMARK, p95)))

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    f = bp.f
    ax[0].semilogx(f / 1e3, 20 * np.log10(abs(h10i)), "k:", label="ideal 10th-order (ref)")
    ax[0].semilogx(f / 1e3, 20 * np.log10(abs(h8i)), "k--", label="ideal 8th-order")
    ax[0].semilogx(f / 1e3, 20 * np.log10(abs(h8)), "b-", label="8th-order redesign (C0G, E96)")
    ax[0].set_ylim(-40, 25); ax[0].set_ylabel("Gain (dB)"); ax[0].legend(fontsize=8)
    ax[0].set_title("8th vs 10th order")
    for h in mc["8th, 1% C0G"][:150]:
        ax[1].semilogx(f / 1e3, abs(h), color="tab:blue", alpha=.08)
    ax[1].semilogx(f / 1e3, abs(h8i), "k--")
    ax[1].set_ylabel("Gain (V/V)"); ax[1].set_title("8th-order, 1% R / 1% C0G (150 runs)")
    for a in ax:
        a.set_xlim(5, 150); a.set_xlabel("Frequency (kHz)"); a.grid(True, which="both", alpha=.3)
        a.axvspan(25, 40, color="g", alpha=.08)
    fig.tight_layout(); fig.savefig("bp8_design.png", dpi=130)
    print("\nSaved bp8_design.png")
