/* NEXUS side-view sprite runtime. Uses every clean imported variant,
 * preserves source aspect ratios, and animates each individual independently. */
(()=>{'use strict';
const MANIFEST_URL=new URL('./runtime-manifest.json',document.currentScript.src).href;
const images=new Map(),entries=[];
const plantSpecies=new Set(['kelp','seagrass','sea_lettuce','mangrove','sargassum','seaweed','macroalgae','eelgrass','coral','coral_polyp','marsh_grass','saltmarsh']);
const speciesAliases={sea_turtle:'turtle',coral_polyp:'coral',kelp:'seaweed',seagrass:'seaweed',sea_lettuce:'seaweed',mangrove:'seaweed',sargassum:'seaweed',eelgrass:'seaweed',gull:'seagull'};
const genericFishSpecies=new Set(['reef_fish','surface_fish','pelagic_fish','deepwater_fish','sardine','mackerel','icefish','coelacanth','lanternfish','anglerfish','piranha','clownfish','tang','angelfish','butterflyfish','wrasse','goby','damselfish','parrotfish','triggerfish','surgeonfish','anchovy','herring','sprat','smelt','fry']);
const normalise=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
const clean=e=>!/(?:_outline|_skeleton)(?:\.[^.]+)?$/i.test(e.filename||e.src||'');
function loadEntry(entry){
 if(!entry?.src)return null;
 const key=new URL(String(entry.src).replace(/^\/+/,''),new URL('../../',MANIFEST_URL)).href;
 if(images.has(key))return images.get(key);
 const image=new Image();image.decoding='async';image.loading='eager';
 const state={image,loaded:false,failed:false};
 image.onload=()=>{state.loaded=true};image.onerror=()=>{state.failed=true};
 image.src=key;images.set(key,state);return state;
}
function variants(kind,name){
 return entries.filter(e=>e.kind===kind&&clean(e)&&e.species===name);
}
function hash(value){let h=2166136261;for(const c of String(value)){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}return h>>>0}
function find(kind,species,seed=0){
 const name=speciesAliases[normalise(species)]||normalise(species);
 const exact=variants(kind,name);const generic=kind==='creature'&&genericFishSpecies.has(normalise(species))?entries.filter(e=>e.kind===kind&&clean(e)&&e.species==='generic'):[];const pool=exact.length?exact:generic;
 return pool.length?pool[hash(seed)%pool.length]:null;
}
function frame(entry,state,time){
 const fw=Math.max(1,Number(entry.frame_width)||state.image.naturalWidth);
 const fh=Math.max(1,Number(entry.frame_height)||state.image.naturalHeight);
 const cols=Math.max(1,Math.floor(state.image.naturalWidth/fw));
 const rows=Math.max(1,Math.floor(state.image.naturalHeight/fh));
 const count=Math.max(1,Number(entry.frames)||cols*rows);
 const index=count>1?Math.floor(time*Math.max(.1,Number(entry.fps)||6))%count:0;
 return {sx:(index%cols)*fw,sy:Math.floor(index/cols)*fh,sw:Math.min(fw,state.image.naturalWidth),sh:Math.min(fh,state.image.naturalHeight)};
}
function drawImage(ctx,entry,x,y,boundW,boundH,time,anchorX=.5,anchorY=.5,flip=false,angle=0,breath=0){
 const state=loadEntry(entry);if(!state?.loaded||state.failed)return false;
 const f=frame(entry,state,time),aspect=f.sw/f.sh;
 let w=boundW,h=boundH;
 if(w/h>aspect)w=h*aspect;else h=w/aspect;
 const bob=breath?Math.sin(time*2.8+hash(entry.filename||entry.src)%31)*breath:0;
 ctx.save();ctx.translate(x,y+bob);ctx.rotate(angle);ctx.scale(flip?-1:1,1);
 ctx.imageSmoothingEnabled=false;
 ctx.drawImage(state.image,f.sx,f.sy,f.sw,f.sh,-w*anchorX,-h*anchorY,w,h);
 ctx.restore();return true;
}
function drawOrganism(ctx,o,x,y,opts={}){
 const species=normalise(o.species),kind=plantSpecies.has(species)?'plant':'creature';
 const entry=find(kind,species,o.id);if(!entry)return false;
 const time=Number(opts.time)||0,size=.82+Math.max(0,Math.min(1,Number(o.genome?.size??.5)))*.36;
 if(kind==='plant'){
  const h=(Number(entry.render_height)||(species==='mangrove'?6:species==='kelp'?3.5:2.4))*size;
  const w=(Number(entry.render_width)||Math.max(1.2,h*.55))*size;
  const baseY=Number.isFinite(opts.plantBaseY)?opts.plantBaseY:y;
  const sway=Math.sin(time*1.25+(Number(o.id)||0)*.71)*.045;
  return drawImage(ctx,entry,x,baseY,w,h,time,Number(entry.anchor_x??.5),1,false,sway,0);
 }
 const large=['whale','shark','dolphin','ray','orca','humpback_whale'].includes(species);
 const tiny=['reef_fish','surface_fish','pelagic_fish','deepwater_fish','sardine','mackerel','lanternfish','anglerfish'].includes(species);
 const bw=(Number(entry.render_width)||(large?6.2:tiny?2.8:3.8))*size;
 const bh=(Number(entry.render_height)||(large?3.4:tiny?2.0:2.8))*size;
 const vx=Number(o.vx)||0,vy=Number(o.vy)||0;
 const heading=Math.atan2(vy,Math.abs(vx)||.0001);
 const swim=Math.sin(time*5.2+(Number(o.id)||0)*.73);
 const turn=Math.max(-.16,Math.min(.16,heading*.22));
 return drawImage(ctx,entry,x,y,bw,bh,time,Number(entry.anchor_x??.5),Number(entry.anchor_y??.5),vx<0,turn+swim*.025,Math.max(.15,bh*.055));
}
function drawBird(ctx,bird,x,y,opts={}){
 const entry=find('bird',bird.species,opts.index)||find('bird','generic',opts.index);if(!entry)return false;
 const w=Number(entry.render_width)||12,h=Number(entry.render_height)||7;
 const flap=bird.state==='gliding'?0:Math.sin((Number(opts.time)||0)*9+(Number(opts.index)||0))*.035;
 return drawImage(ctx,entry,x,y,w,h,Number(opts.time)||0,.5,.5,Number(bird.vx)<0,flap,0);
}
function drawProp(ctx,species,x,y,width,height,time=0,seed=0){
 const entry=find('prop',species,seed);if(!entry)return false;
 return drawImage(ctx,entry,x,y,width,height,time,.5,1,false,0,0);
}
function drawPlant(ctx,x,baseY,width,height,time=0,seed=0){
 const entry=find('plant','seaweed',seed);if(!entry)return false;
 const sway=Math.sin(time*1.25+seed*.71)*.045;
 return drawImage(ctx,entry,x,baseY,width,height,time,.5,1,false,sway,0);
}
function drawIsland(ctx,island,x,y,radius){
 const entry=find('island',island.kind||island.species||'generic',island.id||island.x||0);if(!entry)return false;
 const w=Number(entry.render_width)||Math.max(12,radius*3.6),h=Number(entry.render_height)||Math.max(5,radius*.9);
 return drawImage(ctx,entry,x,y,w,h,0,.5,.8,false,0,0);
}
async function loadManifest(){
 try{
  const response=await fetch(MANIFEST_URL,{cache:'no-cache'});if(!response.ok)throw new Error('manifest HTTP '+response.status);
  const manifest=await response.json();
  for(const entry of manifest.assets||[]){
   if(!entry.src||!['creature','plant','bird','island','background','prop'].includes(entry.kind)||!clean(entry))continue;
   entries.push({...entry,species:normalise(entry.species)});loadEntry(entry);
  }
  window.dispatchEvent(new CustomEvent('nexus:sprites-ready',{detail:{count:entries.length}}));
 }catch(error){console.info('Nexus sprite manifest unavailable; using procedural fallback.',error.message)}
}
window.NexusSprites={drawOrganism,drawBird,drawIsland,drawProp,drawPlant,get status(){return {assets:entries.length,loaded:[...images.values()].filter(v=>v.loaded).length,failed:[...images.values()].filter(v=>v.failed).length}}};
loadManifest();
})();