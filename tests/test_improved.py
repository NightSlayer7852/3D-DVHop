"""Hand-checked tests for the improvements (Eqs. 7-11, MCR hop counting)."""

import unittest

import numpy as np

from algorithms import improved_dvhop as imp
from config import ImprovedConfig, PSOConfig
from simulation.network import Network


def line_network(xs, n_anchor, radius):
    pos = np.array([[x, 0.0, 0.0] for x in xs], float)
    is_anchor = np.zeros(len(xs), bool)
    is_anchor[:n_anchor] = True
    return Network(pos, is_anchor, radius, 100.0)


class TestMCRHops(unittest.TestCase):
    def test_hop_value_levels(self):
        r = 30.0
        d = np.array([0.2 * r, r / 3, 0.5 * r, 2 * r / 3, 0.9 * r, r, 1.5 * r])
        np.testing.assert_allclose(
            imp.mcr_hop_value(d, r), [1 / 3, 1 / 3, 2 / 3, 2 / 3, 1, 1, np.inf]
        )

    def test_anchor_only_hand_example(self):
        # anchor at 0; nodes at 5, 10, 20; R = 15 (R/3 = 5, 2R/3 = 10)
        net = line_network([0, 5, 10, 20], 1, 15.0)
        hops = imp.mcr_hop_counts(net, "anchor_only")
        # node 20: min(1/3 + 1 via node 5, 2/3 + 1 via node 10) = 4/3
        np.testing.assert_allclose(hops[0], [0, 1 / 3, 2 / 3, 4 / 3])

    def test_anchor_only_relays_add_whole_hops(self):
        # anchor at 0; R = 15 (R/3 = 5, 2R/3 = 10); only the first link is fractional.
        net = line_network([0, 4, 8, 12, 22], 1, 15.0)
        hops = imp.mcr_hop_counts(net, "anchor_only")
        # direct: 4 m -> 1/3, 8 m -> 2/3, 12 m -> 1
        np.testing.assert_allclose(hops[0, :4], [0, 1 / 3, 2 / 3, 1])
        # node 22: via 8 (2/3 + 1 whole relay hop, 14 m) = 5/3 ; via 12 = 2 ; 4 is 18 m away
        np.testing.assert_allclose(hops[0, 4], 5 / 3)

    def test_all_links_mode(self):
        net = line_network([0, 4, 8, 12, 26], 1, 15.0)
        hops = imp.mcr_hop_counts(net, "all_links")
        # 0->12 is 12 m: 1 hop direct or 0->4->8->12 = 3 x 1/3 = 1 ; 12->26 = 14 m -> 1 => 2
        # 0->8 (2/3) ->26? 18 m > R. So min is 2.
        np.testing.assert_allclose(hops[0, 4], 2.0)
        np.testing.assert_allclose(hops[0, 2], 2 / 3)

    def test_mcr_never_exceeds_integer_hops(self):
        rng = np.random.default_rng(1)
        pos = rng.uniform(0, 100, (60, 3))
        is_anchor = np.zeros(60, bool)
        is_anchor[:10] = True
        net = Network(pos, is_anchor, 35.0, 100.0)
        from simulation.network import integer_hop_counts

        integer = integer_hop_counts(net.adjacency, net.anchor_idx)
        mcr = imp.mcr_hop_counts(net)
        finite = np.isfinite(integer)
        self.assertTrue(np.all(mcr[finite] <= integer[finite] + 1e-12))
        np.testing.assert_array_equal(np.isfinite(mcr), finite)  # same reachability
        # physical bound: hop value >= distance / R
        d = net.dist[net.anchor_idx]
        self.assertTrue(np.all(mcr[finite] >= d[finite] / 35.0 - 1e-12))


class TestEq7Threshold(unittest.TestCase):
    def test_center_and_corner(self):
        t = imp.hop_thresholds(np.array([[50, 50, 50], [0, 0, 0]], float), 100.0, 50.0)
        np.testing.assert_allclose(t, [np.sqrt(3) * 50 / 50, np.sqrt(3) * 100 / 50])

    def test_eight_endpoints(self):
        self.assertEqual(imp.region_endpoints(10.0).shape, (8, 3))


class TestEqs8to10(unittest.TestCase):
    pos = np.array([[0, 0, 0], [30, 0, 0], [0, 40, 0]], float)

    def test_hand_example(self):
        # anchor 0: d = [30, 40], hops = [1, 2], R = 40
        # c = 1/(30/40 - 1) = -4 ; 1/(40/40 - 2) = -1 ; w = [0.8, 0.2]
        # Hopsize_0 = 0.8 * 30/1 + 0.2 * 40/2 = 28
        hops = np.array([[0, 1, 2], [1, 0, 2], [2, 2, 0]], float)
        hs, stats = imp.weighted_hopsize(self.pos, hops, np.full(3, 10.0), 40.0)
        self.assertAlmostEqual(hs[0], 28.0)
        self.assertEqual(stats["anchors_discarded"], 0)

    def test_weights_positive_and_normalised(self):
        d = np.array([30.0, 40.0])
        c = 1.0 / (d / 40.0 - np.array([1.0, 2.0]))
        self.assertTrue((c < 0).all())
        w = c / c.sum()
        self.assertTrue((w > 0).all())
        self.assertAlmostEqual(w.sum(), 1.0)

    def test_threshold_discards_anchor(self):
        hops = np.array([[0, 1, 2], [1, 0, 2], [2, 2, 0]], float)
        hs, stats = imp.weighted_hopsize(self.pos, hops, np.array([1.5, 10, 10]), 40.0)
        self.assertAlmostEqual(hs[0], 30.0)  # only anchor 1 retained -> d/h = 30
        self.assertEqual(stats["anchors_discarded"], 1)

    def test_fallback_when_all_discarded(self):
        hops = np.array([[0, 1, 2], [1, 0, 2], [2, 2, 0]], float)
        hs, stats = imp.weighted_hopsize(self.pos, hops, np.array([0.5, 10, 10]), 40.0)
        self.assertAlmostEqual(hs[0], 28.0)  # Q3: threshold skipped
        self.assertEqual(stats["threshold_fallback"], 1)

    def test_zero_denominator_excluded(self):
        pos = np.array([[0, 0, 0], [40, 0, 0], [0, 40, 0]], float)
        hops = np.array([[0, 1, 2], [1, 0, 2], [2, 2, 0]], float)  # 40/40 - 1 = 0
        hs, stats = imp.weighted_hopsize(pos, hops, np.full(3, 10.0), 40.0)
        self.assertAlmostEqual(hs[0], 20.0)  # only anchor 2: 40/2
        self.assertEqual(stats["zero_denominator"], 2)  # pair 0-1 seen from anchor 0 and from 1


class TestEq11(unittest.TestCase):
    def test_hand_example(self):
        hopsize = np.array([20.0, 30.0, 40.0])
        hops_au = np.array([[1.0, np.inf], [2.0, np.inf], [3.0, np.inf]])
        est = imp.estimate_distances_eq11(hopsize, hops_au)
        # nearest anchor of UN 0 is anchor 0 (1 hop)
        np.testing.assert_allclose(est[0], [20 * 1, 25 * 2, 30 * 3])
        self.assertTrue(np.isnan(est[1]).all())


class TestImprovedPipeline(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(5)
        pos = rng.uniform(0, 100, (80, 3))
        is_anchor = np.zeros(80, bool)
        is_anchor[:16] = True
        self.net = Network(pos, is_anchor, 40.0, 100.0)

    def test_mle_and_pso_run(self):
        mle = imp.localize(self.net, "mle")
        pso = imp.localize(self.net, "pso", pso_config=PSOConfig(max_iter=50),
                           rng=np.random.default_rng(0))
        self.assertEqual(mle.name, imp.NAME_MLE)
        self.assertEqual(pso.name, imp.NAME_PSO)
        self.assertTrue(pso.localized.all())
        est = pso.estimates[pso.localized]
        self.assertTrue(((est >= 0) & (est <= 100)).all())

    def test_pso_requires_rng(self):
        with self.assertRaises(ValueError):
            imp.localize(self.net, "pso")

    def test_bad_options(self):
        with self.assertRaises(ValueError):
            imp.localize(self.net, "magic")
        with self.assertRaises(ValueError):
            ImprovedConfig(mcr_mode="other")


if __name__ == "__main__":
    unittest.main()
