"""Species-aware social grouping, communication and territory memory."""
from physics import SpatialGrid
SOCIAL_SPECIES={"reef_fish":"school","dolphin":"pod","whale":"pod","shark":"territory","seal":"colony","crab":"aggregation"}
class SocialSystem:
    def __init__(self):
        self.groups={}; self.communications=0; self.territorial_encounters=0
    def step(self,organisms,dt,tick):
        living=[o for o in organisms if o.alive]
        grid=SpatialGrid(5); grid.rebuild(living); groups={}
        for o in living:
            mode=SOCIAL_SPECIES.get(o.species)
            if not mode: continue
            nearby=[p for p in grid.nearby(o.x,o.y,5) if p.id!=o.id and p.species==o.species]
            if mode=="territory":
                if nearby:
                    self.territorial_encounters+=1
                    o.brain.remember({"event":"territory_neighbour","tick":tick,"count":len(nearby)})
                continue
            if nearby:
                ids=sorted([o.id]+[p.id for p in nearby])
                group_id=ids[0]
                groups.setdefault(str(group_id),set()).update(ids)
                o.brain.learning["social_group"]=group_id
                if tick%30==0:
                    o.brain.remember({"event":"social_signal","mode":mode,"tick":tick})
                    self.communications+=1
        self.groups={k:sorted(v) for k,v in groups.items()}
    def snapshot(self):
        return {"active_groups":len(self.groups),"group_members":sum(len(v) for v in self.groups.values()),
                "communications":self.communications,"territorial_encounters":self.territorial_encounters}
    def state(self): return self.snapshot()
    def restore(self,d):
        self.communications=max(0,int(d.get("communications",0))); self.territorial_encounters=max(0,int(d.get("territorial_encounters",0)))
