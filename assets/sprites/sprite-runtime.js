/* Nexus Aquarium side-view sprite renderer.
 * Loads only explicitly imported assets from runtime-manifest.json.
 * Missing/unavailable sprites fall through to the existing procedural renderer.
 */
(()=>{'use strict';
const MANIFEST_URL=new URL('./runtime-manifest.json',document.currentScript.src).href;
const images=new Map(),entries=[];
const plantSpecies=new Set(['kelp','seagrass','sea_lettuce','mangrove','sargassum','seaweed','macroalgae','eelgrass','coral','coral_polyp']);
const speciesAliases={sea_turtle:'turtle',coral_polyp:'coral',reef_fish:'generic',surface_fish:'generic',pelagic_fish:'generic',deepwater_fish:'generic',gull:'seagull'};
const birdSpecies=new Set(['seagull','gull','pelican','albatross','tern','cormorant','frigatebird','macaw','parrot']);
const normalise=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
function loadEntry(entry){
  if(!entry||!entry.src)return null;
  const key=entry.src;
  if(images.has(key))return images.get(key);
  const image=new Image();image.decoding='async';
  const state={image,loaded:false,failed:false};
  image.onload=()=>{state.loaded=true};
  image.onerror=()=>{state.failed=true};
  image.src=entry.src;images.set(key,state);return state;
}
function find(kind,species,seed=0){
  const name=speciesAliases[normalise(species)]||normalise(species);
  const exact=entries.find(e=>e.kind===kind&&e.species===name);
  if(exact)return exact;
  const generic=entries.filter(e=>e.kind===kind&&(e.species==='generic'||e.species===''));
  return generic.length?generic[Math.abs(Number(seed)||0)%generic.length]:null;
}
function frame(entry,state,time){
  const fw=Number(entry.frame_width)||state.image.naturalWidth;
  const fh=Number(entry.frame_height)||state.image.naturalHeight;
  const count=Math.max(1,Number(entry.frames)||Math.floor(state.image.naturalWidth/fw));
  if(count<=1||fw>=state.image.naturalWidth)return {sx:0,sy:0,sw:state.image.naturalWidth,sh:state.image.naturalHeight};
  const fps=Math.max(.1,Number(entry.fps)||6),index=Math.floor(time*fps)%count;
  return {sx:index*fw,sy:0,sw:fw,sh:fh};
}
function drawImage(ctx,entry,x,y,w,h,time,anchorX=.5,anchorY=.5,flip=false,angle=0){
  const state=loadEntry(entry);if(!state||!state.loaded||state.failed)return false;
  const f=frame(entry,state,time);ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.scale(flip?-1:1,1);
  ctx.imageSmoothingEnabled=false;
  ctx.drawImage(state.image,f.sx,f.sy,f.sw,f.sh,-w*anchorX,-h*anchorY,w,h);
  ctx.restore();return true;
}
function drawOrganism(ctx,o,x,y,opts={}){
  const species=normalise(o.species),kind=plantSpecies.has(species)?'plant':'creature',entry=find(kind,species);
  if(!entry)return false;
  const time=Number(opts.time)||0,size=.82+Math.max(0,Math.min(1,Number(o.genome?.size??.5)))*.36;
  if(kind==='plant'){
    const h=(Number(entry.render_height)||(species==='mangrove'?6:species==='kelp'?3.5:2.4))*size,w=(Number(entry.render_width)||Math.max(1.2,h*.55))*size;
    const baseY=Number.isFinite(opts.plantBaseY)?opts.plantBaseY:y;
    const sway=Math.sin(time*1.25+(Number(o.id)||0)*.71)*.045;
    return drawImage(ctx,entry,x,baseY,w,h,time,Number(entry.anchor_x??.5),1,false,sway);
  }
  const large=['whale','shark','dolphin','ray'].includes(species),tiny=['reef_fish','surface_fish','pelagic_fish','deepwater_fish','sardine','mackerel','lanternfish'].includes(species);
  const w=(Number(entry.render_width)||(large?6.2:tiny?1.8:3.2))*size,h=(Number(entry.render_height)||(large?3.4:tiny?1.2:2.0))*size;
  const angle=Math.atan2(Number(o.vy)||0,Number(o.vx)||.01);
  return drawImage(ctx,entry,x,y,w,h,time,Number(entry.anchor_x??.5),Number(entry.anchor_y??.5),Number(o.vx)<0,angle);
}
function drawBird(ctx,bird,x,y,opts={}){
  const entry=find('bird',bird.species,opts.index)||find('bird','generic',opts.index);if(!entry)return false;
  const w=Number(entry.render_width)||12,h=Number(entry.render_height)||7;
  const flap=bird.state==='gliding'?0:Math.sin((Number(opts.time)||0)*9+(Number(opts.index)||0))*0.035;
  return drawImage(ctx,entry,x,y,w,h,Number(opts.time)||0,.5,.5,Number(bird.vx)<0,flap);
}
function drawIsland(ctx,island,x,y,radius){
  const entry=find('island',island.kind||island.species||'generic',island.id||island.x||0);if(!entry)return false;
  const w=Number(entry.render_width)||Math.max(12,radius*3.6),h=Number(entry.render_height)||Math.max(5,radius*.9);
  return drawImage(ctx,entry,x,y,w,h,0,.5,.8,false,0);
}
async function loadManifest(){
  try{
    const response=await fetch(MANIFEST_URL,{cache:'no-cache'});
    if(!response.ok)throw new Error('manifest HTTP '+response.status);
    const manifest=await response.json();
    for(const entry of manifest.assets||[]){
      if(!entry.src||!['creature','plant','bird','island','background','prop'].includes(entry.kind))continue;
      entries.push({...entry,species:normalise(entry.species)});
      loadEntry(entry);
    }
    window.dispatchEvent(new CustomEvent('nexus:sprites-ready',{detail:{count:entries.length}}));
  }catch(error){
    console.info('Nexus sprite manifest unavailable; using procedural fallback.',error.message);
  }
}
window.NexusSprites={drawOrganism,drawBird,drawIsland,get status(){return {assets:entries.length,loaded:[...images.values()].filter(v=>v.loaded).length,failed:[...images.values()].filter(v=>v.failed).length}}};
loadManifest();
})();