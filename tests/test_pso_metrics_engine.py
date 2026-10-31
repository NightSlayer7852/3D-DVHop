"""PSO (Eqs. 12-16), metrics and end-to-end reproducibility."""

import unittest

import numpy as np

from algorithms.pso import inertia_weight, ldw_pso, rms_objective
from config import NetworkConfig, PSOConfig
from evaluation.metrics import error_2d_eq17, error_3d, mean_ci95, normalized_error
from simulation.simulation_engine import ALGORITHMS, run_trial

ANCHORS = np.array(
    [[0, 0, 0], [100, 0, 0], [0, 100, 0], [0, 0, 100], [100, 100, 100], [50, 0, 100]], float
)


class TestPSO(unittest.TestCase):
    def test_objective_eq16_hand(self):
        p = np.array([[[0.0, 0.0, 0.0]]])
        est = np.array([[1.0, 100.0, 103.0, 0, 0, 0]])
        mask = np.array([[True, True, True, False, False, False]])
        # residuals: 0-1=-1, 100-100=0, 100-103=-3 -> sqrt((1+0+9)/3)
        np.testing.assert_allclose(rms_objective(p, ANCHORS, est, mask), [[np.sqrt(10 / 3)]])

    def test_inertia_weight_linear(self):
        cfg = PSOConfig(max_iter=100)
        self.assertAlmostEqual(inertia_weight(0, cfg), 0.9)
        self.assertAlmostEqual(inertia_weight(50, cfg), 0.65)
        self.assertAlmostEqual(inertia_weight(100, cfg), 0.4)
        self.assertEqual(inertia_weight(10, PSOConfig(constant_inertia=0.7)), 0.7)

    def test_converges_to_exact_solution(self):
        targets = np.array([[20.0, 30.0, 40.0], [75.0, 60.0, 10.0]])
        est = np.linalg.norm(targets[:, None, :] - ANCHORS[None], axis=2)
        mask = np.ones_like(est, bool)
        res = ldw_pso(ANCHORS, est, mask, (0, 100), PSOConfig(), np.random.default_rng(1))
        np.testing.assert_allclose(res.best_positions, targets, atol=0.05)
        self.assertTrue((np.diff(res.history, axis=1) <= 1e-12).all())  # gbest never worsens

    def test_reproducible(self):
        est = np.full((1, 6), 50.0)
        mask = np.ones((1, 6), bool)
        a = ldw_pso(ANCHORS, est, mask, (0, 100), PSOConfig(max_iter=30), np.random.default_rng(9))
        b = ldw_pso(ANCHORS, est, mask, (0, 100), PSOConfig(max_iter=30), np.random.default_rng(9))
        np.testing.assert_array_equal(a.best_positions, b.best_positions)

    def test_rejects_problem_without_anchors(self):
        with self.assertRaises(ValueError):
            ldw_pso(ANCHORS, np.zeros((1, 6)), np.zeros((1, 6), bool), (0, 100),
                    PSOConfig(), np.random.default_rng(0))


class TestMetrics(unittest.TestCase):
    def test_errors(self):
        est, true = np.array([[3.0, 4.0, 12.0]]), np.zeros((1, 3))
        np.testing.assert_allclose(error_3d(est, true), [13.0])
        np.testing.assert_allclose(error_2d_eq17(est, true), [5.0])
        self.assertAlmostEqual(normalized_error(np.array([10.0, 30.0]), 40.0), 0.5)
        self.assertTrue(np.isnan(normalized_error(np.array([]), 40.0)))

    def test_ci(self):
        mean, std, half = mean_ci95(np.array([1.0, 2.0, 3.0, np.nan]))
        self.assertAlmostEqual(mean, 2.0)
        self.assertAlmostEqual(std, 1.0)
        self.assertAlmostEqual(half, 1.96 / np.sqrt(3))


class TestEngine(unittest.TestCase):
    cfg = NetworkConfig(n_total=80, anchor_ratio=0.2, comm_radius=40.0)
    pso = PSOConfig(max_iter=40)

    def test_bit_reproducible(self):
        a = run_trial(11, self.cfg, self.pso)
        b = run_trial(11, self.cfg, self.pso)
        for name in ALGORITHMS:
            np.testing.assert_array_equal(a.results[name].estimates, b.results[name].estimates)

    def test_same_network_for_all_algorithms(self):
        trial = run_trial(12, self.cfg, self.pso)
        hops_reach = [np.isfinite(r.hops) for r in trial.results.values()]
        for h in hops_reach[1:]:
            np.testing.assert_array_equal(h, hops_reach[0])
        self.assertEqual(set(trial.results), set(ALGORITHMS))
        self.assertTrue(np.isfinite(trial.errors(ALGORITHMS[0])).all())


if __name__ == "__main__":
    unittest.main()
