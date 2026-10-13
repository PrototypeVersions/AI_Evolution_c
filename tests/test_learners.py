"""Study 1: correctness, determinism, equal compute and containment."""

import ast
import os
import pathlib
import unittest

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from learners import run as runner  # noqa: E402
from learners.arms import ARMS, FWD  # noqa: E402
from learners.net import MLP, softmax  # noqa: E402
from learners.world import SkillWorld  # noqa: E402

TINY = {"batch": 32, "n_eras": 10, "checkpoints": [5, 10], "eval_n": 300, "pop": 4,
        "teach_share": 0.5, "reset_shrink": 0.8, "reset_noise": 0.1, "fitness_window": 20,
        "regimes": {"novelty_interval": [2], "lifespan": [3]}, "lr": 0.003,
        "steps_per_era": 40, "probe_steps": 10, "frozen": False}


def numeric_grad(net, loss):
    g = np.zeros_like(net.theta)
    for k in range(len(net.theta)):
        old = net.theta[k]
        net.theta[k] = old + 1e-6
        up = loss()
        net.theta[k] = old - 1e-6
        down = loss()
        net.theta[k] = old
        g[k] = (up - down) / 2e-6
    return g


class TestNet(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(0)
        self.net = MLP(rng, lr=1e-3, sizes=(5, 7, 6, 4))
        self.x = rng.standard_normal((8, 5))
        self.y = rng.integers(0, 4, 8)

    def test_cross_entropy_gradient(self):
        net, x, y = self.net, self.x, self.y

        def loss():
            p = softmax(net.forward(x)[1])
            return -np.log(p[np.arange(8), y]).mean()

        acts, logits = net.forward(x)
        d = softmax(logits)
        d[np.arange(8), y] -= 1
        net.backward(acts, d / 8)
        self.assertLess(np.abs(numeric_grad(net, loss) - net.grad).max(), 1e-6)

    def test_teaching_gradient(self):
        net, x = self.net, self.x
        teacher = MLP(np.random.default_rng(1), lr=1e-3, sizes=(5, 7, 6, 4))
        t_acts, t_logits = teacher.forward(x)

        def loss():
            acts, logits = net.forward(x)
            p, q = softmax(t_logits), softmax(logits)
            total = (p * (np.log(p) - np.log(q))).sum(axis=1).mean()
            for l in (1, 2):
                total += np.mean((acts[l] - t_acts[l]) ** 2) / (np.mean(t_acts[l] ** 2) + 1e-8)
            return total

        acts, logits = net.forward(x)
        extra = {l: 2 * (acts[l] - t_acts[l]) / (np.mean(t_acts[l] ** 2) + 1e-8) / (8 * t_acts[l].shape[1])
                 for l in (1, 2)}
        net.backward(acts, (softmax(logits) - softmax(t_logits)) / 8, extra)
        self.assertLess(np.abs(numeric_grad(net, loss) - net.grad).max(), 1e-6)

    def test_copy_is_independent(self):
        c = self.net.copy()
        c.theta += 1.0
        c.W[0][0, 0] = 99.0
        self.assertNotEqual(self.net.W[0][0, 0], 99.0)
        self.assertEqual(c.theta[0], 99.0)  # views still point into the copy's vector

    def test_learns_a_task(self):
        world = SkillWorld(3, 2, 5)
        net = MLP(np.random.default_rng(1), lr=3e-3)
        rng = np.random.default_rng(2)
        for _ in range(300):
            net.train_step(*world.batch((0, 1), rng, 32))
        self.assertGreater(net.accuracy(*world.batch((0, 1), rng, 1000)), 0.9)

    def test_teaching_transfers_features(self):
        rng = np.random.default_rng(3)
        teacher = MLP(np.random.default_rng(4), lr=3e-3)
        child = MLP(np.random.default_rng(5), lr=3e-3)
        x = rng.choice([-1.0, 1.0], size=(500, 32))
        gap = lambda: float(np.mean((child.features(x) - teacher.features(x)) ** 2))
        before = gap()
        for _ in range(200):
            child.teach_step(teacher, rng.choice([-1.0, 1.0], size=(32, 32)))
        self.assertLess(gap(), 0.5 * before)


class TestWorld(unittest.TestCase):
    def test_skills_form_a_staircase(self):
        w = SkillWorld(5, 2, 120)
        for k, (support, parent) in enumerate(zip(w.supports, w.parents)):
            if parent >= 0:
                self.assertEqual(len(support), len(w.supports[parent]) + 1)
                self.assertTrue(set(w.supports[parent]) < set(support))
            else:
                self.assertEqual(len(support), 2)
        self.assertEqual(len(set(w.supports)), len(w.supports))

    def test_stream_never_shows_probe_material(self):
        w = SkillWorld(5, 2, 120)
        for era, (a, b) in enumerate(w.tasks):
            n = w.n_introduced(era)
            self.assertNotEqual(a, b)
            self.assertLess(max(a, b), n)
        for cp in (20, 120):
            p = w.probes(cp)
            n = w.n_introduced(cp - 1)
            self.assertTrue(all(k in w.reserved for k in p["novel"]))
            self.assertTrue(all(k >= n and w.parents[k] < n for k in p["frontier"]))
            self.assertEqual(len(p["frontier"]), 6)

    def test_labels_follow_the_parities(self):
        w = SkillWorld(5, 2, 10)
        x, y = w.batch((0, 1), np.random.default_rng(0), 50)
        sa = np.prod(x[:, list(w.supports[0])], axis=1) > 0
        sb = np.prod(x[:, list(w.supports[1])], axis=1) > 0
        np.testing.assert_array_equal(y, 2 * sa + sb)

    def test_world_depends_only_on_seed_and_pace(self):
        self.assertEqual(SkillWorld(7, 6, 50).tasks, SkillWorld(7, 6, 50).tasks)
        self.assertEqual(SkillWorld(7, 6, 50).supports, SkillWorld(7, 6, 50).supports)


class TestRuns(unittest.TestCase):
    def test_runs_are_deterministic(self):
        a = runner.run_one(100, "TEACH", 2, 3, TINY)
        b = runner.run_one(100, "TEACH", 2, 3, TINY)
        for k in ("online", "probes", "lineage", "macs_per_era"):
            self.assertEqual(a[k], b[k])

    def test_every_arm_spends_the_same_compute(self):
        step = TINY["batch"] * 3 * FWD
        for arm in ARMS:
            r = runner.run_one(101, arm, 2, 0 if arm == "IMMORTAL" else 3, TINY)
            for spent in r["macs_per_era"]:
                self.assertLessEqual(spent, r["budget_per_era"], arm)
                self.assertGreater(spent, r["budget_per_era"] - step, arm)

    def test_childhood_keeps_the_parent_until_the_child_graduates(self):
        # TEACH4, lifespan 5: the child is born at era 5 and takes over after
        # era 8, so the parent stays the representative for four more eras
        r = runner.run_one(103, "TEACH4", 2, 5, {**TINY, "n_eras": 12, "checkpoints": [12]})
        self.assertEqual(r["rep_ids"][:9], [r["rep_ids"][0]] * 9)
        self.assertNotEqual(r["rep_ids"][9], r["rep_ids"][0])
        self.assertEqual([(b["era"], b["kind"]) for b in r["lineage"]], [(0, "founder"), (5, "taught"), (10, "taught")])

    def test_probes_do_not_change_a_run(self):
        with_probes = runner.run_one(102, "CLONE", 2, 3, TINY)
        fewer = runner.run_one(102, "CLONE", 2, 3, {**TINY, "checkpoints": [10]})
        self.assertEqual(with_probes["online"], fewer["online"])
        self.assertEqual(with_probes["probes"][10], fewer["probes"][10])

    def test_confirmation_needs_a_frozen_protocol(self):
        import json
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(TINY, f)
        with self.assertRaises(SystemExit):
            runner.main(["--phase", "confirmation", "--seeds", "7000", "--protocol", f.name])
        os.unlink(f.name)


class TestContainment(unittest.TestCase):
    def test_no_networking_or_process_imports(self):
        banned = {"socket", "http", "urllib", "requests", "ftplib", "smtplib", "paramiko", "ssl"}
        for path in pathlib.Path(__file__).resolve().parent.parent.joinpath("learners").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for n in names:
                    self.assertNotIn(n.split(".")[0], banned, f"{path.name} imports {n}")


if __name__ == "__main__":
    unittest.main()
