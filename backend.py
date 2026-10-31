#!/usr/bin/env python3
"""NEXUS AQUARIUM shared simulation backend; Python standard library only."""
from __future__ import annotations
import argparse, json, os, random, secrets, threading, time
from dataclasses import dataclass, field, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

@dataclass
class Genome:
    traits: dict = field(default_factory=lambda: {"speed":.5,"size":.5,"camouflage":.5,"metabolism":.5,"fecundity":.5,"sensory":.5,"resistance":.5})
    generation: int = 0
    def inherit(self, mate, rng):
        out={}
        for k in self.traits.keys()|mate.traits.keys():
            v=self.traits.get(k,.5) if rng.random()<.5 else mate.traits.get(k,.5)
            if rng.random()<.025: v+=rng.gauss(0,.12)
            out[k]=max(0,min(1,v))
        return Genome(out,max(self.generation,mate.generation)+1)

@dataclass
class Brain:
    senses: tuple=("vision","chemical","pressure","electroreception","sound","temperature","touch","light","bioluminescence")
    memory: list=field(default_factory=list)
    learning: dict=field(default_factory=dict)
    def remember(self,event): self.memory=(self.memory+[event])[-32:]
    def learn(self,action,reward): self.learning[action]=self.learning.get(action,0)+.08*(reward-self.learning.get(action,0))

@dataclass
class Organism:
    id: int; species: str; x: float; y: float; vx: float=0.; vy: float=0.
    age: float=0.; energy: float=.9; health: float=1.; alive: bool=True; state: str="cruising"
    genome: Genome=field(default_factory=Genome); brain: Brain=field(default_factory=Brain); cooldown: float=0.

@dataclass
class Water:
    temperature: float=18.; salinity: float=35.; oxygen: float=8.; ph: float=8.1
    nitrate: float=.2; phosphate: float=.03; turbidity: float=.1
    def step(self,dt,biomass,rng):
        self.oxygen=max(0,min(14,self.oxygen+(.015-biomass*.00001)*dt))
        self.ph=max(6.5,min(8.5,self.ph-(self.nitrate+self.phosphate)*.00002*dt))
        self.temperature+=rng.uniform(-.002,.002)*dt
        self.turbidity=max(0,min(1,self.turbidity*.999+biomass*.000001))

class Engine:
    def __init__(self,seed=2026):
        self.rng=random.Random(seed); self.seed=seed; self.tick=0; self.sim_time=0.; self.paused=False
        self.organisms=[]; self.next_id=1; self.water=Water(); self.births=0; self.deaths=0; self.food_web={"reef_fish":["kelp","plankton"],"shark":["reef_fish","eel"],"jellyfish":["plankton"],"turtle":["seagrass","jellyfish"]}
        self.disturbances=[]
        for i in range(18): self.add("reef_fish",8+(i*7)%64,5+(i*3)%16,vx=.1 if i%2 else -.1)
        self.add("shark",40,10,vx=.08); self.add("jellyfish",25,18,vy=.04)
    def add(self,species,x,y,vx=0,vy=0,genome=None):
        o=Organism(self.next_id,species,x,y,vx,vy,genome=genome or Genome()); self.next_id+=1; self.organisms.append(o); return o
    def step(self,dt=1/30):
        if self.paused:return
        self.tick+=1; self.sim_time+=dt
        alive=[o for o in self.organisms if o.alive]
        for o in alive:
            o.age+=dt; o.cooldown=max(0,o.cooldown-dt); o.energy=max(0,o.energy-dt*(.0008+o.genome.traits["metabolism"]*.0007))
            threats=[p for p in alive if p.species=="shark" and o.species not in ("shark",) and (p.x-o.x)**2+(p.y-o.y)**2<36]
            if threats:
                o.state="fleeing"; o.brain.remember({"tick":self.tick,"event":"predator_nearby"})
                p=threats[0]; o.vx+=(o.x-p.x)*.015*dt; o.vy+=(o.y-p.y)*.015*dt
            elif o.species=="reef_fish": o.state="schooling"
            else:o.state="foraging" if o.energy<.5 else "cruising"
            o.x=max(0,min(79,o.x+o.vx*dt)); o.y=max(0,min(23,o.y+o.vy*dt))
            if o.energy<=.02 or o.health<=.01:o.alive=False; self.deaths+=1
        for parent in alive:
            if parent.alive and parent.age>30 and parent.energy>.72 and parent.cooldown<=0 and self.rng.random()<.0008*dt*30:
                child=self.add(parent.species,parent.x,parent.y,genome=parent.genome.inherit(parent.genome,self.rng))
                parent.energy*=.72; parent.cooldown=20; self.births+=1
        biomass=sum(o.energy for o in alive if o.alive); self.water.step(dt,biomass,self.rng)
        for d in self.disturbances:
            d["remaining"]-=dt
            if d["kind"] in ("oxygen_depletion","disease_outbreak","algal_bloom"):
                for o in alive:
                    if o.alive:o.health=max(0,o.health-d["intensity"]*.0005*dt)
        self.disturbances=[d for d in self.disturbances if d["remaining"]>0]
    def snapshot(self):
        return {"tick":self.tick,"simulation_time":self.sim_time,"paused":self.paused,"seed":self.seed,
          "water":asdict(self.water),"population":{"alive":sum(o.alive for o in self.organisms),"births":self.births,"deaths":self.deaths},
          "food_web":self.food_web,"disturbances":self.disturbances,
          "organisms":[{"id":o.id,"species":o.species,"x":o.x,"y":o.y,"energy":o.energy,"health":o.health,"alive":o.alive,"state":o.state,"generation":o.genome.generation,"genome":o.genome.traits,"senses":o.brain.senses,"memory":o.brain.memory[-8:]} for o in self.organisms]}

class Service:
    def __init__(self,token,engine=None):
        self.token=token; self.engine=engine or Engine(); self.lock=threading.RLock(); self.running=True
        self.thread=threading.Thread(target=self.loop,daemon=True); self.thread.start()
    def loop(self):
        last=time.monotonic()
        while self.running:
            now=time.monotonic(); dt=min(.2,now-last); last=now
            with self.lock:self.engine.step(dt)
            time.sleep(1/30)
class Handler(BaseHTTPRequestHandler):
    service=None
    def log_message(self,*args):pass
    def send_json(self,code,data):
        raw=json.dumps(data).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type"); self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def authorized(self):return secrets.compare_digest(self.headers.get("Authorization","").removeprefix("Bearer "),self.service.token)
    def do_OPTIONS(self):self.send_json(204,{})
    def do_GET(self):
        if self.path=="/health":return self.send_json(200,{"ok":True,"engine":"single-authoritative-python-engine"})
        if self.path!="/snapshot":return self.send_json(404,{"error":"not found"})
        if not self.authorized():return self.send_json(401,{"error":"Bearer token required"})
        with self.service.lock:data=self.service.engine.snapshot()
        self.send_json(200,data)
    def do_POST(self):
        if not self.authorized():return self.send_json(401,{"error":"Bearer token required"})
        try:body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))) or b"{}")
        except Exception:return self.send_json(400,{"error":"invalid JSON"})
        with self.service.lock:
            e=self.service.engine
            if self.path=="/control/pause":e.paused=bool(body.get("paused",True)); result={"paused":e.paused}
            elif self.path=="/control/step":
                for _ in range(max(0,min(10000,int(body.get("steps",1))))):e.step()
                result={"tick":e.tick}
            elif self.path=="/control/disturbance":
                kind=str(body.get("kind","storm")); intensity=max(0,min(1,float(body.get("intensity",.5))))
                e.disturbances.append({"kind":kind,"intensity":intensity,"remaining":max(.1,float(body.get("duration",10)))})
                result={"accepted":True,"kind":kind}
            else:return self.send_json(404,{"error":"unknown control"})
        self.send_json(200,result)

def main():
    p=argparse.ArgumentParser();p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=8765);p.add_argument("--token",default=os.getenv("NEXUS_API_TOKEN",""));a=p.parse_args()
    if len(a.token)<16:raise SystemExit("Set NEXUS_API_TOKEN to a secret of at least 16 characters.")
    Handler.service=Service(a.token);print(f"NEXUS AQUARIUM backend on http://{a.host}:{a.port}")
    try:ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
    except KeyboardInterrupt:pass
    finally:Handler.service.running=False
if __name__=="__main__":main()
