"""Species tolerance, environmental stress and gradual acclimation."""
from biodiversity import species_profile

class EnvironmentalResponse:
    def __init__(self):
        self.mean_stress=0.0
        self.stressed_organisms=0
    def step(self,organisms,water,dt,habitat):
        total=0.0; count=0; stressed=0
        for organism in organisms:
            if not organism.alive: continue
            p=species_profile(organism.species)
            lo,hi=p["temperature"]
            temp=max(0.0,lo-water.temperature,water.temperature-hi)/max(1.0,hi-lo)
            oxygen=max(0.0,p["oxygen_min"]-water.oxygen)/max(.5,p["oxygen_min"])
            habitat_penalty=0.12 if habitat not in p["habitats"] and "all" not in p["habitats"] else 0.0
            stress=min(1.0,temp+oxygen+habitat_penalty)
            resistance=organism.genome.traits.get("resistance",.5)
            effective=stress*(1.0-.65*resistance)
            total+=effective; count+=1
            if effective>.05: stressed+=1
            if effective>0:
                organism.health=max(0.0,organism.health-effective*dt*.00035)
                organism.brain.learn("acclimation",effective)
            else:
                organism.health=min(1.0,organism.health+dt*.000015)
        self.mean_stress=total/max(1,count); self.stressed_organisms=stressed
    def state(self): return self.snapshot()
    def restore(self,data):
        self.mean_stress=max(0.0,min(1.0,float(data.get("mean_stress",0))))
        self.stressed_organisms=max(0,int(data.get("stressed_organisms",0)))
    def snapshot(self):
        return {"mean_stress":self.mean_stress,"stressed_organisms":self.stressed_organisms}
