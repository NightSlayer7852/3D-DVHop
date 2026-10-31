"""Experiment definitions (IMPLEMENTATION_PLAN.md §7). Every experiment writes raw data first;
tables and figures are produced only from those files (evaluation/comparison.py, visualization/).

Seeds: trial k of a sweep uses the same seed for every sweep value (common random numbers), so
curves differ only by the swept parameter. Seeds are written to the raw data.
"""

from __future__ import annotations

import csv
import gzip
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

import config as cfg
from algorithms import improved_dvhop, traditional_dvhop
from algorithms.common import anchor_hopsize_eq3
from evaluation.metrics import error_2d_eq17, error_3d, normalized_error
from simulation.simulation_engine import ALGORITHMS, TrialResult, build_network, run_trial

RAW = Path("results/raw_data")
SWEEP_IDS = {"anchor_ratio": 1, "comm_radius": 2, "n_total": 3}


def trial_seed(master: int, experiment_id: int, trial: int) -> int:
    return int(np.random.SeedSequence((master, experiment_id, trial)).generate_state(1)[0])


# --- row builders -------------------------------------------------------------------------------
def summary_rows(trial: TrialResult, extra: dict) -> list[dict]:
    net = trial.network
    rows = []
    for name in ALGORITHMS:
        res = trial.results[name]
        err = trial.errors(name)
        err2d = trial.errors(name, planar=True)
        rows.append({
            **extra, "seed": trial.seed, "algorithm": name,
            "n_total": len(net.positions), "n_anchors": int(net.is_anchor.sum()),
            "comm_radius": net.comm_radius,
            "n_unknown": len(net.unknown_idx), "n_localized": int(res.localized.sum()),
            "n_common": int(trial.common_mask.sum()),
            "mean_error_3d_m": float(err.mean()) if err.size else float("nan"),
            "mean_error_2d_eq17_m": float(err2d.mean()) if err2d.size else float("nan"),
            "normalized_error": normalized_error(err, net.comm_radius),
            "runtime_s": res.runtime_s,
            **{k: v for k, v in res.diagnostics.items() if np.isscalar(v)},
        })
    return rows


def node_rows(trial: TrialResult, extra: dict) -> list[dict]:
    net = trial.network
    truth = net.positions[net.unknown_idx]
    rows = []
    for name in ALGORITHMS:
        res = trial.results[name]
        e3 = error_3d(res.estimates, truth)
        e2 = error_2d_eq17(res.estimates, truth)
        for u, node in enumerate(net.unknown_idx):
            rows.append({
                **extra, "seed": trial.seed, "algorithm": name, "node": int(node),
                "x": truth[u, 0], "y": truth[u, 1], "z": truth[u, 2],
                "x_est": res.estimates[u, 0], "y_est": res.estimates[u, 1], "z_est": res.estimates[u, 2],
                "localized": bool(res.localized[u]), "in_common_set": bool(trial.common_mask[u]),
                "error_3d_m": e3[u], "error_2d_eq17_m": e2[u],
            })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        fields.extend(k for k in row if k not in fields)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_meta(name: str, experiment: cfg.ExperimentConfig, **info) -> None:
    meta = {"experiment": name, "config": asdict(experiment), **info,
            "generated": time.strftime("%Y-%m-%d %H:%M:%S")}
    (RAW / f"{name}_meta.json").write_text(json.dumps(meta, indent=2, default=str))


# --- parallel worker ----------------------------------------------------------------------------
def _sweep_job(args):
    seed, net_cfg, pso_cfg, imp_cfg, extra = args
    trial = run_trial(seed, net_cfg, pso_cfg, imp_cfg)
    return summary_rows(trial, extra), node_rows(trial, extra)


def _workers() -> int:
    return max(1, (os.cpu_count() or 2) - 2)


def run_sweep(parameter: str, values, experiment: cfg.ExperimentConfig, label: str | None = None,
              n_trials: int | None = None) -> None:
    """X1-X3: Fig. 12(a)-(c) analogues. Runtimes from this parallel run are NOT reported."""
    label = label or f"sweep_{parameter}"
    n_trials = n_trials or experiment.n_trials
    jobs = []
    for value in values:
        net_cfg = replace(experiment.network, **{parameter: type(getattr(experiment.network, parameter))(value)})
        for t in range(n_trials):
            seed = trial_seed(experiment.master_seed, SWEEP_IDS.get(parameter, 9), t)
            jobs.append((seed, net_cfg, experiment.pso, experiment.improved,
                         {"sweep": parameter, "value": value, "trial": t}))
    summaries, nodes = [], []
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=_workers()) as pool:
        for s_rows, n_rows in pool.map(_sweep_job, jobs, chunksize=2):
            summaries.extend(s_rows)
            nodes.extend(n_rows)
    write_csv(RAW / f"{label}_trials.csv", summaries)
    write_csv(RAW / f"{label}_nodes.csv.gz", nodes)
    write_meta(label, experiment, parameter=parameter, values=list(values), n_trials=n_trials,
               wall_time_s=time.perf_counter() - start)
    print(f"[{label}] {len(jobs)} trials in {time.perf_counter() - start:.0f} s")


def run_single_deployment(experiment: cfg.ExperimentConfig) -> None:
    """X4 (Fig. 10), X5 (Fig. 11), X6 (Fig. 9): one deployment at the default configuration."""
    seed = trial_seed(experiment.master_seed, 20, 0)
    trial = run_trial(seed, experiment.network, experiment.pso, experiment.improved)
    write_csv(RAW / "single_deployment_nodes.csv", node_rows(trial, {}))
    net = trial.network
    write_csv(RAW / "single_deployment_anchors.csv", [
        {"node": int(i), "x": p[0], "y": p[1], "z": p[2]}
        for i, p in zip(net.anchor_idx, net.anchor_positions)])
    write_meta("single_deployment", experiment, seed=seed)
    print("[single_deployment] done")


def run_runtime_tests(experiment: cfg.ExperimentConfig, n_tests: int = 3, n_extra: int = 20) -> None:
    """X7 (Table 1 analogue): sequential runs so timings are not distorted by parallel load."""
    rows = []
    for t in range(n_tests + n_extra):
        seed = trial_seed(experiment.master_seed, 30, t)
        trial = run_trial(seed, experiment.network, experiment.pso, experiment.improved)
        group = f"Test {t + 1}" if t < n_tests else "extra"
        rows.extend(summary_rows(trial, {"test": group, "trial": t}))
    write_csv(RAW / "runtime_tests_trials.csv", rows)
    write_meta("runtime_tests", experiment, n_tests=n_tests, n_extra=n_extra,
               cpu=os.environ.get("PROCESSOR_IDENTIFIER", "unknown"))
    print("[runtime_tests] done")


def run_convergence(experiment: cfg.ExperimentConfig) -> None:
    """X8 (Fig. 8, partial): Eq. (16) global-best value vs iteration, LDW-PSO vs classic w = 0.7."""
    seed = trial_seed(experiment.master_seed, 40, 0)
    rows = []
    for label, pso_cfg in (("LDW-PSO (w 0.9->0.4)", experiment.pso),
                           ("classic PSO (w = 0.7, assumption)", replace(experiment.pso, constant_inertia=0.7))):
        deploy_seq, pso_seq = np.random.SeedSequence(seed).spawn(2)
        net = build_network(experiment.network, np.random.default_rng(deploy_seq))
        res = improved_dvhop.localize(net, "pso", experiment.improved, pso_cfg,
                                      np.random.default_rng(pso_seq), keep_pso_history=True)
        hist = res.diagnostics["pso_history"]
        for it in range(hist.shape[1]):
            rows.append({"variant": label, "iteration": it, "mean_objective_m": hist[:, it].mean(),
                         "median_objective_m": float(np.median(hist[:, it]))})
    write_csv(RAW / "pso_convergence.csv", rows)
    write_meta("pso_convergence", experiment, seed=seed)
    print("[pso_convergence] done")


def _distance_diag_job(args):
    seed, net_cfg = args
    net = build_network(net_cfg, np.random.default_rng(np.random.SeedSequence(seed).spawn(2)[0]))
    anchors, unknowns = net.anchor_idx, net.unknown_idx
    true = net.dist[np.ix_(unknowns, anchors)]
    trad = traditional_dvhop.localize(net)
    hcmc = improved_dvhop.localize(net, "mle")
    mcr_hops = improved_dvhop.mcr_hop_counts(net)
    thresholds = improved_dvhop.hop_thresholds(net.anchor_positions, net.side_length, net.comm_radius)
    weighted_int, _ = improved_dvhop.weighted_hopsize(net.anchor_positions, trad.hops[:, anchors],
                                                      thresholds, net.comm_radius)
    variants = {
        "DV-HOP (integer hops, Eq.3, Eq.2)": trad.est_dist,
        "MCR hops only (Eq.3, Eq.2)": traditional_dvhop.estimate_distances_eq2(
            anchor_hopsize_eq3(net.anchor_positions, mcr_hops[:, anchors]), mcr_hops[:, unknowns]),
        "Weighted AHD only (integer hops, Eqs.7-11)": improved_dvhop.estimate_distances_eq11(
            weighted_int, trad.hops[:, unknowns]),
        "HCMCDV-HOP full (MCR, Eqs.7-11)": hcmc.est_dist,
    }
    rows = []
    for name, est in variants.items():
        err = est - true
        rows.append({"comm_radius": net.comm_radius, "seed": seed, "variant": name,
                     "bias_m": float(np.nanmean(err)), "mae_m": float(np.nanmean(np.abs(err)))})
    rows.append({"comm_radius": net.comm_radius, "seed": seed, "variant": "_hopsize",
                 "trad_eq3_mean": float(np.nanmean(trad.hopsize)),
                 "hcmc_weighted_mean": float(np.nanmean(hcmc.hopsize))})
    return rows


def run_distance_diagnostic(experiment: cfg.ExperimentConfig, n_trials: int = 20) -> None:
    """Diagnostic (not a paper experiment): which improvement step changes UN->AN distance error."""
    jobs = [(trial_seed(experiment.master_seed, 50, t), replace(experiment.network, comm_radius=r))
            for r in cfg.COMM_RADIUS_SWEEP for t in range(n_trials)]
    rows = []
    with ProcessPoolExecutor(max_workers=_workers()) as pool:
        for r in pool.map(_distance_diag_job, jobs, chunksize=4):
            rows.extend(r)
    write_csv(RAW / "diagnostic_distance_components.csv", rows)
    write_meta("diagnostic_distance_components", experiment, n_trials=n_trials)
    print("[diagnostic_distance_components] done")


def run_sensitivity(experiment: cfg.ExperimentConfig, n_trials: int = 20) -> None:
    """Sensitivity to approved assumptions: Q1 (MCR mode) and Q10 (PSO size)."""
    variants = {
        "baseline (anchor_only, N=30, MaxIt=300)": experiment,
        "Q1 all_links MCR": replace(experiment, improved=replace(experiment.improved, mcr_mode="all_links")),
        "Q10 N=20, MaxIt=100": replace(experiment, pso=replace(experiment.pso, n_particles=20, max_iter=100)),
        "Q10 N=50, MaxIt=500": replace(experiment, pso=replace(experiment.pso, n_particles=50, max_iter=500)),
    }
    jobs = []
    for label, exp in variants.items():
        for t in range(n_trials):
            jobs.append((trial_seed(experiment.master_seed, 60, t), exp.network, exp.pso, exp.improved,
                         {"variant": label, "trial": t}))
    rows = []
    with ProcessPoolExecutor(max_workers=_workers()) as pool:
        for s_rows, _ in pool.map(_sweep_job, jobs, chunksize=2):
            rows.extend(s_rows)
    write_csv(RAW / "sensitivity_trials.csv", rows)
    write_meta("sensitivity", experiment, n_trials=n_trials, variants=list(variants))
    print("[sensitivity] done")


def run_all(experiment: cfg.ExperimentConfig | None = None) -> None:
    experiment = experiment or cfg.ExperimentConfig()
    RAW.mkdir(parents=True, exist_ok=True)
    run_single_deployment(experiment)
    run_convergence(experiment)
    run_runtime_tests(experiment)
    run_sweep("anchor_ratio", cfg.ANCHOR_RATIO_SWEEP, experiment)
    run_sweep("comm_radius", cfg.COMM_RADIUS_SWEEP, experiment)
    run_sweep("n_total", cfg.TOTAL_NODES_SWEEP, experiment)
    run_distance_diagnostic(experiment)
    run_sensitivity(experiment)
