import unittest

import numpy as np

from config import NetworkConfig
from simulation.deployment import deploy_nodes
from simulation.network import Network, adjacency_matrix, integer_hop_counts, pairwise_distances


def line_positions(xs):
    return np.array([[x, 0.0, 0.0] for x in xs], dtype=float)


class TestConnectivity(unittest.TestCase):
    def test_pairwise_distances(self):
        d = pairwise_distances(np.array([[0, 0, 0], [3, 4, 0], [0, 0, 12]], float))
        np.testing.assert_allclose(d[0, 1], 5.0)
        np.testing.assert_allclose(d[0, 2], 12.0)
        np.testing.assert_allclose(d, d.T)

    def test_adjacency_inclusive_radius_no_self_loops(self):
        d = pairwise_distances(line_positions([0, 10, 25]))
        adj = adjacency_matrix(d, 15.0)
        self.assertTrue(adj[0, 1] and adj[1, 2])  # 10 m and exactly 15 m
        self.assertFalse(adj[0, 2])
        self.assertFalse(adj.diagonal().any())

    def test_integer_hops_on_line(self):
        d = pairwise_distances(line_positions([0, 10, 20, 30]))
        hops = integer_hop_counts(adjacency_matrix(d, 15.0), np.array([0, 3]))
        np.testing.assert_array_equal(hops[0], [0, 1, 2, 3])
        np.testing.assert_array_equal(hops[1], [3, 2, 1, 0])

    def test_disconnected_node_is_infinite(self):
        d = pairwise_distances(line_positions([0, 10, 90]))
        hops = integer_hop_counts(adjacency_matrix(d, 15.0), np.array([0]))
        self.assertTrue(np.isinf(hops[0, 2]))

    def test_shortest_not_first_path(self):
        # Triangle: 0-1 direct (1 hop) even though 0-2-1 also exists.
        pos = np.array([[0, 0, 0], [10, 0, 0], [5, 5, 0]], float)
        hops = integer_hop_counts(adjacency_matrix(pairwise_distances(pos), 12.0), np.array([0]))
        np.testing.assert_array_equal(hops[0], [0, 1, 1])

    def test_invalid_radius(self):
        with self.assertRaises(ValueError):
            adjacency_matrix(np.zeros((2, 2)), 0.0)


class TestDeployment(unittest.TestCase):
    def test_counts_bounds_and_reproducibility(self):
        cfg = NetworkConfig(n_total=100, anchor_ratio=0.25, side_length=100.0)
        p1, a1 = deploy_nodes(cfg, np.random.default_rng(7))
        p2, a2 = deploy_nodes(cfg, np.random.default_rng(7))
        self.assertEqual(p1.shape, (100, 3))
        self.assertEqual(a1.sum(), 25)
        self.assertTrue((p1 >= 0).all() and (p1 <= 100).all())
        np.testing.assert_array_equal(p1, p2)
        np.testing.assert_array_equal(a1, a2)

    def test_invalid_configs(self):
        with self.assertRaises(ValueError):
            NetworkConfig(comm_radius=-1)
        with self.assertRaises(ValueError):
            NetworkConfig(anchor_ratio=1.0)
        with self.assertRaises(ValueError):
            deploy_nodes(NetworkConfig(n_total=4, anchor_ratio=0.1), np.random.default_rng(0))

    def test_network_requires_anchor(self):
        with self.assertRaises(ValueError):
            Network(np.zeros((3, 3)), np.zeros(3, bool), 10.0, 100.0)


if __name__ == "__main__":
    unittest.main()
