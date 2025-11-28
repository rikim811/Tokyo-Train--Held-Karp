# Tokyo-Train -- Held–Karp (TSP on Tokyo rail network)

A small research / teaching repository that builds travel-cost matrices for a set of Tokyo rail stations and finds exact k-best tours using the Held–Karp dynamic programming algorithm (with a k-best extension).

This project was created as part of a Math IA / DP exploration. It demonstrates:

- collecting pairwise route metrics (time, fare, transfers) using an external routing API;
- building matrix representations suitable for TSP solvers;
- an exact Held–Karp dynamic programming implementation that returns the top-k tours for small N.

## Repository structure

- `main.py` — interactive script that queries the Ekispert route API to build a metric matrix for a chosen mode (fastest/cheapest) and metric (time/fare/transfers). Requires an API key.
- `create_matrix.py` — automated script that iterates over a station list and queries `main.get_routes()` to produce matrix CSV/JSON output (used to generate files in `Matrix/`).
- `heldKarp_algorithm.py` — the more configurable Held–Karp runner which loads a chosen objective matrix (`W_FILE`) and reporting matrices (T/C/R) then prints the top-k tours and their totals.
- `heldKarp_algorithm_onefile.py` — a self-contained example that uses `Matrix/recommended_weighted_normalized.json` and prints the top-3 tours.
- `add_weight.py`, `add_transfer.py`, `find_efficiency.py`, `get_id.py`, `create_matrix.py` — helper scripts for matrix construction and transformations.
- `Matrix/` — sample matrices (JSON) organized by scenario: `Cheapest/`, `Fastest/`, `Efficient/`. Each folder typically contains `matrix` JSON and separate cost/time/transfers variants.

## Quick motivation

When you need to find a TSP tour for a small set of stations (for example, selecting an ordering of visits for a project), exact DP via Held–Karp is feasible for N up to ~15–18 depending on time/memory. This repo stores multiple metrics and a weighted objective so you can find tours that balance time, cost and transfers.

## Requirements

- Python 3.8+ (3.10 recommended)
- numpy
- requests (only required for `main.py` / `create_matrix.py` which call the Ekispert API)

Install dependencies via pip:

```bash
python -m pip install numpy requests
```

## Data / JSON matrix format

Two accepted JSON forms are used across scripts:

1) Object form (recommended):

```json
{
	"stations": ["Iidabashi", "Tokyo", ...],
	"matrix": [[0, 12, ...], [15, 0, ...], ...],
	"metric": "time",          // optional human-readable label
	"weights": {"time": 0.7, "cost": 0.2, "transfers": 0.1},
	"sources": {"T": "Matrix/Efficient/time_plus_transfers.json", "C": "...", "R": "..."}
}
```

2) Raw matrix form:

```json
[[0, 12, ...], [15, 0, ...], ...]
```

The runner will accept either; when `stations` is present the order is used to map indices to names.

## How to run

1) Build pairwise matrices (if you want to re-create or update matrices)

- `main.py` is interactive and uses the Ekispert API via `main.get_routes()`. You must set a valid API key in `main.py` (the file contains a `KEY` variable and an example/test key). The script will prompt for mode and metric and then query routes for every pair in the `station_list`.

```bash
python main.py
```

- Or use `create_matrix.py` to automatically iterate over `station_list` and save JSON/CSV outputs. Example output names look like `matrix_fastest_minutes_20251128_1200.json`.

```bash
python create_matrix.py
```

2) Run the Held–Karp solver (k-best)

- Quick, self-contained example:

```bash
python heldKarp_algorithm_onefile.py
```

- Configurable runner (edit constants at the top of `heldKarp_algorithm.py`):

```python
# edit paths & start station at the top of heldKarp_algorithm.py
W_FILE = "Matrix/Efficient/weighted_normalized.json"
T_FILE = "Matrix/Efficient/time_plus_transfers.json"
C_FILE = "Matrix/Efficient/cost.json"
R_FILE = "Matrix/Efficient/transfers.json"
START_STATION = "Iidabashi"
K = 3
```

Then run:

```bash
python heldKarp_algorithm.py
```

The script prints the objective metadata and the top-K tours with totals for the reporting metrics (time, cost, transfers).

## Held–Karp algorithm summary (what's implemented)

- The implementation is an exact dynamic-programming Held–Karp solver extended to produce the k-best tours rather than just the single best. It works for asymmetric (directed) costs.
- Complexity: O(n^2 * 2^n) time and O(n * 2^n) memory for the classic Held–Karp; the k-best extension multiplies internal lists but the exponential nature remains. Practically this is usable for n up to ~14–17 depending on k and memory.
- The DP stores up to k partial paths for each state (mask, last_node) and reconstructs tours by closing to the start. Duplicate tours are filtered to produce k unique tours.

Edge cases handled in code:
- Mixed JSON input forms (object vs raw matrix)
- Station order verification between objective and reporting matrices (will raise if orders mismatch)
- Missing/None matrix entries: `create_matrix.py` writes `None` for unreachable pairs; Held–Karp expects finite costs—if you modify matrices containing `None` you should substitute a large finite penalty where appropriate.

## Configuration notes

- API key: `main.py` contains a `KEY` placeholder. Replace with a valid Ekispert (or other) API key if you want to fetch live routes.
- Station list: `main.py` and `create_matrix.py` include a sample `station_list` mapping names to Ekispert IDs. Modify as needed.
- Objective weighting: one of the `Matrix/` files demonstrates a `weighted_normalized.json` objective that combines multiple metrics into a single W matrix. Construct W by normalizing metrics and applying weights.

## Example output (sample lines)

When you run `heldKarp_algorithm.py` you should see something like:

```
Objective file (W): Matrix/Efficient/weighted_normalized.json
W metric: weighted_normalized

#1
Route: Iidabashi -> Tokyo -> Shibuya -> Iidabashi
Total W score: 0.123456
Total time (T): 120.00
Total cost (C): 520
Total transfers (R): 2
------------------------------------------------------------
```

## Limitations & advice

- This repository focuses on clarity and reproducibility, not on extreme performance. For larger N (>18) consider approximation algorithms or ILP solvers.
- Ensure the matrices are complete (no None entries) or replace `None` with a large penalty before running Held–Karp.
- Running `main.py` / `create_matrix.py` will make many web requests; respect rate limits and your API provider's terms.

## Next steps / enhancements

- Add a small test harness / unit tests for the DP implementation (happy path + one unreachable edge case).
- Add an option to treat missing edges as large finite penalties instead of failing.
- Provide a small CLI for `heldKarp_algorithm.py` (argparse) so users can pass `--W`, `--T`, `--start`, `--k` from the command line.

## Contribution

PRs and issues welcome. If you change JSON formats, update the loader helpers in `heldKarp_algorithm.py` and `heldKarp_algorithm_onefile.py`.

## License

This repository does not include a license file; add one (for example MIT) if you intend to publish or share broadly.

