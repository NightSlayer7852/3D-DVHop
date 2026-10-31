"""One simulation trial: deploy once, run every algorithm on the SAME network.

Common random numbers: deployment and PSO randomness both derive from the trial seed,
so a trial is bit-reproducible and all algorithms see identical conditions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from algorithms import improved_dvhop, traditional_dvhop
from algorithms.common import LocalizationResult
from config import ImprovedConfig, NetworkConfig, PSOConfig
from evaluation.metrics import error_2d_eq17, error_3d
from simulation.deployment import deploy_nodes
from simulation.network import Network

ALGORITHMS = (traditional_dvhop.NAME, improved_dvhop.NAME_MLE, improved_dvhop.NAME_PSO)


@dataclass
class TrialResult:
    seed: int
    network: Network
    results: dict[str, LocalizationResult]
    common_mask: np.ndarray  # (n_u,) UNs localised by every algorithm (Q14 evaluation set)

    def errors(self, name: str, common_only: bool = True, planar: bool = False) -> np.ndarray:
        res = self.results[name]
        mask = self.common_mask if common_only else res.localized
        truth = self.network.positions[self.network.unknown_idx][mask]
        metric = error_2d_eq17 if planar else error_3d
        return metric(res.estimates[mask], truth)


def build_network(config: NetworkConfig, rng: np.random.Generator) -> Network:
    positions, is_anchor = deploy_nodes(config, rng)
    return Network(positions, is_anchor, config.comm_radius, config.side_length)


def run_trial(
    seed: int,
    network_config: NetworkConfig,
    pso_config: PSOConfig | None = None,
    improved_config: ImprovedConfig | None = None,
    keep_pso_history: bool = False,
) -> TrialResult:
    deploy_seq, pso_seq = np.random.SeedSequence(seed).spawn(2)
    network = build_network(network_config, np.random.default_rng(deploy_seq))
    pso_rng = np.random.default_rng(pso_seq)

    runs = {
        traditional_dvhop.NAME: lambda: traditional_dvhop.localize(network),
        improved_dvhop.NAME_MLE: lambda: improved_dvhop.localize(
            network, "mle", improved_config
        ),
        improved_dvhop.NAME_PSO: lambda: improved_dvhop.localize(
            network, "pso", improved_config, pso_config, pso_rng, keep_pso_history
        ),
    }
    results: dict[str, LocalizationResult] = {}
    for name, run in runs.items():
        start = time.perf_counter()
        result = run()
        result.runtime_s = time.perf_counter() - start
        results[name] = result

    common = np.logical_and.reduce([r.localized for r in results.values()])
    return TrialResult(seed, network, results, common)
