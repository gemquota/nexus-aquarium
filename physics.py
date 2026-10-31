"""Lightweight marine motion and SPH-inspired particle field for NEXUS."""
from __future__ import annotations
from dataclasses import dataclass
import math, random

@dataclass
class FluidParticle:
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    density: float = 1.0
    pressure: float = 0.0

class SpatialGrid:
    def __init__(self, cell_size=4.0):
        self.cell_size=max(.1,float(cell_size)); self.cells={}
    def rebuild(self,items):
        self.cells={}
        for item in items:
            key=(int(item.x//self.cell_size),int(item.y//self.cell_size))
            self.cells.setdefault(key,[]).append(item)
    def nearby(self,x,y,radius):
        reach=max(1,int(math.ceil(radius/self.cell_size))); cx=int(x//self.cell_size); cy=int(y//self.cell_size)
        found=[]
        for gx in range(cx-reach,cx+reach+1):
            for gy in range(cy-reach,cy+reach+1): found.extend(self.cells.get((gx,gy),()))
        return [v for v in found if (v.x-x)**2+(v.y-y)**2<=radius*radius]

class CurrentField:
    def __init__(self,seed=0):
        self.phase=(seed%10000)/1000
        self.base_x=.035; self.base_y=.008; self.tilt_x=0.0; self.tilt_y=0.0
    def sample(self,x,y,t):
        return (self.base_x+self.tilt_x*.045+math.sin(y*.31+t*.17+self.phase)*.025,
                self.base_y+self.tilt_y*.025+math.cos(x*.19-t*.11+self.phase)*.012)

class MarinePhysics:
    """Bounded, deterministic current/drag/buoyancy and SPH-inspired fluid particles."""
    def __init__(self,seed=0,width=80,height=24,particle_count=48):
        self.width=width; self.height=height; self.waterline=height*.9; self.currents=CurrentField(seed)
        rng=random.Random(seed ^ 0xA51); self.particles=[FluidParticle(rng.random()*width,rng.random()*height,
            rng.uniform(-.02,.02),rng.uniform(-.01,.01)) for _ in range(particle_count)]
        self.grid=SpatialGrid(4); self.smoothing_radius=3.0; self.rest_density=1.0
    def move(self,organism,dt,t):
        cx,cy=self.currents.sample(organism.x,organism.y,t)
        traits=organism.genome.traits
        mass=max(.2,float(traits.get("size",.5))+0.5)
        agility=max(0.0,min(1.0,float(traits.get("agility",.5))))
        speed=max(.05,min(2.0,float(traits.get("speed",.5))*1.5))
        turn_rate=max(.05,min(1.0,float(traits.get("turn_rate",.5))))
        drag=max(.02,1-float(traits.get("size",.5))*.08)
        buoyancy=(.012 if organism.species in ("jellyfish","whale","dolphin","sea_turtle","seal") else (-.004 if organism.species in ("ray","crab","sea_star","sea_urchin","clam","octopus") else 0.0))
        # Individual swim thrust, responsiveness and turning authority.
        heading=math.atan2(organism.vy,organism.vx) if abs(organism.vx)+abs(organism.vy)>1e-8 else self.currents.phase
        thrust=speed*(.055+.11*agility)*dt
        organism.vx=(organism.vx+cx*dt+math.cos(heading)*thrust)*drag
        organism.vy=(organism.vy+(cy+buoyancy)*dt+math.sin(heading)*thrust)*drag
        organism.vx*=.985+.014*turn_rate
        organism.vy*=.985+.014*turn_rate
        organism.x+=organism.vx*dt/mass
        organism.y+=organism.vy*dt/mass
        # The dynamic waterline is a hard upper boundary: marine life stays submerged.
        lower=max(0.0,min(self.height-1.0,float(self.waterline)))
        if organism.y<lower:
            organism.y=lower; organism.vy=abs(organism.vy)*.25
        if organism.x<0 or organism.x>self.width-1:
            organism.x=max(0,min(self.width-1,organism.x)); organism.vx*=-.55
        if organism.y>self.height-1:
            organism.y=self.height-1; organism.vy*=-.35
    def step_particles(self,dt,t):
        for p in self.particles:
            cx,cy=self.currents.sample(p.x,p.y,t)
            p.vx=(p.vx+cx*dt)*.995; p.vy=(p.vy+cy*dt)*.995
            p.x=(p.x+p.vx*dt)%self.width; p.y=(p.y+p.vy*dt)%self.height
        self.grid.rebuild(self.particles)
        for p in self.particles:
            neighbours=self.grid.nearby(p.x,p.y,self.smoothing_radius)
            # Compact poly6-style kernel, normalized to a stable reference density.
            p.density=sum(max(0,1-(math.hypot(q.x-p.x,q.y-p.y)/self.smoothing_radius)**2)**3 for q in neighbours)
            p.density=max(.05,p.density)
            p.pressure=max(-.2,min(2.0,.35*(p.density-self.rest_density)))
        # Bounded pressure and viscosity forces; this advances the fluid field
        # without claiming a calibrated full-scale SPH solver.
        accelerations=[]
        for p in self.particles:
            ax=0.0; ay=0.0
            for q in self.grid.nearby(p.x,p.y,self.smoothing_radius):
                if q is p: continue
                dx=q.x-p.x; dy=q.y-p.y; r=math.hypot(dx,dy)
                if r<=1e-6 or r>=self.smoothing_radius: continue
                kernel=(self.smoothing_radius-r)/self.smoothing_radius
                pressure=(p.pressure+q.pressure)*.5
                ax+=pressure*kernel*dx/r*.0008
                ay+=pressure*kernel*dy/r*.0008
                ax+=(q.vx-p.vx)*kernel*.00015
                ay+=(q.vy-p.vy)*kernel*.00015
            accelerations.append((ax,ay))
        for p,(ax,ay) in zip(self.particles,accelerations):
            p.vx=max(-.25,min(.25,p.vx+ax*dt))
            p.vy=max(-.25,min(.25,p.vy+ay*dt))
    def state(self):
        return {"particles":[{"x":p.x,"y":p.y,"vx":p.vx,"vy":p.vy,"density":p.density,"pressure":p.pressure} for p in self.particles],
                "phase":self.currents.phase,"base_x":self.currents.base_x,"base_y":self.currents.base_y,"tilt_x":self.currents.tilt_x,"tilt_y":self.currents.tilt_y}
    def restore(self,data):
        self.particles=[FluidParticle(**p) for p in data.get("particles",[])][:20000]
        self.currents.phase=float(data.get("phase",self.currents.phase))
        self.currents.base_x=float(data.get("base_x",self.currents.base_x)); self.currents.base_y=float(data.get("base_y",self.currents.base_y))
        self.currents.tilt_x=max(-1.0,min(1.0,float(data.get("tilt_x",0.0)))); self.currents.tilt_y=max(-1.0,min(1.0,float(data.get("tilt_y",0.0))))
        self.grid.rebuild(self.particles)
    def snapshot(self):
        return {"particle_count":len(self.particles),"mean_density":sum(p.density for p in self.particles)/max(1,len(self.particles)),
                "mean_pressure":sum(p.pressure for p in self.particles)/max(1,len(self.particles)),
                "current_strength":math.hypot(*self.currents.sample(self.width/2,self.height/2,0)),
                "tilt":{"x":self.currents.tilt_x,"y":self.currents.tilt_y},
                "particles":[{"x":p.x,"y":p.y,"vx":p.vx,"vy":p.vy,"density":p.density} for p in self.particles]}
