# 3D-DVHop: Localization Accuracy and Performance Analysis in WSNs

This project reproduces the methodology of:

> Y. Wu, C. Zhang, L. Tong, X. Shi, "Location Optimization Based on Improved 3D DV-HOP Algorithm in Wireless Sensor Networks," *IEEE Access*, vol. 11, pp. 85525–85536, 2023. DOI: 10.1109/ACCESS.2023.3303569.

It compares **traditional 3D DV-HOP** with the paper's **HCMSPSO-DV-HOP**. It also includes the paper's intermediate **HCMCDV-HOP**, which applies the hop and distance corrections but still uses the MLE step, so the effect of the corrections can be separated from the effect of PSO. The simulation is in Python with NumPy and Matplotlib.

## Requirements

- Python ≥ 3.10 (developed on 3.11.9)
- `pip install -r requirements.txt` (numpy, matplotlib)

## Usage

```bash
python main.py all                                  # run every experiment, then build tables + figures
python main.py run                                  # experiments only  -> results/raw_data/
python main.py report                               # tables + figures from existing raw data
python main.py run --experiment sweep_comm_radius   # one experiment
python main.py run --trials 5                       # quick run (5 Monte-Carlo trials per point)
python -m unittest discover -s tests -t .           # 44 unit tests
```

A full run took about 20–25 minutes on a 16-core machine (the three sweeps: 7 + 5 + 4 min). Monte-Carlo trials run in parallel; the runtime tests run sequentially.

Experiments: `single_deployment`, `pso_convergence`, `runtime_tests`, `sweep_anchor_ratio`, `sweep_comm_radius`, `sweep_n_total`, `distance_diagnostic`, `sensitivity`.

## Project layout

```
algorithms/      traditional_dvhop.py, improved_dvhop.py (improvements only), pso.py, common.py
simulation/      deployment.py, network.py, simulation_engine.py
evaluation/      metrics.py, experiments.py, comparison.py
visualization/   network/localization visualisation, result_plots.py, style.py
results/         raw_data/ (CSV + seeds), tables/ (CSV + Markdown), figures/ (PNG)
tests/           unittest suite
config.py        every parameter, tagged PAPER or ASSUMPTION (Q-number)
```

## Documents

| File | Contents |
|---|---|
| `PAPER_ANALYSIS.md` | Equations, parameters, experiments and inconsistencies extracted from the paper, with page references |
| `IMPLEMENTATION_PLAN.md` | Approved plan; §10 lists the 18 ambiguities and their approved resolutions |
| `TECHNICAL_DOCUMENTATION.md` | Architecture, equations, how each one is implemented |
| `TESTING.md` | Test strategy and inventory |
| `RESULTS_AND_ANALYSIS.md` | Findings, interpretation, comparison with the paper, limitations |
| `VIVA_PREPARATION.md` | Viva questions and answers |
| `REPORT_OUTLINE.md` | Research report outline |

## What is and is not reproduced

- **Reproduced (methodology):**
  - traditional 3D DV-HOP, HCMCDV-HOP and HCMSPSO-DV-HOP;
  - error vs anchor ratio, communication radius and node count (Fig. 12);
  - per-node error (Figs. 9, 10);
  - positioning scatter (Fig. 11);
  - running time (Table 1);
  - PSO convergence (Fig. 8, LDW-PSO only).
- **Not reproduced:**
  - comparison algorithms the paper names but does not specify (GA-, BEW-, GWO-DV-HOP, ACO, WSA, DA, Methods 2–5);
  - terrain types (Fig. 13), which are undefined;
  - "positioning accuracy (%)", which is undefined.
- **Assumptions:** The paper omits many parameters (defaults, PSO settings, metric definitions). Every assumption is listed in `IMPLEMENTATION_PLAN.md` §10 and tagged in `config.py`. Exact numerical agreement with the paper is therefore not expected.
# 3D-DVHop
