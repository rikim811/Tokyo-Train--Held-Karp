import json
import glob
import os

V = 900  # yen per hour saved threshold

FILES = {
    "FC": "Matrix/Fastest/cost.json",
    "CC": "Matrix/Cheapest/cost.json",
    "FT": "Matrix/Fastest/time_plus_transfers.json",
    "CT": "Matrix/Cheapest/time_plus_transfers.json",
    "FR": "Matrix/Fastest/transfers.json",
    "CR": "Matrix/Cheapest/transfers.json",  # optional but recommended
}

OUT = {
    "EC": "Matrix/Efficient/cost.json",
    "ET": "Matrix/Efficient/time_plus_transfers.json",
    "ER": "Matrix/Efficient/transfers.json",
}

def load_matrix(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d["stations"], d["matrix"], d

def dump_matrix(path, stations, matrix, meta):
    out = {
        "stations": stations,
        **meta,
        "matrix": matrix,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

def safe_float(x):
    if x is None:
        return None
    return float(x)

def delete_old_outputs():
    # adjust patterns if you want stricter/looser deletion
    patterns = [
        "./Matrix/efficiency_*.json",
        "./Matrix/efficient_*.json",
    ]
    deleted = 0
    for pat in patterns:
        for p in glob.glob(pat):
            try:
                os.remove(p)
                deleted += 1
            except FileNotFoundError:
                pass
    print(f"Deleted {deleted} old output file(s).")

def main():
    delete_old_outputs()

    # Load required matrices
    st_fc, FC, meta_fc = load_matrix(FILES["FC"])
    st_cc, CC, meta_cc = load_matrix(FILES["CC"])
    st_ft, FT, meta_ft = load_matrix(FILES["FT"])
    st_ct, CT, meta_ct = load_matrix(FILES["CT"])
    st_fr, FR, meta_fr = load_matrix(FILES["FR"])

    # Cheapest transfers is optional
    CR = None
    meta_cr = {}
    if os.path.exists(FILES["CR"]):
        st_cr, CR, meta_cr = load_matrix(FILES["CR"])
    else:
        print("Warning: cheapest_transfers.json not found -> transfers will remain fastest.")

    # Station order checks
    stations = st_fc
    if not (stations == st_cc == st_ft == st_ct == st_fr):
        raise SystemExit("Station order mismatch across fastest/cheapest files.")
    if CR is not None and st_cr != stations:
        raise SystemExit("Station order mismatch in cheapest_transfers.json.")

    n = len(stations)

    # Start by copying FASTEST into EFFICIENT
    EC = [row[:] for row in FC]
    ET = [row[:] for row in FT]
    ER = [row[:] for row in FR]  # replaced only if cheapest transfers exists

    switched = 0
    switched_pairs = []  # optional: keep log

    for i in range(n):
        for j in range(n):
            if i == j:
                # keep diagonals clean
                EC[i][j] = 0
                ET[i][j] = 0
                ER[i][j] = 0
                continue

            fc = safe_float(FC[i][j])
            cc = safe_float(CC[i][j])
            ft = safe_float(FT[i][j])
            ct = safe_float(CT[i][j])

            if any(v is None for v in [fc, cc, ft, ct]):
                continue  # skip if missing data

            A = fc - cc          # extra yen paid for fastest
            B = ct - ft          # extra minutes spent if choosing cheapest

            # Robust rule:
            # - If cheapest is not slower (B <= 0), choose cheapest (dominates or ties on time and is cheaper by definition)
            # - Else if fastest is not more expensive (A <= 0), keep fastest
            # - Else compute value = (A/B)*60 and switch to cheapest if value >= V
            choose_cheapest = False
            if B <= 0:
                choose_cheapest = True
            elif A <= 0:
                choose_cheapest = False
            else:
                value = (A / B) * 60.0  # yen per hour saved
                if value >= V:
                    choose_cheapest = True

            if choose_cheapest:
                EC[i][j] = CC[i][j]
                ET[i][j] = CT[i][j]
                if CR is not None:
                    ER[i][j] = CR[i][j]
                switched += 1
                switched_pairs.append((stations[i], stations[j]))

    # Metadata for outputs
    rule_text = "Let A=FC-CC, B=CT-FT. If B<=0 choose cheapest; else if A<=0 keep fastest; else if (A/B)*60>=V choose cheapest."
    base_meta = {
        "mode": "efficient",
        "metric": "chosen per-pair using yen-per-hour-saved threshold",
        "V": V,
        "rule": rule_text,
        "switched_pairs_count": switched,
        "sources": FILES,
        "date_time": {
            "fastest_cost": {"date": meta_fc.get("date"), "time": meta_fc.get("time")},
            "cheapest_cost": {"date": meta_cc.get("date"), "time": meta_cc.get("time")},
            "fastest_time_plus_transfers": {"date": meta_ft.get("date"), "time": meta_ft.get("time")},
            "cheapest_time_plus_transfers": {"date": meta_ct.get("date"), "time": meta_ct.get("time")},
            "fastest_transfers": {"date": meta_fr.get("date"), "time": meta_fr.get("time")},
            "cheapest_transfers": {"date": meta_cr.get("date"), "time": meta_cr.get("time")} if meta_cr else None,
        },
    }

    dump_matrix(OUT["EC"], stations, EC, base_meta | {"field": "cost_yen"})
    dump_matrix(OUT["ET"], stations, ET, base_meta | {"field": "time_plus_transfers"})
    dump_matrix(OUT["ER"], stations, ER, base_meta | {"field": "transfers"})

    print("Saved:")
    for k, p in OUT.items():
        print(" ", p)
    print(f"\nSwitched {switched} directed pairs to cheapest (out of {n*(n-1)}).")

if __name__ == "__main__":
    main()
