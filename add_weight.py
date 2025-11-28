import json
from decimal import Decimal, ROUND_HALF_UP

T_PATH = "Matrix/Fastest/time_plus_transfers.json"
C_PATH = "Matrix/Fastest/cost.json"
R_PATH = "Matrix/Fastest/transfers.json"

ALPHA, BETA, GAMMA = 0.8, 0.2, 0.2
OUT_PATH = "Matrix/recommended_weighted_normalized.json"

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def max_offdiag(M):
    m = None
    n = len(M)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            v = M[i][j]
            if v is None:
                continue
            v = float(v)
            if m is None or v > m:
                m = v
    if m is None or m == 0:
        raise ValueError("Matrix has no non-diagonal numeric values (or max is 0).")
    return m

def round_sig_decimal(x: Decimal, sig=3):
    if x == 0:
        return Decimal("0")
    exp = x.adjusted()
    quant = Decimal("1e{}".format(exp - sig + 1))
    return x.quantize(quant, rounding=ROUND_HALF_UP)

def bmatrix(mat):
    rows = ["  " + " & ".join(f"{x:g}" for x in row) + r" \\" for row in mat]
    return "\\begin{bmatrix}\n" + "\n".join(rows) + "\n\\end{bmatrix}"

def main():
    Tj, Cj, Rj = load(T_PATH), load(C_PATH), load(R_PATH)
    if not (Tj["stations"] == Cj["stations"] == Rj["stations"]):
        raise SystemExit("Station order mismatch across T/C/R.")

    stations = Tj["stations"]
    T, C, R = Tj["matrix"], Cj["matrix"], Rj["matrix"]
    n = len(stations)

    tmax, cmax, rmax = max_offdiag(T), max_offdiag(C), max_offdiag(R)

    W = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                W[i][j] = 0.0
                continue

            tn = Decimal(str(float(T[i][j]) / tmax))
            cn = Decimal(str(float(C[i][j]) / cmax))
            rn = Decimal(str(float(R[i][j]) / rmax))

            w = Decimal(str(ALPHA))*tn + Decimal(str(BETA))*cn + Decimal(str(GAMMA))*rn
            W[i][j] = float(round_sig_decimal(w, 3))

    out = {
        "stations": stations,
        "mode": "fastest",
        "metric": "alpha*T_norm + beta*C_norm + gamma*R_norm (3sf)",
        "date": Tj.get("date"),
        "time": Tj.get("time"),
        "weights": {"alpha": ALPHA, "beta": BETA, "gamma": GAMMA},
        "max": {"T": tmax, "C": cmax, "R": rmax},
        "sources": {"T": T_PATH, "C": C_PATH, "R": R_PATH},
        "matrix": W,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved -> {OUT_PATH}\n")

    # LaTeX
    print(r"\[")
    print(
        rf"\tilde{{M}}_{{ij}} = {ALPHA}\frac{{T_{{ij}}}}{{\max(T)}} + "
        rf"{BETA}\frac{{C_{{ij}}}}{{\max(C)}} + {GAMMA}\frac{{R_{{ij}}}}{{\max(R)}}"
    )
    print(r"\]")
    print("% Station order:")
    print("% " + ", ".join(stations))
    print(r"\[")
    print(bmatrix(W))
    print(r"\]")

if __name__ == "__main__":
    main()
