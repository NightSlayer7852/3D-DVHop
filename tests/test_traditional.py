"""Hand-checked tests for traditional 3D DV-HOP (Eqs. 2, 3, 5, 6)."""

import unittest

import numpy as np

from algorithms import traditional_dvhop
from algorithms.common import anchor_hopsize_eq3, mle_localize_all, mle_position, nearest_anchor
from simulation.network import Network

TETRA = np.array([[0, 0, 0], [60, 0, 0], [0, 60, 0], [0, 0, 60], [60, 60, 60]], float)


class TestEq3Hopsize(unittest.TestCase):
    def test_hand_example(self):
        # anchors at x = 0, 30, 70 ; hops 0-1: 1, 0-2: 3, 1-2: 2
        pos = np.array([[0, 0, 0], [30, 0, 0], [70, 0, 0]], float)
        hops = np.array([[0, 1, 3], [1, 0, 2], [3, 2, 0]], float)
        hs = anchor_hopsize_eq3(pos, hops)
        np.testing.assert_allclose(hs, [(30 + 70) / 4, (30 + 40) / 3, (70 + 40) / 5])

    def test_unreachable_anchor_excluded_and_isolated_nan(self):
        pos = np.array([[0, 0, 0], [30, 0, 0], [99, 0, 0]], float)
        hops = np.array([[0, 2, np.inf], [2, 0, np.inf], [np.inf, np.inf, 0]], float)
        hs = anchor_hopsize_eq3(pos, hops)
        np.testing.assert_allclose(hs[:2], [15.0, 15.0])
        self.assertTrue(np.isnan(hs[2]))


class TestNearestAnchor(unittest.TestCase):
    def test_tie_breaks_to_lowest_index_and_unreachable(self):
        hops = np.array([[2, np.inf, 1], [1, np.inf, 1], [1, np.inf, 3]], float)
        np.testing.assert_array_equal(nearest_anchor(hops), [1, -1, 0])


class TestMLE(unittest.TestCase):
    def test_exact_distances_recover_point(self):
        target = np.array([17.0, 41.0, 29.0])
        d = np.linalg.norm(TETRA - target, axis=1)
        np.testing.assert_allclose(mle_position(TETRA, d), target, atol=1e-9)

    def test_matrix_rows_match_eq6(self):
        # 4 anchors, b row 1 computed by hand for anchor 1 vs reference anchor 4.
        anchors = TETRA[:4]
        d = np.array([10.0, 20.0, 30.0, 40.0])
        x = mle_position(anchors, d)
        a = 2 * (anchors[:3] - anchors[3])
        b0 = 0 - 0 + 0 - 0 + 0 - 3600 + 40**2 - 10**2
        b = np.array([b0, 3600 - 3600 + 1600 - 400, 0 + 1600 - 900])
        np.testing.assert_allclose(x, np.linalg.solve(a.T @ a, a.T @ b))

    def test_too_few_and_coplanar_anchors(self):
        self.assertIsNone(mle_position(TETRA[:3], np.ones(3)))
        coplanar = np.array([[0, 0, 0], [50, 0, 0], [0, 50, 0], [50, 50, 0], [25, 10, 0]], float)
        self.assertIsNone(mle_position(coplanar, np.ones(5) * 10))

    def test_localize_all_skips_insufficient(self):
        est = np.array([[1, 2, 3, 4, 5], [1, 2, 3, np.nan, np.nan]], float)
        _, localized, singular = mle_localize_all(TETRA, est)
        np.testing.assert_array_equal(localized, [True, False])
        self.assertEqual(singular, 0)


class TestTraditionalPipeline(unittest.TestCase):
    def _network(self):
        rng = np.random.default_rng(3)
        pos = rng.uniform(0, 100, (80, 3))
        is_anchor = np.zeros(80, bool)
        is_anchor[:16] = True
        return Network(pos, is_anchor, 40.0, 100.0)

    def test_distances_follow_eq2(self):
        net = self._network()
        res = traditional_dvhop.localize(net)
        hops_au = res.hops[:, net.unknown_idx]
        nearest = nearest_anchor(hops_au)
        for u in range(len(net.unknown_idx)):
            expected = res.hopsize[nearest[u]] * hops_au[:, u]
            np.testing.assert_allclose(res.est_dist[u], expected)

    def test_hops_are_integers(self):
        res = traditional_dvhop.localize(self._network())
        finite = res.hops[np.isfinite(res.hops)]
        np.testing.assert_array_equal(finite, np.round(finite))

    def test_isolated_unknown_not_localized(self):
        pos = np.vstack([TETRA, [[30, 30, 30], [99, 99, 0]]])
        is_anchor = np.array([1, 1, 1, 1, 1, 0, 0], bool)
        net = Network(pos, is_anchor, 70.0, 100.0)
        res = traditional_dvhop.localize(net)
        self.assertTrue(res.localized[0])
        self.assertFalse(res.localized[1])  # (99,99,0) is > 70 m from every node
        self.assertTrue(np.isnan(res.estimates[1]).all())


if __name__ == "__main__":
    unittest.main()
