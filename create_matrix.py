# pip install requests
import time
import csv
import json

from main import get_routes, station_list


STATIONS = list(station_list.keys())  

MODE_CHOICES = {"1": "fastest", "2": "cheapest"}
METRIC_CHOICES = {"1": "minutes", "2": "fare", "3": "transfers"}


def best_route(frm_key: str, to_key: str, mode: str, retry: int = 1):
    for attempt in range(retry + 1):
        try:
            routes = get_routes(frm_key, to_key, date=20251128, time=1200, answer_count=20)
            if not routes:
                return None

            if mode == "fastest":
                return min(routes, key=lambda x: (x["minutes"], x["transfers"], x["fare"]))
            else:
                return min(routes, key=lambda x: (x["fare"], x["minutes"], x["transfers"]))

        except Exception as e:
            if attempt >= retry:
                print(f"Error {frm_key}->{to_key}: {e}")
                return None
            time.sleep(0.5)


def matrix_to_latex(matrix, na="NA"):
    def cell(v):
        return str(v) if v is not None else na
    rows = ["  " + " & ".join(cell(v) for v in row) + r" \\" for row in matrix]
    return "\\begin{bmatrix}\n" + "\n".join(rows) + "\n\\end{bmatrix}"


def main():
    print("Choose route mode:")
    print("  1) Fastest")
    print("  2) Cheapest")
    mode_in = input("Mode (1/2): ").strip()
    mode = MODE_CHOICES.get(mode_in)
    if not mode:
        raise SystemExit("Invalid mode. Choose 1 or 2.")

    print("\nChoose matrix metric:")
    print("  1) Duration (minutes)")
    print("  2) Fare (yen)")
    print("  3) Transfers (count)")
    metric_in = input("Metric (1/2/3): ").strip()
    metric = METRIC_CHOICES.get(metric_in)
    if not metric:
        raise SystemExit("Invalid metric. Choose 1, 2, or 3.")

    delay = 0.25  
    retry = 1

    n = len(STATIONS)
    matrix = [[0 for _ in range(n)] for __ in range(n)]

    for i, frm in enumerate(STATIONS):
        for j, to in enumerate(STATIONS):
            if i == j:
                matrix[i][j] = 0
                continue

            r = best_route(frm, to, mode=mode, retry=retry)
            matrix[i][j] = r[metric] if r else None

            print(f"{frm:>12} -> {to:<12} = {matrix[i][j]}")
            time.sleep(delay)

    # Print station order + matrix
    print("\nStation order (rows/cols):")
    print(STATIONS)
    print("\nMatrix (Python list):")
    print(matrix)

    # Save CSV + JSON
    out_base = f"matrix_{mode}_{metric}_20251128_1200"
    with open(out_base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([""] + STATIONS)
        for name, row in zip(STATIONS, matrix):
            w.writerow([name] + row)

    with open(out_base + ".json", "w", encoding="utf-8") as f:
        json.dump(
            {"stations": STATIONS, "mode": mode, "metric": metric, "date": 20251128, "time": 1200, "matrix": matrix},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nSaved: {out_base}.csv and {out_base}.json")
    print("\nLaTeX bmatrix (paste into your IA):")
    print(matrix_to_latex(matrix, na="NA"))


if __name__ == "__main__":
    main()
