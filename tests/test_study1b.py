"""Study 1b: pairing of the arms, equal compute, and the runner's guards."""

import json
import os
import tempfile
import unittest

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from learners import arms_1b  # noqa: E402
from learners import run as runner  # noqa: E402
from learners.arms import FWD  # noqa: E402
from learners.world import SkillWorld  # noqa: E402

TINY = {"study": "1b", "study_name": "test", "batch": 32, "n_eras": 10, "checkpoints": [5, 10],
        "eval_n": 300, "pop": 4, "teach_share": 0.5, "reset_shrink": 0.8, "reset_noise": 0.1,
        "fitness_window": 20, "regimes": {"novelty_interval": [2], "lifespan": [5]}, "lr": 0.003,
        "steps_per_era": 40, "probe_steps": 10, "frozen": False}


def thetas(arm):
    return [m.net.theta.copy() for m in arm.members]


def advance(arms, world, eras):
    for era in eras:
        for a in arms:
            a.era(world, era)


class TestPairing(unittest.TestCase):
    def setUp(self):
        self.world = SkillWorld(300, 2, TINY["n_eras"])
        self.make = lambda arm, L: arms_1b.make(arm, 300, 2, L, TINY)

    def test_copying_arms_match_their_controls_until_the_first_birth(self):
        for group in (("SOLO4", "COPY4"), ("SOLO4P", "COPY4P", "CLONE")):
            arms = [self.make(a, 0 if a in arms_1b.NO_BIRTHS else 5) for a in group]
            advance(arms, self.world, range(5))
            first = thetas(arms[0])
            for a in arms[1:]:
                for x, y in zip(first, thetas(a)):
                    np.testing.assert_array_equal(x, y, err_msg=a.name)
            advance(arms, self.world, [5])
            self.assertFalse(all(np.array_equal(x, y) for x, y in zip(thetas(arms[0]), thetas(arms[1]))),
                             f"{group}: the birth at era 5 changed nothing")

    def test_quarter_is_the_first_member_of_solo4(self):
        # same founder and the same batches: QUARTER's network and SOLO4's
        # first member stay identical for the whole run
        q, s, i = self.make("QUARTER", 0), self.make("SOLO4", 0), self.make("IMMORTAL", 0)
        np.testing.assert_array_equal(i.members[0].net.theta, q.members[0].net.theta)
        advance([q, s], self.world, range(TINY["n_eras"]))
        np.testing.assert_array_equal(q.members[0].net.theta, s.members[0].net.theta)

    def test_quarter_trains_on_the_first_quarter_of_immortals_batches(self):
        q, i = self.make("QUARTER", 0), self.make("IMMORTAL", 0)
        world = self.world
        seen = {"QUARTER": [], "IMMORTAL": []}
        original = world.batch

        def spy(name):
            def batch(task, rng, n):
                x, y = original(task, rng, n)
                seen[name].append(x[0, :4].tolist())
                return x, y
            return batch
        for a in (q, i):
            world.batch = spy(a.name)
            a.era(world, 0)
        world.batch = original
        self.assertEqual(len(seen["IMMORTAL"]), 4 * len(seen["QUARTER"]))
        self.assertEqual(seen["QUARTER"], seen["IMMORTAL"][:len(seen["QUARTER"])])

    def test_starting_settings(self):
        default = self.make("SOLO4", 0)
        self.assertTrue(all(m.net.lr == TINY["lr"] and m.net.wd == 0.0 for m in default.members))
        prior = self.make("SOLO4P", 0)
        self.assertEqual(len({m.net.lr for m in prior.members}), 4)
        self.assertTrue(all(1e-6 <= m.net.wd <= 1e-3 for m in prior.members))

    def test_copying_keeps_the_learning_rate_and_clone_mutates_it(self):
        c, k = self.make("COPY4P", 5), self.make("CLONE", 5)
        advance([c, k], self.world, range(6))
        founders = {b["id"]: b["lr"] for b in c.lineage if b["kind"] == "founder"}
        copies = [b for b in c.lineage if b["kind"] == "copy"]
        self.assertEqual(len(copies), 2)
        for b in copies:
            self.assertEqual(b["lr"], founders[b["parent"]])
        clones = [b for b in k.lineage if b["kind"] == "clone"]
        self.assertEqual(len(clones), 2)
        for b in clones:
            self.assertNotEqual(b["lr"], founders[b["parent"]])


class TestRuns1b(unittest.TestCase):
    def test_compute_never_exceeds_the_budget(self):
        step = TINY["batch"] * 3 * FWD
        for arm in arms_1b.ARM_ORDER_1B:
            r = runner.run_one(301, arm, 2, 0 if arm in arms_1b.NO_BIRTHS else 5, TINY)
            share = 0.25 if arm == "QUARTER" else 1.0
            for spent in r["macs_per_era"]:
                self.assertLessEqual(spent, r["budget_per_era"] * share, arm)
                self.assertGreater(spent, r["budget_per_era"] * share - 4 * step, arm)

    def test_runs_are_deterministic(self):
        a = runner.run_one(302, "CLONE", 2, 5, TINY)
        b = runner.run_one(302, "CLONE", 2, 5, TINY)
        for k in ("online", "probes", "lineage", "macs_per_era"):
            self.assertEqual(a[k], b[k])

    def test_jobs(self):
        js = runner.jobs([8000], {**TINY, "regimes": {"novelty_interval": [2, 6], "lifespan": [5, 20]}})
        self.assertEqual(len(js), 22)
        self.assertEqual(sorted({j[3] for j in js if j[1] in arms_1b.NO_BIRTHS + ("SCRATCH",)}), [0])

    def test_phase_must_match_the_protocol(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(TINY, f)
        for phase in ("pilot", "confirmation_1b"):  # wrong study; not frozen
            with self.assertRaises(SystemExit):
                runner.main(["--phase", phase, "--seeds", "8000", "--protocol", f.name])
        os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
