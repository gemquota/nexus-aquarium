"""Quantitative marine genetics: locus-aware recombination and bounded mutation."""
from __future__ import annotations
import random

LOCI={
 "speed":{"dominance":0.5,"mutation_sd":0.08},
 "size":{"dominance":0.5,"mutation_sd":0.06},
 "camouflage":{"dominance":0.5,"mutation_sd":0.07},
 "metabolism":{"dominance":0.5,"mutation_sd":0.05},
 "fecundity":{"dominance":0.5,"mutation_sd":0.06},
 "sensory":{"dominance":0.5,"mutation_sd":0.08},
 "resistance":{"dominance":0.5,"mutation_sd":0.07},
 "agility":{"dominance":0.5,"mutation_sd":0.08},
 "turn_rate":{"dominance":0.5,"mutation_sd":0.06},
 "tracking":{"dominance":0.5,"mutation_sd":0.08},
 "transparency":{"dominance":0.5,"mutation_sd":0.05},
 "hue":{"dominance":0.5,"mutation_sd":0.10},
 "pattern":{"dominance":0.5,"mutation_sd":0.08},
 "fin_size":{"dominance":0.5,"mutation_sd":0.07}
}
def bounded(value): return max(0.0,min(1.0,float(value)))
def recombine(parent_a,parent_b,rng):
    child={}
    for locus,spec in LOCI.items():
        a=bounded(parent_a.get(locus,.5)); b=bounded(parent_b.get(locus,.5))
        # Recombination switches parental contribution at each quantitative locus.
        inherited=a if rng.random()<.5 else b
        if rng.random()<.025:
            inherited+=rng.gauss(0,spec["mutation_sd"])
        child[locus]=bounded(inherited)
    return child
def mutation_load(parent,child):
    return sum(abs(bounded(child.get(k,.5))-bounded(parent.get(k,.5))) for k in LOCI)/len(LOCI)
def population_diversity(organisms):
    living=[o for o in organisms if getattr(o,"alive",False)]
    if not living:return {"trait_means":{},"trait_ranges":{}}
    means={}; ranges={}
    for locus in LOCI:
        values=[bounded(o.genome.traits.get(locus,.5)) for o in living]
        means[locus]=sum(values)/len(values); ranges[locus]=max(values)-min(values)
    return {"trait_means":means,"trait_ranges":ranges}
def selection_pressure(organism,stress,food_availability):
    resistance=bounded(organism.genome.traits.get("resistance",.5))
    metabolism=bounded(organism.genome.traits.get("metabolism",.5))
    return resistance*max(0.0,min(1.0,stress)) + (1-metabolism)*(1-max(0.0,min(1.0,food_availability)))
