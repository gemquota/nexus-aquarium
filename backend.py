#!/usr/bin/env python3
"""NEXUS AQUARIUM shared simulation backend; Python standard library only."""
from __future__ import annotations
import argparse, json, os, random, secrets, threading, time
from dataclasses import dataclass, field, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from physics import MarinePhysics

ENGINE_VERSION = 2
DEFAULT_CONFIG = {"world_width":80,"world_height":24,"fixed_dt":1/30,"max_frame_dt":0.2,"checkpoint_interval":15.0,"max_organisms":5000}

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
    def __init__(self,seed=2026,config=None):
        self.config={**DEFAULT_CONFIG,**(config or {})}; self.validate_config(self.config)
        self.rng=random.Random(seed); self.seed=seed; self.tick=0; self.sim_time=0.; self.paused=False
        self.physics=MarinePhysics(seed,self.config["world_width"],self.config["world_height"])
        self.organisms=[]; self.next_id=1; self.water=Water(); self.births=0; self.deaths=0; self.food_web={"reef_fish":["kelp","plankton"],"shark":["reef_fish","eel"],"jellyfish":["plankton"],"turtle":["seagrass","jellyfish"]}
        self.disturbances=[]
        for i in range(18): self.add("reef_fish",8+(i*7)%64,5+(i*3)%16,vx=.1 if i%2 else -.1)
        self.add("shark",40,10,vx=.08); self.add("jellyfish",25,18,vy=.04)
    @staticmethod
    def validate_config(config):
        for key in ("world_width","world_height","max_organisms"):
            if int(config[key])<1: raise ValueError(f"{key} must be positive")
        if not 0.001<=float(config["fixed_dt"])<=1: raise ValueError("fixed_dt must be between 0.001 and 1")
        if not 0.1<=float(config["max_frame_dt"])<=2: raise ValueError("max_frame_dt must be between 0.1 and 2")
        if float(config["checkpoint_interval"])<1: raise ValueError("checkpoint_interval must be at least 1 second")

    def add(self,species,x,y,vx=0,vy=0,genome=None):
        if len(self.organisms)>=self.config["max_organisms"]: raise RuntimeError("organism capacity reached")
        if not species or not isinstance(species,str): raise ValueError("species must be a non-empty string")
        x=float(x); y=float(y)
        if not all(map(lambda v: v==v and abs(v)<1e9,(x,y))): raise ValueError("organism coordinates must be finite")
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
            self.physics.move(o,dt,self.sim_time)
            if o.energy<=.02 or o.health<=.01:o.alive=False; self.deaths+=1
        for parent in alive:
            if parent.alive and parent.age>30 and parent.energy>.72 and parent.cooldown<=0 and self.rng.random()<.0008*dt*30:
                child=self.add(parent.species,parent.x,parent.y,genome=parent.genome.inherit(parent.genome,self.rng))
                parent.energy*=.72; parent.cooldown=20; self.births+=1
        self.physics.step_particles(dt,self.sim_time)
        biomass=sum(o.energy for o in alive if o.alive); self.water.step(dt,biomass,self.rng)
        for d in self.disturbances:
            d["remaining"]-=dt
            if d["kind"] in ("oxygen_depletion","disease_outbreak","algal_bloom"):
                for o in alive:
                    if o.alive:o.health=max(0,o.health-d["intensity"]*.0005*dt)
        self.disturbances=[d for d in self.disturbances if d["remaining"]>0]
    def save_state(self,path):
        """Write a portable JSON checkpoint using atomic replacement."""
        if not path: return
        data={"engine_version":ENGINE_VERSION,"config":self.config,"seed":self.seed,"tick":self.tick,"sim_time":self.sim_time,"paused":self.paused,
              "next_id":self.next_id,"births":self.births,"deaths":self.deaths,
              "water":asdict(self.water),"food_web":self.food_web,"disturbances":self.disturbances,
              "rng_state":self.rng.getstate(),
              "organisms":[{"id":o.id,"species":o.species,"x":o.x,"y":o.y,"vx":o.vx,"vy":o.vy,
                "age":o.age,"energy":o.energy,"health":o.health,"alive":o.alive,"state":o.state,
                "cooldown":o.cooldown,"genome":asdict(o.genome),"brain":{"senses":list(o.brain.senses),
                "memory":o.brain.memory,"learning":o.brain.learning}} for o in self.organisms]}
        target=os.path.abspath(path); os.makedirs(os.path.dirname(target),exist_ok=True)
        tmp=target+".tmp"
        with open(tmp,"w",encoding="utf-8") as handle:
            json.dump(data,handle,separators=(",",":"),allow_nan=False); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp,target)

    @classmethod
    def load_state(cls,path):
        if not path or not os.path.isfile(path): return cls()
        with open(path,encoding="utf-8") as handle: data=json.load(handle)
        version=int(data.get("engine_version",1))
        if version>ENGINE_VERSION: raise ValueError(f"checkpoint version {version} is newer than engine version {ENGINE_VERSION}")
        engine=cls(data.get("seed",2026),data.get("config"))
        engine.tick=max(0,int(data.get("tick",0))); engine.sim_time=max(0.0,float(data.get("sim_time",0.0)))
        engine.paused=data.get("paused",False); engine.next_id=data.get("next_id",1)
        engine.births=data.get("births",0); engine.deaths=data.get("deaths",0)
        engine.water=Water(**data.get("water",{})); engine.food_web=data.get("food_web",engine.food_web)
        engine.disturbances=data.get("disturbances",[])
        def tuples(value): return tuple(tuples(v) for v in value) if isinstance(value,list) else value
        if data.get("rng_state"): engine.rng.setstate(tuples(data["rng_state"]))
        engine.organisms=[]
        for item in data.get("organisms",[]):
            genome=Genome(**item.get("genome",{})); brain_data=item.get("brain",{})
            brain=Brain(tuple(brain_data.get("senses",Brain.senses)),brain_data.get("memory",[]),brain_data.get("learning",{}))
            fields={k:item[k] for k in ("id","species","x","y","vx","vy","age","energy","health","alive","state","cooldown") if k in item}
            fields["genome"]=genome; fields["brain"]=brain; engine.organisms.append(Organism(**fields))
        return engine

    def snapshot(self):
        living=[o for o in self.organisms if o.alive]
        species_counts={}
        for o in living: species_counts[o.species]=species_counts.get(o.species,0)+1
        return {"tick":self.tick,"simulation_time":self.sim_time,"paused":self.paused,"seed":self.seed,
          "world":{"width":self.config["world_width"],"height":self.config["world_height"],"habitat":"temperate reef","engine":"NEXUS Python ecosystem"},
          "physics":self.physics.snapshot(),
          "water":asdict(self.water),
          "population":{"alive":len(living),"total":len(self.organisms),"births":self.births,"deaths":self.deaths,
            "species_count":len(species_counts),"species":species_counts,
            "mean_energy":sum(o.energy for o in living)/len(living) if living else 0,
            "mean_health":sum(o.health for o in living)/len(living) if living else 0},
          "ecology":{"food_web_links":sum(len(v) for v in self.food_web.values()),
            "active_disturbances":len(self.disturbances),"trophic_groups":len(self.food_web)},
          "food_web":self.food_web,"disturbances":self.disturbances,
          "organisms":[{"id":o.id,"species":o.species,"x":o.x,"y":o.y,"vx":o.vx,"vy":o.vy,
            "energy":o.energy,"health":o.health,"alive":o.alive,"state":o.state,"age":o.age,
            "generation":o.genome.generation,"genome":o.genome.traits,"senses":o.brain.senses,
            "memory":o.brain.memory[-8:]} for o in self.organisms]}

class Service:
    def __init__(self,token,engine=None,state_path=""):
        self.token=token; self.state_path=state_path; self.engine=engine or Engine.load_state(state_path)
        self.lock=threading.RLock(); self.running=True; self.last_save=time.monotonic()
        self.thread=threading.Thread(target=self.loop,daemon=True); self.thread.start()
    def loop(self):
        last=time.monotonic()
        while self.running:
            now=time.monotonic(); dt=min(.2,now-last); last=now
            with self.lock:
                self.engine.step(dt)
                if self.state_path and now-self.last_save>=self.engine.config["checkpoint_interval"]:
                    self.engine.save_state(self.state_path); self.last_save=now
            time.sleep(1/30)
class Handler(BaseHTTPRequestHandler):
    service=None
    def log_message(self,*args):pass
    def send_json(self,code,data):
        raw=json.dumps(data).encode() if code!=204 else b""; self.send_response(code); self.send_header("Content-Type","application/json")
        origin=self.headers.get("Origin","")
        allowed=os.getenv("NEXUS_ALLOWED_ORIGIN","https://gemquota.github.io")
        if origin==allowed: self.send_header("Access-Control-Allow-Origin",allowed); self.send_header("Vary","Origin")
        self.send_header("Access-Control-Allow-Headers","Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.send_header("Content-Length",str(len(raw))); self.end_headers()
        if code!=204: self.wfile.write(raw)
    def authorized(self):return secrets.compare_digest(self.headers.get("Authorization","").removeprefix("Bearer "),self.service.token)
    def do_OPTIONS(self):
        origin=self.headers.get("Origin","")
        if origin!=os.getenv("NEXUS_ALLOWED_ORIGIN","https://gemquota.github.io"):
            return self.send_json(403,{"error":"origin not allowed"})
        self.send_json(204,{})
    def do_GET(self):
        if self.path=="/":
            return self.send_json(200,{"service":"NEXUS AQUARIUM","status":"online","health":"/health",
              "snapshot":"/snapshot","dashboard":"https://gemquota.github.io/nexus-aquarium/"})
        if self.path=="/health":return self.send_json(200,{"ok":True,"engine":"single-authoritative-python-engine","version":ENGINE_VERSION})
        if self.path!="/snapshot":return self.send_json(404,{"error":"not found"})
        if not self.authorized():return self.send_json(401,{"error":"Bearer token required"})
        with self.service.lock:data=self.service.engine.snapshot()
        self.send_json(200,data)
    def do_POST(self):
        if not self.authorized():return self.send_json(401,{"error":"Bearer token required"})
        length=int(self.headers.get("Content-Length",0))
        if length>8192:return self.send_json(413,{"error":"request too large"})
        try:body=json.loads(self.rfile.read(length) or b"{}")
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
    p=argparse.ArgumentParser();p.add_argument("--host",default=os.getenv("HOST","0.0.0.0"));p.add_argument("--port",type=int,default=int(os.getenv("PORT","8000")));p.add_argument("--token",default=os.getenv("NEXUS_API_TOKEN",""));a=p.parse_args()
    if len(a.token)<16:raise SystemExit("Set NEXUS_API_TOKEN to a secret of at least 16 characters.")
    state_path=os.getenv("NEXUS_STATE_FILE","/data/nexus-state.json")
    Handler.service=Service(a.token,state_path=state_path);print(f"NEXUS AQUARIUM backend on http://{a.host}:{a.port}")
    server=ThreadingHTTPServer((a.host,a.port),Handler); server.daemon_threads=True
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        Handler.service.running=False
        Handler.service.thread.join(timeout=3)
        with Handler.service.lock:Handler.service.engine.save_state(state_path)
        server.server_close()
if __name__=="__main__":main()
