"""Marine species catalogue, habitat profiles and ecological classifications."""
SPECIES = {
 "reef_fish":{"group":"fish","trophic":"omnivore","habitats":["coral_reef","kelp_forest"],"temperature":[18,29],"oxygen_min":4.0,"speed":0.75,"size":0.25,"fecundity":0.8},
 "shark":{"group":"shark","trophic":"apex_predator","habitats":["open_ocean","coral_reef"],"temperature":[12,28],"oxygen_min":3.5,"speed":0.9,"size":0.95,"fecundity":0.2},
 "jellyfish":{"group":"cnidarian","trophic":"planktivore","habitats":["open_ocean"],"temperature":[8,30],"oxygen_min":2.0,"speed":0.25,"size":0.4,"fecundity":0.9},
 "ray":{"group":"elasmobranch","trophic":"benthic_predator","habitats":["sandy_seabed","coral_reef"],"temperature":[15,27],"oxygen_min":3.0,"speed":0.45,"size":0.8,"fecundity":0.3},
 "dolphin":{"group":"marine_mammal","trophic":"predator","habitats":["open_ocean","coral_reef"],"temperature":[8,30],"oxygen_min":5.0,"speed":0.95,"size":0.9,"fecundity":0.25},
 "whale":{"group":"marine_mammal","trophic":"filter_feeder","habitats":["open_ocean"],"temperature":[-1,25],"oxygen_min":2.5,"speed":0.5,"size":1.0,"fecundity":0.1},
 "crab":{"group":"crustacean","trophic":"detritivore","habitats":["rocky_seabed","coral_reef"],"temperature":[5,28],"oxygen_min":2.0,"speed":0.2,"size":0.2,"fecundity":0.7},
 "octopus":{"group":"mollusc","trophic":"predator","habitats":["rocky_seabed","coral_reef"],"temperature":[10,28],"oxygen_min":3.0,"speed":0.4,"size":0.45,"fecundity":0.6},
 "eel":{"group":"fish","trophic":"predator","habitats":["rocky_seabed","coral_reef"],"temperature":[8,28],"oxygen_min":2.5,"speed":0.4,"size":0.5,"fecundity":0.4},
 "sea_turtle":{"group":"reptile","trophic":"omnivore","habitats":["seagrass","open_ocean"],"temperature":[18,30],"oxygen_min":3.0,"speed":0.4,"size":0.8,"fecundity":0.4},
 "seal":{"group":"marine_mammal","trophic":"predator","habitats":["rocky_seabed","open_ocean"],"temperature":[-2,24],"oxygen_min":4.0,"speed":0.65,"size":0.75,"fecundity":0.3},
 "sea_snake":{"group":"reptile","trophic":"predator","habitats":["coral_reef","seagrass"],"temperature":[22,30],"oxygen_min":3.0,"speed":0.5,"size":0.35,"fecundity":0.35},
 "sea_star":{"group":"echinoderm","trophic":"benthic_omnivore","habitats":["rocky_seabed","coral_reef"],"temperature":[4,27],"oxygen_min":2.0,"speed":0.08,"size":0.2,"fecundity":0.7},
 "sea_urchin":{"group":"echinoderm","trophic":"herbivore","habitats":["kelp_forest","rocky_seabed"],"temperature":[4,26],"oxygen_min":2.0,"speed":0.05,"size":0.15,"fecundity":0.8},
 "shrimp":{"group":"crustacean","trophic":"detritivore","habitats":["seagrass","coral_reef"],"temperature":[10,29],"oxygen_min":2.0,"speed":0.35,"size":0.08,"fecundity":0.9},
 "clam":{"group":"mollusc","trophic":"filter_feeder","habitats":["sandy_seabed"],"temperature":[4,28],"oxygen_min":1.5,"speed":0.01,"size":0.2,"fecundity":0.9},
 "coral_polyp":{"group":"cnidarian","trophic":"symbiont","habitats":["coral_reef"],"temperature":[20,29],"oxygen_min":4.0,"speed":0.0,"size":0.15,"fecundity":0.6},
 "kelp":{"group":"macroalgae","trophic":"producer","habitats":["kelp_forest","rocky_seabed"],"temperature":[4,20],"oxygen_min":0.0,"speed":0.0,"size":0.8,"fecundity":0.5},
 "seagrass":{"group":"seagrass","trophic":"producer","habitats":["seagrass"],"temperature":[15,30],"oxygen_min":0.0,"speed":0.0,"size":0.7,"fecundity":0.5},
 "phytoplankton":{"group":"microorganism","trophic":"producer","habitats":["open_ocean"],"temperature":[0,30],"oxygen_min":0.0,"speed":0.0,"size":0.01,"fecundity":1.0},
 "zooplankton":{"group":"microorganism","trophic":"planktivore","habitats":["open_ocean"],"temperature":[0,30],"oxygen_min":0.5,"speed":0.1,"size":0.01,"fecundity":1.0},
 "bacteria":{"group":"microorganism","trophic":"decomposer","habitats":["all"],"temperature":[-2,40],"oxygen_min":0.0,"speed":0.0,"size":0.001,"fecundity":1.0}
}
HABITATS = {
 "coral_reef":{"temperature":25.0,"salinity":35.0,"oxygen":7.0,"ph":8.1,"turbidity":0.12,"primary_producers":["coral_polyp","seagrass","phytoplankton"]},
 "open_ocean":{"temperature":18.0,"salinity":35.0,"oxygen":7.5,"ph":8.1,"turbidity":0.03,"primary_producers":["phytoplankton"]},
 "deep_sea":{"temperature":3.0,"salinity":34.7,"oxygen":4.5,"ph":7.8,"turbidity":0.2,"primary_producers":["bacteria"]},
 "seagrass":{"temperature":23.0,"salinity":35.0,"oxygen":7.0,"ph":8.1,"turbidity":0.1,"primary_producers":["seagrass","phytoplankton"]},
 "kelp_forest":{"temperature":12.0,"salinity":34.5,"oxygen":8.0,"ph":8.1,"turbidity":0.08,"primary_producers":["kelp","phytoplankton"]},
 "rocky_seabed":{"temperature":14.0,"salinity":35.0,"oxygen":6.0,"ph":8.0,"turbidity":0.15,"primary_producers":["kelp","bacteria"]},
 "sandy_seabed":{"temperature":16.0,"salinity":35.0,"oxygen":5.5,"ph":8.0,"turbidity":0.18,"primary_producers":["phytoplankton"]},
 "hydrothermal_vent":{"temperature":8.0,"salinity":34.8,"oxygen":1.0,"ph":6.9,"turbidity":0.6,"primary_producers":["bacteria"]}
}
# Additional vertical niches and marine life.
SPECIES.update({
 "surface_fish":{"group":"fish","trophic":"planktivore","habitats":["open_ocean","coral_reef"],"temperature":[8,30],"oxygen_min":3,"speed":.8,"size":.18,"fecundity":.8,"zone":"surface"},
 "pelagic_fish":{"group":"fish","trophic":"planktivore","habitats":["open_ocean"],"temperature":[4,28],"oxygen_min":3,"speed":.8,"size":.4,"fecundity":.6,"zone":"open_water"},
 "deepwater_fish":{"group":"fish","trophic":"predator","habitats":["deep_sea"],"temperature":[-1,12],"oxygen_min":.5,"speed":.3,"size":.4,"fecundity":.3,"zone":"deep"},
 "sardine":{"group":"fish","trophic":"planktivore","habitats":["open_ocean"],"temperature":[8,28],"oxygen_min":3,"speed":.85,"size":.12,"fecundity":.9,"zone":"surface"},
 "mackerel":{"group":"fish","trophic":"predator","habitats":["open_ocean"],"temperature":[8,26],"oxygen_min":4,"speed":.9,"size":.38,"fecundity":.7,"zone":"open_water"},
 "anglerfish":{"group":"fish","trophic":"apex_predator","habitats":["deep_sea"],"temperature":[1,8],"oxygen_min":.5,"speed":.18,"size":.5,"fecundity":.2,"zone":"deep"},
 "lanternfish":{"group":"fish","trophic":"planktivore","habitats":["deep_sea"],"temperature":[2,16],"oxygen_min":1,"speed":.38,"size":.1,"fecundity":.9,"zone":"deep"},
 "orca":{"group":"marine_mammal","trophic":"apex_predator","habitats":["open_ocean"],"temperature":[-1,28],"oxygen_min":4,"speed":.95,"size":1,"fecundity":.12,"zone":"open_water"},
 "sea_lion":{"group":"marine_mammal","trophic":"predator","habitats":["rocky_seabed","open_ocean"],"temperature":[2,26],"oxygen_min":4,"speed":.8,"size":.72,"fecundity":.3,"zone":"surface"},
 "humpback_whale":{"group":"marine_mammal","trophic":"filter_feeder","habitats":["open_ocean"],"temperature":[-1,28],"oxygen_min":2,"speed":.45,"size":1,"fecundity":.1,"zone":"open_water"},
 "manatee":{"group":"marine_mammal","trophic":"herbivore","habitats":["seagrass"],"temperature":[20,32],"oxygen_min":2,"speed":.2,"size":.8,"fecundity":.15,"zone":"surface"},
 "lobster":{"group":"crustacean","trophic":"scavenger","habitats":["rocky_seabed","coral_reef"],"temperature":[4,24],"oxygen_min":2,"speed":.18,"size":.36,"fecundity":.65,"zone":"benthic"},
 "crayfish":{"group":"crustacean","trophic":"detritivore","habitats":["sandy_seabed","rocky_seabed"],"temperature":[8,28],"oxygen_min":2,"speed":.22,"size":.2,"fecundity":.8,"zone":"benthic"},
 "hermit_crab":{"group":"crustacean","trophic":"detritivore","habitats":["rocky_seabed","sandy_seabed"],"temperature":[8,28],"oxygen_min":1.5,"speed":.12,"size":.16,"fecundity":.7,"zone":"benthic"},
 "sargassum":{"group":"macroalgae","trophic":"producer","habitats":["open_ocean","coral_reef"],"temperature":[15,30],"oxygen_min":0,"speed":0,"size":.6,"fecundity":.5,"zone":"surface"},
 "sea_lettuce":{"group":"macroalgae","trophic":"producer","habitats":["rocky_seabed","coral_reef"],"temperature":[8,28],"oxygen_min":0,"speed":0,"size":.4,"fecundity":.6,"zone":"benthic"},
 "mangrove":{"group":"coastal_plant","trophic":"producer","habitats":["seagrass","sandy_seabed"],"temperature":[18,32],"oxygen_min":0,"speed":0,"size":.9,"fecundity":.3,"zone":"shore"}
})
def species_profile(name):
    return SPECIES.get(name,{"group":"unknown","trophic":"omnivore","habitats":["open_ocean"],"temperature":[0,35],"oxygen_min":1.0,"speed":.4,"size":.4,"fecundity":.4})

# Additional coastal, pelagic and deep-ocean ecoregions.
HABITATS.update({
 "mangrove_forest":{"temperature":26.0,"salinity":28.0,"oxygen":6.0,"ph":7.9,"turbidity":0.35,"primary_producers":["mangrove","seagrass","phytoplankton"]},
 "estuary":{"temperature":20.0,"salinity":18.0,"oxygen":6.5,"ph":7.8,"turbidity":0.3,"primary_producers":["seagrass","phytoplankton"]},
 "polar_shelf":{"temperature":-1.5,"salinity":34.0,"oxygen":8.5,"ph":8.0,"turbidity":0.08,"primary_producers":["phytoplankton"]},
 "seamount":{"temperature":5.0,"salinity":34.8,"oxygen":4.8,"ph":7.9,"turbidity":0.16,"primary_producers":["bacteria","phytoplankton"]},
 "abyssal_plain":{"temperature":2.0,"salinity":34.7,"oxygen":4.0,"ph":7.7,"turbidity":0.22,"primary_producers":["bacteria"]}
})
SPECIES.update({
 "mangrove":{"group":"coastal_plant","trophic":"producer","habitats":["mangrove_forest","estuary"],"temperature":[18,32],"oxygen_min":0,"speed":0,"size":.9,"fecundity":.3,"zone":"shore"},
 "eelgrass":{"group":"seagrass","trophic":"producer","habitats":["seagrass","estuary"],"temperature":[8,30],"oxygen_min":0,"speed":0,"size":.65,"fecundity":.55,"zone":"benthic"},
 "sea_cucumber":{"group":"echinoderm","trophic":"detritivore","habitats":["abyssal_plain","deep_sea","sandy_seabed"],"temperature":[-1,12],"oxygen_min":.5,"speed":.04,"size":.3,"fecundity":.6,"zone":"benthic"},
 "giant_isopod":{"group":"crustacean","trophic":"scavenger","habitats":["abyssal_plain","deep_sea"],"temperature":[-1,8],"oxygen_min":.5,"speed":.12,"size":.28,"fecundity":.45,"zone":"benthic"},
 "icefish":{"group":"fish","trophic":"planktivore","habitats":["polar_shelf","open_ocean"],"temperature":[-2,5],"oxygen_min":5,"speed":.45,"size":.42,"fecundity":.4,"zone":"open_water"},
 "coelacanth":{"group":"fish","trophic":"predator","habitats":["seamount","deep_sea"],"temperature":[8,20],"oxygen_min":2,"speed":.28,"size":.62,"fecundity":.12,"zone":"deep"},
 "manta_ray":{"group":"elasmobranch","trophic":"filter_feeder","habitats":["coral_reef","open_ocean","seamount"],"temperature":[18,30],"oxygen_min":3,"speed":.65,"size":.95,"fecundity":.12,"zone":"open_water"},
 "seahorse":{"group":"fish","trophic":"planktivore","habitats":["seagrass","mangrove_forest","coral_reef"],"temperature":[18,29],"oxygen_min":3,"speed":.12,"size":.18,"fecundity":.5,"zone":"vegetation"},
 "nudibranch":{"group":"mollusc","trophic":"herbivore","habitats":["coral_reef","rocky_seabed"],"temperature":[8,28],"oxygen_min":2,"speed":.03,"size":.08,"fecundity":.7,"zone":"benthic"}
})
