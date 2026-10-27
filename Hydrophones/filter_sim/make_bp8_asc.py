"""Writes Hydrophone_8th_Order_Quad_Filter.asc: the 8th-order bandpass (4 MFB stages on an
AD8608 quad, all caps 2.2 nF) as an LTspice schematic.  Run: python make_bp8_asc.py"""

STAGES = [  # (label, note, R1 in, R2 to VREF, R5 feedback)
    ("A", "37.1 kHz, Q 1.11", "1.05k", "5.49k", "4.32k"),
    ("B", "24.2 kHz, Q 1.11", "1.58k", "8.87k", "6.65k"),
    ("C", "47.2 kHz, Q 2.89", "909", "374", "8.87k"),
    ("D", "19.0 kHz, Q 2.91", "2.32k", "909", "22.1k"),
]
NETS = ["in", "s1", "s2", "s3", "out"]
C = "2.2n"
PITCH = 768

wires, flags, syms, texts = [], [], [], []


def W(x1, y1, x2, y2):
    assert x1 == x2 or y1 == y2, "diagonal wire"
    wires.append(f"WIRE {x1} {y1} {x2} {y2}")


def F(x, y, name):
    flags.append(f"FLAG {x} {y} {name}")


def S(sym, x, y, rot, name, value, windows=()):
    syms.append(f"SYMBOL {sym} {x} {y} {rot}")
    syms.extend(windows)
    syms.append(f"SYMATTR InstName {name}")
    if value is not None:
        syms.append(f"SYMATTR Value {value}")


# ---- sources (left) ----
for i, (name, val, plus, minus) in enumerate([("V1", "AC 1", "in", "VREF"),
                                               ("Vref", "1.65", "VREF", "0"),
                                               ("Vdd", "3.3", "VDD", "0")]):
    vx = -1024 + i * 144
    S("voltage", vx, -80, "R0", name, val)
    W(vx, -64, vx, -112); F(vx, -112, plus)   # + pin (vx,-64)
    W(vx, 16, vx, 64); F(vx, 64, minus)       # - pin (vx,16)

# ---- four MFB stages ----
for k, (lab, note, r1, r2, r5) in enumerate(STAGES):
    X = -256 + k * PITCH  # local x=0 is the op amp's In- pin
    nin, nout = NETS[k], NETS[k + 1]
    # op amp AD8608 at (X+32, -48): In-(X,0) In+(X,32) V+(X+32,-16) V-(X+32,48) OUT(X+64,16)
    S("OpAmps\\\\AD8608", X + 32, -48, "R0", f"U{lab}", None)
    W(X + 32, -16, X + 32, -64); F(X + 32, -64, "VDD")
    W(X + 32, 48, X + 32, 96); F(X + 32, 96, "0")
    W(X, 32, X - 64, 32); W(X - 64, 32, X - 64, 96); F(X - 64, 96, "VREF")
    # inverting node: In- (X,0) <- junction (X-48,0) <- Cb A (X-96,0)
    W(X, 0, X - 48, 0); W(X - 48, 0, X - 96, 0)
    S("cap", X - 96, -16, "R90", f"Cb{lab}", C)            # A (X-96,0)  B (X-160,0)
    # node n1 at (X-224,0)
    W(X - 160, 0, X - 224, 0)
    S("res", X - 256, -16, "R90", f"R1{lab}", r1)          # A (X-272,0) B (X-352,0)
    W(X - 272, 0, X - 224, 0)
    W(X - 352, 0, X - 400, 0); F(X - 400, 0, nin)
    S("res", X - 240, 32, "R0", f"R2{lab}", r2)            # A (X-224,48) B (X-224,128)
    W(X - 224, 0, X - 224, 48)
    W(X - 224, 128, X - 224, 176); F(X - 224, 176, "VREF")
    S("cap", X - 240, -112, "R0", f"Ca{lab}", C)           # A (X-224,-112) B (X-224,-48)
    W(X - 224, -48, X - 224, 0)
    W(X - 224, -112, X - 224, -224); W(X - 224, -224, X + 144, -224)
    # R5 from the inverting node to the output, above the op amp
    W(X - 48, 0, X - 48, -144); W(X - 48, -144, X + 16, -144)
    S("res", X + 112, -160, "R90", f"R5{lab}", r5)         # A (X+96,-144) B (X+16,-144)
    W(X + 96, -144, X + 144, -144)
    W(X + 144, -224, X + 144, -144); W(X + 144, -144, X + 144, 16)
    # output
    W(X + 64, 16, X + 144, 16); W(X + 144, 16, X + 208, 16); F(X + 208, 16, nout)
    texts.append(f"TEXT {X - 352} -288 Left 2 ;Stage {lab}: {note}")

y = 288
for line in [";Hydrophone 8th-order Butterworth bandpass, 30 kHz centre, 30 kHz BW, 20 dB. One AD8608 quad, all caps 2.2 nF C0G 1%, resistors 1% E96.",
             "!.ac dec 400 1k 1Meg",
             "!.meas AC pk MAX mag(V(out))",
             "!.meas AC f_lo WHEN mag(V(out))=pk/sqrt(2) CROSS=1",
             "!.meas AC f_hi WHEN mag(V(out))=pk/sqrt(2) CROSS=LAST",
             "!.meas AC g25k FIND mag(V(out)) AT 25k",
             "!.meas AC g30k FIND mag(V(out)) AT 30k",
             "!.meas AC g40k FIND mag(V(out)) AT 40k"]:
    texts.append(f"TEXT -1056 {y} Left 2 {line}")
    y += 32

out = ["Version 4.1", "SHEET 1 2880 640"] + wires + flags + syms + texts
open("Hydrophone_8th_Order_Quad_Filter.asc", "w", encoding="latin-1", newline="\n").write("\n".join(out) + "\n")
print("wrote", len(wires), "wires,", len(syms), "symbol lines")
