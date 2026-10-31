"""Species-aware steering: schooling, pursuit, evasion, cruising and benthic behaviour."""
import math
from biodiversity import species_profile
from physics import SpatialGrid

PELAGIC={"reef_fish","dolphin","whale","seal","shark","ray","jellyfish","sea_turtle","sea_snake","eel","shrimp"}
PREDATORS={"shark","dolphin","seal","octopus","eel","sea_snake"}
PREY={"reef_fish","shrimp","zooplankton","clam","jellyfish"}

class BehaviourSystem:
 def __init__(self):
  self.decisions=0; self.school_links=0; self.flee_responses=0; self.hunts=0; self.foraging=0; self.resting=0
 def step(self,organisms,dt,rng):
  living=[o for o in organisms if o.alive]
  grid=SpatialGrid(12); grid.rebuild(living)
  for o in living:
   profile=species_profile(o.species); group=profile["group"]
   traits=o.genome.traits; agility=max(.1,min(1,float(traits.get("agility",.5))))
   turn=max(.1,min(1,float(traits.get("turn_rate",.5))))
   speed=max(.02,float(profile["speed"])*(.55+.9*float(traits.get("speed",.5))))
   nearby=[p for p in grid.nearby(o.x,o.y,12) if p.id!=o.id]
   threats=[p for p in nearby if p.species in PREDATORS and p.species!=o.species]
   prey=[p for p in nearby if p.species in PREY and p.species!=o.species]
   ax=0.; ay=0.; state="cruising"
   if threats:
    predator=min(threats,key=lambda q:(q.x-o.x)**2+(q.y-o.y)**2)
    dx=o.x-predator.x; dy=o.y-predator.y; mag=max(.01,math.hypot(dx,dy))
    ax+=dx/mag*speed*1.8; ay+=dy/mag*speed*1.8; state="fleeing"; self.flee_responses+=1
    if not o.brain.memory or o.brain.memory[-1].get("event")!="predator_nearby": o.brain.remember({"event":"predator_nearby","tick":getattr(o,"age",0)})
   elif o.species in PREDATORS and prey and o.energy<.85:
    target=min(prey,key=lambda q:(q.x-o.x)**2+(q.y-o.y)**2)
    dx=target.x-o.x; dy=target.y-o.y; mag=max(.01,math.hypot(dx,dy))
    ax+=dx/mag*speed*1.25; ay+=dy/mag*speed*1.25; state="hunting"; self.hunts+=1
   elif group=="fish" or o.species in ("dolphin","seal"):
    school=[p for p in nearby if p.species==o.species]
    if school:
     cx=sum(p.x for p in school)/len(school)-o.x; cy=sum(p.y for p in school)/len(school)-o.y
     avx=sum(p.vx for p in school)/len(school)-o.vx; avy=sum(p.vy for p in school)/len(school)-o.vy
     separation_x=sum((o.x-p.x)/(math.hypot(o.x-p.x,o.y-p.y)**2+.2) for p in school)
     separation_y=sum((o.y-p.y)/(math.hypot(o.x-p.x,o.y-p.y)**2+.2) for p in school)
     ax+=cx*.16+avx*.9+separation_x*.35; ay+=cy*.16+avy*.9+separation_y*.35
     state="schooling"; self.school_links+=len(school)
    else: state="exploring"; ax+=math.sin(o.age*.7+o.id)*speed*.35; ay+=math.cos(o.age*.53+o.id)*speed*.18
   elif o.species in ("ray","crab","sea_star","sea_urchin","clam","octopus"):
    target_y=max(0,self._water_bottom(organisms)-2)
    ay+=(target_y-o.y)*.08; ax+=math.sin(o.age*.25+o.id)*speed*.15
    state="benthic_foraging" if o.energy<.75 else "resting"
    if state=="resting": self.resting+=1
   elif o.species in ("whale","jellyfish"):
    ay+=math.sin(o.age*.18+o.id*.7)*speed*.45
    ax+=math.sin(o.age*.09+o.id)*speed*.2
    state="filter_feeding" if o.species=="whale" else "drifting"
   elif o.species in ("kelp","seagrass","coral_polyp","phytoplankton","bacteria"):
    state="attached" if o.species not in ("phytoplankton","bacteria") else "drifting"
   elif o.energy<.35:
    state="foraging"; ax+=math.sin(o.age*.4+o.id)*speed*.35; ay+=math.cos(o.age*.31+o.id)*speed*.2; self.foraging+=1
   else:
    ax+=math.sin(o.age*.33+o.id*1.7)*speed*.22
    ay+=math.cos(o.age*.27+o.id*.8)*speed*.16
   # Smooth acceleration prevents abrupt direction changes while keeping motion lively.
   o.vx+=max(-2.0,min(2.0,ax))*dt*agility
   o.vy+=max(-1.5,min(1.5,ay))*dt*agility
   damping=max(.90,1.0-.18*dt*(1.1-turn))
   o.vx*=damping; o.vy*=damping
   cap=max(.02,speed*(1.0 if state not in ("resting","attached") else .18))
   magnitude=math.hypot(o.vx,o.vy)
   if magnitude>cap: o.vx*=cap/magnitude; o.vy*=cap/magnitude
   o.state=state; self.decisions+=1
 def _water_bottom(self,organisms):
  # Used only to keep benthic animals close to the local lower habitat boundary.
  return max((p.y for p in organisms if p.alive),default=0)
 def state(self):
  return {"decisions":self.decisions,"school_links":self.school_links,"flee_responses":self.flee_responses,"hunts":self.hunts,"foraging":self.foraging,"resting":self.resting}
 def restore(self,d):
  for key in ("decisions","school_links","flee_responses","hunts","foraging","resting"): setattr(self,key,max(0,int(d.get(key,0))))
 def snapshot(self): return self.state()
