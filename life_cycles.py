"""Species-aware maturation and breeding rules."""
from biodiversity import species_profile
MATURITY_AGE={"fish":8.0,"shark":35.0,"elasmobranch":24.0,"marine_mammal":45.0,"crustacean":3.0,"mollusc":4.0,"cnidarian":2.0,"reptile":25.0,"echinoderm":5.0,"macroalgae":1.0,"seagrass":1.0,"microorganism":0.2}
def maturity_age(species): return MATURITY_AGE.get(species_profile(species)["group"],8.0)
def life_stage(species,age):
    threshold=maturity_age(species)
    return "juvenile" if age<threshold*.25 else "subadult" if age<threshold else "adult"
def compatible(a,b): return a.id!=b.id and a.alive and b.alive and a.species==b.species
def reproduction_probability(o,dt): return min(.08,dt*.002*species_profile(o.species)["fecundity"]*(.5+o.genome.traits.get("fecundity",.5)))
