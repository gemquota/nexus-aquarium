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


class EngineFoundationTests(unittest.TestCase):
    def test_config_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"state.json")
            engine=Engine(seed=44,config={"max_organisms":100})
            engine.save_state(path)
            restored=Engine.load_state(path)
            self.assertEqual(restored.config["max_organisms"],100)

    def test_invalid_config_rejected(self):
        with self.assertRaises(ValueError): Engine(config={"max_organisms":0})

    def test_organism_capacity_enforced(self):
        engine=Engine(config={"max_organisms":20})
        with self.assertRaises(RuntimeError): engine.add("reef_fish",1,1)

    def test_future_checkpoint_version_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"state.json")
            with open(path,"w") as f: json.dump({"engine_version":999},f)
            with self.assertRaises(ValueError): Engine.load_state(path)


class PhysicsTests(unittest.TestCase):
    def test_particle_field_is_seeded_and_bounded(self):
        from physics import MarinePhysics
        a=MarinePhysics(77); b=MarinePhysics(77)
        self.assertEqual([(p.x,p.y) for p in a.particles],[(p.x,p.y) for p in b.particles])
        a.step_particles(.1,1.0)
        self.assertTrue(all(0<=p.x<80 and 0<=p.y<24 for p in a.particles))
        self.assertTrue(all(p.density>0 for p in a.particles))

    def test_spatial_grid_neighbour_query(self):
        from physics import FluidParticle, SpatialGrid
        grid=SpatialGrid(2); a=FluidParticle(1,1); b=FluidParticle(2,1); c=FluidParticle(10,10)
        grid.rebuild([a,b,c])
        self.assertEqual(len(grid.nearby(1,1,2)),2)

if __name__=="__main__":
    unittest.main()
