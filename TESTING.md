# TESTING.md

## How to run

```
python -m unittest discover -s tests -t .
```

Only the standard library `unittest` is used, with no extra dependencies. The last full run gave **44 tests, all passing**. The verbose log is saved in `results/test_report.txt`.

## Strategy

The tests work at four levels, matching Phase 4 of the brief:

1. **Hand-calculated values.** Small networks (lines, a triangle, a tetrahedron of anchors) where every expected number was worked out by hand and written into the test.
2. **Mathematical properties.** Invariants that must hold on random networks, such as MCR hops ≤ integer hops, hops ≥ d/R, and weights that are positive and sum to 1.
3. **Edge cases and invalid input.** Disconnected nodes, too few anchors, coplanar anchors, a zero denominator, every anchor discarded, bad configuration values.
4. **Pipeline and reproducibility.** End-to-end runs, the same network for every algorithm, bit-identical results for a repeated seed.

## Test inventory

| File | Area | What is checked |
|---|---|---|
| `test_network.py` | Connectivity | Distance matrix (3-4-5 and 12 m cases); inclusive radius (link at exactly R); no self-loops; integer hops on a 4-node line = [0, 1, 2, 3] in both directions; disconnected node → ∞; shortest path chosen over a longer one |
| | Deployment | Node and anchor counts; positions inside [0, 100]³; same seed → identical deployment |
| | Invalid input | Negative R; anchor ratio = 1; zero anchors; network without anchors → `ValueError` |
| `test_traditional.py` | Eq. (3) | Hand example: anchors at x = 0, 30, 70 with hops 1, 3, 2 → AHD = [25, 23.33, 22]; unreachable anchor ignored; isolated anchor → NaN |
| | Nearest anchor | Ties → lowest index; no reachable anchor → −1 |
| | Eqs. (5)–(6) | Exact distances recover the true point to 1e-9; matrix rows match a hand-built A, b; < 4 anchors → None; coplanar anchors (singular AᵀA) → None |
| | Pipeline | `est_dist` equals Eq. (2) for every UN; DV-HOP hops are integers; isolated UN is not localised and its estimate is NaN |
| `test_improved.py` | MCR value | 0.2R → 1/3, R/3 → 1/3, 0.5R → 2/3, 2R/3 → 2/3, 0.9R → 1, R → 1, 1.5R → ∞ |
| | MCR anchor-only | Line example (R = 15): nodes at 5, 10, 20 → 1/3, 2/3, 4/3. Line at 4, 8, 12, 22 → 1/3, 2/3, 1, 5/3 (only the first link fractional) |
| | MCR all-links | Same line, all links fractional → 2 for the far node, 2/3 for the 8 m node |
| | MCR properties | On a random network: MCR ≤ integer hops; same reachability; MCR hop ≥ d/R |
| | Eq. (7) | Centre anchor t = √3·50/50; corner anchor t = √3·100/50; 8 endpoints |
| | Eqs. (8)–(10) | Hand example: d = [30, 40], hops = [1, 2], R = 40 → c = [−4, −1], w = [0.8, 0.2], AHD = 28 m. c negative and w positive / normalised. Threshold discards an anchor (AHD = 30). Q3 fallback (AHD = 28, fallback counted). Q5 zero denominator excluded and counted (AHD = 20) |
| | Eq. (11) | Hand example: AHD [20, 30, 40], hops [1, 2, 3] → [20, 50, 90] m; unreachable UN → NaN |
| | Pipeline | MLE and PSO variants run; PSO localises all connected UNs within the region; PSO without rng → error; invalid estimator / MCR mode → error |
| `test_pso_metrics_engine.py` | Eq. (16) | Hand example with a mask: residuals −1, 0, −3 → √(10/3) |
| | Eq. (15) | w = 0.9, 0.65, 0.4 at t = 0, MaxIt/2, MaxIt; constant-w mode |
| | Convergence | Exact distances from 6 anchors: PSO recovers two targets to within 0.05 m; gbest is monotone non-increasing |
| | Reproducibility | Same rng → identical PSO output; a problem with no anchors is rejected |
| | Metrics | 3D error 13 m and Eq. (17) 2D error 5 m for (3, 4, 12); normalised error; empty input → NaN; CI half-width = 1.96·s/√n |
| | Engine | Same seed → bit-identical estimates for all 3 algorithms; all algorithms see the same connectivity |

## Bugs found by testing

Two first-run failures came from **wrong hand calculations in the tests**, not from the code. Both were checked against the paper's rules before the expectations were changed:

- The MCR line test assumed a node 12 m from the anchor (R = 15) got 2/3 hop. Since 12 > 2R/3 = 10, the paper's rule gives 1 hop. The test was rewritten so it actually exercises a 2/3 first hop.
- The zero-denominator test expected 1 excluded pair. The pair is seen from both anchors, so 2 is correct.

## Numerical stability notes

- Eq. (8) is guarded only at exact zero (|den| < 1e-12), as approved in Q5. In the experiment runs the `zero_denominator` counter was **0** in every trial (see the raw CSVs). Near-zero denominators do occur and produce very large weights. This is a property of the formula, analysed in `RESULTS_AND_ANALYSIS.md`.
- Eq. (5) uses a rank check before `np.linalg.solve`. The `singular_matrix` counter was **0** in all logged trials with random 3D anchors.
- PSO positions are clipped to the region, so the objective is always finite.

## Validation against the paper

The paper gives no worked numerical example, so validation against it is at the level of **trends** only. That comparison is in `RESULTS_AND_ANALYSIS.md` §5.
