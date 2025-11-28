import json

TIME_PATH = "Matrix/Cheapest/time.json"
TRANSFERS_PATH = "Matrix/Cheapest/transfers.json"
OUT_PATH = "Matrix/Cheapest/time_plus_transfers.json"
ALPHA = 3.4

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    t = load(TIME_PATH)
    r = load(TRANSFERS_PATH)

    if t["stations"] != r["stations"]:
        raise SystemExit("Station order mismatch between the two JSON files.")

    T = t["matrix"]
    R = r["matrix"]
    n = len(t["stations"])

    if any(len(row) != n for row in T) or any(len(row) != n for row in R):
        raise SystemExit("Matrix size mismatch / not square.")

    M = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(0)
            else:
                row.append(float(T[i][j]) + ALPHA * float(R[i][j]))
        M.append(row)

    out = {
        "stations": t["stations"],
        "mode": t.get("mode", "fastest"),
        "metric": f"{t.get('metric','minutes')}+{ALPHA}*{r.get('metric','transfers')}",
        "date": t.get("date"),
        "time": t.get("time"),
        "alpha": ALPHA,
        "sources": {
            "time_file": TIME_PATH,
            "transfers_file": TRANSFERS_PATH
        },
        "matrix": M
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Saved -> {OUT_PATH}")

if __name__ == "__main__":
    main()
