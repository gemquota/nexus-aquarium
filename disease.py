"""Spatially local disease exposure with incubation, resistance and recovery."""
from physics import SpatialGrid
class DiseaseSystem:
    def __init__(self):
        self.infected=0; self.new_infections=0; self.recoveries=0
    def step(self,organisms,disturbances,dt,rng):
        active=any(e.get("kind")=="disease_outbreak" for e in disturbances)
        living=[o for o in organisms if o.alive]
        grid=SpatialGrid(3); grid.rebuild(living)
        for o in living:
            load=float(o.brain.learning.get("pathogen_load",0.0))
            if active and load<=0:
                nearby=[p for p in grid.nearby(o.x,o.y,2.5) if p.id!=o.id and p.brain.learning.get("pathogen_load",0)>.2]
                if nearby and rng.random()<min(.5,dt*.025*(1-o.genome.traits.get("resistance",.5))):
                    load=.25; o.brain.remember({"event":"infection","tick":getattr(o,"last_tick",0)}); self.new_infections+=1
            if load>0:
                incubation=min(1.0,load+dt*.012)
                o.brain.learning["pathogen_load"]=incubation
                resistance=o.genome.traits.get("resistance",.5)
                o.health=max(0.0,o.health-dt*.00018*incubation*(1-resistance*.7))
                if not active and rng.random()<min(.2,dt*.004*(.5+resistance)):
                    o.brain.learning["pathogen_load"]=0.0; self.recoveries+=1
        self.infected=sum(1 for o in living if o.brain.learning.get("pathogen_load",0)>.05)
    def state(self): return {"infected":self.infected,"new_infections":self.new_infections,"recoveries":self.recoveries}
    def restore(self,d):
        self.infected=max(0,int(d.get("infected",0))); self.new_infections=max(0,int(d.get("new_infections",0))); self.recoveries=max(0,int(d.get("recoveries",0)))
    def snapshot(self): return self.state()
