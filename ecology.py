"""Deterministic trophic interactions and simplified nutrient cycling."""
from __future__ import annotations
import math
from biodiversity import species_profile
from physics import SpatialGrid

PRODUCER_GROUPS={"macroalgae","seagrass","microorganism"}
class Ecology:
    def __init__(self):
        self.detritus=0.0; self.feedings=0; self.predation_events=0; self.decomposed=0.0
    def step(self,organisms,food_web,water,dt,rng):
        living=[o for o in organisms if o.alive]
        by_species={}
        for o in living: by_species.setdefault(o.species,[]).append(o)
        for o in living:
            profile=species_profile(o.species)
            group=profile["group"]
            if group in PRODUCER_GROUPS:
                o.energy=min(1.0,o.energy+dt*.0008*(1-water.turbidity*.4))
                continue
            needs=food_web.get(o.species,[])
            if not needs or o.energy>.78: continue
            candidates=[p for name in needs for p in by_species.get(name,[]) if p.alive and p.id!=o.id]
            if candidates:
                prey=min(candidates,key=lambda p:(p.x-o.x)**2+(p.y-o.y)**2)
                distance=math.hypot(prey.x-o.x,prey.y-o.y)
                if distance<2.8 and rng.random()<min(.9,dt*.7):
                    prey.energy=max(0,prey.energy-.18)
                    o.energy=min(1,o.energy+.12)
                    self.feedings+=1
                    if prey.energy<=.02 and species_profile(prey.species)["trophic"] not in ("producer",):
                        prey.alive=False; self.predation_events+=1
            elif group not in ("filter_feeder","detritivore","benthic_omnivore"):
                self.detritus+=dt*.0002
        dead=[o for o in organisms if not o.alive and getattr(o,"_decomposed",False) is False]
        for o in dead:
            self.detritus+=max(0,o.energy)*.05
            o._decomposed=True
            self.decomposed+=1
        decomposition=min(self.detritus,dt*.002)
        self.detritus-=decomposition
        water.nitrate=max(0,min(10,water.nitrate+decomposition*.4-dt*.0003))
        water.phosphate=max(0,min(5,water.phosphate+decomposition*.08-dt*.00005))
        water.oxygen=max(0,min(14,water.oxygen+dt*.0002*sum(1 for o in living if species_profile(o.species)["trophic"]=="producer")))
    def state(self): return {"detritus":self.detritus,"feedings":self.feedings,"predation_events":self.predation_events,"decomposed":self.decomposed}
    def restore(self,data):
        self.detritus=max(0,float(data.get("detritus",0))); self.feedings=max(0,int(data.get("feedings",0))); self.predation_events=max(0,int(data.get("predation_events",0))); self.decomposed=max(0,int(data.get("decomposed",0)))
    def snapshot(self):
        return {"feedings":self.feedings,"predation_events":self.predation_events,
                "decomposed_organisms":self.decomposed,"detritus":self.detritus}
