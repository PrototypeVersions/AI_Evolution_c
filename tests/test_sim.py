import ast
import pathlib
import unittest

from sim.engine import Engine, EngineConfig, run_once


class Reproducibility(unittest.TestCase):
    def test_same_seed_same_result(self):
        cfg = EngineConfig(max_steps=40)
        a, b = run_once(cfg, 7).as_dict(), run_once(cfg, 7).as_dict()
        self.assertEqual(a, b)

    def test_different_seeds_differ(self):
        cfg = EngineConfig(max_steps=40)
        self.assertNotEqual(run_once(cfg, 7).population_by_step, run_once(cfg, 8).population_by_step)


class Inheritance(unittest.TestCase):
    def test_none_mode_children_start_without_memory(self):
        eng = Engine(EngineConfig(inheritance="none", max_steps=30), 3)
        eng.run()
        children = [a for a in eng.agents if a.parent_id is not None]
        self.assertTrue(children)
        # A child may have recorded its own observations after birth, but never
        # more arch entries than it could have tested in its own lifetime.
        for c in children:
            self.assertLessEqual(len(c.memory), c.age)

    def test_related_mode_copies_not_aliases(self):
        eng = Engine(EngineConfig(inheritance="related", max_steps=30), 3)
        eng.run()
        children = [a for a in eng.agents if a.parent_id is not None]
        parents = {a.aid: a for a in eng.agents}
        for c in children:
            for arch, entry in c.memory.items():
                p = parents[c.parent_id].memory.get(arch)
                self.assertIsNot(entry, p)


class Limits(unittest.TestCase):
    def test_population_cap_enforced(self):
        r = run_once(EngineConfig(max_population=30, max_steps=200, shift_step=None), 11)
        self.assertLessEqual(max(r.population_by_step), 30)
        self.assertTrue(r.capped)

    def test_simulator_imports_no_networking(self):
        banned = {"socket", "http", "urllib", "requests", "ssl", "paramiko", "subprocess", "asyncio"}
        for path in pathlib.Path("sim").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [n.name.split(".")[0] for n in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module.split(".")[0]]
                for n in names:
                    self.assertNotIn(n, banned, f"{path} imports {n}")


if __name__ == "__main__":
    unittest.main()
