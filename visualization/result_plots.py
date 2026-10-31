"""Result figures, built only from results/raw_data."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from evaluation.comparison import RAW, SWEEP_LABELS, read_csv
from evaluation.metrics import mean_ci95
from simulation.simulation_engine import ALGORITHMS
from visualization.localization_visualization import plot_error_lines_3d, plot_projection_panels
from visualization.network_visualization import plot_network_3d
from visualization.style import INK_2, SERIES, apply_style, save

FIGURES = Path("results/figures")


def _sweep_curves(parameter: str):
    data = read_csv(RAW / f"sweep_{parameter}_trials.csv")
    values = np.array(sorted(set(data["value"])))
    curves = {}
    for alg in ALGORITHMS:
        stats = [mean_ci95(data["normalized_error"][(data["value"] == v) & (data["algorithm"] == alg)])
                 for v in values]
        curves[alg] = (np.array([s[0] for s in stats]), np.array([s[2] for s in stats]))
    n_trials = int(((data["value"] == values[0]) & (data["algorithm"] == ALGORITHMS[0])).sum())
    return values, curves, n_trials


def _draw_sweep(ax, parameter: str) -> int:
    values, curves, n_trials = _sweep_curves(parameter)
    for alg, (mean, ci) in curves.items():
        style = SERIES[alg]
        ax.fill_between(values, mean - ci, mean + ci, color=style["color"], alpha=0.15, linewidth=0)
        ax.plot(values, mean, label=alg, **style)
    ax.set_xlabel(SWEEP_LABELS[parameter])
    ax.set_ylabel("Normalised positioning error (mean error / R)")
    ax.set_ylim(bottom=0)
    return n_trials


def plot_sweeps() -> None:
    params = [p for p in SWEEP_LABELS if (RAW / f"sweep_{p}_trials.csv").exists()]
    if not params:
        return
    apply_style()
    fig, axes = plt.subplots(1, len(params), figsize=(5.2 * len(params), 4.4))
    axes = np.atleast_1d(axes)
    letters = "abc"
    for k, (ax, p) in enumerate(zip(axes, params)):
        n = _draw_sweep(ax, p)
        ax.set_title(f"({letters[k]}) {SWEEP_LABELS[p]}  ·  {n} trials/point")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(labels), bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Normalised error vs network parameters (Fig. 12 analogue; shaded band = 95% CI)",
                 color=INK_2)
    save(fig, FIGURES / "fig12_sweeps_combined.png")
    for p in params:
        fig, ax = plt.subplots(figsize=(6, 4.4))
        n = _draw_sweep(ax, p)
        ax.set_title(f"Normalised error vs {SWEEP_LABELS[p].lower()} ({n} trials/point, 95% CI)")
        ax.legend(loc="upper right")
        save(fig, FIGURES / f"fig12_sweep_{p}.png")


def plot_single_deployment() -> None:
    path = RAW / "single_deployment_nodes.csv"
    if not path.exists():
        return
    nodes = read_csv(path)
    anchors = read_csv(RAW / "single_deployment_anchors.csv")
    anchor_xyz = np.c_[anchors["x"], anchors["y"], anchors["z"]]
    meta = json.loads((RAW / "single_deployment_meta.json").read_text())
    side = meta["config"]["network"]["side_length"]
    radius = meta["config"]["network"]["comm_radius"]
    first = nodes["algorithm"] == ALGORITHMS[0]
    unknown_xyz = np.c_[nodes["x"][first], nodes["y"][first], nodes["z"][first]]

    # Fig. 9(a) analogue
    plot_network_3d(unknown_xyz, anchor_xyz, side,
                    f"Node distribution in 3D space (seed {meta['seed']})", FIGURES / "fig09a_network_3d.png")

    # Fig. 9(b) analogue: per-node relative error (delta / R) of HCMSPSO-DV-HOP
    apply_style()
    sel = (nodes["algorithm"] == ALGORITHMS[2]) & nodes["in_common_set"]
    rel = nodes["error_3d_m"][sel] / radius
    fig, ax = plt.subplots(figsize=(6.4, 4))
    ax.scatter(np.arange(1, rel.size + 1), rel, s=14, color=SERIES[ALGORITHMS[2]]["color"],
               marker=SERIES[ALGORITHMS[2]]["marker"])
    ax.axhline(rel.mean(), color=INK_2, linewidth=1, linestyle=":")
    ax.annotate(f"mean {rel.mean():.3f}", (rel.size, rel.mean()), xytext=(0, 4),
                textcoords="offset points", ha="right", color=INK_2)
    ax.set_xlabel("Test-set node serial number")
    ax.set_ylabel("Relative error  δ / R")
    ax.set_title(f"{ALGORITHMS[2]}: per-node relative error (Fig. 9(b) analogue)")
    ax.set_ylim(bottom=0)
    save(fig, FIGURES / "fig09b_relative_error.png")

    # Fig. 10 analogue: per-node error (m) for the first 60 common-set UNs
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    common_nodes = np.sort(nodes["node"][(nodes["algorithm"] == ALGORITHMS[0]) & nodes["in_common_set"]])[:60]
    for alg in ALGORITHMS:
        a = nodes["algorithm"] == alg
        err = np.array([nodes["error_3d_m"][a & (nodes["node"] == n)][0] for n in common_nodes])
        ax.plot(np.arange(1, err.size + 1), err, label=f"{alg} (mean {err.mean():.1f} m)",
                markersize=4, linewidth=1.2, **SERIES[alg])
    ax.set_xlabel("Node number")
    ax.set_ylabel("3D positioning error (m)")
    ax.set_title("Per-node positioning error, 60 unknown nodes (Fig. 10 analogue)")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right")
    save(fig, FIGURES / "fig10_per_node_error.png")

    # Fig. 11 analogue
    plot_projection_panels(nodes, anchor_xyz, side, FIGURES / "fig11_positioning_xy.png")
    plot_error_lines_3d(nodes, anchor_xyz, side, FIGURES / "fig11_positioning_3d.png")


def plot_convergence() -> None:
    path = RAW / "pso_convergence.csv"
    if not path.exists():
        return
    data = read_csv(path)
    apply_style()
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    variants = list(dict.fromkeys(data["variant"]))
    styles = {variants[0]: (SERIES[ALGORITHMS[2]], 3, 1.6), variants[1]: (SERIES[ALGORITHMS[0]], 2, 3.2)}
    for variant in reversed(variants):  # LDW-PSO drawn last, on top
        style, z, width = styles[variant]
        sel = data["variant"] == variant
        y = data["mean_objective_m"][sel]
        ax.plot(data["iteration"][sel], y, color=style["color"], linestyle=style["linestyle"],
                linewidth=width, zorder=z,
                label=f"{variant}: start {y[0]:.2f} m, final {y[-1]:.3f} m")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Eq. (16) objective, mean over UNs (m)")
    ax.set_title("PSO convergence on one deployment (Fig. 8 partial analogue)")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right")
    save(fig, FIGURES / "fig08_pso_convergence.png")


def plot_distance_diagnostic() -> None:
    path = RAW / "diagnostic_distance_components.csv"
    if not path.exists():
        return
    data = read_csv(path)
    variants = [v for v in dict.fromkeys(data["variant"]) if not v.startswith("_")]
    radii = np.array(sorted(set(data["comm_radius"])))
    palette = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    markers = ["o", "s", "^", "D"]
    lines = ["-", "--", "-.", ":"]
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for k, v in enumerate(variants):
        for ax, col in zip(axes, ("mae_m", "bias_m")):
            y = [np.mean(data[col][(data["variant"] == v) & (data["comm_radius"] == r)]) for r in radii]
            ax.plot(radii, y, color=palette[k], marker=markers[k], linestyle=lines[k], label=v)
    axes[0].set_ylabel("Mean absolute error of UN→AN distance (m)")
    axes[1].set_ylabel("Bias of UN→AN distance (m)")
    axes[1].axhline(0, color=INK_2, linewidth=0.8)
    for ax in axes:
        ax.set_xlabel("Communication radius R (m)")
    axes[0].set_ylim(bottom=0)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Diagnostic: distance-estimate error by improvement component (not a paper experiment)",
                 color=INK_2)
    save(fig, FIGURES / "diag_distance_components.png")


def build_all_figures() -> None:
    plot_sweeps()
    plot_single_deployment()
    plot_convergence()
    plot_distance_diagnostic()
    print(f"figures written to {FIGURES}")
