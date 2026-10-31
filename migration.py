"""Habitat-seeking migration for mobile marine taxa."""
import math
from biodiversity import species_profile
MIGRATORY={"reef_fish","shark","ray","dolphin","whale","sea_turtle","seal","sea_snake"}
class MigrationSystem:
    def __init__(self): self.migrating=0; self.completed=0
    def step(self,organisms,habitat_map,dt):
        active=0
        for o in organisms:
            if not o.alive or o.species not in MIGRATORY: continue
            profile=species_profile(o.species)
            preferred=profile["habitats"]
            current=habitat_map.at(o.x,o.y)
            stress=float(o.brain.learning.get("acclimation",0))
            target=None
            if current not in preferred or stress>.6:
                options=[]
                for (cx,cy),name in habitat_map.tiles.items():
                    if name in preferred:
                        tx=min(habitat_map.width-1,cx*habitat_map.cell_size+habitat_map.cell_size/2)
                        ty=min(habitat_map.height-1,cy*habitat_map.cell_size+habitat_map.cell_size/2)
                        d=(tx-o.x)**2+(ty-o.y)**2
                        options.append((d,tx,ty))
                if options: _,tx,ty=min(options); target=(tx,ty)
            if target:
                dx=target[0]-o.x; dy=target[1]-o.y; mag=max(.1,math.hypot(dx,dy))
                o.vx+=dx/mag*.012*dt; o.vy+=dy/mag*.012*dt
                o.state="migrating"; active+=1
        self.migrating=active
    def snapshot(self): return {"migrating_organisms":self.migrating,"completed_migrations":self.completed}
    def state(self): return self.snapshot()
    def restore(self,d): self.migrating=max(0,int(d.get("migrating_organisms",0))); self.completed=max(0,int(d.get("completed_migrations",0)))
