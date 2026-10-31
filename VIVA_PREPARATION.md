# VIVA_PREPARATION.md

Answers point to the paper (Wu et al., *IEEE Access* 2023) by equation or figure, and to this project's files.

## A. Fundamentals

**1. What is DV-HOP and why is it "range-free"?**
Nodes never measure distance. Anchors (nodes with known position) flood the network, and every node learns its minimum hop count to each anchor. Anchors turn their known separations into an average distance per hop (AHD). A node then estimates its distance to an anchor as AHD × hops and solves for its position. No RSSI, ToA or AoA hardware is needed, which keeps it cheap (§III-A).

**2. What changes from 2D to 3D?**
- The AHD includes the z term (Eq. 3 vs Eq. 1).
- The position has three unknowns, so the linear system (Eq. 6) needs at least 4 non-coplanar anchors instead of 3.
- Paths in 3D are more irregular, so hop-count error matters more.

**3. Explain Eqs. (5)–(6).**
- Write $\lVert X - a_k\rVert^2 = d_k^2$ for every anchor.
- Subtract the equation of the reference anchor *n*. The quadratic $\lVert X\rVert^2$ cancels and leaves a linear system $AX = b$.
- Solve it in the least-squares sense: $X = (A^TA)^{-1}A^Tb$.

The paper calls this "maximum likelihood estimation". Mathematically it is linear least squares, which equals ML only under Gaussian, equal-variance errors on the linearised equations.

**4. What are the main error sources the authors identify?**
Isolated nodes; anchor density; integer hop counts; bent ("broken-line") paths with use of only the nearest anchor's AHD; and the final estimation step (§III-A, p. 85529).

## B. The improvements

**5. What does MCR do?**
Anchors broadcast at R/3, 2R/3 and R. A node in the innermost ring records 1/3 hop and a node in the middle ring 2/3, instead of 1. Hop counts become fractional and track distance more closely (p. 85530, Fig. 5).

**6. Which MCR interpretation did you use, and why?**
Anchor-only (Q1): only the anchor's first link is fractional, and relays add whole hops. The paper explicitly says *the AN* broadcasts at three radii and never says ordinary nodes do. The alternative, every link fractional, is tested as a sensitivity case. It gives much better results (normalised error 0.174 vs 0.256 for HCMSPSO), so this is the most important open interpretation.

**7. Explain Eq. (7).**
$t_i = \max_m d_{im}/R$ over the region's 8 corners (Q2). This is the largest number of hops a straight path from anchor *i* could need inside the cube. Anchors farther away in hops than $t_i$ must lie on strongly bent paths, so they are excluded from anchor *i*'s AHD.

**8. Explain Eqs. (8)–(10). What did you find?**
- $c_{ij} = 1/(d_{ij}/R - hops_{ij})$. Because hops ≥ d/R, every $c_{ij}$ is ≤ 0.
- Normalising (Eq. 9) gives positive weights that favour straight paths.
- The AHD is the weighted mean of $d_{ij}/hops_{ij}$ (Eq. 10).

**Finding:** the weight has a pole where each hop spans a full radius, so those pairs dominate and the AHD is pulled toward *R*. This produces a +7 to +19 m distance bias (diagnostic, RESULTS §4).

**9. Eq. (9) has a typo. How did you handle it?**
As printed, the denominator is $\sum_l c_{ij}$, which makes all weights equal and cancels the weighting. It was implemented as $\sum_l c_{il}$ and documented as a typo correction (Q4).

**10. What is Eq. (11)?**
$d_{uj} = \tfrac12(Hopsize_{a^*} + Hopsize_j)\,h_{uj}$. It is the mean of the UN's nearest-anchor AHD and the target anchor's AHD, because the paper says the nearest anchor's AHD alone ignores the target's. The paper calls this the "median"; the median of two values is their mean.

**11. Why replace MLE with PSO?**
The paper says $A^TA$ can be non-invertible (p. 85530), and PSO needs no matrix inversion. *In our runs $A^TA$ was never singular* with random 3D anchors. PSO's real benefit here was its bounded search, which keeps estimates inside the region when the distances are overestimated.

**12. Describe your PSO.**
- Objective: Eq. (16), the RMS of the distance residuals.
- Initialisation: Eq. (14).
- pbest / gbest: Eqs. (12)–(13).
- Inertia: Eq. (15) with w from 0.9 to 0.4. The printed formula has no iteration variable, so it was corrected to $t/MaxIt$ (Q8).
- Update rule and settings: the paper gives no velocity update. We used the standard inertia-weight update with c₁ = c₂ = 2, N = 30, MaxIt = 300 and v_max = 10 m. These are labelled assumptions.

**13. Does the linearly decreasing weight help?**
Not measurably here. LDW reached 6.313 m and classic w = 0.7 reached 6.315 m, both within about 20 iterations. The 3-variable objective is easy for both. The paper's Fig. 8 advantage was not reproduced.

## C. Methodology and integrity

**14. Which paper parameters were missing, and what did you do?**
Default N, anchor ratio, R; number of runs; PSO size, iterations, learning factors and v_max; definitions of normalised error, relative error and accuracy %. Each was listed (plan §10), a value was recommended, approved, and tagged ASSUMPTION in `config.py`. Defaults lie inside the paper's own sweep ranges.

**15. How do you ensure a fair comparison?**
- All three algorithms run on the identical network in each trial.
- Trial *k* uses the same seed at every sweep value.
- Errors are averaged only over UNs localised by *all* algorithms.
- Coverage is reported separately.

**16. Why 3D error rather than Eq. (17)?**
Eq. (17) omits z, which hides about a third of the error in a 3D study. The 3D error is primary, and the Eq. (17) value is stored in the raw data (Q14).

**17. How did you define normalised error?**
Mean 3D error ÷ R. The paper does not define it, and this is the usual normalisation in DV-HOP work (Q15). We did **not** report "positioning accuracy (%)" because the paper never defines it.

**18. Why didn't you implement GA-DV-HOP, the GWO variant, or the terrain experiments?**
The paper names them but gives no algorithm or terrain model. Implementing them would mean inventing methods, which would misrepresent the comparison.

**19. How was the code validated?**
44 unit tests: hand-calculated hops, AHD, MCR values, the Eq. (8)–(10) example (weights 0.8/0.2, AHD 28 m), exact-distance recovery by MLE and PSO, edge cases, and bit-reproducibility (TESTING.md).

## D. Results

**20. Does the improved algorithm beat traditional DV-HOP?**
HCMSPSO-DV-HOP has lower normalised error in 25 of 27 sweep points: about −20% at the default setting and up to −47% at R = 65 m. It is worse at R ≤ 30 m.

**21. Why is HCMCDV-HOP often worse than DV-HOP?**
The weighted AHD bias (see answer 8). MCR alone cuts the distance MAE substantially (e.g. 8.0 → 5.1 m at R = 40). The weighting adds a +10 m bias, so the net effect depends on which is larger. That makes HCMCDV-HOP better only at large R or high density.

**22. Why does the improvement grow with R?**
At large R, one integer hop spans 0 to R, so integer hop counts are coarse. MCR's fractional values matter most there. DV-HOP's absolute error even rises with R (13 → 19 m), while HCMSPSO stays at about 10 m.

**23. Why do PSO estimates sit on the boundary?**
The distances are overestimated, so the best-fit point lies outside the cube, and the search-box clamp holds it on the face: 85 of 160 nodes in the example deployment. The clamp limits the damage, which explains much of PSO's gain over MLE.

**24. How does your result compare with the paper numerically?**
- The paper's improved normalised error is about 0.09–0.12; ours is 0.16–0.29 for R ≥ 40 m.
- The paper's runtime is 0.49 s; ours is 2.7 s in Python.

Defaults, PSO settings and metric definitions are unknown, so only trends can be compared. RESULTS §6 lists each claim as reproduced, partial or not reproduced.

**25. What is the biggest limitation of your study?**
Its dependence on interpretation, especially MCR propagation (Q1). It changes the conclusions qualitatively. Next is the set of unknown parameters, then the ideal radio model.

**26. What would you do next?**
1. Run the full sweeps under all-links MCR.
2. Test whether a plausible misprint in Eq. (8) explains the bias.
3. Add radio irregularity.
4. Ask the authors for their parameters.
