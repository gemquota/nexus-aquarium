"""Persistent individual goals and species-aware marine behaviour."""
import math
from biodiversity import species_profile
from physics import SpatialGrid

PREDATORS={"shark","dolphin","seal","octopus","eel","sea_snake"}
PREY={"reef_fish","shrimp","zooplankton","clam","jellyfish"}
PLANTS={"kelp","seagrass","phytoplankton"}
BENTHIC={"ray","crab","sea_star","sea_urchin","clam","octopus"}
ATTACHED={"kelp","seagrass","coral_polyp","bacteria"}
HERBIVORES={"sea_urchin","sea_turtle","clam"}
MAMMALS={"whale","dolphin","seal"}

class BehaviourSystem:
 def __init__(self):
  self.decisions=0; self.school_links=0; self.flee_responses=0; self.hunts=0; self.foraging=0; self.resting=0
  self.goal_changes=0; self.memory_events=0; self.patrols=0; self.migrations=0
 def step(self,organisms,dt,rng):
  living=[o for o in organisms if o.alive]
  grid=SpatialGrid(18); grid.rebuild(living)
  for o in living:
   if "goal_timer" in o.brain.learning: o.brain.learning["goal_timer"]=max(0.0,float(o.brain.learning["goal_timer"])-dt)
   profile=species_profile(o.species); traits=o.genome.traits
   agility=max(.1,min(1,float(traits.get("agility",.5))))
   turn=max(.1,min(1,float(traits.get("turn_rate",.5))))
   tracking=max(.1,min(1,float(traits.get("tracking",.5))))
   speed=max(.025,float(profile["speed"])*(.6+.8*float(traits.get("speed",.5))))
   nearby=[p for p in grid.nearby(o.x,o.y,18) if p.id!=o.id and p.alive]
   threats=[p for p in nearby if p.species in PREDATORS and p.species!=o.species]
   prey=[p for p in nearby if p.species in PREY and p.species!=o.species]
   goal=self._goal(o)
   ax=0.; ay=0.; state="cruising"; event=None
   # Immediate survival overrides every other goal.
   if threats and o.species not in PREDATORS:
    predator=min(threats,key=lambda p:self._distance2(o,p))
    dx=o.x-predator.x; dy=o.y-predator.y; mag=max(.01,math.hypot(dx,dy))
    ax+=dx/mag*speed*2.0; ay+=dy/mag*speed*2.0
    state="fleeing"; event="predator_nearby"; self.flee_responses+=1
   elif o.species in PREDATORS and prey and o.energy<.9:
    target=self._select_target(o,prey,goal,rng,"hunt")
    self._set_goal(o,target,"hunt",rng)
    dx=target.x-o.x; dy=target.y-o.y
    # Tracking predicts a short lead from the prey's current velocity.
    lead=min(2.5,tracking*2.5)
    dx+=target.vx*lead; dy+=target.vy*lead
    mag=max(.01,math.hypot(dx,dy))
    ax+=dx/mag*speed*(1.2+.7*tracking); ay+=dy/mag*speed*(1.2+.7*tracking)
    state="hunting"; event="target_acquired"; self.hunts+=1
   elif o.species in HERBIVORES and o.energy<.8:
    food=[p for p in nearby if p.species in PLANTS]
    if food:
     target=self._select_target(o,food,goal,rng,"graze"); self._set_goal(o,target,"graze",rng)
     dx=target.x-o.x; dy=target.y-o.y; mag=max(.01,math.hypot(dx,dy))
     ax+=dx/mag*speed*.9; ay+=dy/mag*speed*.9; state="foraging"; self.foraging+=1
    else: state="searching"; ax+=math.sin(o.age*.22+o.id)*speed*.3; ay+=math.cos(o.age*.19+o.id)*speed*.2
   elif o.species in ("reef_fish","dolphin","seal"):
    school=[p for p in nearby if p.species==o.species]
    if school:
     cx=sum(p.x for p in school)/len(school)-o.x; cy=sum(p.y for p in school)/len(school)-o.y
     avx=sum(p.vx for p in school)/len(school)-o.vx; avy=sum(p.vy for p in school)/len(school)-o.vy
     sx=sum((o.x-p.x)/(self._distance2(o,p)+.2) for p in school)
     sy=sum((o.y-p.y)/(self._distance2(o,p)+.2) for p in school)
     ax+=cx*.13+avx*.8+sx*.32; ay+=cy*.13+avy*.8+sy*.32
     state="schooling"; self.school_links+=len(school)
    else:
     state="exploring"; ax+=math.sin(o.age*.55+o.id)*speed*.45; ay+=math.cos(o.age*.41+o.id)*speed*.25
   elif o.species in BENTHIC:
    target_y=max(o.y,min(o.y+2.0, self._seabed_y(o,organisms)))
    ay+=(target_y-o.y)*.22; ax+=math.sin(o.age*.2+o.id)*speed*.2
    state="benthic_foraging" if o.energy<.75 else "resting"
    if state=="resting": self.resting+=1
   elif o.species in ("whale","jellyfish"):
    # Vertical dives and ascent cycles, with gentle horizontal cruising.
    phase=(o.age*.11+o.id*.37)%(2*math.pi)
    ay+=math.sin(phase)*speed*.75; ax+=math.sin(phase*.5)*speed*.3
    state="diving" if math.sin(phase)>.15 else "ascending"; 
   elif o.species in ATTACHED:
    state="attached"
   elif o.species in ("eel","sea_snake"):
    ax+=math.sin(o.age*.31+o.id)*speed*.7; ay+=math.sin(o.age*.17+o.id*1.3)*speed*.25
    state="undulating"
   elif o.energy<.35:
    state="resting"; self.resting+=1
   else:
    # Individual cruising route with occasional exploratory course changes.
    if goal is None or self._goal_timer(o)<=0:
     self._set_waypoint(o,rng); self.goal_changes+=1
    gx=float(o.brain.learning.get("goal_x",o.x)); gy=float(o.brain.learning.get("goal_y",o.y))
    dx=gx-o.x; dy=gy-o.y; mag=max(.01,math.hypot(dx,dy))
    ax+=dx/mag*speed*.55+math.sin(o.age*.23+o.id)*speed*.12
    ay+=dy/mag*speed*.55+math.cos(o.age*.19+o.id)*speed*.10
    state="patrolling"; self.patrols+=1
   # Persistent memories are sparse and bounded, rather than appended every frame.
   if event and (not o.brain.memory or o.brain.memory[-1].get("event")!=event):
    o.brain.remember({"event":event,"tick":int(o.age),"target":getattr(predator if threats else None,"id",None)})
    self.memory_events+=1
   o.vx+=max(-2.4,min(2.4,ax))*dt*agility
   o.vy+=max(-1.8,min(1.8,ay))*dt*agility
   damping=max(.91,1.0-.16*dt*(1.1-turn)); o.vx*=damping; o.vy*=damping
   cap=max(.025,speed*(1.0 if state not in ("resting","attached") else .16))
   magnitude=math.hypot(o.vx,o.vy)
   if magnitude>cap: o.vx*=cap/magnitude; o.vy*=cap/magnitude
   o.state=state; self.decisions+=1
 def _distance2(self,a,b): return (a.x-b.x)**2+(a.y-b.y)**2
 def _goal(self,o):
  l=o.brain.learning
  if self._goal_timer(o)<=0:return None
  return (l.get("goal_x"),l.get("goal_y"),l.get("goal_kind","patrol"))
 def _goal_timer(self,o): return float(o.brain.learning.get("goal_timer",0))
 def _set_goal(self,o,target,kind,rng):
  l=o.brain.learning
  if l.get("goal_id")!=target.id or l.get("goal_kind")!=kind:
   l.update({"goal_x":float(target.x),"goal_y":float(target.y),"goal_id":int(target.id),"goal_kind":kind,"goal_timer":2.0})
   self.goal_changes+=1
 def _set_waypoint(self,o,rng):
  l=o.brain.learning
  l.update({"goal_x":o.x+rng.uniform(-24,24),"goal_y":o.y+rng.uniform(-7,7),"goal_id":-1,"goal_kind":"patrol","goal_timer":rng.uniform(3,8)})
 def _select_target(self,o,candidates,goal,rng,kind):
  if goal and goal[2]==kind:
   current=next((p for p in candidates if p.id==o.brain.learning.get("goal_id")),None)
   if current:return current
  return min(candidates,key=lambda p:self._distance2(o,p))
 def _seabed_y(self,o,organisms):
  # In this coordinate system the seabed is the high-y boundary.
  return max((p.y for p in organisms if p.alive),default=o.y)
 def state(self):
  return {"decisions":self.decisions,"school_links":self.school_links,"flee_responses":self.flee_responses,"hunts":self.hunts,"foraging":self.foraging,"resting":self.resting,"goal_changes":self.goal_changes,"memory_events":self.memory_events,"patrols":self.patrols,"migrations":self.migrations}
 def restore(self,d):
  for key in ("decisions","school_links","flee_responses","hunts","foraging","resting","goal_changes","memory_events","patrols","migrations"): setattr(self,key,max(0,int(d.get(key,0))))
 def snapshot(self): return self.state()
