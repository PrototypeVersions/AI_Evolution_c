import ast
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from longrun import advance as adv
from longrun.model import World

CFG = json.loads(pathlib.Path("longrun/config.json").read_text())


def _state(w):
    return json.dumps(w.to_state(), sort_keys=True)


class Persistence(unittest.TestCase):
    def test_checkpoint_resume_is_identical_to_continuous_run(self):
        a = World(CFG)
        for _ in range(400):
            a.step()
        b = World(CFG)
        for _ in range(200):
            b.step()
        c = World.from_state(CFG, json.loads(json.dumps(b.to_state())))
        for _ in range(200):
            c.step()
        self.assertEqual(_state(a), _state(c))


class Advance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = pathlib.Path(self.tmp.name)
        cfg_path = d / "config.json"
        cfg_path.write_text(json.dumps(CFG))
        self.cfg_path = cfg_path
        self.patches = [mock.patch.multiple(
            adv, CONFIG=str(cfg_path), STATE_DIR=str(d / "state"), STATE=str(d / "state/world.json.gz"),
            META=str(d / "state/meta.json"), HIST_HAB=str(d / "state/h.jsonl"),
            HIST_WORLD=str(d / "state/w.jsonl"), EVENTS=str(d / "state/e.jsonl"), DOCS=str(d / "longrun.json"),
        )]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_advances_continue_and_append(self):
        out1 = adv.advance(300, init=True)
        out2 = adv.advance(300)
        self.assertEqual(out1["tick"], 300)
        self.assertEqual(out2["tick"], 600)
        self.assertEqual(len(out2["advances"]), 2)
        self.assertEqual(out2["world_history"][-1][0], 600)
        self.assertEqual(out2["events"][0]["kind"], "genesis")
        self.assertEqual(out2["interventions"], [])

    def test_strategy_tree_is_identical_across_checkpoints(self):
        one = adv.advance(600, init=True)
        meta_one = json.loads(pathlib.Path(adv.META).read_text())["phylo"]
        adv.advance(300, init=True)
        two = adv.advance(300)
        meta_two = json.loads(pathlib.Path(adv.META).read_text())["phylo"]
        self.assertEqual(meta_one, meta_two)
        self.assertEqual(one["phylo"], two["phylo"])
        self.assertEqual(one["shape_history"], two["shape_history"])
        self.assertTrue(one["phylo"], "expected at least one registered strategy shape")
        ids = {s["id"] for s in one["phylo"]}
        for s in one["phylo"]:
            self.assertTrue(s["parent"] is None or s["parent"] in ids, "tree must stay connected")

    def test_snapshot_matches_world(self):
        out = adv.advance(200, init=True)
        self.assertEqual(len(out["snapshot"]["agents"]), out["totals"]["alive"])
        occupied = sum(n[3] for hab in out["snapshot"]["nodes"] for n in hab)
        self.assertEqual(occupied, out["totals"]["alive"])

    def test_replay_reproduces_checkpoint(self):
        from longrun import replay
        adv.advance(250, init=True)
        adv.advance(250)
        report = replay.replay(rewrite=True)
        self.assertTrue(report["state_matches"])
        self.assertTrue(report["events_match"])

    def test_config_change_is_logged_as_intervention(self):
        adv.advance(100, init=True)
        cfg = dict(CFG)
        cfg["habitats"] = [dict(h) for h in CFG["habitats"]]
        cfg["habitats"][0]["regen"] = 0.1
        self.cfg_path.write_text(json.dumps(cfg))
        out = adv.advance(100)
        self.assertEqual(len(out["interventions"]), 1)
        self.assertIn("intervention", [e["kind"] for e in out["events"]])

    def test_advance_respects_tick_cap(self):
        cfg = dict(CFG, max_ticks_per_advance=50)
        self.cfg_path.write_text(json.dumps(cfg))
        self.assertEqual(adv.advance(1000, init=True)["tick"], 50)


class Containment(unittest.TestCase):
    def test_longrun_imports_no_networking(self):
        banned = {"socket", "http", "urllib", "requests", "ssl", "paramiko", "asyncio", "ftplib", "smtplib"}
        for path in pathlib.Path("longrun").glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                names = []
                if isinstance(node, ast.Import):
                    names = [n.name.split(".")[0] for n in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module.split(".")[0]]
                for n in names:
                    self.assertNotIn(n, banned, f"{path} imports {n}")


if __name__ == "__main__":
    unittest.main()
