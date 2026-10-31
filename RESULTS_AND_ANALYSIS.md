# RESULTS_AND_ANALYSIS.md

All numbers below come from simulation outputs in `results/raw_data` and are aggregated in `results/tables`. Figures are in `results/figures`. No value was edited or tuned to match the paper.

## 1. Setup recap

| Item | Value | Provenance |
|---|---|---|
| Region | 100 × 100 × 100 m | PAPER |
| Default network | 200 nodes, anchor ratio 0.2 (40 anchors), R = 40 m | ASSUMPTION Q16 |
| Sweeps | ratio 0.10–0.50 (step 0.05); R 25–65 m (step 5); nodes 80–240 (step 20) | ranges PAPER Fig. 12; steps Q16 |
| Trials | 50 random deployments per sweep point (same 50 seeds at every point) | Q16 |
| PSO | N = 30, MaxIt = 300, w 0.9 → 0.4, c₁ = c₂ = 2, v_max = 10 m | w PAPER; rest Q7/Q10 |
| MCR | anchor-only fractional first hop | Q1 |
| Metric | Normalised error = mean 3D error ÷ R over UNs localised by all three algorithms | Q14/Q15 |

Integrity counters across **all** trials:
- singular matrices = 0;
- zero denominators in Eq. (8) = 0;
- threshold fallbacks (Q3) = 0;
- coverage ≥ 99.7% for every algorithm, with only a few isolated UNs at R = 25 m.

## 2. Headline results

Normalised error, mean ± 95% CI over 50 trials, at three points of each sweep. Full tables are in `results/tables/sweep_*.md`.

| Condition | DV-HOP | HCMCDV-HOP | HCMSPSO-DV-HOP | HCMSPSO vs DV-HOP |
|---|---|---|---|---|
| Ratio 0.10 | 0.364 ± 0.008 | 0.357 ± 0.018 | **0.257 ± 0.013** | −29.4% |
| Ratio 0.20 (default) | 0.320 | 0.333 | **0.259** | −19.1% |
| Ratio 0.50 | 0.302 ± 0.005 | 0.353 ± 0.014 | **0.288 ± 0.007** | −4.9% |
| R = 25 m | **0.576 ± 0.018** | 0.930 ± 0.059 | 0.703 ± 0.031 | **+22.2% (worse)** |
| R = 40 m | 0.325 ± 0.006 | 0.335 ± 0.012 | **0.260 ± 0.007** | −20.0% |
| R = 65 m | 0.294 ± 0.005 | 0.186 ± 0.006 | **0.156 ± 0.004** | −46.7% |
| 80 nodes | 0.461 ± 0.021 | 0.695 ± 0.057 | **0.442 ± 0.023** | −4.2% |
| 240 nodes | 0.311 ± 0.006 | 0.297 ± 0.012 | **0.238 ± 0.007** | −23.7% |

**Answer to the core question:** Under the tested conditions, **HCMSPSO-DV-HOP has lower error than traditional 3D DV-HOP in 25 of the 27 sweep points**. The reduction is up to 47%, and about 20% at the default setting. It is **worse at small communication radius** (R = 25 and 30 m). The intermediate **HCMCDV-HOP is worse than DV-HOP in most low-R / low-density settings** and only better at R ≥ 45 m or ≥ 200 nodes. PSO is what makes the improved method consistently competitive.

## 3. Experiment by experiment

### 3.1 Effect of anchor ratio: Fig. 12(a) analogue (`fig12_sweep_anchor_ratio.png`)

**What it shows.** Normalised error vs fraction of nodes that are anchors (R = 40 m, 200 nodes).

**Observations.**
- DV-HOP falls from 0.364 to 0.302 as the ratio grows, as expected.
- HCMSPSO-DV-HOP is the best at every ratio, but its error **rises slightly** (0.257 → 0.288).
- HCMCDV-HOP stays at about 0.33–0.36, worse than DV-HOP from ratio 0.15 upward.

**Interpretation.** The advantage of the improved methods shrinks as anchors become denser. A likely mechanism, consistent with §4 but not separately isolated, is this. More anchors means more anchor pairs that are 1–2 hops apart with spacing close to *R* per hop. Those pairs get the very large Eq. (8) weights, which raises the weighted AHD and therefore the distance overestimate. The hop threshold (Eq. 7) removes only about 5% of anchor pairs (0.9 of 19 per anchor at ratio 0.1; 4.6 of 99 at ratio 0.5), so it does not counteract this.

### 3.2 Effect of communication radius: Fig. 12(b) analogue (`fig12_sweep_comm_radius.png`)

**What it shows.** Normalised error vs R (ratio 0.2, 200 nodes).

**Observations.**
- All errors fall as R grows.
- The improved methods fall much faster: HCMSPSO goes from 0.70 to 0.16, while DV-HOP goes from 0.58 to 0.29.
- **The curves cross at R ≈ 33 m for HCMSPSO and ≈ 40 m for HCMCDV-HOP.**
- In absolute terms DV-HOP gets *worse* at large R (13.0 m at R = 40 → 19.1 m at R = 65), while HCMSPSO stays at about 10 m.

**Interpretation.**
- *Large R:* each integer hop then covers very different physical distances, so integer hop counts become coarse. MCR's 1/3 and 2/3 hop values resolve this, which is exactly the problem the paper says MCR solves (§III-B). The diagnostic (§4) shows MCR hops alone cut the distance MAE from 11.9 m to 5.5 m at R = 65.
- *Small R:* paths are long and bent. The weighted AHD of Eq. (10) overestimates the per-hop distance most strongly here (+12 m distance bias at R = 25), and PSO can only partly compensate.

### 3.3 Effect of network size: Fig. 12(c) analogue (`fig12_sweep_n_total.png`)

**What it shows.** Normalised error vs total nodes (ratio 0.2, R = 40 m).

**Observations.**
- All errors fall with density.
- HCMSPSO is best at every size, but only marginally at 80 nodes (0.442 vs 0.461, overlapping CIs).
- HCMCDV-HOP is much worse than DV-HOP for sparse networks (0.695 vs 0.461 at 80 nodes) and draws level at about 200 nodes.

**Interpretation.** It is the same mechanism as small R. Sparse networks have more irregular, bent paths, where the Eq. (8)–(10) weighting is most biased.

### 3.4 Per-node error: Fig. 10 analogue (`fig10_per_node_error.png`)

**What it shows.** 3D error of each of the first 60 UNs of one default deployment.

**Observations.** Over all 160 UNs of that deployment:

| | DV-HOP | HCMCDV-HOP | HCMSPSO-DV-HOP |
|---|---|---|---|
| Mean 3D error | 12.23 m | 13.76 m | 11.99 m |
| Median | 11.96 m | 12.40 m | 11.67 m |

- HCMSPSO has visibly fewer extreme values than DV-HOP but also fewer very small errors. Its per-node error is *more uniform*, not uniformly lower.
- In this single deployment, the advantage of HCMSPSO (0.24 m) is much smaller than the Monte-Carlo average at R = 40 (2.6 m). A single deployment is not representative, which is why the sweeps use 50 trials.

### 3.5 Positioning scatter: Fig. 11 analogue (`fig11_positioning_xy.png`, `fig11_positioning_3d.png`)

**What it shows.** Lines from each estimate to the true position, for each algorithm, as an x–y projection like the paper's plus a 3D view.

**Observations.** HCMSPSO estimates **pile up on the region boundary**. In the default deployment, 85 of 160 HCMSPSO estimates have at least one coordinate clamped to 0 or 100 m. HCMCDV-HOP puts 55 of 160 estimates *outside* the region, and DV-HOP puts 8 of 160 outside.

**Interpretation.** Overestimated distances (§4) push the least-squares solution outward. PSO's search-box clamp then pulls these back to the boundary, which explains much of why PSO beats MLE on the same distances. The paper's Fig. 11(c) shows no such boundary effect. This may come from its 2D projection, from parameters it does not report, or from implementation differences that cannot be checked.

### 3.6 Error distribution: Fig. 9 analogue (`fig09a_network_3d.png`, `fig09b_relative_error.png`)

- Mean relative error δ/R of HCMSPSO-DV-HOP in this deployment is **0.300**. Only 4% of nodes are at or below 0.15.
- The paper reports a mean of 0.048, with most errors between 0 and 0.15. **This is not reproduced.**
- Since the paper does not define "relative error" (Q15), the two numbers may not measure the same thing.

### 3.7 PSO convergence: Fig. 8 partial analogue (`fig08_pso_convergence.png`)

- The LDW-PSO objective (Eq. 16), averaged over 160 UNs, falls from 13.23 m to 6.313 m. It is essentially converged within about 20 iterations.
- Classic PSO with w = 0.7 (an assumption) reaches 6.315 m on the same curve.
- The final value is not zero, because the estimated distances are inconsistent with any single point. The floor is set by distance-estimation error, not by the optimiser.
- **The paper's claim that LDW-PSO converges faster than classic PSO (172 vs 246 iterations) is not reproduced** in this setting. The 3-variable, smooth objective is easy for both. Also, the paper's "loss" and "target loss 0.0036" are undefined.
- The sensitivity runs agree: N = 20 / MaxIt = 100 gives 0.257 and N = 50 / MaxIt = 500 gives 0.255, against 0.256 at baseline. PSO settings hardly matter.

### 3.8 Running time: Table 1 analogue (`results/tables/runtime_table.md`)

| Algorithm | Test 1 | Test 2 | Test 3 | Mean of 23 runs |
|---|---|---|---|---|
| DV-HOP | 0.080 s | 0.056 s | 0.056 s | 0.058 ± 0.005 s |
| HCMCDV-HOP | 0.058 s | 0.051 s | 0.053 s | 0.054 ± 0.003 s |
| HCMSPSO-DV-HOP | 2.714 s | 2.751 s | 2.753 s | 2.735 ± 0.018 s |

These times are for the whole network (160 UNs), Python/NumPy, run sequentially.
- PSO costs about 50× the MLE runtime. That is the price of its accuracy gain here.
- The paper's 0.49 s (MATLAB, scope of timing unstated) cannot be compared directly.
- Positioning accuracy (%) is not reported, because the paper does not define it.

## 4. Why HCMCDV-HOP underperforms: component diagnostic

`diag_distance_components.png`, `results/tables/distance_diagnostic.md`. This is a diagnostic, not a paper experiment: 20 deployments per R, error of the UN→AN distance estimates.

| R | DV-HOP MAE / bias | MCR hops only | Weighted AHD only (Eqs. 7–11) | HCMCDV-HOP (both) |
|---|---|---|---|---|
| 25 m | 7.5 / +0.4 | 6.9 / +0.5 | 12.4 / **+10.8** | 13.1 / +12.0 |
| 40 m | 8.0 / −0.1 | **5.1 / +0.2** | 12.3 / **+10.4** | 8.1 / +7.0 |
| 65 m | 11.9 / −0.3 | **5.5 / +0.1** | 20.8 / **+19.1** | 8.5 / +7.4 |

1. **MCR is a clear, unbiased improvement.** It lowers the distance MAE at every R, by up to 54% at R = 65. This supports the paper's first improvement.
2. **The weighted AHD (Eqs. 7–10), implemented as printed, introduces a large positive bias.** Mean anchor AHD rises from 28.5 to 34.8 m/hop at R = 40.
   - *Mechanism:* $c_{ij} = 1/(d_{ij}/R - hops_{ij})$ has its pole where the path is a straight line with each hop spanning a full radius. Pairs near that pole receive almost all the weight. Their per-hop distance $d_{ij}/hops_{ij}$ is close to *R*, so the weighted average is pulled toward *R*, above the true average per-hop distance.
   - Eq. (11) then carries this upward bias into every UN→AN distance.
3. In the full HCMCDV-HOP, MCR partly offsets this. Fractional hop counts are smaller, which reduces the product. That is why HCMCDV-HOP beats DV-HOP once MCR's gain is large (large R) but loses when it is small.

This is the main **discrepancy with the paper**, which reports HCMCDV-HOP better than DV-HOP everywhere in Fig. 12. The discrepancy is **not** caused by a coding error:
- Eqs. (8)–(10) are unit-tested on hand-computed examples.
- The bias follows analytically from the sign and pole structure of Eq. (8).

Possible explanations, none of which can be verified from the paper:
- Eq. (8) may be misprinted in the paper (as Eqs. 9, 15 and 17 appear to be).
- The authors' MCR may differ from the anchor-only reading (see §5).
- Their parameter settings may make the effect smaller.

## 5. Sensitivity to the approved interpretation of MCR (Q1)

Default network, the same 20 deployments for each variant (`results/tables/sensitivity.md`):

| Variant | DV-HOP | HCMCDV-HOP | HCMSPSO-DV-HOP |
|---|---|---|---|
| Anchor-only MCR (approved, used above) | 0.333 | 0.344 | 0.256 |
| **All-links MCR** (every link 1/3, 2/3, 1) | 0.333 | **0.222** | **0.174** |

**The Q1 interpretation is the single most influential assumption.**
- Under the all-links reading, which is common in MCR DV-HOP literature, both improved algorithms beat DV-HOP clearly at the default setting: −33% for HCMCDV-HOP and −48% for HCMSPSO.
- This is much closer to the paper's qualitative claims.
- The main results keep the approved anchor-only reading, which is the literal text of the paper. A full sweep under all-links MCR would show whether the paper's trends are recovered everywhere. That is a recommended follow-up, and it needs your approval because it changes an approved decision.

## 6. Comparison with the paper's reported trends

| Paper claim (source) | This reproduction | Status |
|---|---|---|
| Error falls as anchor ratio grows (Fig. 12a) | True for DV-HOP; flat to rising for the improved methods | Partially reproduced |
| Error falls as R grows; improved varies least (Fig. 12b) | Falls for all; improved varies **most** | Partially reproduced |
| Error falls as node count grows (Fig. 12c) | Yes, for all three | Reproduced |
| HCMCPSO best of the algorithms compared (Fig. 12) | Best of the three in 25/27 points; worse at R ≤ 30 m | Mostly reproduced |
| HCMCDV-HOP better than DV-HOP (Fig. 12) | Only at large R or dense networks | **Not reproduced** (§4) |
| Normalised error of improved ≈ 0.09–0.12 (Figs. 12–13 text) | 0.16–0.29 at R ≥ 40 m | Not reproduced (magnitudes; defaults unknown) |
| Per-node error lower for HCMSPSO (Fig. 10) | Lower on average (Monte-Carlo); mixed node by node | Reproduced on average |
| Relative error mostly 0–0.15, mean 0.048 (Fig. 9) | Mean 0.30 | Not reproduced (metric undefined) |
| LDW-PSO converges faster than classic PSO (Fig. 8) | No measurable difference | Not reproduced |
| ART 0.49 s (Table 1) | 2.7 s for 160 UNs in Python | Not comparable |
| GA/BEW/GWO, terrains, Methods 2–5, accuracy % | — | Not attempted (unspecified in paper) |

## 7. Limitations

1. **Missing parameters.** Defaults, PSO settings, metric definitions and the number of runs are not in the paper. They are our documented assumptions (§10 of the plan), so absolute numbers cannot match.
2. **Interpretation dependence.** Q1 (MCR propagation) changes the conclusions materially (§5). Q2, Q4, Q6, Q8 and Q9 are typo-corrections or readings that the paper's text supports, but they are still interpretations.
3. **Ideal radio model.** There is no noise, irregularity or packet loss, consistent with the paper, which models none.
4. **Uniform deployment.** The paper's Fig. 9 suggests non-uniform placement, which it never defines.
5. **Comparators and terrains** from the paper were not implemented because they are unspecified.
6. **Runtime** is Python-specific. Only the relative cost of the algorithms is meaningful.
7. **Single-deployment figures** (Figs. 9–11 analogues) illustrate behaviour. Conclusions rest on the 50-trial sweeps.

## 8. Conclusion

Implemented as approved, the paper's improved 3D DV-HOP (**HCMSPSO-DV-HOP**) localises better than traditional 3D DV-HOP in most tested conditions. The reduction in normalised error is about 20% at the default setting and up to 47% at large radius. It costs about 50× more computation and is worse when the communication radius is small (≤ 30 m in a 100 m cube).

Of its components, **multiple communication radii** give a clean, unbiased gain. The **weighted hop distance (Eqs. 8–10) as printed biases distances upward**, and PSO's bounded search mainly compensates for that bias rather than adding accuracy of its own. LDW-PSO shows no convergence advantage over classic PSO here. The interpretation of how fractional hops propagate (Q1) strongly affects the outcome. Under the all-links reading the paper's qualitative claims are largely recovered at the default setting.
