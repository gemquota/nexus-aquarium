"""Simple reef-building coral condition, bleaching and calcification model."""
class CoralReefSystem:
    """Tracks living coral condition from local water quality and light.

    This is an educational proxy model, not a calibrated reef forecast.
    """
    def __init__(self):
        self.bleaching=0.0
        self.cumulative_calcification=0.0
        self.mean_coral_health=1.0
        self.live_polyps=0
        self.recovery_rate=0.0

    def step(self, organisms, water, dt, light=0.5, plankton_bloom=0.0):
        corals=[o for o in organisms if o.alive and o.species=="coral_polyp"]
        self.live_polyps=len(corals)
        if not corals:
            self.mean_coral_health=0.0
            self.recovery_rate=0.0
            self.bleaching=max(0.0,self.bleaching-dt*0.00002)
            return
        # Heat stress rises above the warm edge of the simplified coral range.
        heat=max(0.0,water.temperature-28.0)/4.0
        acid=max(0.0,8.0-water.ph)/0.5
        sediment=max(0.0,water.turbidity-0.35)/0.65
        bloom=max(0.0,plankton_bloom-0.65)/0.35
        stress=min(1.0,heat*0.55+acid*0.25+sediment*0.12+bloom*0.08)
        target_bleaching=max(0.0,min(1.0,stress))
        # Bleaching develops faster than it reverses, as in real reef heatwaves.
        rate=0.0018 if target_bleaching>self.bleaching else 0.00035
        self.bleaching=max(0.0,min(1.0,self.bleaching+(target_bleaching-self.bleaching)*min(1.0,dt*rate)))
        optimal_temp=max(0.0,1.0-abs(water.temperature-26.0)/7.0)
        chemistry=max(0.0,min(1.0,(water.ph-7.4)/0.7))
        clarity=max(0.0,min(1.0,1.0-water.turbidity))
        calcification=optimal_temp*chemistry*clarity*max(0.0,min(1.0,light))
        self.cumulative_calcification+=calcification*len(corals)*dt*0.00001
        recovery=max(0.0,calcification*(1.0-self.bleaching)-stress)
        self.recovery_rate=recovery
        for coral in corals:
            coral.health=max(0.0,min(1.0,coral.health+(recovery*0.00008-stress*0.00022)*dt))
            coral.energy=max(0.0,min(1.0,coral.energy+(calcification*0.00004-stress*0.00008)*dt))
        self.mean_coral_health=sum(o.health for o in corals)/len(corals)

    def state(self):
        return {"bleaching":self.bleaching,"cumulative_calcification":self.cumulative_calcification,
                "mean_coral_health":self.mean_coral_health,"live_polyps":self.live_polyps,
                "recovery_rate":self.recovery_rate}

    def restore(self,data):
        self.bleaching=max(0.0,min(1.0,float(data.get("bleaching",0.0))))
        self.cumulative_calcification=max(0.0,float(data.get("cumulative_calcification",0.0)))
        self.mean_coral_health=max(0.0,min(1.0,float(data.get("mean_coral_health",1.0))))
        self.live_polyps=max(0,int(data.get("live_polyps",0)))
        self.recovery_rate=max(0.0,float(data.get("recovery_rate",0.0)))

    def snapshot(self):
        condition="bleached" if self.bleaching>=0.6 else "stressed" if self.bleaching>=0.2 else "healthy"
        return {**self.state(),"condition":condition}
