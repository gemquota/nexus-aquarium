import math
from biodiversity import species_profile
class BehaviourSystem:
 def __init__(self): self.decisions=0; self.school_links=0; self.flee_responses=0
 def step(self,organisms,dt,rng):
  living=[o for o in organisms if o.alive]
  for o in living:
   profile=species_profile(o.species); nearby=[p for p in living if p.id!=o.id and (p.x-o.x)**2+(p.y-o.y)**2<64]
   threats=[p for p in nearby if p.species=="shark" and o.species!="shark"]
   if threats:
    p=min(threats,key=lambda q:(q.x-o.x)**2+(q.y-o.y)**2); dx=o.x-p.x; dy=o.y-p.y; mag=max(.01,math.hypot(dx,dy))
    o.vx+=dx/mag*.035*dt; o.vy+=dy/mag*.035*dt; o.state="fleeing"; self.flee_responses+=1
   elif profile["group"]=="fish":
    school=[p for p in nearby if p.species==o.species]
    if school:
     ax=sum(p.vx for p in school)/len(school); ay=sum(p.vy for p in school)/len(school)
     cx=sum(p.x for p in school)/len(school)-o.x; cy=sum(p.y for p in school)/len(school)-o.y
     o.vx+=((ax-o.vx)*.08+cx*.002)*dt; o.vy+=((ay-o.vy)*.08+cy*.002)*dt; o.state="schooling"; self.school_links+=len(school)
    else: o.state="exploring"
   elif o.energy<.35: o.state="foraging"
   else: o.state="cruising"
   speed=math.hypot(o.vx,o.vy); cap=max(.01,profile["speed"]*.25)
   if speed>cap: o.vx*=cap/speed; o.vy*=cap/speed
   self.decisions+=1
 def state(self): return {"decisions":self.decisions,"school_links":self.school_links,"flee_responses":self.flee_responses}
 def restore(self,d): self.decisions=max(0,int(d.get("decisions",0))); self.school_links=max(0,int(d.get("school_links",0))); self.flee_responses=max(0,int(d.get("flee_responses",0)))
 def snapshot(self): return {"decisions":self.decisions,"school_links":self.school_links,"flee_responses":self.flee_responses}
