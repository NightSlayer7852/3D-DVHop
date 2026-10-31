"""Entry point for the 3D DV-HOP reproduction (Wu et al., IEEE Access 2023).

    python main.py run        # run all experiments -> results/raw_data
    python main.py report     # tables + figures from raw data -> results/tables, results/figures
    python main.py all        # both
    python main.py run --experiment sweep_comm_radius   # a single experiment
    python main.py run --trials 5                        # quick smoke run (fewer Monte-Carlo trials)
"""

from __future__ import annotations

import os

# One BLAS thread per worker process; parallelism comes from the process pool.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import argparse  # noqa: E402
from dataclasses import replace  # noqa: E402

import config as cfg  # noqa: E402
from evaluation import experiments  # noqa: E402

SINGLE = {
    "single_deployment": experiments.run_single_deployment,
    "pso_convergence": experiments.run_convergence,
    "runtime_tests": experiments.run_runtime_tests,
    "sweep_anchor_ratio": lambda e: experiments.run_sweep("anchor_ratio", cfg.ANCHOR_RATIO_SWEEP, e),
    "sweep_comm_radius": lambda e: experiments.run_sweep("comm_radius", cfg.COMM_RADIUS_SWEEP, e),
    "sweep_n_total": lambda e: experiments.run_sweep("n_total", cfg.TOTAL_NODES_SWEEP, e),
    "distance_diagnostic": experiments.run_distance_diagnostic,
    "sensitivity": experiments.run_sensitivity,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("run", "report", "all"))
    parser.add_argument("--experiment", choices=sorted(SINGLE), help="run only this experiment")
    parser.add_argument("--trials", type=int, help="Monte-Carlo trials per sweep point (default 50)")
    args = parser.parse_args()

    experiment = cfg.ExperimentConfig()
    if args.trials:
        experiment = replace(experiment, n_trials=args.trials)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if args.command in ("run", "all"):
        if args.experiment:
            SINGLE[args.experiment](experiment)
        else:
            experiments.run_all(experiment)
    if args.command in ("report", "all"):
        from evaluation import comparison
        from visualization import result_plots

        comparison.build_tables()
        result_plots.build_all_figures()


if __name__ == "__main__":
    main()
