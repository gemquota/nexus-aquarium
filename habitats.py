"""Spatially connected habitat mosaic for multi-biome worlds."""
from __future__ import annotations
import random
from biodiversity import HABITATS

class HabitatMap:
    def __init__(self,width=80,height=24,seed=0,cell_size=16,base_habitat="coral_reef"):
        self.width=max(1,int(width)); self.height=max(1,int(height))
        self.cell_size=max(2,int(cell_size)); self.seed=int(seed)
        if base_habitat not in HABITATS: raise ValueError("unknown base habitat")
        self.base_habitat=base_habitat
        self.tiles={}
        cols=(self.width+self.cell_size-1)//self.cell_size
        rows=(self.height+self.cell_size-1)//self.cell_size
        rng=random.Random(self.seed)
        alternatives=[name for name in sorted(HABITATS) if name!=base_habitat]
        # A small number of broad, overlapping patches creates contiguous ecotones
        # rather than the old checkerboard of isolated one-cell habitats.
        patch_count=max(1,min(18,round(cols*rows/95)))
        patches=[]
        for _ in range(patch_count):
            name=rng.choice(alternatives)
            cx=rng.uniform(0,max(0,cols-1)); cy=rng.uniform(0,max(0,rows-1))
            rx=rng.uniform(max(1,cols*.035),max(1.5,cols*.13))
            ry=rng.uniform(max(1,rows*.08),max(1.5,rows*.24))
            patches.append((name,cx,cy,rx,ry,rng.uniform(.75,1.3)))
        for y in range(rows):
            for x in range(cols):
                candidates=[]
                for name,cx,cy,rx,ry,weight in patches:
                    distance=(((x-cx)/rx)**2+((y-cy)/ry)**2)/weight
                    if distance<1.0:candidates.append((distance,name))
                self.tiles[(x,y)]=min(candidates)[1] if candidates else base_habitat
    def set_base(self,habitat):
        if habitat not in HABITATS: raise ValueError("unknown habitat")
        self.base_habitat=habitat
        self.tiles={key:habitat for key in self.tiles}
    def at(self,x,y):
        key=(max(0,min((self.width-1)//self.cell_size,int(x)//self.cell_size)),
             max(0,min((self.height-1)//self.cell_size,int(y)//self.cell_size)))
        return self.tiles.get(key,self.base_habitat)
    def neighbours(self,x,y):
        key=(int(x)//self.cell_size,int(y)//self.cell_size)
        return [self.tiles[p] for p in ((key[0]-1,key[1]),(key[0]+1,key[1]),(key[0],key[1]-1),(key[0],key[1]+1)) if p in self.tiles]
    def connected(self,a,b):
        return any(name==a and any(self.tiles.get(q)==b for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))) for p,name in self.tiles.items())
    def snapshot(self):
        return {"cell_size":self.cell_size,"tiles":[{"x":x,"y":y,"habitat":name} for (x,y),name in sorted(self.tiles.items())],
                "habitat_count":len(set(self.tiles.values())),"base_habitat":self.base_habitat}
