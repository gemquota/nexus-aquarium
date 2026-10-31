"""Species-aware maturation and breeding rules."""
from biodiversity import species_profile
MATURITY_AGE={"fish":8.0,"shark":35.0,"elasmobranch":24.0,"marine_mammal":45.0,"crustacean":3.0,"mollusc":4.0,"cnidarian":2.0,"reptile":25.0,"echinoderm":5.0,"macroalgae":1.0,"seagrass":1.0,"microorganism":0.2}
def maturity_age(species): return life_history_profile(species)["maturity"] if "life_history_profile" in globals() else MATURITY_AGE.get(species_profile(species)["group"],8.0)
def life_stage(species,age):
    profile=life_history_profile(species)
    return "juvenile" if age<profile["juvenile"] else "subadult" if age<profile["maturity"] else "adult"
def compatible(a,b): return a.id!=b.id and a.alive and b.alive and a.species==b.species
def reproduction_probability(o,dt): return min(.08,dt*.002*species_profile(o.species)["fecundity"]*(.5+o.genome.traits.get("fecundity",.5)))

ASEXUAL_SPECIES={"coral_polyp","kelp","seagrass","phytoplankton","zooplankton","bacteria"}
def reproductive_mode(species):
    return "asexual_or_fragmentation" if species in ASEXUAL_SPECIES else "sexual"
def offspring_position(parent,mate=None):
    if mate is None: return parent.x,parent.y
    return (parent.x+mate.x)/2,(parent.y+mate.y)/2

# Coarse life-history templates. Durations use simulation-time units, not real years.
LIFE_HISTORY={
 "fish":{"juvenile":2.0,"subadult":6.0,"maturity":8.0,"maximum_age":900.0,"strategy":"broadcast_spawning"},
 "shark":{"juvenile":12.0,"subadult":23.0,"maturity":35.0,"maximum_age":9000.0,"strategy":"internal_fertilisation"},
 "elasmobranch":{"juvenile":8.0,"subadult":16.0,"maturity":24.0,"maximum_age":6000.0,"strategy":"internal_fertilisation"},
 "marine_mammal":{"juvenile":15.0,"subadult":30.0,"maturity":45.0,"maximum_age":12000.0,"strategy":"live_birth_and_care"},
 "crustacean":{"juvenile":.8,"subadult":2.2,"maturity":3.0,"maximum_age":300.0,"strategy":"larval_release"},
 "mollusc":{"juvenile":1.0,"subadult":3.0,"maturity":4.0,"maximum_age":1200.0,"strategy":"spawning_or_brooding"},
 "cnidarian":{"juvenile":.5,"subadult":1.5,"maturity":2.0,"maximum_age":3000.0,"strategy":"budding_and_spawning"},
 "reptile":{"juvenile":8.0,"subadult":17.0,"maturity":25.0,"maximum_age":10000.0,"strategy":"egg_laying"},
 "echinoderm":{"juvenile":1.0,"subadult":4.0,"maturity":5.0,"maximum_age":1500.0,"strategy":"broadcast_spawning"},
 "macroalgae":{"juvenile":.2,"subadult":.8,"maturity":1.0,"maximum_age":500.0,"strategy":"spores_and_fragmentation"},
 "seagrass":{"juvenile":.2,"subadult":.8,"maturity":1.0,"maximum_age":800.0,"strategy":"clonal_growth_and_seeds"},
 "microorganism":{"juvenile":.05,"subadult":.15,"maturity":.2,"maximum_age":30.0,"strategy":"binary_fission_or_spores"}
}
def life_history_profile(species):
    group=species_profile(species)["group"]
    base=LIFE_HISTORY.get(group,LIFE_HISTORY["fish"])
    return dict(base)
def age_specific_survival(species,age,health,resistance=.5):
    profile=life_history_profile(species)
    senescence=max(0.0,(age-profile["maximum_age"]*.75)/(profile["maximum_age"]*.25))
    condition=max(0.0,min(1.0,health))
    return max(0.0,min(1.0,condition*(1.0-min(.8,senescence))*(.8+.2*resistance)))
