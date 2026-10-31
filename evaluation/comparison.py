"""Aggregate raw experiment data into comparison tables (results/tables).

Only reads results/raw_data; never generates numbers of its own.
"""

from __future__ import annotations

import csv
import gzip
from collections import defaultdict
from pathlib import Path

import numpy as np

from evaluation.metrics import mean_ci95
from simulation.simulation_engine import ALGORITHMS

RAW = Path("results/raw_data")
TABLES = Path("results/tables")
SWEEP_LABELS = {
    "anchor_ratio": "Anchor ratio",
    "comm_radius": "Communication radius R (m)",
    "n_total": "Total nodes",
}


def read_csv(path: Path) -> dict[str, np.ndarray]:
    """Read a raw CSV into columns; numeric columns become float arrays."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    columns: dict[str, np.ndarray] = {}
    for key in rows[0]:
        values = [r[key] for r in rows]
        try:
            columns[key] = np.array([float(v) if v not in ("", None) else np.nan for v in values])
        except ValueError:
            if set(values) <= {"True", "False"}:
                columns[key] = np.array([v == "True" for v in values])
            else:
                columns[key] = np.array(values)
    return columns


def _fmt(x: float, digits: int = 3) -> str:
    return "—" if not np.isfinite(x) else f"{x:.{digits}f}"


def _write(name: str, header: list[str], rows: list[list], title: str, note: str = "") -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    with open(TABLES / f"{name}.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    lines = [f"### {title}", ""]
    if note:
        lines += [note, ""]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for row in rows:
        lines.append("| " + " | ".join(_fmt(c) if isinstance(c, float) else str(c) for c in row) + " |")
    (TABLES / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def sweep_table(parameter: str) -> dict:
    data = read_csv(RAW / f"sweep_{parameter}_trials.csv")
    values = sorted(set(data["value"]))
    rows, curves = [], defaultdict(dict)
    for v in values:
        for alg in ALGORITHMS:
            sel = (data["value"] == v) & (data["algorithm"] == alg)
            nle_mean, nle_std, nle_ci = mean_ci95(data["normalized_error"][sel])
            err_mean, _, _ = mean_ci95(data["mean_error_3d_m"][sel])
            coverage = data["n_localized"][sel].sum() / data["n_unknown"][sel].sum()
            rows.append([v, alg, int(sel.sum()), nle_mean, nle_std, nle_ci, err_mean, coverage])
            curves[alg][v] = (nle_mean, nle_ci)
    _write(
        f"sweep_{parameter}",
        [SWEEP_LABELS[parameter], "Algorithm", "Trials", "Normalised error (mean)", "Std",
         "95% CI ±", "Mean 3D error (m)", "Coverage"],
        rows,
        f"Normalised positioning error vs {SWEEP_LABELS[parameter].lower()} (Fig. 12 analogue)",
        "Normalised error = mean 3D error over UNs localised by all three algorithms ÷ R (Q14/Q15). "
        "Coverage = fraction of UNs each algorithm localised.",
    )
    # Relative improvement of HCMSPSO-DV-HOP over DV-HOP at each point
    imp_rows = []
    for v in values:
        base = curves[ALGORITHMS[0]][v][0]
        imp_rows.append([v] + [100.0 * (base - curves[a][v][0]) / base for a in ALGORITHMS[1:]])
    _write(
        f"sweep_{parameter}_improvement",
        [SWEEP_LABELS[parameter]] + [f"{a} reduction vs DV-HOP (%)" for a in ALGORITHMS[1:]],
        imp_rows,
        f"Relative error reduction vs DV-HOP — {SWEEP_LABELS[parameter].lower()}",
        "Positive = lower error than DV-HOP; negative = higher error.",
    )
    return curves


def runtime_table() -> None:
    data = read_csv(RAW / "runtime_tests_trials.csv")
    rows = []
    for alg in ALGORITHMS:
        row = [alg]
        for test in ("Test 1", "Test 2", "Test 3"):
            sel = (data["test"] == test) & (data["algorithm"] == alg)
            row += [float(data["runtime_s"][sel][0]), float(data["normalized_error"][sel][0]),
                    float(data["mean_error_3d_m"][sel][0])]
        sel = data["algorithm"] == alg
        rt_mean, _, rt_ci = mean_ci95(data["runtime_s"][sel])
        row += [rt_mean, rt_ci, int(sel.sum())]
        rows.append(row)
    header = ["Algorithm"]
    for t in (1, 2, 3):
        header += [f"Test {t} time (s)", f"Test {t} norm. error", f"Test {t} error (m)"]
    header += ["Mean time (s), all runs", "95% CI ±", "Runs"]
    _write("runtime_table", header, rows, "Running time and error in three tests (Table 1 analogue)",
           "Sequential runs at the default configuration (200 nodes, ratio 0.2, R = 40 m). Python/NumPy "
           "timings on this machine; not comparable with the paper's MATLAB timings. "
           "'Positioning accuracy (%)' is not reported because the paper does not define it (Q15).")


def sensitivity_table() -> None:
    data = read_csv(RAW / "sensitivity_trials.csv")
    rows = []
    for variant in dict.fromkeys(data["variant"]):
        for alg in ALGORITHMS:
            sel = (data["variant"] == variant) & (data["algorithm"] == alg)
            m, s, ci = mean_ci95(data["normalized_error"][sel])
            rows.append([variant, alg, int(sel.sum()), m, s, ci])
    _write("sensitivity", ["Variant", "Algorithm", "Trials", "Normalised error", "Std", "95% CI ±"],
           rows, "Sensitivity to approved assumptions Q1 and Q10",
           "Default network. Same 20 deployments for every variant. DV-HOP is unaffected by these "
           "switches and is listed as a reference.")


def distance_diagnostic_table() -> None:
    data = read_csv(RAW / "diagnostic_distance_components.csv")
    rows = []
    radii = sorted(set(data["comm_radius"]))
    variants = [v for v in dict.fromkeys(data["variant"]) if not v.startswith("_")]
    for r in radii:
        for v in variants:
            sel = (data["comm_radius"] == r) & (data["variant"] == v)
            rows.append([r, v, float(np.mean(data["bias_m"][sel])), float(np.mean(data["mae_m"][sel]))])
        sel = (data["comm_radius"] == r) & (data["variant"] == "_hopsize")
        rows.append([r, "AHD: Eq.(3) vs weighted Eq.(10) (m/hop)",
                     float(np.mean(data["trad_eq3_mean"][sel])), float(np.mean(data["hcmc_weighted_mean"][sel]))])
    _write("distance_diagnostic", ["R (m)", "Variant", "Bias (m) / Eq.3 AHD", "MAE (m) / weighted AHD"],
           rows, "Diagnostic: UN→AN distance-estimate error by improvement component",
           "Not a paper experiment. Bias = mean(estimated − true distance); MAE = mean |estimated − true|. "
           "Last row per R compares mean anchor AHD from Eq. (3) and from Eqs. (7)-(10).")


def build_tables() -> None:
    for parameter in SWEEP_LABELS:
        if (RAW / f"sweep_{parameter}_trials.csv").exists():
            sweep_table(parameter)
    for path, fn in (("runtime_tests_trials.csv", runtime_table),
                     ("sensitivity_trials.csv", sensitivity_table),
                     ("diagnostic_distance_components.csv", distance_diagnostic_table)):
        if (RAW / path).exists():
            fn()
    print(f"tables written to {TABLES}")
