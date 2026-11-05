/* NEXUS side-view sprite runtime.
 * Sprite geometry is expressed in world-height fractions, not arbitrary pixels.
 * Transparent padding is trimmed once at load; fish swim with a travelling tail wave. */
(()=>{'use strict';
const MANIFEST_URL=new URL('./runtime-manifest.json',document.currentScript.src).href;
const images=new Map(),entries=[];
const fishSpecies=new Set(['reef_fish','surface_fish','pelagic_fish','deepwater_fish','sardine','mackerel','lanternfish','anglerfish']);
const plantSpecies=new Set(['seaweed']);
const speciesAliases={reef_fish:'generic',surface_fish:'generic',pelagic_fish:'generic',deepwater_fish:'generic',sardine:'generic',mackerel:'generic',lanternfish:'generic',anglerfish:'generic'};
const normalise=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
const clean=e=>!/(?:_outline|_skeleton)(?:\.[^.]+)?$/i.test(e.filename||e.src||'');
function alphaBounds(image){
 try{
  const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
  const c=canvas.getContext('2d',{willReadFrequently:true});c.drawImage(image,0,0);
  const pixels=c.getImageData(0,0,canvas.width,canvas.height).data;
  let minX=canvas.width,minY=canvas.height,maxX=-1,maxY=-1;
  for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++)if(pixels[(y*canvas.width+x)*4+3]>12){if(x<minX)minX=x;if(y<minY)minY=y;if(x>maxX)maxX=x;if(y>maxY)maxY=y}
  if(maxX<minX||maxY<minY)return null;
  const pad=1;minX=Math.max(0,minX-pad);minY=Math.max(0,minY-pad);maxX=Math.min(canvas.width-1,maxX+pad);maxY=Math.min(canvas.height-1,maxY+pad);
  return {x:minX,y:minY,w:maxX-minX+1,h:maxY-minY+1};
 }catch(_){return null}
}
function loadEntry(entry){
 if(!entry?.src)return null;
 const key=new URL(String(entry.src).replace(/^\/+/,''),new URL('../../',MANIFEST_URL)).href;
 if(images.has(key))return images.get(key);
 const image=new Image();image.decoding='async';image.loading='eager';
 const state={image,loaded:false,failed:false,bounds:null};
 image.onload=()=>{state.bounds=alphaBounds(image);state.loaded=true};
 image.onerror=()=>{state.failed=true};
 image.src=key;images.set(key,state);return state;
}
function variants(kind,name){return entries.filter(e=>e.kind===kind&&clean(e)&&(e.species===name||e.species==='generic'||e.species===''))}
function hash(value){let h=2166136261;for(const c of String(value)){h^=c.charCodeAt(0);h=Math.imul(h,16777619)}return h>>>0}
function find(kind,species,seed=0){
 const name=speciesAliases[normalise(species)]||normalise(species);
 const exact=variants(kind,name),pool=exact.length?exact:variants(kind,'generic');
 return pool.length?pool[hash(seed)%pool.length]:null;
}
function frame(entry,state,time){
 const fw=Math.max(1,Number(entry.frame_width)||state.image.naturalWidth),fh=Math.max(1,Number(entry.frame_height)||state.image.naturalHeight);
 const cols=Math.max(1,Math.floor(state.image.naturalWidth/fw)),count=Math.max(1,Number(entry.frames)||cols*Math.max(1,Math.floor(state.image.naturalHeight/fh)));
 const index=count>1?Math.floor(time*Math.max(.1,Number(entry.fps)||6))%count:0;
 return {sx:(index%cols)*fw,sy:Math.floor(index/cols)*fh,sw:Math.min(fw,state.image.naturalWidth),sh:Math.min(fh,state.image.naturalHeight)};
}
function drawImage(ctx,entry,state,x,y,boundW,boundH,time,flip,angle,bob,tailWave,minimumPixels,zoom=1){
 const f=frame(entry,state,time),crop=state.bounds&&Number(entry.frames||1)===1?state.bounds:{x:0,y:0,w:f.sw,h:f.sh};
 const sx=f.sx+crop.x,sy=f.sy+crop.y,sw=Math.min(crop.w,f.sw-crop.x),sh=Math.min(crop.h,f.sh-crop.y);
 if(sw<1||sh<1)return false;
 const aspect=sw/sh;let w=boundW,h=boundH;
 if(w/h>aspect)w=h*aspect;else h=w/aspect;
 const minCanvas=(minimumPixels||1.5)/Math.max(.25,zoom||1);
 if(w<minCanvas){h*=minCanvas/w;w=minCanvas}
 const bobAmount=Math.min(bob||0,2.5/Math.max(.25,zoom||1)),tailAmount=Math.min(tailWave||0,4/Math.max(.25,zoom||1));
 const bobOffset=bobAmount?Math.sin(time*2.8+hash(entry.filename||entry.src)%31)*bobAmount:0;
 ctx.save();ctx.translate(x,y+bobOffset);ctx.rotate(angle);ctx.scale(flip?-1:1,1);ctx.imageSmoothingEnabled=false;
 if(tailAmount>0&&w*zoom>10){
  const slices=8,destSlice=w/slices;
  for(let i=0;i<slices;i++){
   const u=(i+.5)/slices,sourceX=sx+i*sw/slices,sourceW=sw/slices+1;
   const wave=Math.sin(time*8.2-u*2.7+hash(entry.filename||entry.src)%19)*tailAmount*Math.pow(1-u,2);
   ctx.drawImage(state.image,sourceX,sy,Math.min(sourceW,sx+sw-sourceX),sh,-w/2+i*destSlice-.35,-h/2+wave,destSlice+.7,h);
  }
 }else ctx.drawImage(state.image,sx,sy,sw,sh,-w/2,-h/2,w,h);
 ctx.restore();return true;
}
function drawOrganism(ctx,o,x,y,opts={}){
 const species=normalise(o.species);
 if(!fishSpecies.has(species)&&!plantSpecies.has(species))return false;
 const kind=plantSpecies.has(species)?'plant':'creature',entry=find(kind,species,o.id);
 if(!entry)return false;
 const state=loadEntry(entry);if(!state?.loaded||state.failed)return false;
 const time=Number(opts.time)||0,worldHeight=Math.max(1,Number(opts.worldHeight)||100000),unitScale=Math.max(.000001,Number(opts.worldToCanvasScale)||1),zoom=Math.max(.25,Number(opts.zoom)||1);
 const size=.84+Math.max(0,Math.min(1,Number(o.genome?.size??.5)))*.32;
 if(kind==='plant'){
  const h=worldHeight*.052*size*unitScale,w=worldHeight*.025*size*unitScale;
  const sway=Math.sin(time*1.25+(Number(o.id)||0)*.71)*.045;
  const baseY=Number.isFinite(opts.plantBaseY)?opts.plantBaseY:y;
  return drawImage(ctx,entry,state,x,baseY-h/2,w,h,time,false,sway,0,0,1.5,zoom);
 }
 const lengths={reef_fish:.019,surface_fish:.018,pelagic_fish:.021,deepwater_fish:.017,sardine:.015,mackerel:.023,lanternfish:.014,anglerfish:.019};
 const width=worldHeight*(lengths[species]||.018)*size*unitScale,height=worldHeight*.0105*size*unitScale;
 const vx=Number(o.vx)||0,vy=Number(o.vy)||0,heading=Math.atan2(vy,Math.abs(vx)||.0001);
 const swim=Math.sin(time*5.2+(Number(o.id)||0)*.73);
 const turn=Math.max(-.16,Math.min(.16,heading*.22));
 return drawImage(ctx,entry,state,x,y,width,height,time,vx<0,turn+swim*.025,height*.055,height*.075,1.7,zoom);
}
function measureOrganism(species,worldHeight,unitScale,zoom,genomeSize=.5){
 const entry=find('creature',species,1);if(!entry)return null;
 const state=loadEntry(entry);if(!state?.loaded||state.failed)return null;
 const f=frame(entry,state,0),crop=state.bounds&&Number(entry.frames||1)===1?state.bounds:{x:0,y:0,w:f.sw,h:f.sh};
 const sw=Math.min(crop.w,f.sw-crop.x),sh=Math.min(crop.h,f.sh-crop.y);if(sw<1||sh<1)return null;
 const lengths={reef_fish:.019,surface_fish:.018,pelagic_fish:.021,deepwater_fish:.017,sardine:.015,mackerel:.023,lanternfish:.014,anglerfish:.019};
 const size=.84+Math.max(0,Math.min(1,Number(genomeSize)||.5))*.32,worldH=Math.max(1,Number(worldHeight)||100000),scale=Math.max(.000001,Number(unitScale)||1),z=Math.max(.25,Number(zoom)||1);
 let w=worldH*(lengths[normalise(species)]||.018)*size*scale,h=worldH*.0105*size*scale;
 const aspect=sw/sh;if(w/h>aspect)w=h*aspect;else h=w/aspect;
 const minCanvas=1.7/z;if(w<minCanvas){h*=minCanvas/w;w=minCanvas}
 return {width:w*z,height:h*z};
}
function drawBird(ctx,bird,x,y,opts={}){
 const entry=find('bird',bird.species,opts.index)||find('bird','generic',opts.index);if(!entry)return false;
 const state=loadEntry(entry);if(!state?.loaded||state.failed)return false;
 const worldHeight=Number(opts.worldHeight)||100000,pixelsPerUnit=Number(opts.pixelsPerUnit)||.006,w=worldHeight*.018*pixelsPerUnit,h=worldHeight*.012*pixelsPerUnit;
 const flap=bird.state==='gliding'?0:Math.sin((Number(opts.time)||0)*9+(Number(opts.index)||0))*.035;
 return drawImage(ctx,entry,state,x,y,w,h,Number(opts.time)||0,Number(bird.vx)<0,flap,0,0,2,1);
}
function drawIsland(ctx,island,x,y,radius,opts={}){
 const entry=find('island',island.kind||island.species||'generic',island.id||island.x||0);if(!entry)return false;
 const state=loadEntry(entry);if(!state?.loaded||state.failed)return false;
 const w=Math.max(12,radius*3.6),h=Math.max(5,radius*.9);
 return drawImage(ctx,entry,state,x,y,w,h,0,false,0,0,0,2,1);
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
window.NexusSprites={drawOrganism,drawBird,drawIsland,measureOrganism,get status(){const states=[...images.values()];return {assets:entries.length,loaded:states.filter(v=>v.loaded).length,failed:states.filter(v=>v.failed).length,pending:states.filter(v=>!v.loaded&&!v.failed).length}}};
loadManifest();
})();