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
        engine=Engine(config={"max_organisms":39})
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


class EcologyTests(unittest.TestCase):
    def test_food_web_feeding_and_nutrients(self):
        from ecology import Ecology
        from backend import Water
        engine=Engine(seed=4); ecology=Ecology(); predator=engine.add("shark",10,10); prey=engine.add("reef_fish",10.2,10)
        predator.energy=.2; prey.energy=.5
        water=Water(); before=predator.energy
        for _ in range(100): ecology.step(engine.organisms,{"shark":["reef_fish"]},water,.1,engine.rng)
        self.assertGreaterEqual(predator.energy,before)
        self.assertGreater(ecology.feedings,0)
        self.assertGreaterEqual(water.nitrate,0)


class ReleaseARegressionTests(unittest.TestCase):
    def test_habitat_profile_initializes_water_and_snapshot(self):
        engine=Engine(seed=3,config={"habitat":"deep_sea"})
        self.assertEqual(engine.habitat,"deep_sea")
        self.assertEqual(engine.snapshot()["world"]["habitat"],"deep_sea")
        self.assertAlmostEqual(engine.water.temperature,3.0)
    def test_organisms_expose_life_stage_and_trophic_role(self):
        organism=Engine(seed=3).snapshot()["organisms"][0]
        self.assertIn(organism["life_stage"],("juvenile","subadult","adult"))
        self.assertIn("trophic_role",organism)
    def test_subsystem_state_survives_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"full.json")
            engine=Engine(seed=9); engine.ecology.feedings=12; engine.behaviour.flee_responses=4
            engine.events.total_events=2; engine.environment.mean_stress=.23
            engine.physics.particles[0].vx=.123
            engine.save_state(path); restored=Engine.load_state(path)
            self.assertEqual(restored.ecology.feedings,12)
            self.assertEqual(restored.behaviour.flee_responses,4)
            self.assertEqual(restored.events.total_events,2)
            self.assertAlmostEqual(restored.environment.mean_stress,.23)
            self.assertAlmostEqual(restored.physics.particles[0].vx,.123)
    def test_species_reproductive_modes(self):
        from life_cycles import reproductive_mode
        self.assertEqual(reproductive_mode("coral_polyp"),"asexual_or_fragmentation")
        self.assertEqual(reproductive_mode("reef_fish"),"sexual")
    def test_environmental_stress_is_bounded(self):
        from environment import EnvironmentalResponse
        engine=Engine(seed=2); response=EnvironmentalResponse()
        response.step(engine.organisms,engine.water,1.0,"deep_sea")
        self.assertGreaterEqual(response.mean_stress,0)
        self.assertLessEqual(response.mean_stress,1)


class ReleaseBSubsystemTests(unittest.TestCase):
    def test_life_history_profile_contains_stage_and_strategy(self):
        from life_cycles import life_history_profile
        profile=life_history_profile("whale")
        self.assertEqual(profile["strategy"],"live_birth_and_care")
        self.assertGreater(profile["maximum_age"],profile["maturity"])
    def test_genetic_diversity_metrics(self):
        from genetics import population_diversity
        engine=Engine(seed=10)
        metrics=population_diversity(engine.organisms)
        self.assertIn("speed",metrics["trait_means"])
        self.assertGreaterEqual(metrics["trait_ranges"]["speed"],0)
    def test_spatial_habitat_map_is_deterministic(self):
        from habitats import HabitatMap
        a=HabitatMap(80,24,seed=55); b=HabitatMap(80,24,seed=55)
        self.assertEqual(a.snapshot(),b.snapshot())
        self.assertIn(a.at(5,5),("coral_reef","open_ocean","deep_sea","seagrass","kelp_forest","rocky_seabed","sandy_seabed","hydrothermal_vent"))
    def test_nutrient_cycle_bounds_water(self):
        from nutrients import NutrientCycle
        engine=Engine(seed=7); cycle=NutrientCycle()
        for _ in range(100): cycle.step(engine.organisms,engine.water,.1)
        self.assertGreaterEqual(engine.water.oxygen,0)
        self.assertLessEqual(engine.water.oxygen,14)
    def test_event_history_is_bounded_and_persisted(self):
        engine=Engine(seed=8)
        engine.events.add(engine,"storm",.4,5)
        self.assertEqual(engine.events.history[-1]["kind"],"storm")
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"events.json"); engine.save_state(path)
            restored=Engine.load_state(path)
            self.assertEqual(restored.events.history[-1]["kind"],"storm")
    def test_spatial_disease_system_reports_zero_without_outbreak(self):
        from disease import DiseaseSystem
        engine=Engine(seed=9); disease=DiseaseSystem()
        disease.step(engine.organisms,[],.1,engine.rng)
        self.assertEqual(disease.infected,0)

if __name__=="__main__":
    unittest.main()
