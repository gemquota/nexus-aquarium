"""Deterministic trophic interactions and simplified nutrient cycling."""
from __future__ import annotations
import math
from biodiversity import species_profile
from physics import SpatialGrid

PRODUCER_GROUPS={"macroalgae","seagrass","microorganism"}
class Ecology:
    def __init__(self):
        self.detritus=0.0; self.feedings=0; self.predation_events=0; self.decomposed=0.0
        self.energy_consumed=0.0; self.energy_assimilated=0.0; self.energy_waste=0.0
        self.energy_produced=0.0; self.metabolic_loss=0.0; self.respired_energy=0.0
    def record_metabolic_loss(self,amount):
        amount=max(0.0,float(amount))
        self.metabolic_loss+=amount
        self.detritus+=amount*.35
        self.respired_energy+=amount*.65

    def step(self,organisms,food_web,water,dt,rng,predation_intensity=1.0):
        living=[o for o in organisms if o.alive]
        grid=SpatialGrid(3.0); grid.rebuild(living)
        for o in living:
            profile=species_profile(o.species)
            group=profile["group"]
            if group in PRODUCER_GROUPS:
                production=min(1.0-o.energy,dt*.0008*(1-water.turbidity*.4))
                o.energy+=production
                self.energy_produced+=production
                continue
            needs=food_web.get(o.species,[])
            if not needs or o.energy>.78: continue
            wanted=set(needs)
            candidates=[p for p in grid.nearby(o.x,o.y,2.8) if p.id!=o.id and p.alive and p.species in wanted]
            if candidates:
                prey=min(candidates,key=lambda p:(p.x-o.x)**2+(p.y-o.y)**2)
                distance=math.hypot(prey.x-o.x,prey.y-o.y)
                if distance<2.8 and rng.random()<min(.95,dt*.7*max(0.0,float(predation_intensity))):
                    consumed=min(.18,prey.energy)
                    assimilated=consumed*(2.0/3.0)
                    waste=consumed-assimilated
                    prey.energy=max(0.0,prey.energy-consumed)
                    o.energy=min(1.0,o.energy+assimilated)
                    self.energy_consumed+=consumed
                    self.energy_assimilated+=assimilated
                    self.energy_waste+=waste
                    self.detritus+=waste
                    self.feedings+=1
                    if prey.energy<=.02 and species_profile(prey.species)["trophic"] not in ("producer",):
                        prey.alive=False; self.predation_events+=1
            elif group not in ("filter_feeder","detritivore","benthic_omnivore"):
                self.detritus+=dt*.0002
        dead=[o for o in organisms if not o.alive and getattr(o,"_decomposed",False) is False]
        for o in dead:
            self.detritus+=max(0.0,o.energy)
            o.energy=0.0
            o._decomposed=True
            self.decomposed+=1
        decomposition=min(self.detritus,dt*.002)
        self.detritus-=decomposition
        water.nitrate=max(0,min(10,water.nitrate+decomposition*.4-dt*.0003))
        water.phosphate=max(0,min(5,water.phosphate+decomposition*.08-dt*.00005))
        water.oxygen=max(0,min(14,water.oxygen+dt*.0002*sum(1 for o in living if species_profile(o.species)["trophic"]=="producer")))
    def state(self):
        return {k:getattr(self,k) for k in ("detritus","feedings","predation_events","decomposed","energy_consumed","energy_assimilated","energy_waste","energy_produced","metabolic_loss","respired_energy")}
    def restore(self,data):
        for key in self.state():
            value=data.get(key,0)
            setattr(self,key,max(0.0,float(value)))
    def snapshot(self):
        return {"feedings":self.feedings,"predation_events":self.predation_events,
                "decomposed_organisms":self.decomposed,"detritus":self.detritus,
                "energy_consumed":self.energy_consumed,"energy_assimilated":self.energy_assimilated,
                "energy_waste":self.energy_waste,"energy_produced":self.energy_produced,
                "metabolic_loss":self.metabolic_loss,"respired_energy":self.respired_energy}
