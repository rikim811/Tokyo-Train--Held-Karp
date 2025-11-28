import json
import numpy as np
import time

# ----------------------------
# CONFIG (edit these paths)
# ----------------------------


W_FILE = "Matrix/Efficient/weighted_normalized.json"        # objective used for TSP (minimize)
T_FILE = "Matrix/Efficient/time_plus_transfers.json"        # report "time" totals from this matrix (often same as W)
C_FILE = "Matrix/Efficient/cost.json"        # report "cost" totals from this matrix
R_FILE = "Matrix/Efficient/transfers.json"  
START_STATION = "Iidabashi"
K = 3  # top-k tours

# ----------------------------
# HELPERS
# ----------------------------
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_matrix(path: str):
    """
    Accepts either:
      - {"stations":[...], "matrix":[[...]...]}  (dict form)
      - [[...], [...]]                          (raw matrix list form)
    Returns: (stations_or_None, numpy_matrix)
    """
    data = load_json(path)
    if isinstance(data, dict) and "matrix" in data:
        stations = data.get("stations")
        mat = np.array(data["matrix"], dtype=float)
        return stations, mat
    elif isinstance(data, list):
        mat = np.array(data, dtype=float)
        return None, mat
    else:
        raise ValueError(f"Unrecognized matrix JSON format in {path}")

def sum_along_path(M: np.ndarray, path: list[int]) -> float:
    return float(sum(M[a, b] for a, b in zip(path, path[1:])))

def k_best_tsp_held_karp(W: np.ndarray, start: int = 0, k: int = 3):
    """
    Exact k-best TSP tours (directed/asymmetric supported) using Held–Karp DP.
    dp[(mask, j)] stores up to k best ways to reach j having visited mask.
    Returns list of (total_cost, path_indices) with path starting/ending at start.
    """
    n = W.shape[0]
    ALL = (1 << n) - 1
    START_MASK = 1 << start

    dp = {}

    # base: start -> j
    for j in range(n):
        if j == start:
            continue
        mask = START_MASK | (1 << j)
        dp[(mask, j)] = [(W[start, j], start, -1)]

    # build up
    for mask in range(ALL + 1):
        if not (mask & START_MASK) or mask == START_MASK:
            continue

        for j in range(n):
            if j == start or not (mask & (1 << j)):
                continue

            prev_mask = mask ^ (1 << j)
            if prev_mask == START_MASK:
                continue

            candidates = []
            for m in range(n):
                if m == start or not (prev_mask & (1 << m)):
                    continue
                prev_list = dp.get((prev_mask, m))
                if not prev_list:
                    continue
                for rank_idx, (prev_cost, _prev_node, _prev_rank) in enumerate(prev_list):
                    candidates.append((prev_cost + W[m, j], m, rank_idx))

            if candidates:
                candidates.sort(key=lambda x: x[0])
                dp[(mask, j)] = candidates[:k]

    # close tours back to start
    closing = []
    for j in range(n):
        if j == start:
            continue
        lst = dp.get((ALL, j))
        if not lst:
            continue
        for rank_idx, (cost, _prev, _pr) in enumerate(lst):
            closing.append((cost + W[j, start], j, rank_idx))

    closing.sort(key=lambda x: x[0])

    results = []
    seen = set()

    for total_cost, end, end_rank in closing:
        mask = ALL
        j = end
        rank = end_rank
        rev = [j]

        while True:
            cost, prev, prev_rank = dp[(mask, j)][rank]
            rev.append(prev)
            if prev == start:
                break
            mask ^= (1 << j)
            j = prev
            rank = prev_rank

        path = list(reversed(rev))
        path.append(start)  # close tour

        t = tuple(path)
        if t not in seen:
            seen.add(t)
            results.append((float(total_cost), path))
        if len(results) == k:
            break

    return results

# ----------------------------
# MAIN
# ----------------------------
def main():
    # Load objective W (from plain JSON like your example)
    dataW = load_json(W_FILE)
    stations = dataW["stations"]
    W = np.array(dataW["matrix"], dtype=float)

    start = stations.index(START_STATION)

    # Load reporting matrices (T/C/R) — can be same file or different
    st_T, T = load_matrix(T_FILE)
    st_C, C = load_matrix(C_FILE)
    st_R, R = load_matrix(R_FILE)

    # Verify station order matches, if provided in the files
    for st, name in [(st_T, "T"), (st_C, "C"), (st_R, "R")]:
        if st is not None and st != stations:
            raise ValueError(f"Station order mismatch between W and {name} file.")

    top3 = k_best_tsp_held_karp(W, start=start, k=K)

    print("Objective file (W):", W_FILE)
    print("W metric:", dataW.get("metric"))
    print()

    for rank, (best_w, path) in enumerate(top3, start=1):
        route_names = [stations[i] for i in path]

        total_T = sum_along_path(T, path)
        total_C = sum_along_path(C, path)
        total_R = sum_along_path(R, path)

        print(f"#{rank}")
        print("Route:", " -> ".join(route_names))
        print(f"Total W score: {best_w:.6f}")
        print(f"Total time (T): {total_T:.2f}")
        print(f"Total cost (C): {total_C:.0f}")
        print(f"Total transfers (R): {total_R:.0f}")
        print("-" * 60)

if __name__ == "__main__":
    main()
