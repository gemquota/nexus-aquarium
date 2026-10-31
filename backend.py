#!/usr/bin/env python3
"""NEXUS AQUARIUM shared simulation backend; Python standard library only."""
from __future__ import annotations
import argparse, json, os, random, secrets, threading, time
from dataclasses import dataclass, field, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from physics import MarinePhysics
from biodiversity import species_profile, HABITATS
from ecology import Ecology
from life_cycles import life_stage, compatible, reproduction_probability, reproductive_mode, offspring_position
from behaviour import BehaviourSystem
from events import EventSystem
from environment import EnvironmentalResponse
from genetics import recombine, population_diversity
from habitats import HabitatMap
from nutrients import NutrientCycle
from disease import DiseaseSystem
from social import SocialSystem
from migration import MigrationSystem

ENGINE_VERSION = 3
DEFAULT_CONFIG = {"world_width":80,"world_height":24,"fixed_dt":1/30,"max_frame_dt":0.2,"checkpoint_interval":15.0,"max_organisms":5000,"habitat":"coral_reef","initial_fluid_particles":48}

@dataclass
class Genome:
    traits: dict = field(default_factory=lambda: {"speed":.5,"size":.5,"camouflage":.5,"metabolism":.5,"fecundity":.5,"sensory":.5,"resistance":.5})
    generation: int = 0
    def inherit(self, mate, rng):
        return Genome(recombine(self.traits,mate.traits,rng),max(self.generation,mate.generation)+1)


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
        self.physics=MarinePhysics(seed,self.config["world_width"],self.config["world_height"],self.config["initial_fluid_particles"]); self.ecology=Ecology(); self.behaviour=BehaviourSystem(); self.events=EventSystem(); self.environment=EnvironmentalResponse(); self.habitat_map=HabitatMap(self.config["world_width"],self.config["world_height"],seed); self.nutrients=NutrientCycle(); self.disease=DiseaseSystem(); self.social=SocialSystem(); self.migration=MigrationSystem()
        self.organisms=[]; self.next_id=1; self.habitat=self.config["habitat"]; hp=HABITATS[self.habitat]; self.water=Water(temperature=hp["temperature"],salinity=hp["salinity"],oxygen=hp["oxygen"],ph=hp["ph"],turbidity=hp["turbidity"]); self.births=0; self.deaths=0; self.food_web={"reef_fish":["zooplankton","shrimp"],"shark":["reef_fish","eel","ray"],"jellyfish":["zooplankton"],"dolphin":["reef_fish"],"whale":["zooplankton"],"octopus":["crab","shrimp"],"sea_turtle":["seagrass","jellyfish"],"sea_urchin":["kelp"],"clam":["phytoplankton"],"zooplankton":["phytoplankton"]}
        self.disturbances=[]
        for i in range(18): self.add("reef_fish",8+(i*7)%64,5+(i*3)%16,vx=.1 if i%2 else -.1)
        self.add("shark",40,10,vx=.08); self.add("jellyfish",25,18,vy=.04)
        extras=("ray","dolphin","whale","crab","octopus","eel","sea_turtle","seal","sea_snake","sea_star","sea_urchin","shrimp","clam","coral_polyp","kelp","seagrass","phytoplankton","zooplankton","bacteria")
        for i,name in enumerate(extras): self.add(name,5+(i*13)%70,2+(i*7)%20,vx=species_profile(name)["speed"]*.02)
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
        profile=species_profile(species)
        if genome is None: genome=Genome({"speed":profile["speed"],"size":profile["size"],"camouflage":.5,"metabolism":.5,"fecundity":profile["fecundity"],"sensory":.5,"resistance":.5})
        o=Organism(self.next_id,species,x,y,vx,vy,genome=genome); self.next_id+=1; self.organisms.append(o); return o
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
            if len(self.organisms)>=self.config["max_organisms"]: break
            if not parent.alive or life_stage(parent.species,parent.age)!="adult" or parent.energy<.72 or parent.cooldown>0: continue
            mode=reproductive_mode(parent.species)
            mates=[m for m in alive if compatible(parent,m) and m.energy>.65 and life_stage(m.species,m.age)=="adult" and (m.x-parent.x)**2+(m.y-parent.y)**2<100] if mode=="sexual" else []
            mate=min(mates,key=lambda m:(m.x-parent.x)**2+(m.y-parent.y)**2) if mates else None
            if (mate is not None or mode!="sexual") and self.rng.random()<reproduction_probability(parent,dt):
                x,y=offspring_position(parent,mate)
                genome=parent.genome.inherit(mate.genome,self.rng) if mate else parent.genome.inherit(parent.genome,self.rng)
                self.add(parent.species,x,y,genome=genome)
                parent.energy*=.82
                if mate: mate.energy*=.9; mate.cooldown=30
                parent.cooldown=30; self.births+=1
        self.behaviour.step(self.organisms,dt,self.rng)
        self.social.step(self.organisms,dt,self.tick)
        self.migration.step(self.organisms,self.habitat_map,dt)
        self.physics.step_particles(dt,self.sim_time)
        self.ecology.step(self.organisms,self.food_web,self.water,dt,self.rng)
        self.nutrients.step(self.organisms,self.water,dt)
        biomass=sum(o.energy for o in alive if o.alive); self.water.step(dt,biomass,self.rng)
        self.events.step(self,dt)
        self.disease.step(self.organisms,self.disturbances,dt,self.rng)
        self.environment.step(self.organisms,self.water,dt,self.habitat_map)
    def save_state(self,path):
        """Write a portable JSON checkpoint using atomic replacement."""
        if not path: return
        data={"engine_version":ENGINE_VERSION,"config":self.config,"habitat":self.habitat,"seed":self.seed,"tick":self.tick,"sim_time":self.sim_time,"paused":self.paused,
              "next_id":self.next_id,"births":self.births,"deaths":self.deaths,
              "water":asdict(self.water),"food_web":self.food_web,"disturbances":self.disturbances,
              "physics_state":self.physics.state(),"ecology_state":self.ecology.state(),"behaviour_state":self.behaviour.state(),"events_state":self.events.state(),"environment_state":self.environment.snapshot(),"nutrient_state":self.nutrients.state(),"disease_state":self.disease.state(),"social_state":self.social.state(),"migration_state":self.migration.state(),
              "rng_state":self.rng.getstate(),
              "organisms":[{"id":o.id,"species":o.species,"x":o.x,"y":o.y,"vx":o.vx,"vy":o.vy,
                "age":o.age,"energy":o.energy,"health":o.health,"alive":o.alive,"state":o.state,
                "cooldown":o.cooldown,"genome":asdict(o.genome),"brain":{"senses":list(o.brain.senses),
                "memory":o.brain.memory,"learning":o.brain.learning},"decomposed":getattr(o,"_decomposed",False)} for o in self.organisms]}
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
        engine.water=Water(**data.get("water",{})); engine.habitat=data.get("habitat",engine.config.get("habitat","coral_reef")); engine.food_web=data.get("food_web",engine.food_web)
        engine.disturbances=data.get("disturbances",[])
        if data.get("physics_state"): engine.physics.restore(data["physics_state"])
        engine.ecology.restore(data.get("ecology_state",{})); engine.behaviour.restore(data.get("behaviour_state",{})); engine.events.restore(data.get("events_state",{})); engine.environment.restore(data.get("environment_state",{})); engine.nutrients.restore(data.get("nutrient_state",{})); engine.disease.restore(data.get("disease_state",{})); engine.social.restore(data.get("social_state",{})); engine.migration.restore(data.get("migration_state",{}))
        def tuples(value): return tuple(tuples(v) for v in value) if isinstance(value,list) else value
        if data.get("rng_state"): engine.rng.setstate(tuples(data["rng_state"]))
        engine.organisms=[]
        for item in data.get("organisms",[]):
            genome=Genome(**item.get("genome",{})); brain_data=item.get("brain",{})
            brain=Brain(tuple(brain_data.get("senses",Brain.senses)),brain_data.get("memory",[]),brain_data.get("learning",{}))
            fields={k:item[k] for k in ("id","species","x","y","vx","vy","age","energy","health","alive","state","cooldown") if k in item}
            fields["genome"]=genome; fields["brain"]=brain; organism=Organism(**fields); organism._decomposed=bool(item.get("decomposed",False)); engine.organisms.append(organism)
        return engine

    def snapshot(self):
        living=[o for o in self.organisms if o.alive]
        species_counts={}
        for o in living: species_counts[o.species]=species_counts.get(o.species,0)+1
        return {"tick":self.tick,"simulation_time":self.sim_time,"paused":self.paused,"seed":self.seed,
          "world":{"width":self.config["world_width"],"height":self.config["world_height"],"habitat":self.habitat,"engine":"NEXUS Python ecosystem"},
          "physics":self.physics.snapshot(),"ecology_metrics":self.ecology.snapshot(),"behaviour":self.behaviour.snapshot(),"event_metrics":self.events.snapshot(self),"environment":self.environment.snapshot(),
          "water":asdict(self.water),
          "genetics":population_diversity(living),"nutrients":self.nutrients.snapshot(),"disease":self.disease.snapshot(),"social":self.social.snapshot(),"migration":self.migration.snapshot(),
          "habitat_map":self.habitat_map.snapshot(),
          "population":{"alive":len(living),"total":len(self.organisms),"births":self.births,"deaths":self.deaths,
            "species_count":len(species_counts),"species":species_counts,
            "mean_energy":sum(o.energy for o in living)/len(living) if living else 0,
            "mean_health":sum(o.health for o in living)/len(living) if living else 0},
          "ecology":{"food_web_links":sum(len(v) for v in self.food_web.values()),
            "active_disturbances":len(self.disturbances),"trophic_groups":len(self.food_web)},
          "food_web":self.food_web,"disturbances":self.disturbances,
          "organisms":[{"id":o.id,"species":o.species,"x":o.x,"y":o.y,"vx":o.vx,"vy":o.vy,
            "energy":o.energy,"health":o.health,"alive":o.alive,"state":o.state,"age":o.age,
            "generation":o.genome.generation,"life_stage":life_stage(o.species,o.age),"trophic_role":species_profile(o.species)["trophic"],"genome":o.genome.traits,"senses":o.brain.senses,
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
            return self.send_json(200,{"service":"NEXUS AQUARIUM","status":"online","health":"/health","snapshot":"/snapshot","dashboard":"https://gemquota.github.io/nexus-aquarium/"})
        if self.path=="/health":return self.send_json(200,{"ok":True,"engine":"single-authoritative-python-engine","version":ENGINE_VERSION})
        if self.path=="/catalogue":return self.send_json(200,{"species":{k:{"group":v["group"],"trophic":v["trophic"],"habitats":v["habitats"],"temperature":v["temperature"],"oxygen_min":v["oxygen_min"]} for k,v in __import__("biodiversity").SPECIES.items()},"habitats":HABITATS})
        if self.path not in ("/snapshot","/metrics"):return self.send_json(404,{"error":"not found"})
        if not self.authorized():return self.send_json(401,{"error":"Bearer token required"})
        with self.service.lock:
            data=self.service.engine.snapshot()
            if self.path=="/metrics": data={k:data[k] for k in ("tick","simulation_time","paused","population","water","physics","ecology_metrics","behaviour","event_metrics")}
        self.send_json(200,data)
    def do_POST(self):
        if not self.authorized():return self.send_json(401,{"error":"Bearer token required"})
        try: length=int(self.headers.get("Content-Length",0))
        except ValueError: return self.send_json(400,{"error":"invalid content length"})
        if length<0:return self.send_json(400,{"error":"invalid content length"})
        if length>8192:return self.send_json(413,{"error":"request too large"})
        try:body=json.loads(self.rfile.read(length) or b"{}")
        except Exception:return self.send_json(400,{"error":"invalid JSON"})
        if not isinstance(body,dict):return self.send_json(400,{"error":"JSON object required"})
        with self.service.lock:
            e=self.service.engine
            if self.path=="/control/pause":
                e.paused=bool(body.get("paused",True)); result={"paused":e.paused}
            elif self.path=="/control/step":
                try: steps=max(0,min(10000,int(body.get("steps",1))))
                except (TypeError,ValueError): return self.send_json(400,{"error":"steps must be an integer"})
                for _ in range(steps):e.step()
                result={"tick":e.tick,"steps":steps}
            elif self.path=="/control/disturbance":
                try:
                    kind=str(body.get("kind","storm")); intensity=max(0,min(1,float(body.get("intensity",.5))))
                    e.events.add(e,kind,intensity,float(body.get("duration",10)))
                except (ValueError,TypeError) as exc:return self.send_json(400,{"error":str(exc)})
                result={"accepted":True,"kind":kind}
            elif self.path=="/control/config":
                candidate={**e.config,**{k:v for k,v in body.items() if k in e.config}}
                try: Engine.validate_config(candidate)
                except (ValueError,TypeError) as exc:return self.send_json(400,{"error":str(exc)})
                e.config=candidate
                e.physics.width=candidate["world_width"]; e.physics.height=candidate["world_height"]; e.habitat_map=HabitatMap(e.physics.width,e.physics.height,e.seed)
                for organism in e.organisms:
                    organism.x=max(0,min(e.physics.width-1,organism.x)); organism.y=max(0,min(e.physics.height-1,organism.y))
                if candidate["habitat"]!=e.habitat:
                    hp=HABITATS[candidate["habitat"]]; e.habitat=candidate["habitat"]
                    e.water=Water(temperature=hp["temperature"],salinity=hp["salinity"],oxygen=hp["oxygen"],ph=hp["ph"],turbidity=hp["turbidity"])
                result={"config":e.config,"habitat":e.habitat}
            elif self.path=="/control/save":
                if not self.service.state_path:return self.send_json(503,{"error":"checkpoint storage is disabled"})
                e.save_state(self.service.state_path); result={"saved":True,"tick":e.tick}
            elif self.path=="/control/reset":
                try: seed=int(body.get("seed",e.seed))
                except (TypeError,ValueError): return self.send_json(400,{"error":"seed must be an integer"})
                self.service.engine=Engine(seed); result={"reset":True,"seed":seed}
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
