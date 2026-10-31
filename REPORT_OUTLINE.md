# Research Report Outline

**Working title:** Localization Accuracy and Performance Analysis of Traditional and Improved 3D DV-HOP in Wireless Sensor Networks: A Reproduction Study

Each section lists what to write and which project file holds the material.

## 1. Abstract (150–250 words)
- Context: range-free localisation in 3D WSNs.
- Aim: reproduce the methodology of Wu et al. (2023), comparing 3D DV-HOP with HCMSPSO-DV-HOP.
- Method: Python simulation, 100 m cube, Monte-Carlo sweeps of anchor ratio, R and node count.
- Key results (RESULTS §2):
  - about 20% lower normalised error at the default setting, up to 47% at large R;
  - worse at R ≤ 30 m;
  - about 50× runtime;
  - the weighted-AHD bias finding.
- One-line conclusion with its caveats.

## 2. Introduction
- Why node position matters in WSNs, and why 3D deployments (paper §I).
- Range-based vs range-free localisation.
- Contribution of this report: an independent, documented reproduction, plus a component-level analysis.

## 3. Literature Review
- Use only works cited by the primary paper (its Refs. [1]–[21]), described as the paper describes them (paper §II).
- DV-HOP variants mentioned there: DECPSOHDV-hop [12], GWO-based [13], Monte Carlo localisation [14], DV-MDS-SA [15], GA-based [16].
- Do **not** add references that have not been read and verified.

## 4. Problem Statement
- 3D DV-HOP accuracy is limited by integer hop counts, bent paths and the estimation step (PAPER_ANALYSIS §1).
- Question: does the proposed improvement reduce error, under which conditions, and at what cost?

## 5. Objectives
1. Extract the algorithm and experimental methodology.
2. Implement both algorithms faithfully.
3. Reproduce the experiments that can be reproduced.
4. Evaluate them with the paper's metrics.
5. Explain the differences.

## 6. Proposed Methodology (as in the paper)
- Traditional 3D DV-HOP pipeline (Fig. 4).
- Improvements (Fig. 7): MCR → hop threshold → weighted AHD → two-AHD distance → LDW-PSO.
- Source: PAPER_ANALYSIS §3–4.

## 7. Mathematical Formulation
- Eqs. (1)–(17) with variables and units: PAPER_ANALYSIS §3–4 and TECHNICAL_DOCUMENTATION §3–6.
- Clearly mark the corrected typos (Eqs. 9, 15), the 2D Eq. (17), and the missing PSO update.
- Include the sign/pole analysis of Eq. (8) (TECHNICAL_DOCUMENTATION §4).

## 8. Implementation
- Architecture and data flow (TECHNICAL_DOCUMENTATION §1).
- Hop-count engine (min-plus relaxation).
- Vectorised PSO.
- Ambiguity table: the 18 questions and their resolutions (IMPLEMENTATION_PLAN §10).
- Testing summary (TESTING.md).

## 9. Experimental Setup
- Parameter table with PAPER / ASSUMPTION provenance (RESULTS §1, `config.py`).
- Experiment list mapped to paper figures (IMPLEMENTATION_PLAN §7).
- Fairness controls: common random numbers and the common evaluation set.

## 10. Results and Analysis
- Fig. 12 analogues, headline table, per-sweep discussion (RESULTS §2–3.3).
- Per-node error, scatter, error distribution (RESULTS §3.4–3.6).
- PSO convergence and runtime (RESULTS §3.7–3.8).
- Component diagnostic (RESULTS §4) and MCR sensitivity (RESULTS §5).
- Claim-by-claim comparison with the paper (RESULTS §6).

## 11. Inference
- MCR is the effective component.
- The weighted AHD as printed is biased upward.
- PSO mostly compensates through its bounded search.
- The benefit depends on R and density.
- The MCR interpretation is decisive.

## 12. Limitations
RESULTS §7: missing parameters, interpretation dependence, ideal radio, uniform deployment, unimplemented comparators and terrains, Python timing.

## 13. Conclusion
RESULTS §8, plus future work (VIVA Q26).

## 14. References
[1] Y. Wu, C. Zhang, L. Tong, and X. Shi, "Location Optimization Based on Improved 3D DV-HOP Algorithm in Wireless Sensor Networks," *IEEE Access*, vol. 11, pp. 85525–85536, 2023, doi: 10.1109/ACCESS.2023.3303569. **(Primary reference.)**

Further entries: only references from the primary paper's own list (its pp. 85536) that are actually discussed, copied exactly from that list.

The standard inertia-weight PSO form used for Q7 should be credited to its original source **only after you have obtained and checked that source**. It is not cited by the primary paper.
