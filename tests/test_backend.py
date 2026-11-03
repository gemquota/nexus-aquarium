import json
import random
import os
import tempfile
import unittest
from backend import Engine, Genome, FixedStepClock

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
    def test_invalid_habitat_is_rejected(self):
        with self.assertRaises(ValueError): Engine(config={"habitat":"not_a_biome"})
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

class TiltAndPhenotypeTests(unittest.TestCase):
    def test_tilt_changes_current_field_and_is_bounded(self):
        from physics import MarinePhysics
        physics=MarinePhysics(seed=4)
        baseline=physics.currents.sample(40,12,0)
        physics.currents.tilt_x=1.0
        physics.currents.tilt_y=-1.0
        steered=physics.currents.sample(40,12,0)
        self.assertGreater(steered[0],baseline[0])
        self.assertLess(steered[1],baseline[1])

    def test_tilt_survives_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"tilt.json")
            engine=Engine(seed=5)
            engine.physics.currents.tilt_x=.7
            engine.physics.currents.tilt_y=-.4
            engine.save_state(path)
            restored=Engine.load_state(path)
            self.assertAlmostEqual(restored.physics.currents.tilt_x,.7)
            self.assertAlmostEqual(restored.physics.currents.tilt_y,-.4)

    def test_organisms_have_individual_appearance_and_movement_traits(self):
        engine=Engine(seed=6)
        traits=[o.genome.traits for o in engine.organisms]
        for key in ("agility","turn_rate","tracking","transparency","hue","pattern","fin_size"):
            self.assertTrue(all(0<=item[key]<=1 for item in traits))
        self.assertGreater(len({round(item["hue"],4) for item in traits}),1)
        self.assertGreater(len({round(item["agility"],4) for item in traits}),1)

if __name__=="__main__":
    unittest.main()


class DynamicOceanTests(unittest.TestCase):
    def test_rain_gradually_raises_waterline(self):
        engine=Engine(seed=81,config={"rain_rate":0.01})
        start=engine.water_fraction
        for _ in range(30): engine.step(0.2)
        self.assertGreater(engine.water_fraction,start)
        self.assertLessEqual(engine.water_fraction,1.0)

    def test_organisms_are_kept_below_dynamic_surface(self):
        engine=Engine(seed=82,config={"initial_water_fraction":0.2})
        engine.physics.waterline=engine.config["world_height"]*(1-engine.water_fraction)
        organism=engine.add("reef_fish",20,0,vx=0,vy=-1)
        engine.physics.move(organism,0.1,0.0)
        self.assertGreaterEqual(organism.y,engine.physics.waterline)

    def test_species_behaviour_produces_multiple_states(self):
        engine=Engine(seed=83)
        for _ in range(60): engine.step(0.1)
        states={o.state for o in engine.organisms if o.alive}
        self.assertGreaterEqual(len(states),2)
        metrics=engine.behaviour.snapshot()
        self.assertGreater(metrics["decisions"],0)


class IndividualBehaviourTests(unittest.TestCase):
    def test_individual_patrol_goals_and_behaviour_metrics(self):
        engine=Engine(seed=91)
        engine.organisms=[]
        mobile=[engine.add("shark",100,100)]
        for _ in range(12): engine.behaviour.step(engine.organisms,0.25,engine.rng)
        self.assertTrue(any("goal_x" in o.brain.learning for o in mobile))
        metrics=engine.behaviour.snapshot()
        self.assertGreater(metrics["goal_changes"],0)
        self.assertGreater(metrics["patrols"]+metrics["school_links"],0)

    def test_predator_target_is_remembered(self):
        engine=Engine(seed=92)
        engine.organisms=[]
        predator=engine.add("shark",100,100)
        prey=engine.add("reef_fish",104,100)
        predator.energy=.2
        engine.behaviour.step(engine.organisms,0.2,engine.rng)
        self.assertEqual(predator.state,"hunting")
        self.assertEqual(predator.brain.learning.get("goal_id"),prey.id)
        self.assertGreater(engine.behaviour.hunts,0)

    def test_goal_memory_survives_checkpoint(self):
        engine=Engine(seed=93)
        for _ in range(8): engine.step(.2)
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"goals.json")
            engine.save_state(path)
            restored=Engine.load_state(path)
            original=next(o for o in engine.organisms if o.brain.learning.get("goal_kind"))
            clone=next(o for o in restored.organisms if o.id==original.id)
            self.assertEqual(clone.brain.learning.get("goal_kind"),original.brain.learning.get("goal_kind"))
            self.assertEqual(clone.brain.learning.get("goal_x"),original.brain.learning.get("goal_x"))


class ScalingRegressionTests(unittest.TestCase):
    def test_spatial_feeding_ignores_distant_prey(self):
        engine=Engine(seed=101)
        engine.organisms=[]
        predator=engine.add("shark",10,10)
        predator.energy=.2
        near=engine.add("reef_fish",11,10)
        far=engine.add("reef_fish",700,200)
        engine.ecology.step(engine.organisms,engine.food_web,engine.water,1.0,engine.rng)
        self.assertLess(near.energy,1.0)
        self.assertEqual(far.energy,0.9)

    def test_large_population_spatial_subsystems_complete(self):
        engine=Engine(seed=102,config={"max_organisms":1200})
        for i in range(900):
            engine.add("reef_fish",float((i*17)%790),float(216+(i%20)))
        engine.step(0.03)
        self.assertGreater(engine.tick,0)
        self.assertGreater(engine.behaviour.decisions,0)


class PerformanceTelemetryTests(unittest.TestCase):
    def test_step_reports_bounded_performance_telemetry(self):
        engine=Engine(seed=20261031)
        engine.step(1/30)
        metrics=engine.snapshot()["performance"]
        self.assertEqual(metrics["samples"],1)
        self.assertGreaterEqual(metrics["step_ms"],0)
        self.assertGreaterEqual(metrics["step_ema_ms"],0)
        self.assertIn(metrics["slowest_stage"],("life_support_ms","reproduction_ms","behaviour_physics_ms","ecosystem_ms"))
        self.assertEqual(metrics["organisms"],len(engine.organisms))
        self.assertEqual(metrics["alive"],sum(1 for item in engine.organisms if item.alive))
        self.assertGreaterEqual(metrics["budget_utilization"],0)

    def test_performance_telemetry_is_not_advanced_while_paused(self):
        engine=Engine(seed=20261032)
        engine.step(1/30)
        before=engine.snapshot()["performance"]["samples"]
        engine.paused=True
        engine.step(1/30)
        self.assertEqual(engine.snapshot()["performance"]["samples"],before)


class LivingOceanWorldTests(unittest.TestCase):
    def test_lunar_tide_and_moon_phase_are_exposed(self):
        engine=Engine(seed=310)
        for _ in range(30): engine.step(.5)
        snap=engine.snapshot()
        self.assertGreaterEqual(snap["weather"]["moon_phase"],0)
        self.assertLess(snap["weather"]["moon_phase"],1)
        self.assertTrue(-.026<=snap["weather"]["tide_height"]<=.026)
        self.assertIn("swell",snap["weather"])

    def test_seabirds_are_simulated_and_can_catch_fish(self):
        engine=Engine(seed=311)
        engine.organisms=[]
        surface=engine.config["world_height"]*(1-engine.water_fraction)
        prey=engine.add("reef_fish",100,surface)
        bird=engine.seabirds[0]
        bird.update({"x":100.0,"y":surface-1.0,"state":"diving","hunger":.8,"dive_cooldown":0.0})
        before=prey.energy
        engine._step_seabirds(.5)
        self.assertLess(prey.energy,before)
        self.assertGreater(engine.seabird_catches,0)
        self.assertEqual(bird["state"],"soaring")

    def test_plankton_bloom_is_reported_and_bounded(self):
        engine=Engine(seed=312)
        engine.water.nitrate=5.0
        engine.water.phosphate=1.0
        for _ in range(90): engine.step(.5)
        bloom=engine.snapshot()["environment"]["plankton_bloom"]
        self.assertGreaterEqual(bloom,0.0)
        self.assertLessEqual(bloom,1.0)
        self.assertIn("season_phase",engine.snapshot()["environment"])

    def test_new_ocean_state_survives_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"ocean.json")
            engine=Engine(seed=313)
            engine.moon_phase=.42; engine.tide_height=.017; engine.plankton_bloom=.61
            engine.seabirds[0]["state"]="diving"; engine.seabird_catches=9
            engine.save_state(path)
            restored=Engine.load_state(path)
            self.assertAlmostEqual(restored.moon_phase,.42)
            self.assertAlmostEqual(restored.tide_height,.017)
            self.assertAlmostEqual(restored.plankton_bloom,.61)
            self.assertEqual(restored.seabirds[0]["state"],"diving")
            self.assertEqual(restored.seabird_catches,9)


class CoralReefHealthTests(unittest.TestCase):
    def test_heat_and_acidification_drive_bleaching(self):
        from coral import CoralReefSystem
        engine=Engine(seed=410)
        coral=next(o for o in engine.organisms if o.species=="coral_polyp")
        system=CoralReefSystem()
        engine.water.temperature=32.0
        engine.water.ph=7.6
        system.step(engine.organisms,engine.water,1000.0,light=0.8,plankton_bloom=0.2)
        self.assertGreater(system.bleaching,0.5)
        self.assertLess(coral.health,1.0)
        self.assertEqual(system.snapshot()["condition"],"bleached")

    def test_coral_can_recover_under_favourable_conditions(self):
        from coral import CoralReefSystem
        engine=Engine(seed=411)
        coral=next(o for o in engine.organisms if o.species=="coral_polyp")
        coral.health=0.6
        system=CoralReefSystem()
        system.bleaching=0.7
        engine.water.temperature=26.0
        engine.water.ph=8.1
        engine.water.turbidity=0.05
        system.step(engine.organisms,engine.water,100000.0,light=1.0,plankton_bloom=0.1)
        self.assertLess(system.bleaching,0.1)
        self.assertGreater(coral.health,0.6)
        self.assertGreater(system.cumulative_calcification,0.0)

    def test_coral_state_survives_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,"coral.json")
            engine=Engine(seed=412)
            engine.coral.bleaching=0.37
            engine.coral.cumulative_calcification=1.25
            engine.save_state(path)
            restored=Engine.load_state(path)
            self.assertAlmostEqual(restored.coral.bleaching,0.37)
            self.assertAlmostEqual(restored.coral.cumulative_calcification,1.25)


class MarineDiversityTests(unittest.TestCase):
    def test_surface_pelagic_and_deep_communities_are_seeded(self):
        engine=Engine(seed=902)
        names={o.species for o in engine.organisms if o.alive}
        self.assertTrue({"surface_fish","sardine","pelagic_fish","mackerel","deepwater_fish","lanternfish","anglerfish"}<=names)
        surface=engine.config["world_height"]*(1-engine.water_fraction)
        fish=[o for o in engine.organisms if o.species in {"surface_fish","sardine","pelagic_fish","mackerel","deepwater_fish","lanternfish","anglerfish"}]
        self.assertTrue(any(o.y<surface+30 for o in fish))
        self.assertTrue(any(o.y>engine.config["world_height"]*.8 for o in fish))

    def test_marine_mammals_crustaceans_and_plants_are_catalogued(self):
        from biodiversity import SPECIES
        expected={"orca","humpback_whale","sea_lion","manatee","lobster","crayfish","hermit_crab","sargassum","sea_lettuce","mangrove"}
        self.assertTrue(expected<=set(SPECIES))
        self.assertEqual(SPECIES["lobster"]["zone"],"benthic")
        self.assertEqual(SPECIES["sargassum"]["zone"],"surface")

    def test_seabird_variety_and_islets_are_exposed(self):
        engine=Engine(seed=903)
        snap=engine.snapshot()
        self.assertGreaterEqual(len(snap["seabirds"]),8)
        self.assertGreaterEqual(len({b["species"] for b in snap["seabirds"]}),6)
        self.assertGreaterEqual(len(snap["floating_islets"]),2)


class ExpandedWorldQualityTests(unittest.TestCase):
    def test_default_world_is_300k_by_100k(self):
        engine=Engine(seed=71)
        self.assertEqual(engine.config["world_width"],300000)
        self.assertEqual(engine.config["world_height"],100000)
        self.assertGreaterEqual(len(engine.organisms),39)
    def test_seeded_reef_fish_and_benthic_life_are_not_buried(self):
        engine=Engine(seed=73)
        height=engine.config["world_height"]
        surface=height*(1-engine.water_fraction)
        reef=[o for o in engine.organisms if o.species=="reef_fish"]
        self.assertEqual(len(reef),18)
        self.assertTrue(all(surface<o.y<height*.91 for o in reef))
        benthic=[o for o in engine.organisms if o.species in {"crab","lobster","crayfish","hermit_crab","octopus","eel","sea_star","sea_urchin","shrimp","clam","coral_polyp"}]
        self.assertTrue(benthic)
        self.assertTrue(all(o.y<height*.91 for o in benthic))

    def test_small_capacity_seeds_without_crashing_and_enforces_add_limit(self):
        engine=Engine(seed=72,config={"max_organisms":39})
        self.assertEqual(len(engine.organisms),39)
        with self.assertRaises(RuntimeError): engine.add("reef_fish",1,1)


class PerformanceInstrumentationTests(unittest.TestCase):
    def test_step_profiler_reports_budget_and_stage_timings(self):
        engine=Engine(seed=880)
        for _ in range(4): engine.step(1/30)
        perf=engine.performance
        self.assertEqual(perf["samples"],4)
        self.assertGreaterEqual(perf["step_ms"],0)
        self.assertGreater(perf["budget_ms"],0)
        self.assertGreaterEqual(perf["budget_utilization"],0)
        self.assertTrue(perf["stages_ms"])
        self.assertIn(perf["slowest_stage"],perf["stages_ms"])
        self.assertEqual(perf["organisms"],len(engine.organisms))
        self.assertEqual(perf["fluid_particles"],len(engine.physics.particles))

    def test_snapshot_exposes_performance_telemetry(self):
        engine=Engine(seed=881); engine.step(1/30)
        perf=engine.snapshot()["performance"]
        self.assertIn("step_ema_ms",perf)
        self.assertIn("stages_ms",perf)
        self.assertIn("budget_utilization",perf)


class EcologicalIntegrityReleaseTests(unittest.TestCase):
    def test_fixed_step_clock_accumulates_fractional_frames(self):
        clock=FixedStepClock()
        self.assertEqual(clock.advance(.01,.02,.1),0)
        self.assertEqual(clock.advance(.01,.02,.1),1)
        self.assertAlmostEqual(clock.accumulator,0.0)

    def test_fixed_step_clock_bounds_hitch_catchup(self):
        clock=FixedStepClock()
        self.assertEqual(clock.advance(.25,.02,.1),5)
        self.assertAlmostEqual(clock.dropped_time,.15)
        self.assertAlmostEqual(clock.accumulator,0.0)

    def test_fixed_dt_is_used_by_engine_default_step(self):
        engine=Engine(seed=600,config={"fixed_dt":.02,"simulation_speed":2.0})
        engine.step()
        self.assertAlmostEqual(engine.sim_time,.04)
        self.assertEqual(engine.tick,1)

    def test_config_rejects_non_finite_and_fractional_integer_values(self):
        with self.assertRaises(ValueError):
            Engine(config={"rain_rate":float("nan")})
        with self.assertRaises(ValueError):
            Engine(config={"max_organisms":39.5})
        with self.assertRaises(ValueError):
            Engine(config={"fixed_dt":.2,"max_frame_dt":.1})

    def test_genetic_inheritance_preserves_render_phenotype_loci(self):
        parent=Genome()
        child=parent.inherit(parent,random.Random(601))
        for trait in ("agility","turn_rate","tracking","transparency","hue","pattern","fin_size"):
            self.assertIn(trait,child.traits)
            self.assertGreaterEqual(child.traits[trait],0.0)
            self.assertLessEqual(child.traits[trait],1.0)

    def test_feeding_energy_is_split_between_assimilation_and_waste(self):
        import random
        engine=Engine(seed=602)
        engine.organisms=[]
        predator=engine.add("shark",10,10)
        prey=engine.add("reef_fish",10.2,10)
        predator.energy=.2
        prey.energy=.5
        engine.ecology.step(engine.organisms,{"shark":["reef_fish"]},engine.water,1.0,random.Random(1),3.0)
        self.assertAlmostEqual(engine.ecology.energy_consumed,.18)
        self.assertAlmostEqual(engine.ecology.energy_assimilated,.12)
        self.assertAlmostEqual(engine.ecology.energy_waste,.06)
        self.assertAlmostEqual(engine.ecology.energy_consumed,engine.ecology.energy_assimilated+engine.ecology.energy_waste)

    def test_deceased_biomass_is_transferred_to_detritus_once(self):
        import random
        engine=Engine(seed=603)
        organism=engine.organisms[0]
        organism.alive=False
        organism.energy=.4
        before=engine.ecology.detritus
        engine.ecology.step(engine.organisms,{},engine.water,0.0,random.Random(2))
        self.assertAlmostEqual(engine.ecology.detritus-before,.4)
        self.assertEqual(organism.energy,0.0)
        engine.ecology.step(engine.organisms,{},engine.water,0.0,random.Random(2))
        self.assertAlmostEqual(engine.ecology.detritus-before,.4)

    def test_identical_seed_and_fixed_tick_inputs_reproduce_world_state(self):
        a=Engine(seed=604)
        b=Engine(seed=604)
        for _ in range(120):
            a.step(a.config["fixed_dt"])
            b.step(b.config["fixed_dt"])
        self.assertEqual(a.tick,b.tick)
        self.assertEqual(a.snapshot()["organisms"],b.snapshot()["organisms"])
        self.assertEqual(a.snapshot()["water"],b.snapshot()["water"])
        self.assertEqual(a.ecology.state(),b.ecology.state())


class DisturbanceValidationTests(unittest.TestCase):
    def test_event_rejects_non_finite_intensity_and_duration(self):
        from events import EventSystem
        engine=Engine(seed=605)
        events=EventSystem()
        with self.assertRaises(ValueError):
            events.add(engine,"storm",float("nan"),10)
        with self.assertRaises(ValueError):
            events.add(engine,"storm",.5,float("inf"))
        with self.assertRaises(ValueError):
            events.add(engine,"not_an_event",.5,10)


class OrganismResourceApiTests(unittest.TestCase):
    def _request(self, server, path):
        import urllib.request
        request=urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}{path}",
            headers={"Authorization":"Bearer test-token"})
        with urllib.request.urlopen(request,timeout=3) as response:
            return response.status,json.loads(response.read().decode("utf-8"))

    def test_organism_collection_is_bounded_and_viewport_scoped(self):
        import threading
        from http.server import ThreadingHTTPServer
        from types import SimpleNamespace
        from backend import Handler
        engine=Engine(seed=701)
        service=SimpleNamespace(token="test-token",engine=engine,lock=threading.RLock(),
            last_loop_error=None,last_checkpoint_error=None,
            clock=SimpleNamespace(dropped_time=0.0))
        previous=Handler.service
        Handler.service=service
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            status,page=self._request(server,"/organisms?limit=3&offset=0")
            self.assertEqual(status,200)
            self.assertEqual(len(page["organisms"]),3)
            self.assertGreater(page["total"],3)
            self.assertTrue(page["has_more"])
            item=page["organisms"][0]
            status,detail=self._request(server,f"/organism/{item['id']}")
            self.assertEqual(status,200)
            self.assertEqual(detail["organism"]["id"],item["id"])
            status,scoped=self._request(server,"/organisms?x_min=0&x_max=1&y_min=0&y_max=1")
            self.assertEqual(status,200)
            self.assertTrue(all(0<=o["x"]<=1 and 0<=o["y"]<=1 for o in scoped["organisms"]))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            Handler.service=previous

    def test_organism_collection_rejects_invalid_pagination(self):
        import threading
        from http.server import ThreadingHTTPServer
        from types import SimpleNamespace
        from urllib.error import HTTPError
        from backend import Handler
        service=SimpleNamespace(token="test-token",engine=Engine(seed=702),lock=threading.RLock(),
            last_loop_error=None,last_checkpoint_error=None,
            clock=SimpleNamespace(dropped_time=0.0))
        previous=Handler.service
        Handler.service=service
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            import urllib.request
            request=urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/organisms?limit=1.5",
                headers={"Authorization":"Bearer test-token"})
            with self.assertRaises(HTTPError) as caught:
                urllib.request.urlopen(request,timeout=3)
            self.assertEqual(caught.exception.code,400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            Handler.service=previous
