#!/usr/bin/env python3
"""Import sprite ZIPs safely. Public mode is restricted to verified CC0 packs.

Examples:
  python3 tools/import_sprite_packs.py asset_staging/kenney_fish-pack_2.0.zip --pack kenney-fish --public
  python3 tools/import_sprite_packs.py asset_staging/fathom.zip --pack fathom-underwater

Non-CC0 packs stay in local_assets and are never published to the public repository.
"""
from __future__ import annotations
import argparse, json, shutil, stat, zipfile
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/"assets/sprites/sources.json"
RUNTIME=ROOT/"assets/sprites/runtime-manifest.json"
IMAGE_SUFFIXES={".png",".webp",".gif",".jpg",".jpeg"}
META_SUFFIXES={".json",".txt",".md",".gpl",".ase",".aseprite",".csv",".xml"}
MAX_FILES=12000
MAX_MEMBER_BYTES=80*1024*1024
MAX_TOTAL_BYTES=1024*1024*1024
ALIASES={
 "shark":["shark"],"ray":["ray","manta"],"jellyfish":["jelly","medusa"],
 "turtle":["turtle"],"octopus":["octopus"],"squid":["squid"],"crab":["crab"],
 "shrimp":["shrimp","prawn"],"lobster":["lobster"],"seahorse":["seahorse"],
 "eel":["eel","moray"],"whale":["whale"],"dolphin":["dolphin"],
 "seagull":["seagull","gull"],"pelican":["pelican"],"albatross":["albatross"],
 "tern":["tern"],"cormorant":["cormorant"],"macaw":["macaw"],"parrot":["parrot"],
 "kelp":["kelp"],"seagrass":["seagrass","eelgrass"],"seaweed":["seaweed","algae"],
 "mangrove":["mangrove"],"coral":["coral"],"island":["island","shore","coast"]
}
def safe_member(info):
 name=info.filename.replace("\\","/")
 path=PurePosixPath(name);mode=info.external_attr>>16
 if path.is_absolute() or any(p in ("",".","..") for p in path.parts) or stat.S_ISLNK(mode) or info.is_dir():return None
 return path
def classify(path):
 stem=path.stem.lower().replace("-","_").replace(" ","_")
 for species,terms in ALIASES.items():
  if any(term in stem for term in terms):
   kind="bird" if species in {"seagull","pelican","albatross","tern","cormorant","macaw","parrot"} else "plant" if species in {"kelp","seagrass","seaweed","mangrove","coral"} else "island" if species=="island" else "creature"
   return kind,species
 if any(t in stem for t in ("bird","avian")):return "bird","generic"
 if any(t in stem for t in ("fish","animal","creature","sea_life","marine")):return "creature","generic"
 if any(t in stem for t in ("plant","flora","vegetation")):return "plant","generic"
 if any(t in stem for t in ("islet","island","shoreline","beach")):return "island","generic"
 return "prop",""
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("archive",type=Path);p.add_argument("--pack",required=True);p.add_argument("--public",action="store_true")
 a=p.parse_args()
 archive=a.archive if a.archive.is_absolute() else ROOT/a.archive
 if not archive.is_file() or archive.suffix.lower()!=".zip":p.error("archive must be an existing ZIP")
 sources=json.loads(SOURCES.read_text(encoding="utf-8"))
 pack=next((x for x in sources["packs"] if x["id"]==a.pack),None)
 if not pack:p.error("unknown pack ID in sources.json")
 if pack.get("projection")!="side_view":p.error("only side-view packs may be imported")
 if a.public and "CC0" not in pack.get("license","").upper():p.error("--public is allowed only for a source explicitly marked CC0")
 target=(ROOT/"assets/sprites/imported"/a.pack) if a.public else (ROOT/"local_assets/sprites"/a.pack)
 target.mkdir(parents=True,exist_ok=True);files=[];assets=[];total=0
 with zipfile.ZipFile(archive) as zf:
  infos=zf.infolist()
  if len(infos)>MAX_FILES:raise SystemExit("archive has too many entries")
  for info in infos:
   rel=safe_member(info)
   if rel is None:continue
   suffix=rel.suffix.lower()
   if suffix not in IMAGE_SUFFIXES|META_SUFFIXES:continue
   if info.file_size>MAX_MEMBER_BYTES:raise SystemExit("oversized archive member: "+info.filename)
   total+=info.file_size
   if total>MAX_TOTAL_BYTES:raise SystemExit("archive expands beyond 1 GiB")
   dest=target.joinpath(*rel.parts);dest.parent.mkdir(parents=True,exist_ok=True)
   with zf.open(info) as src,dest.open("wb") as out:shutil.copyfileobj(src,out,1024*1024)
   files.append({"path":dest.relative_to(ROOT).as_posix(),"source_path":rel.as_posix(),"bytes":info.file_size})
   if suffix in IMAGE_SUFFIXES:
    kind,species=classify(rel)
    if kind!="prop" and not any(token in rel.stem.lower() for token in ("sheet","atlas","spritesheet")):
     assets.append({"kind":kind,"species":species,"src":"/"+dest.relative_to(ROOT).as_posix(),"source_pack":a.pack,"filename":rel.name,"frames":1,"fps":6})
 manifest={"schema_version":1,"pack":a.pack,"projection":"side_view","public":a.public,"files":files,"image_count":sum(x["path"].lower().endswith(tuple(IMAGE_SUFFIXES)) for x in files),"assets":assets}
 (target/"import-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
 if a.public:
  current=json.loads(RUNTIME.read_text(encoding="utf-8")) if RUNTIME.exists() else {"schema_version":1,"projection":"side_view","assets":[]}
  current["assets"]=[x for x in current.get("assets",[]) if x.get("source_pack")!=a.pack]+assets
  RUNTIME.write_text(json.dumps(current,indent=2)+"\n",encoding="utf-8")
 print(f"Imported {len(files)} files; {len(assets)} renderable sprite candidates.")
 print("Destination:",target)
 print("Public CC0 import is ready to commit." if a.public else "Private/licensed import remains local and is not published.")
if __name__=="__main__":main()
