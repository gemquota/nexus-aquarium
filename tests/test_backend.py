import json
import os
import tempfile
import unittest
from backend import Engine, Genome

class PersistenceTests(unittest.TestCase):
    def test_json_checkpoint_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"state.json")
            engine=Engine(seed=123)
            engine.step(0.5)
            engine.organisms[0].brain.remember({"event":"test"})
            engine.save_state(path)
            restored=Engine.load_state(path)
            self.assertEqual(restored.tick,engine.tick)
            self.assertEqual(restored.seed,engine.seed)
            self.assertEqual(restored.snapshot()["organisms"],engine.snapshot()["organisms"])
            self.assertEqual(restored.water.oxygen,engine.water.oxygen)
            self.assertEqual(restored.rng.random(),engine.rng.random())

    def test_missing_checkpoint_starts_new_world(self):
        engine=Engine.load_state("/path/that/does/not/exist/nexus.json")
        self.assertEqual(engine.tick,0)
        self.assertGreater(len(engine.organisms),0)

if __name__=="__main__":
    unittest.main()
