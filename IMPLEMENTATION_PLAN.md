# IMPLEMENTATION_PLAN.md

**Status: APPROVED 2026-10-31.** All recommendations in §10 were approved by the project owner as written ("do what u seem ok"). Implementation follows them exactly.

This plan implements the methodology of Wu et al., *IEEE Access* 2023 (DOI 10.1109/ACCESS.2023.3303569). Equation, figure and page references point to that paper. `PAPER_ANALYSIS.md` has the full extraction. Every point that needs a decision is collected in **§10, Unresolved Questions and Ambiguities**, with a recommended resolution. None of those resolutions will be applied until approved.

---

## 1. Scope

**In scope**

| Algorithm | What it is | Paper source |
|---|---|---|
| **DV-HOP (traditional 3D)** | Integer hops + Eq. (3) AHD + Eq. (2) distance + Eqs. (5)–(6) "MLE" | §III-A, Fig. 4 |
| **HCMCDV-HOP** (intermediate, *proposed for approval*) | MCR hops + hop threshold (7) + weighted AHD (8)–(10) + distance (11) + MLE (5)–(6) | §III-B p. 85529–85530, Fig. 12 curve |
| **HCMSPSO-DV-HOP** (improved) | As HCMCDV-HOP, but with LDW-PSO (12)–(16) instead of MLE | §III-B, Fig. 7 |

HCMCDV-HOP is the authors' own intermediate algorithm and is plotted in Fig. 12. Including it adds no new method. It separates the effect of the hop/distance corrections from the effect of PSO (Q12).

**Out of scope** (no implementable specification in the paper; see Q13): GA-DV-HOP, 3D-DV-HOP-BEW, Weight GWO DV-HOP, ACO, chaotic WSA, DA, Methods 2–5, and the terrain models of Fig. 13.

---

## 2. Proposed module architecture

The structure follows the brief, with small changes justified below and marked ★.

```
3D-DVHop/
├── algorithms/
│   ├── common.py              ★ Shared math: Eq.(3) AHD, nearest-anchor selection,
│   │                            Eqs.(5)-(6) least-squares "MLE". Used by both algorithms → no duplication.
│   ├── traditional_dvhop.py   DV-HOP pipeline (Eqs. 2, 3, 5, 6)
│   ├── improved_dvhop.py      Improvements ONLY: MCR hops, Eq.(7) threshold, Eqs.(8)-(10) weights,
│   │                            Eq.(11) distance; estimator = "mle" (HCMCDV-HOP) | "pso" (HCMSPSO-DV-HOP)
│   └── pso.py                 ★ Linear-decreasing-weight PSO, Eqs.(12)-(16). Separate so it is testable alone.
├── simulation/
│   ├── deployment.py          Random 3D node placement, anchor selection
│   ├── network.py             Distance matrix, adjacency (radius R), integer BFS hop counts,
│   │                            generic weighted shortest-path (Dijkstra, heapq) for MCR
│   └── simulation_engine.py   One trial: deploy → run all algorithms on the SAME network → per-node results
│   (node.py — ★ proposed to DROP, see note)
├── evaluation/
│   ├── metrics.py             Eq.(17) error, normalised error, (accuracy only if defined — Q15)
│   ├── experiments.py         Experiment definitions (sweeps, seeds, repetitions)
│   └── comparison.py          Aggregation, mean / std / 95% CI, tables
├── visualization/
│   ├── network_visualization.py       3D deployment + connectivity (Fig. 9a analogue)
│   ├── localization_visualization.py  True vs estimated with error lines (Fig. 11 analogue)
│   └── result_plots.py                Sweep curves (Fig. 12 analogue), per-node error (Fig. 10, 9b)
├── results/{figures,tables,raw_data}/
├── tests/                     unittest (stdlib) — runnable with `python -m unittest`
├── config.py                  ★ Every parameter in one place, each tagged PAPER / ASSUMPTION with source
├── PAPER_ANALYSIS.md, IMPLEMENTATION_PLAN.md, README.md, requirements.txt
└── main.py                    CLI: run experiments, regenerate figures from raw data
```

**Justification for the ★ changes**
- `common.py`: Eq. (3) and Eqs. (5)–(6) are used by both DV-HOP and HCMCDV-HOP. One shared implementation avoids duplicated logic, as the brief requires.
- `pso.py`: PSO is a self-contained component with its own equations (12–16). Keeping it separate lets it be unit-tested on synthetic problems with known optima.
- `config.py`: Keeps the paper/assumption distinction visible in code.
- **Drop `node.py`:** A per-node object model would force Python loops over nodes. NumPy arrays (positions `(n,3)`, boolean anchor mask, hop matrix `(n_anchor, n)`) are faster, simpler and easier to test. If you prefer, `node.py` can stay as a thin `dataclass` used only for readability. **Needs approval.**

## 3. Data structures

| Name | Type / shape | Meaning |
|---|---|---|
| `positions` | `float64 (n, 3)` | True coordinates, m |
| `is_anchor` | `bool (n,)` | Anchor mask |
| `anchor_idx`, `unknown_idx` | `int` arrays | Index views |
| `dist` | `float64 (n, n)` | True Euclidean distances, m (used only for connectivity and for anchor–anchor $d_{ij}$, which anchors legitimately know) |
| `adjacency` | `bool (n, n)` | `dist <= R` and `i != j` |
| `hops` | `float64 (n_a, n)` | Min hop count anchor → every node. `np.inf` = unreachable. Integer-valued for DV-HOP, fractional for MCR |
| `hopsize` | `float64 (n_a,)` | AHD per anchor, m/hop |
| `est_dist` | `float64 (n_u, n_a)` | Estimated UN → AN distances, m |
| `estimates` | `float64 (n_u, 3)` | Estimated coordinates. `NaN` = not localised |
| `TrialResult` | dataclass | Per-algorithm estimates, localised mask, runtime, seed, config |

## 4. Algorithm implementation sequence

1. `deployment.py` and `network.py`: deployment, adjacency, BFS hops (integer).
2. `common.py`: Eq. (3), nearest-anchor selection, Eqs. (5)–(6).
3. `traditional_dvhop.py`: full DV-HOP. Unit tests on hand-computed networks.
4. `improved_dvhop.py`, in steps, each tested separately:
   (a) MCR hop counting → (b) Eq. (7) threshold → (c) Eqs. (8)–(10) weighted AHD → (d) Eq. (11) distances → (e) MLE back-end = HCMCDV-HOP.
5. `pso.py`: Eqs. (12)–(16). Tested on synthetic noiseless problems where the true point is the optimum.
6. Plug PSO into `improved_dvhop.py` = HCMSPSO-DV-HOP.
7. `metrics.py`, `simulation_engine.py`, `experiments.py`, `comparison.py`.
8. Visualization.
9. Full experiment runs, then documentation (Phases 5–6).

## 5. Mathematical calculations (by step)

**Traditional DV-HOP**
1. `hops` = BFS on `adjacency` from each anchor (§III-A flooding; Fig. 4).
2. $Hopsize'_i = \sum_{j\neq i} d_{ij} / \sum_{j\neq i} h_{ij}$ over reachable anchors *j* (Eq. 3).
3. For each UN *u*: nearest anchor $a^* = \arg\min_a h_{au}$ (Q6 tie-break). Then $d_{uj} = Hopsize'_{a^*}\cdot h_{uj}$ (Eq. 2).
4. Build *A*, *b* (Eq. 6) with the last reachable anchor as reference. $X = (A^TA)^{-1}A^Tb$ (Eq. 5) via `np.linalg.solve(A.T@A, A.T@b)` (Q11).

**Improved (HCMCDV-HOP / HCMSPSO-DV-HOP)**
1. MCR hop counts (Q1), weighted shortest path with hop weights 1/3, 2/3, 1.
2. $t_i = \max_m d_{i,\text{endpoint}_m}/R$ (Eq. 7, Q2). Keep anchors *j* with $hops_{ij} \le t_i$.
3. $c_{ij} = 1/(d_{ij}/R - hops_{ij})$ (Eq. 8, Q5). $w_{ij} = c_{ij}/\sum_l c_{il}$ (Eq. 9, Q4). $Hopsize_i = \sum_j w_{ij}\, d_{ij}/hops_{ij}$ (Eq. 10). Fallback for empty set: Q3.
4. $d_{uj} = \tfrac12(Hopsize_{a^*(u)} + Hopsize_j)\cdot h_{uj}$ (Eq. 11, Q6).
5. Estimator:
   - **MLE:** Eqs. (5)–(6) as above (HCMCDV-HOP).
   - **PSO:** minimise Eq. (16), $f(p) = \sqrt{\tfrac1m\sum_j(\lVert p - a_j\rVert - d_{uj})^2}$, with:
     - pbest/gbest per Eqs. (12)/(13);
     - initialisation per Eq. (14);
     - inertia weight $w(t)$ per Eq. (15) (Q8);
     - velocity/position update (Q7);
     - search box = deployment region (Q10).

     Vectorised across all UNs at once, shape `(n_u, N_particles, 3)`, for speed. This is numerically identical to running them one by one.

## 6. Simulation workflow (one trial)

```
seed → deploy n nodes uniformly in [0,100]^3 → choose anchors → build adjacency(R)
     → DV-HOP(network)         → estimates_A, runtime_A
     → HCMCDV-HOP(network)     → estimates_B, runtime_B
     → HCMSPSO-DV-HOP(network) → estimates_C, runtime_C
     → per-node errors on the common evaluation set (Q14) → TrialResult
```

All algorithms get the **same** deployment, anchors and radius in each trial (common random numbers). The PSO random stream is derived from the trial seed, so every trial is exactly reproducible.

## 7. Experimental workflow

Defaults when a parameter is not being swept: see Q16.

| ID | Mirrors | Sweep | Output |
|---|---|---|---|
| X1 | Fig. 12(a) | Anchor ratio 0.10 → 0.50 | Mean normalised error ± 95% CI vs ratio, 3 algorithms |
| X2 | Fig. 12(b) | R = 25 → 65 m | Same, vs R |
| X3 | Fig. 12(c) | Total nodes 80 → 240 | Same, vs N |
| X4 | Fig. 10 | One deployment, 60 unknown nodes | Per-node error (m) |
| X5 | Fig. 11 | One deployment | True vs estimated with error lines: x–y projection (as paper) **plus** 3D view |
| X6 | Fig. 9 | One deployment | 3D node layout; per-node relative error of HCMSPSO-DV-HOP |
| X7 | Table 1 | 3 independent tests (paper) + Monte-Carlo summary | Running time (s) and error metrics per algorithm |
| X8 | Fig. 8 (partial) | One UN, PSO iterations | Objective (Eq. 16) vs iteration for LDW-PSO. *Optional:* constant-weight PSO for contrast (Q17) |
| X9 | Fig. 14 (partial) | Nodes to locate 30 → 360 | Only if an accuracy definition is approved (Q15) |
| — | Fig. 13 | — | **Not reproduced**: terrain models undefined (Q13) |

Every experiment writes raw per-trial, per-node data to `results/raw_data/*.csv` (or `.npz`) with seed and config. Tables and figures are generated **only** from these files.

## 8. Evaluation methodology

- Metrics: only those used by the paper, with definitions approved under Q14 (Eq. 17 dimensionality) and Q15 (normalised error, relative error, PA).
- Reported per data point: mean, standard deviation and 95% CI over Monte-Carlo trials. Also the **localisation coverage** (fraction of UNs localised), so that excluding nodes cannot hide failures.
- Runtime is measured with `time.perf_counter()` around each algorithm's full run on one network, excluding deployment. Python and MATLAB timings are **not** comparable to the paper's 0.49 s. Only relative timing between algorithms will be discussed.
- Comparison with the paper covers **trends** only: ordering of the algorithms, direction of change under each sweep, and relative improvement. Absolute values cannot be compared, because the defaults are missing.

## 9. Validation strategy (Phase 4 preview)

- **Hand-checked micro-networks:** e.g. a 5-node line or a cube of anchors. Expected hop counts, Eq. (3) AHDs, Eq. (2) distances and LS solutions are computed by hand in the tests.
- **Exactness test:** With exact distances supplied, Eqs. (5)–(6) must recover the true point to ~1e-9. PSO must reach it within a tolerance.
- **MCR hops:** Nodes placed at known distances (0.2R, 0.5R, 0.9R, 1.5R) must get the expected fractional values.
- **Eqs. (7)–(10):** Hand-computed threshold, $c_{ij}$ (negative), $w_{ij}$ (positive, sum = 1) and AHD.
- **Edge cases:**
  - disconnected UN → not localised;
  - fewer than 4 anchors reachable;
  - coplanar anchors → singular $A^TA$;
  - all anchors eliminated by the threshold;
  - $d/R - hops \approx 0$;
  - R so small that the graph is disconnected;
  - invalid inputs (negative R, ratio outside (0,1), too few nodes) raise `ValueError`.
- **Reproducibility:** The same seed gives bit-identical raw data.
- **Sanity:** Error decreases with more anchors and larger R, as in Fig. 12. Deviations are investigated and documented, never tuned away.

## 10. UNRESOLVED QUESTIONS AND AMBIGUITIES

Each entry gives the issue, why it matters, the options, and a **recommendation** with justification. Nothing here will be applied without approval.

### Algorithm questions

**Q1. How MCR fractional hops propagate beyond the first hop (§III-B, p. 85530; Fig. 5).**
- *Issue:* The text says **anchors** broadcast at R/3, 2R/3 and R, giving 1/3, 2/3 and 1 hop to nodes at those ranges. Beyond the first hop it only says "the OH value will be forwarded", without saying what relays add.
- *Why it matters:* It defines every hop count in the improved algorithm. That is the core of the improvement.
- *Options:*
  - (a) **Anchor-only MCR:** the first link from the anchor is fractional and every relay adds 1. Hop = min over first-hop neighbours *k* of $q(d_{ak}) + h_{\text{int}}(k,u)$.
  - (b) **All-link MCR:** every link weighs 1/3, 2/3 or 1 by its length, and hop = weighted shortest path. This is the variant common in MCR DV-HOP literature and matches "the hops' quantity in nodes is decimalized" (Abstract).
- *Recommendation:* **(a)**. It is the literal reading: the paper only ever says *the AN* uses three radii. (b) would require every node to have three transmit powers, which the paper never states. If you prefer (b), it is a one-line switch, and both could be reported as a sensitivity check. **This is the most consequential question; please decide.**

**Q2. Meaning of "endpoints" in Eq. (7).**
- *Issue:* "M is the endpoints' quantity in a TDS; d serves as the distance from each endpoint to AN i."
- *Why it matters:* It sets the threshold that removes anchors.
- *Options:* (a) the 8 vertices of the 100 m cube (M = 8); (b) all other anchors.
- *Recommendation:* **(a)**. "Endpoints of the 3D space" naturally means its corners. Under (b), $t_i$ would come from the anchors themselves, and the threshold would almost never remove anything, because $hops_{ij} \ge d_{ij}/R$ for the farthest anchor makes the test close to redundant.

**Q3. Every anchor removed by the threshold (s = 0).**
- *Issue:* Eqs. (9)–(10) are undefined if no other anchor satisfies $hops_{ij} \le t_i$.
- *Why it matters:* This happens for some anchors at small R, which would crash the algorithm or produce NaN.
- *Options:* (a) fall back to the unweighted Eq. (3) AHD for that anchor; (b) use the weighted formula over all anchors (no threshold) for that anchor; (c) mark the anchor's AHD invalid and let UNs use their next-nearest anchor.
- *Recommendation:* **(b)**. It keeps the authors' weighting and only skips the step that cannot be applied. Every occurrence will be counted and reported.

**Q4. Index typo in Eq. (9).**
- *Issue:* As printed, the denominator is $\sum_{l} c_{ij}$, which makes all weights equal.
- *Options:* (a) literal; (b) $\sum_{l\neq i,\,l\in S_i} c_{il}$.
- *Recommendation:* **(b)**. The literal form cancels the weighting and contradicts the text ("each KN … is given a weight value"). This will be documented as a typo correction.

**Q5. Division by zero / near-zero in Eq. (8).**
- *Issue:* $d_{ij}/R - hops_{ij} = 0$ gives an infinite weight. Values very close to 0 dominate the sum.
- *Options:* (a) implement literally and only guard exact zero, by skipping that pair and logging it; (b) clamp $|denominator| \ge \varepsilon$.
- *Recommendation:* **(a)**, the literal formula with an exact-zero guard (`abs(den) < 1e-12` → exclude and log). The paper does not mention clamping. Clamping would change the authors' algorithm.

**Q6. Which hop distance a UN uses (Eqs. 2 and 11), and the tie-break.**
- *Issue:* Eq. (11) needs $Hopsize_i$ for a UN. A UN has no AHD, and "nearest AN" has no tie-break rule.
- *Recommendation:* $Hopsize_i$ := the AHD of the anchor with the **fewest hops** to the UN, ties broken by **lowest anchor index** (deterministic). The same rule applies to traditional Eq. (2). Alternative tie-break: average of the tied anchors' AHD. I recommend against it because it adds averaging the paper does not describe.

**Q7. PSO velocity/position update and learning factors (missing).**
- *Issue:* The paper gives pbest, gbest, initialisation and inertia weight, but no update equation and no $c_1$, $c_2$.
- *Why it matters:* PSO cannot run without them.
- *Recommendation:* Use the standard inertia-weight PSO update, $v \leftarrow w v + c_1 r_1 (P_i - x) + c_2 r_2 (P_g - x)$, $x \leftarrow x + v$, with $r_1, r_2 \sim U(0,1)$, which is the form the paper's terminology ("inertia weight", "learning factors") refers to. Use **$c_1 = c_2 = 2.0$**, the conventional values. Both are **assumptions** and will be labelled as such. Velocity is clamped to $[-v_{max}, v_{max}]$ and position to the search box.

**Q8. Eq. (15) as printed is not decreasing.**
- *Issue:* $w = w_s - (w_s-w_e)(MaxIt/N)$ contains no iteration variable. It would give a constant, possibly negative, *w*.
- *Recommendation:* $w(t) = w_s - (w_s - w_e)\, t/MaxIt$, with $w_s = 0.9$ and $w_e = 0.4$ (paper values). This is the only form consistent with "linear decreasing weight" from 0.9 to 0.4. It will be documented as a typo correction.

**Q9. Undefined m and w in Eq. (16).**
- *Recommendation:* m = w = the number of anchors that have a finite hop count to the UN, i.e. all anchors whose distance enters Eq. (11). The hop threshold of Eq. (7) is applied only to AHD computation, as the text describes, not to this sum.

**Q10. PSO numeric settings (missing).**
- *Issue:* Population N, MaxIt, $v_{max}$, $v_{min}$ and search bounds are not given.
- *Recommendation (all ASSUMPTIONS):*
  - Search box = deployment region [0, 100] m per axis.
  - **N = 30** particles.
  - **MaxIt = 300**. Fig. 8's x-axis ends at 300 and I-PSO converges at 172.
  - $v_{max}$ = 10 m (10% of range), $v_{min} = -v_{max}$.
  - Initial velocity per Eq. (14): $\mathrm{rdft}()\cdot v_{max}$, which is non-negative, kept literal.

  A small sensitivity check on N and MaxIt will be reported, not tuned.

**Q11. Singular / ill-conditioned $A^TA$ in "MLE" (Eq. 5), and the minimum anchor count.**
- *Issue:* Eqs. (5)–(6) need ≥ 4 non-coplanar anchors. The paper itself names matrix irreversibility as an MLE weakness.
- *Options:* (a) literal `solve`, where a singular matrix means the node is not localised and the failure is counted; (b) pseudo-inverse / `lstsq`, which always returns a point.
- *Recommendation:* **(a)**. It is faithful to Eq. (5) and to the paper's motivation for PSO. The failure rate is reported per algorithm. With random 3D anchors exact singularity is extremely rare, so this will not distort results in practice.

**Q12. Include HCMCDV-HOP?**
- *Recommendation:* **Yes.** It is the authors' own algorithm (Fig. 12) and separates the effect of hop/distance correction from the effect of PSO, which strengthens the analysis. It adds no new method.

**Q13. Comparison algorithms and terrains the paper does not specify.**
- *Issue:* GA-DV-HOP, 3D-DV-HOP-BEW, Weight GWO, ACO, WSA, DA, Methods 2–5 and the four terrain models (Fig. 13) are named without implementable detail.
- *Recommendation:* **Exclude** them. State in the results that Figs. 8 (mostly), 13 and 14 and Table 1's cross-method comparison are **not reproduced**, and why. Implementing them would mean inventing algorithms or terrain models, which the integrity rules forbid.

### Metric questions

**Q14. Eq. (17) is 2D; which nodes are evaluated.**
- *Issue:* $\delta = \sqrt{(x-x')^2 + (y-y')^2}$ ignores z in a 3D study.
- *Options:* (a) literal 2D; (b) full 3D Euclidean error.
- *Recommendation:* **(b) 3D** as the primary metric, with the 2D Eq. (17) value also stored in raw data for transparency. A 3D localisation error that ignores z would hide a third of the error.
- *Evaluation set:* Compute errors over UNs **localised by all three algorithms** (connected to ≥ 4 anchors, non-singular), so every algorithm is scored on the same nodes. Report coverage separately.

**Q15. Normalised error, relative error and "positioning accuracy (%)" are undefined.**
- *Why it matters:* Figs. 9, 12, 13 and 14 and Table 1 all use them.
- *Options for normalised error:* (a) mean δ / R, the most common normalisation in DV-HOP literature; (b) mean δ / region side (100 m).
- *Recommendation:*
  - Normalised error = **mean δ / R**, for Figs. 12 analogues.
  - Per-node relative error = **δ / R**, for the Fig. 9(b) analogue.
  - **Do not report "positioning accuracy (%)"** unless you supply or approve a definition. One candidate is $(1 - \text{normalised error})\times 100\%$, but that is our own construction, not the paper's.

  All metric definitions will be labelled as assumptions.

**Q16. Default parameters for non-swept experiments (missing).**
- *Recommendation (ASSUMPTIONS, chosen inside the paper's own sweep ranges):*
  - **Total nodes = 200**, inside Fig. 12(c)'s 80–240.
  - **Anchor ratio = 0.2**, inside Fig. 12(a)'s 0.1–0.5.
  - **R = 40 m**, inside Fig. 12(b)'s 25–65.
  - For X3, the anchor **ratio** is held at 0.2 (not the anchor count).
  - Sweep steps: ratio 0.05, R 5 m, nodes 20.
  - **50 Monte-Carlo trials per point**, with fixed master seed 2023.
  - Placement **uniform random** in the cube; anchors = random subset.

  Uniform random is used because no non-uniform model is defined, and uniform random placement already produces the irregular density the paper describes.

**Q17. Fig. 8 convergence experiment.**
- *Recommendation:* Plot only the LDW-PSO objective (Eq. 16) vs iteration, averaged over UNs. A constant-*w* "classic PSO" curve would need a *w* value the paper does not give. If you want that contrast, I suggest w = 0.7 as a labelled assumption. ACO, WSA and DA are excluded (Q13).

**Q18. Tooling.**
- *Recommendation:*
  - `requirements.txt` = `numpy`, `matplotlib` only. Shortest paths use stdlib `heapq`/`collections` (no SciPy), and tests use stdlib `unittest`.
  - PyMuPDF was installed **only** to read the PDF for this analysis. It is not a project dependency.
  - Python 3.11 (found on this machine).

## 11. Expected outputs

- `results/raw_data/`: per-trial, per-node CSV/NPZ with seed, config and per-algorithm estimates.
- `results/tables/`: per-sweep mean / std / CI tables, runtime table (Table 1 analogue), coverage table.
- `results/figures/`:
  - X1–X3 sweep curves (Fig. 12 analogue);
  - X4 per-node error (Fig. 10);
  - X5 positioning scatter (Fig. 11);
  - X6 3D layout and relative error (Fig. 9);
  - X8 PSO convergence (Fig. 8 partial).
- `python main.py --experiment all` reproduces everything. `python -m unittest` runs the tests.
