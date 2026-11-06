/* NEXUS side-view sprite runtime. Uses every clean imported variant,
 * preserves source aspect ratios, and animates each individual independently. */
(()=>{'use strict';
const MANIFEST_URL=new URL('./runtime-manifest.json',document.currentScript.src).href;
const images=new Map(),entries=[];
const plantSpecies=new Set(['kelp','seagrass','sea_lettuce','mangrove','sargassum','seaweed','macroalgae','eelgrass','coral','coral_polyp','marsh_grass','saltmarsh']);
const speciesAliases={shark:'great_white_shark',whale:'humpback_whale',dolphin:'bottlenose_dolphin',seal:'harbor_seal',sea_lion:'california_sea_lion',manatee:'west_indian_manatee',sunfish:'ocean_sunfish',seahorse:'pacific_seahorse',jellyfish:'moon_jellyfish',sea_turtle:'green_sea_turtle',turtle:'green_sea_turtle',clown_fish:'clownfish',coral_polyp:'coral',kelp:'seaweed',seagrass:'seaweed',sea_lettuce:'seaweed',mangrove:'seaweed',sargassum:'seaweed',eelgrass:'seaweed',gull:'seagull'};
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
function findView(kind,species,view,seed=0){
 const name=speciesAliases[normalise(species)]||normalise(species);
 const pool=entries.filter(e=>e.kind===kind&&clean(e)&&e.species===name&&e.view===view);
 return pool.length?pool[hash(String(seed)+':'+view)%pool.length]:null;
}
function chooseView(vx,vy){
 // In a side-view world, screen-space vertical movement is not camera-facing yaw.
 // Use the side pose unless the simulation explicitly supplies a view state.
 return 'side';
}
function resolveView(o,time=0){
 const state=normalise(o.animation_state||o.behaviour||o.behavior||o.state||'');
 // A turning clip owns pose selection until it completes. A stale side-view
 // orientation field must not short-circuit the authored turn transition.
 if(state==='turning'||state==='turn'){
  const target=normalise(o.turn_target_view||o.target_view||'front_three_quarter');
  const valid=['front','front_three_quarter','rear_three_quarter','rear'].includes(target)?target:'front_three_quarter';
  const elapsed=Math.max(0,Number(o.animation_elapsed??o.state_elapsed??0)||0);
  const progress=clampView(elapsed/.9,0,1);
  if(progress<.28)return 'side';
  if(progress<.72)return valid==='rear'||valid==='rear_three_quarter'?'rear_three_quarter':'front_three_quarter';
  return valid;
 }
 const explicit=normalise(o.view||o.facing_view||o.orientation_view||'');
 if(['front','front_three_quarter','side','rear_three_quarter','rear'].includes(explicit))return explicit;
 return 'side';
}
function clampView(v){return Math.max(0,Math.min(1,v));}
function frame(entry,state,time){
 const fw=Math.max(1,Number(entry.frame_width)||state.image.naturalWidth);
 const fh=Math.max(1,Number(entry.frame_height)||state.image.naturalHeight);
 const cols=Math.max(1,Math.floor(state.image.naturalWidth/fw));
 const rows=Math.max(1,Math.floor(state.image.naturalHeight/fh));
 const count=Math.max(1,Number(entry.frames)||cols*rows);
 const index=count>1?Math.floor(time*Math.max(.1,Number(entry.fps)||6))%count:0;
 return {sx:(index%cols)*fw,sy:Math.floor(index/cols)*fh,sw:Math.min(fw,state.image.naturalWidth),sh:Math.min(fh,state.image.naturalHeight)};
}
function drawImage(ctx,entry,x,y,boundW,boundH,time,anchorX=.5,anchorY=.5,flip=false,angle=0,breath=0,deformX=1,deformY=1,flex=0,roll=0,opacity=1){
 const state=loadEntry(entry);if(!state?.loaded||state.failed)return false;
 const f=frame(entry,state,time),aspect=f.sw/f.sh;
 let w=boundW,h=boundH;
 if(w/h>aspect)w=h*aspect;else h=w/aspect;
 const bob=breath?Math.sin(time*2.8+hash(entry.filename||entry.src)%31)*breath:0;
 ctx.save();ctx.globalAlpha=opacity;ctx.translate(x,y+bob);ctx.rotate(angle+roll);ctx.scale(flip?-1:1,1);ctx.scale(deformX,deformY);
 ctx.imageSmoothingEnabled=false;
 if(Math.abs(flex)>.0005&&f.sw>=5){
  // Six overlapping horizontal body slices approximate a low-cost spine mesh.
  // Each slice has its own joint angle and travelling-wave offset.
  const segments=6,strip=f.sw/segments;
  for(let i=0;i<segments;i++){
   const t=(i+.5)/segments,theta=flex*Math.cos(t*Math.PI*2),offset=Math.sin(t*Math.PI)*flex*h*1.8;
   const dx=-w*anchorX+t*w,dy=-h*anchorY+offset;
   ctx.save();ctx.translate(dx,dy);ctx.rotate(theta);
   ctx.drawImage(state.image,f.sx+i*strip,f.sy,Math.ceil(strip)+1,f.sh,-w/segments*.52,-h*.5,w/segments*1.04,h);
   ctx.restore();
  }
 }else{
  ctx.drawImage(state.image,f.sx,f.sy,f.sw,f.sh,-w*anchorX,-h*anchorY,w,h);
 }
 ctx.restore();return true;
}
const spriteTiming={far:[],body:[],near:[]};function recordSpriteTime(layer,start){const a=spriteTiming[layer];a.push(performance.now()-start);if(a.length>120)a.shift()}function metric(a,q){if(!a.length)return 0;const v=[...a].sort((x,y)=>x-y);return v[Math.min(v.length-1,Math.floor((v.length-1)*q))]}
function drawOrganism(ctx,o,x,y,opts={}){
 const species=normalise(o.species),kind=plantSpecies.has(species)?'plant':'creature';
 const vx=Number(o.vx)||0,vy=Number(o.vy)||0,time=Number(opts.time)||0,view=resolveView(o,time);
 const canonical=speciesAliases[species]||species;
 const entry=kind==='creature'?(findView(kind,canonical,view,o.id)||find(kind,species,o.id)):find(kind,species,o.id);
 if(!entry)return false;
 const size=.82+Math.max(0,Math.min(1,Number(o.genome?.size??.5)))*.36;
 if(kind==='plant'){
  const h=(Number(entry.render_height)||(species==='mangrove'?6:species==='kelp'?3.5:2.4))*size;
  const w=(Number(entry.render_width)||Math.max(1.2,h*.55))*size;
  const baseY=Number.isFinite(opts.plantBaseY)?opts.plantBaseY:y;
  const sway=Math.sin(time*1.25+(Number(o.id)||0)*.71)*.045;
  return drawImage(ctx,entry,x,baseY,w,h,time,Number(entry.anchor_x??.5),1,false,sway,0);
 }
 const large=['whale','shark','dolphin','ray','orca','humpback_whale','great_white_shark','hammerhead_shark','whale_shark','bottlenose_dolphin','harbor_seal','california_sea_lion','west_indian_manatee','ocean_sunfish','green_sea_turtle'].includes(canonical);
 const tiny=['reef_fish','surface_fish','pelagic_fish','deepwater_fish','sardine','mackerel','lanternfish','anglerfish'].includes(species);
 const bw=(Number(entry.render_width)||(large?6.2:tiny?2.8:3.8))*size;
 const bh=(Number(entry.render_height)||(large?3.4:tiny?2.0:2.8))*size;
 const heading=Math.atan2(vy,Math.abs(vx)||.0001);
 const swim=Math.sin(time*5.2+(Number(o.id)||0)*.73);
 const turn=Math.max(-.08,Math.min(.08,heading*.08));
 const flip=(view==='side'||view.includes('three_quarter'))&&vx<0;
 const sample=(Number(o.id)||0)%8===0,farStart=sample?performance.now():0;
 const rig=window.NexusCreatureAnimation?.draw(ctx,o,x,y,bw,bh,time,{view,flip,layer:'far'});
 if(sample)recordSpriteTime('far',farStart);
 const bodyFlex=rig?.bodyFlex||0;
 const bodyY=y+(rig?.sinkY||0)*bh,bodyX=x+(rig?.bodySurgeX||0)*bw;
 const bodyStart=sample?performance.now():0;
 const rendered=drawImage(ctx,entry,bodyX,bodyY,bw,bh,time,Number(entry.anchor_x??.5),Number(entry.anchor_y??.5),flip,turn+swim*.006+(rig?.bodyPitch||0),Math.max(.025,bh*.012),rig?.bodyScaleX||1,rig?.bodyScaleY||1,bodyFlex,rig?.bodyRoll||0,rig?.bodyOpacity||1);
 if(sample)recordSpriteTime('body',bodyStart);
 if(rendered){const nearStart=sample?performance.now():0;window.NexusCreatureAnimation?.draw(ctx,o,bodyX,bodyY,bw,bh,time,{view,flip,layer:'near'});if(sample)recordSpriteTime('near',nearStart)}
 return rendered;
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
function drawPlant(ctx,x,baseY,width,height,time=0,seed=0,category='kelp'){
 const name=normalise(category);
 const rules={
  kelp:e=>/^seaweed_green_[a-d]\.png$/i.test(e.filename||''),
  seagrass:e=>/^seaweed_grass_[ab]\.png$/i.test(e.filename||''),
  mangrove:e=>/^background_seaweed_[a-h]\.png$/i.test(e.filename||''),
  sargassum:e=>/^seaweed_(green|orange)_[a-d]\.png$/i.test(e.filename||''),
  macroalgae:e=>/^seaweed_(green|orange|pink)_[a-d]\.png$/i.test(e.filename||'')
 };
 const rule=name==='coral'?e=>/^coral_.*\.svg$/i.test(e.filename||''):(rules[name]||rules.kelp);
 const targetSpecies=name==='coral'?'coral':'seaweed';
 const pool=entries.filter(e=>e.kind==='plant'&&e.species===targetSpecies&&clean(e)&&rule(e));
 if(!pool.length)return false;
 const entry=pool[hash(String(seed)+':'+name)%pool.length];
 const sway=Math.sin(time*1.25+seed*.71)*.045;
 // Kenney's flora frames are square canvases with transparent margins. Keep
 // their native aspect ratio and anchor the bottom edge to the substrate.
 return drawImage(ctx,entry,x,baseY,Math.max(width,height*.92),height,time,.5,1,false,sway,0);
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
window.NexusSprites={drawOrganism,drawBird,drawIsland,drawProp,drawPlant,chooseView,resolveView,get metrics(){return {far:{median:metric(spriteTiming.far,.5),p95:metric(spriteTiming.far,.95),samples:spriteTiming.far.length},body:{median:metric(spriteTiming.body,.5),p95:metric(spriteTiming.body,.95),samples:spriteTiming.body.length},near:{median:metric(spriteTiming.near,.5),p95:metric(spriteTiming.near,.95),samples:spriteTiming.near.length}}},get status(){return {assets:entries.length,loaded:[...images.values()].filter(v=>v.loaded).length,failed:[...images.values()].filter(v=>v.failed).length}}};
loadManifest();
})();