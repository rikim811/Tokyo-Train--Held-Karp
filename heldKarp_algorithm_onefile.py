import json
from math import inf
import numpy as np


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

    # dp[(mask, j)] = list of (cost, prev_node, prev_rank) sorted by cost
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
                continue  # already initialized

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

    # reconstruct up to k unique tours
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

        path = list(reversed(rev))  # starts with start, ends with end
        path.append(start)          # close tour

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
W_FILE = "./Matrix/recommended_weighted_normalized.json"

data = load_json(W_FILE)
stations = data["stations"]
W = np.array(data["matrix"], dtype=float)

start = stations.index("Iidabashi")  # safer than assuming index 0

# Load T/C/R from the "sources" inside your JSON
src_T = data["sources"]["T"]
src_C = data["sources"]["C"]
src_R = data["sources"]["R"]

st_T, T = load_matrix(src_T)
st_C, C = load_matrix(src_C)
st_R, R = load_matrix(src_R)

# Optional: verify station order matches (if the source files include stations)
for st, name in [(st_T, "T"), (st_C, "C"), (st_R, "R")]:
    if st is not None and st != stations:
        raise ValueError(f"Station order mismatch between W and {name} source file.")

top3 = k_best_tsp_held_karp(W, start=start, k=3)

print("Weights used:", data.get("weights"))
print("Metric used:", data.get("metric"))
print()

for rank, (best_w, path) in enumerate(top3, start=1):
    route_names = [stations[i] for i in path]

    total_time = sum_along_path(T, path)   # note: your file name suggests "time_plus_transfers"
    total_cost = sum_along_path(C, path)
    total_transfers = sum_along_path(R, path)

    print(f"#{rank}")
    print("Route:", " -> ".join(route_names))
    print(f"Total W score: {best_w:.6f}")
    print(f"Total time (from {src_T}): {total_time:.2f}")
    print(f"Total cost (yen): {total_cost:.0f}")
    print(f"Total transfers: {total_transfers:.0f}")
    print("-" * 60)
