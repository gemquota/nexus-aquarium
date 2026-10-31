"""Multi-pool carbon, nitrogen, phosphorus and oxygen bookkeeping."""
class NutrientCycle:
    def __init__(self):
        self.doc=0.0; self.poc=0.0; self.nitrogen=0.0; self.phosphorus=0.0
        self.primary_production=0.0; self.respiration=0.0; self.mineralized=0.0
    def step(self,organisms,water,dt):
        living=[o for o in organisms if o.alive]
        producers=[o for o in living if o.species in ("kelp","seagrass","phytoplankton","coral_polyp")]
        consumers=[o for o in living if o not in producers]
        light=max(0.0,1.0-water.turbidity)
        nutrient_limit=min(1.0,water.nitrate/0.5,water.phosphate/0.05)
        production=len(producers)*dt*.00012*light*nutrient_limit
        respiration=sum(max(0.0,o.energy)*.000015 for o in consumers)*dt
        self.primary_production+=production; self.respiration+=respiration
        self.doc+=respiration*.35; self.poc+=production*.15
        mineral=min(self.doc+self.poc,dt*.0004)
        self.doc=max(0.0,self.doc-mineral*.65); self.poc=max(0.0,self.poc-mineral*.35)
        self.mineralized+=mineral
        self.nitrogen=max(0.0,self.nitrogen+mineral*.08-production*.04)
        self.phosphorus=max(0.0,self.phosphorus+mineral*.015-production*.008)
        water.oxygen=max(0.0,min(14.0,water.oxygen+production*1.4-respiration))
        water.nitrate=max(0.0,min(10.0,water.nitrate+mineral*.03-production*.01))
        water.phosphate=max(0.0,min(5.0,water.phosphate+mineral*.006-production*.002))
    def state(self):
        return {k:getattr(self,k) for k in ("doc","poc","nitrogen","phosphorus","primary_production","respiration","mineralized")}
    def restore(self,data):
        for k in self.state(): setattr(self,k,max(0.0,float(data.get(k,0))))
    def snapshot(self):
        return {"dissolved_organic_carbon":self.doc,"particulate_organic_carbon":self.poc,
                "nitrogen_pool":self.nitrogen,"phosphorus_pool":self.phosphorus,
                "cumulative_primary_production":self.primary_production,
                "cumulative_respiration":self.respiration,"cumulative_mineralization":self.mineralized}
