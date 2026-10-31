"""Spatially connected habitat mosaic for multi-biome worlds."""
from __future__ import annotations
from biodiversity import HABITATS

class HabitatMap:
    def __init__(self,width=80,height=24,seed=0,cell_size=16,base_habitat="coral_reef"):
        self.width=max(1,int(width)); self.height=max(1,int(height))
        self.cell_size=max(2,int(cell_size)); self.seed=int(seed)
        if base_habitat not in HABITATS: raise ValueError("unknown base habitat")
        self.tiles={}
        cols=(self.width+self.cell_size-1)//self.cell_size
        rows=(self.height+self.cell_size-1)//self.cell_size
        names=sorted(HABITATS)
        for y in range(rows):
            for x in range(cols):
                index=(x*7+y*11+(self.seed%len(names)))%len(names)
                self.tiles[(x,y)]=base_habitat if (x+y*cols+self.seed)%5 else names[index]
    def set_base(self,habitat):
        if habitat not in HABITATS: raise ValueError("unknown habitat")
        self.tiles={key:habitat for key in self.tiles}
    def at(self,x,y):
        key=(max(0,min((self.width-1)//self.cell_size,int(x)//self.cell_size)),
             max(0,min((self.height-1)//self.cell_size,int(y)//self.cell_size)))
        return self.tiles.get(key,"coral_reef")
    def neighbours(self,x,y):
        key=(int(x)//self.cell_size,int(y)//self.cell_size)
        return [self.tiles[p] for p in ((key[0]-1,key[1]),(key[0]+1,key[1]),(key[0],key[1]-1),(key[0],key[1]+1)) if p in self.tiles]
    def connected(self,a,b):
        return any(name==a and any(self.tiles.get(q)==b for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))) for p,name in self.tiles.items())
    def snapshot(self):
        return {"cell_size":self.cell_size,"tiles":[{"x":x,"y":y,"habitat":name} for (x,y),name in sorted(self.tiles.items())],
                "habitat_count":len(set(self.tiles.values()))}
