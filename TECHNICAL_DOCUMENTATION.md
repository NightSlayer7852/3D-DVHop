# TECHNICAL_DOCUMENTATION.md

This is the technical reference for the reproduction of Wu et al., "Location Optimization Based on Improved 3D DV-HOP Algorithm in Wireless Sensor Networks", *IEEE Access* 11, 2023 (DOI 10.1109/ACCESS.2023.3303569).

- Equation numbers refer to the paper.
- **Q-numbers** refer to the approved decisions in `IMPLEMENTATION_PLAN.md` §10.
- The full extraction from the paper is in `PAPER_ANALYSIS.md`.

---

## 1. Architecture

```
config.py                         all parameters, each tagged PAPER / ASSUMPTION (Qn)
simulation/
  deployment.py                   uniform random placement in [0, L]^3, random anchor subset
  network.py                      Network dataclass, distance matrix, adjacency (radius R),
                                  min-plus shortest paths (shared hop-count engine)
  simulation_engine.py            run_trial(seed, ...) -> TrialResult (all algorithms, same network)
algorithms/
  common.py                       Eq.(3) AHD, nearest anchor, Eqs.(5)-(6) "MLE", LocalizationResult
  traditional_dvhop.py            DV-HOP (Eqs. 2, 3, 5, 6)
  improved_dvhop.py               the authors' improvements only: MCR, Eq.(7), Eqs.(8)-(10), Eq.(11);
                                  estimator "mle" -> HCMCDV-HOP, "pso" -> HCMSPSO-DV-HOP
  pso.py                          LDW-PSO (Eqs. 12-16), vectorised over many UNs
evaluation/
  metrics.py                      3D error, Eq.(17) 2D error, normalised error, CI
  experiments.py                  experiment definitions; writes results/raw_data only
  comparison.py                   raw data -> results/tables
visualization/
  style.py                        fixed series colours/markers
  network_visualization.py        3D layout (Fig. 9a analogue)
  localization_visualization.py   estimate->truth error lines (Fig. 11 analogue)
  result_plots.py                 raw data -> results/figures
tests/                            44 unittest cases (see TESTING.md)
main.py                           CLI
```

Approved deviations from the suggested structure: `node.py` was dropped in favour of NumPy arrays, and `common.py`, `pso.py`, `config.py` and `style.py` were added. The reasons are in the plan, §2.

Data flow: `experiments.py` → `results/raw_data/*.csv(.gz)` + `*_meta.json` → `comparison.py` / `result_plots.py` → `results/tables`, `results/figures`. No figure or table is computed from anything except the raw files.

## 2. Network model

| Item | Implementation | Provenance |
|---|---|---|
| Region | Cube [0, 100]³ m | PAPER §IV |
| Placement | i.i.d. uniform; anchors = random subset of `round(ratio × N)` nodes | ASSUMPTION Q16 |
| Radio | Ideal sphere: link iff distance ≤ R | INTERP (implied by paper) |
| Hop counts | `min_plus_shortest_paths(initial, link_weights)`: Bellman-Ford relaxation until no value changes | equivalent to "keep minimum hop" flooding, Fig. 4 |

The min-plus routine computes $H[s,v] = \min_{\text{paths}}\big(\text{initial}[s,u_1] + \sum w(u_k,u_{k+1})\big)$. Choosing `initial` and `link_weights` gives the three hop models:

| Model | initial | link weights |
|---|---|---|
| DV-HOP integer flooding | 0 at source | 1 per link |
| MCR anchor-only (Q1, used) | $q(d_{a,v})$ for direct neighbours of anchor *a* | 1 per relay link |
| MCR all-links (sensitivity only) | 0 at source | $q(d_{u,v})$ per link |

where $q(d) = 1/3$ if $d \le R/3$, $2/3$ if $d \le 2R/3$, $1$ if $d \le R$ (p. 85530).

## 3. Traditional 3D DV-HOP (`algorithms/traditional_dvhop.py`)

1. Integer hops $h$ from every anchor.
2. Eq. (3): $Hopsize'_i = \sum_{j\ne i} \lVert a_i - a_j\rVert \,/\, \sum_{j\ne i} h_{ij}$ over anchors *j* reachable from *i*. Units: m/hop.
3. For each UN *u*: $a^*(u) = \arg\min_a h_{au}$ (ties → lowest index, Q6). Eq. (2): $d_{uj} = Hopsize'_{a^*}\, h_{uj}$ (m).
4. Eqs. (5)–(6): $A_k = 2(a_k - a_n)$ and $b_k = \lVert a_k\rVert^2 - \lVert a_n\rVert^2 + d_n^2 - d_k^2$ for $k = 1..n-1$, with the last reachable anchor as reference. Then $X = (A^TA)^{-1}A^Tb$, solved with `np.linalg.solve`.
   - It needs ≥ 4 reachable anchors.
   - If `rank(A) < 3` the node is **not localised** and counted as `singular_matrix` (Q11).

## 4. Improved algorithm (`algorithms/improved_dvhop.py`)

| Step | Equation | Function | Notes |
|---|---|---|---|
| MCR hops | p. 85530 | `mcr_hop_counts` | Q1 anchor-only |
| Hop threshold | (7) $t_i = \max_m d_{im}/R$ | `hop_thresholds` | M = 8 cube vertices (Q2) |
| Weights | (8) $c_{ij} = 1/(d_{ij}/R - hops_{ij})$ | `weighted_hopsize` | exact-zero guard, $\lvert den\rvert < 10^{-12}$ excluded (Q5) |
| Normalisation | (9) $w_{ij} = c_{ij}/\sum_{l\in S_i} c_{il}$ | `weighted_hopsize` | index typo corrected (Q4) |
| Weighted AHD | (10) $Hopsize_i = \sum_{j\in S_i} w_{ij}\, d_{ij}/hops_{ij}$ | `weighted_hopsize` | $S_i$ = reachable anchors with $hops_{ij} \le t_i$. If empty, threshold skipped (Q3) |
| UN→AN distance | (11) $d_{uj} = \tfrac12(Hopsize_{a^*(u)} + Hopsize_j)\, h_{uj}$ | `estimate_distances_eq11` | Q6 |
| Estimator (MLE) | (5)–(6) | `common.mle_localize_all` | → HCMCDV-HOP |
| Estimator (PSO) | (12)–(16) | `pso.ldw_pso` | → HCMSPSO-DV-HOP |

**Sign property of Eq. (8).** Each hop covers at most its radius, so $hops_{ij} \ge d_{ij}/R$ and every $c_{ij} \le 0$. Eq. (9) divides same-sign numbers, so the weights are positive and sum to 1. The largest weights go to pairs where $hops_{ij} \to d_{ij}/R$, i.e. where each hop is nearly a full radius. This pulls the weighted AHD toward *R*. The consequence is measured in `RESULTS_AND_ANALYSIS.md`.

Diagnostics returned in `LocalizationResult.diagnostics`: `anchors_discarded`, `threshold_fallback`, `zero_denominator`, `singular_matrix`.

## 5. LDW-PSO (`algorithms/pso.py`)

| Element | Implementation | Provenance |
|---|---|---|
| Objective | Eq. (16): $f(p) = \sqrt{\tfrac1m \sum_j (\lVert p - a_j\rVert - d_{uj})^2}$, m = anchors with finite $d_{uj}$ | PAPER; m/w per Q9 |
| Initialisation | Eq. (14): $x = U(0,1)(x_{max}-x_{min}) + x_{min}$, $v = U(0,1)\,v_{max}$ | PAPER |
| Inertia | $w(t) = 0.9 - 0.5\,t/MaxIt$, t = 1..MaxIt | PAPER values; form Q8 |
| Update | $v \leftarrow wv + c_1r_1(P_i - x) + c_2r_2(P_g - x)$; $v \in [-v_{max}, v_{max}]$; $x \leftarrow \mathrm{clip}(x + v, 0, 100)$ | ASSUMPTION Q7 |
| pbest / gbest | Eq. (12) (ties take the new position), Eq. (13) | PAPER |
| Settings | N = 30, MaxIt = 300, $c_1 = c_2 = 2$, $v_{max}$ = 10 m | ASSUMPTION Q7/Q10 |
| Output | $P_g$ after MaxIt iterations | Fig. 6 |

Vectorisation: arrays of shape `(B, P, 3)`, where B is the number of UNs. Each UN has its own independent swarm. Because the random draws are batched, results equal a per-UN loop in distribution, though not draw-for-draw. The run is bit-reproducible for a given seed.

Orphan UNs (no anchor information) are not localised (Fig. 7).

## 6. Evaluation (`evaluation/metrics.py`)

| Metric | Formula | Provenance |
|---|---|---|
| 3D error (primary) | $\delta = \lVert p - \hat p\rVert$ (m) | Q14 |
| 2D error | Eq. (17) $\sqrt{(x-x')^2 + (y-y')^2}$ (m), stored in raw data | PAPER |
| Normalised error | $\overline{\delta}/R$ over the common evaluation set | Q15 |
| Relative error (per node) | $\delta/R$ | Q15 |
| Coverage | localised UNs / all UNs, per algorithm | plan §8 |
| Running time | `time.perf_counter()` around each algorithm's full run (hops → estimate), sequential runs only | plan §8 |

**Common evaluation set (Q14):** errors are averaged only over UNs localised by *all three* algorithms, so no algorithm benefits from skipping hard nodes. "Positioning accuracy (%)" is **not** computed, because the paper never defines it (Q15).

## 7. Reproducibility

- `trial_seed(master=2023, experiment_id, trial)` is built from `SeedSequence`.
- Each trial seed spawns two independent streams: deployment and PSO.
- Within a sweep, trial *k* uses the same seed at every swept value (common random numbers).
- Seeds are stored in every raw row and meta file.
- `tests/test_pso_metrics_engine.py::TestEngine.test_bit_reproducible` checks that identical seeds give identical estimates.

## 8. Complexity

- **Hops:** $O(I \cdot n_a \cdot n^2)$ per network for the min-plus relaxation, where I ≈ network diameter in hops.
- **Weighted AHD:** $O(n_a^2)$.
- **PSO:** $O(MaxIt \cdot n_u \cdot P \cdot n_a)$, about $300 \times 160 \times 30 \times 40 \approx 5.8\times10^7$ distance evaluations at the default setting. This is why HCMSPSO-DV-HOP is around 50× slower than the MLE variants in Python (Table 1 analogue).
