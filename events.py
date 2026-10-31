EVENTS={"storm","algal_bloom","oxygen_depletion","coral_bleaching","disease_outbreak","habitat_damage","invasive_species","food_shortage","heatwave","volcanic_activity"}
class EventSystem:
 def __init__(self): self.total_events=0
 def add(self,engine,kind,intensity=.4,duration=20):
  if kind not in EVENTS: raise ValueError("unsupported event")
  item={"kind":kind,"intensity":max(0,min(1,float(intensity))),"remaining":max(.1,min(3600,float(duration)))}
  engine.disturbances.append(item); self.total_events+=1; return item
 def step(self,engine,dt):
  for e in engine.disturbances:
   e["remaining"]-=dt; k=e["kind"]; p=e["intensity"]; w=engine.water
   if k=="storm": w.turbidity=min(1,w.turbidity+p*.002*dt)
   elif k=="algal_bloom": w.turbidity=min(1,w.turbidity+p*.001*dt); w.oxygen=max(0,w.oxygen-p*.001*dt)
   elif k=="oxygen_depletion": w.oxygen=max(0,w.oxygen-p*.003*dt)
   elif k=="heatwave": w.temperature=min(40,w.temperature+p*.001*dt)
   elif k=="volcanic_activity": w.temperature=min(40,w.temperature+p*.004*dt); w.turbidity=min(1,w.turbidity+p*.003*dt)
   elif k=="coral_bleaching":
    for o in engine.organisms:
     if o.alive and o.species=="coral_polyp": o.health=max(0,o.health-p*.0008*dt)
   elif k=="disease_outbreak":
    for o in engine.organisms:
     if o.alive: o.health=max(0,o.health-p*.0003*dt)
   elif k=="habitat_damage" or k=="food_shortage":
    for o in engine.organisms:
     if o.alive: o.energy=max(0,o.energy-p*.0001*dt)
  engine.disturbances=[e for e in engine.disturbances if e["remaining"]>0]
 def snapshot(self,engine): return {"active":len(engine.disturbances),"events_started":self.total_events,"event_types":sorted(EVENTS)}
