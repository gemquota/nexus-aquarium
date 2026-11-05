/* NEXUS biome scenery: deterministic, layered side-view habitat dressing.
 * Vegetation is patch-based: dense nursery/reef hotspots fade into sparse
 * transition zones instead of repeating evenly spaced decorative tufts. */
(()=>{'use strict';
const palettes={
 coral_reef:{rock:'#344d50',light:'#73958a',plants:['#e879a7','#ffad72','#9c8bd7','#54c5a0'],density:1.9},
 kelp_forest:{rock:'#354a43',light:'#718b68',plants:['#4caa70','#76bd62','#a3c879'],density:1.65},
 seagrass:{rock:'#9a8c69',light:'#c5b58a',plants:['#6dbb83','#9cce81','#4c9e76'],density:1.55},
 sandy_seabed:{rock:'#9a8c69',light:'#c5b58a',plants:['#80a878','#b2c987'],density:.34},
 rocky_seabed:{rock:'#3b4a49',light:'#7d8980',plants:['#7ca77b','#a4b57b','#8b8da9'],density:.82},
 deep_sea:{rock:'#172a35',light:'#344c55',plants:['#6a78a8','#8275a8','#58a5a0'],density:.2},
 hydrothermal_vent:{rock:'#202d35',light:'#46565a',plants:['#d58a52','#a7a06d','#7c9b82'],density:.34},
 open_ocean:{rock:'#455b57',light:'#84958a',plants:['#8caf85','#a9b987'],density:.12},
 mangrove_forest:{rock:'#665c46',light:'#a49a70',plants:['#4f9361','#79ad68','#b5bd72'],density:1.8},
 estuary:{rock:'#77745a',light:'#b5a77b',plants:['#75aa75','#9bbf7c','#c0b66d'],density:1.25},
 polar_shelf:{rock:'#667d82',light:'#b5d0cf',plants:['#79a7a1','#b1c7ad'],density:.24},
 seamount:{rock:'#3a4a52',light:'#71868a',plants:['#a78b77','#8d9c8d','#7b88a9'],density:.72},
 abyssal_plain:{rock:'#17242d',light:'#35434a',plants:['#657b8a','#766f98'],density:.08}
};
const hash=n=>{let x=(n|0)^0x9e3779b9;x=Math.imul(x^(x>>>16),0x21f0aaad);x=Math.imul(x^(x>>>15),0x735a2d97);return (x^(x>>>15))>>>0};
const pick=(a,n)=>a[hash(n)%a.length];
const unit=n=>hash(n)/4294967295;
const smooth=(a,b,v)=>{const q=Math.max(0,Math.min(1,(v-a)/(b-a)));return q*q*(3-2*q)};
function patchIntensity(seed,x,habitat){
 // Overlapping deterministic bands create broad beds with irregular edges.
 const broad=.5+.5*Math.sin(x*.000021+seed*.17);
 const medium=.5+.5*Math.sin(x*.000083+seed*.71);
 const fine=.5+.5*Math.sin(x*.00031+seed*1.91);
 const noise=broad*.56+medium*.29+fine*.15;
 const threshold=habitat==='coral_reef'?.40:habitat==='kelp_forest'?.36:habitat==='mangrove_forest'?.38:.48;
 return smooth(threshold,threshold+.34,noise);
}
function draw(ctx,o){
 const {ox,oy,sx,sy,width,height,worldWidth,worldHeight,bathymetry,time,zoom,habitatMap,defaultHabitat}=o;
 if(!sx||!sy||!bathymetry)return;
 const tiles=habitatMap?.tiles||[],cell=Number(habitatMap?.cell_size)||0,tileIndex=new Map(tiles.map(q=>[q.x+','+q.y,q.habitat]));
 const habitatAt=x=>{if(cell&&tileIndex.size){const tx=Math.max(0,Math.floor(x/cell)),ty=Math.max(0,Math.floor((worldHeight*.91)/cell));return tileIndex.get(tx+','+ty)||defaultHabitat||'coral_reef'}return defaultHabitat||'coral_reef'};
 const left=Math.max(0,(0-ox)/sx),right=Math.min(worldWidth,(width-ox)/sx);
 const stride=Math.max(worldWidth/180,520),scale=Math.max(.55,Math.min(1.8,zoom));
 for(let x=Math.floor(left/stride)*stride;x<right;x+=stride){
  const h=habitatAt(x),p=palettes[h]||palettes.coral_reef,seed=Math.floor(x/stride),r=hash(seed),base=bathymetry(x),px=ox+x*sx,py=oy+base*sy;
  const intensity=patchIntensity(seed,x,h),cluster=unit(seed+81);
  if(h==='hydrothermal_vent'||h==='deep_sea'||h==='abyssal_plain'){
   ctx.save();ctx.globalAlpha=h==='hydrothermal_vent'?.78:.42;ctx.fillStyle=p.rock;
   ctx.beginPath();ctx.moveTo(px-42*scale,py);ctx.lineTo(px-25*scale,py-18*scale);ctx.lineTo(px-12*scale,py-52*scale);ctx.lineTo(px+1*scale,py-58*scale);ctx.lineTo(px+12*scale,py-23*scale);ctx.lineTo(px+36*scale,py);ctx.closePath();ctx.fill();
   if(h==='hydrothermal_vent'){
    ctx.fillStyle='#b9a17b';for(let tube=0;tube<3;tube++){const tx=px+(tube-1)*12*scale;ctx.fillRect(tx-2*scale,py-(26+tube%2*10)*scale,4*scale,28*scale)}
    ctx.strokeStyle='rgba(228,142,83,.82)';ctx.lineWidth=2*scale;ctx.beginPath();ctx.moveTo(px,py-55*scale);ctx.quadraticCurveTo(px+10*scale,py-82*scale+Math.sin(time+seed)*4,px+18*scale,py-102*scale);ctx.stroke();
    for(let q=0;q<7;q++){const bx=px+Math.sin(time*.5+seed+q)*12*scale,by=py-105*scale-q*13*scale;ctx.fillStyle='rgba(205,157,111,.18)';ctx.beginPath();ctx.arc(bx,by,4*scale+q*.45,0,Math.PI*2);ctx.fill()}
   }else{
    ctx.fillStyle='rgba(118,150,191,.58)';for(let q=0;q<(h==='deep_sea'?8:3);q++){const dx=(hash(seed+q)%90-45)*scale,dy=(hash(seed+q+77)%20-30)*scale;ctx.beginPath();ctx.arc(px+dx,py+dy,1.1*scale,0,Math.PI*2);ctx.fill()}
   }
   ctx.restore();continue;
  }
  const mound=10+cluster*32;
  ctx.save();const hasRock=window.NexusSprites?.drawProp?.(ctx,'rock',px,py,78*scale,42*scale,time,seed);ctx.fillStyle=p.rock;ctx.globalAlpha=hasRock?0.18:.75;ctx.beginPath();ctx.moveTo(px-48*scale,py);ctx.quadraticCurveTo(px-35*scale,py-mound*scale,px-10*scale,py-mound*.72*scale);ctx.quadraticCurveTo(px+16*scale,py-mound*1.35*scale,px+48*scale,py);ctx.closePath();ctx.fill();
  ctx.globalAlpha=.22;ctx.strokeStyle=p.light;ctx.lineWidth=2*scale;ctx.beginPath();ctx.moveTo(px-22*scale,py-8*scale);ctx.quadraticCurveTo(px,py-mound*scale,px+24*scale,py-7*scale);ctx.stroke();ctx.restore();
  const baseCount=Math.round(p.density*(h==='coral_reef'?5:4));
  const count=Math.max(0,Math.round(baseCount*(.18+intensity*1.95)));
  for(let n=0;n<count;n++){
   const id=seed*131+n*29,dx=(hash(id)%94-47)*scale,plantX=px+dx,plantY=py-(hash(id+4)%12)*scale;
   const tall=(18+(hash(id+8)%50))*scale*(.68+intensity*.72),colour=pick(p.plants,id);
   const spritePlant=['coral_reef','kelp_forest','seagrass','mangrove_forest','estuary','rocky_seabed'].includes(h);
   if(spritePlant&&intensity>.45)window.NexusSprites?.drawPlant?.(ctx,plantX,plantY,Math.max(12,tall*.72),Math.max(18,tall*1.35),time,id);
   ctx.save();ctx.translate(plantX,plantY);ctx.strokeStyle=colour;ctx.fillStyle=colour;ctx.lineWidth=(1.2+(hash(id+5)%3)*.45)*scale;ctx.lineCap='round';
   if(h==='coral_reef'){
    const arms=4+hash(id+9)%5;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-tall*.48);
    for(let a=0;a<arms;a++){const side=a%2?1:-1,yy=-tall*(.18+a/arms*.68);ctx.moveTo(0,yy);ctx.quadraticCurveTo(side*tall*.18,yy-tall*.12,side*tall*.28,yy-tall*.25);ctx.moveTo(0,yy-tall*.12);ctx.lineTo(-side*tall*.12,yy-tall*.27)}ctx.stroke();
    ctx.globalAlpha=.8;for(let q=0;q<4;q++){ctx.beginPath();ctx.arc((q-1.5)*tall*.11,-tall*(.5+q*.09),Math.max(1.2,2.4*scale),0,Math.PI*2);ctx.fill()}
   }else if(h==='kelp_forest'){
    for(let b=0;b<4;b++){const sway=Math.sin(time*.8+id+b)*tall*.12,offset=(b-1.5)*tall*.075;ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(offset+sway,-tall*.28,offset-sway,-tall*.68,offset+sway,-tall);ctx.stroke();ctx.beginPath();ctx.ellipse(offset+sway,-tall*.55,Math.max(1.5,tall*.055),tall*.17,sway*.015,0,Math.PI*2);ctx.fill()}
   }else if(h==='mangrove_forest'||h==='estuary'){
    for(let b=0;b<4;b++){const sway=Math.sin(time*.55+id+b)*tall*.045,side=b%2?1:-1;ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(side*tall*.12+sway,-tall*.6,side*tall*.2+sway,-tall);ctx.stroke();ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(side*tall*.2, tall*.04,side*tall*.32,tall*.16);ctx.stroke()}
   }else if(h==='seagrass'||h==='sandy_seabed'||h==='polar_shelf'){
    const blades=h==='seagrass'?7:4;for(let b=0;b<blades;b++){const sway=Math.sin(time+id+b)*tall*.08;ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo((b-(blades-1)/2)*tall*.08+sway,-tall*.55,(b-(blades-1)/2)*tall*.12+sway,-tall*(.65+(b%3)*.1));ctx.stroke()}
   }else{
    ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-tall*.65);ctx.stroke();ctx.beginPath();ctx.ellipse(0,-tall*.7,3*scale,7*scale,0,0,Math.PI*2);ctx.fill()
   }
   ctx.restore();
  }
  if(h==='coral_reef'&&intensity>.35){
   // Small sponge/anemone forms fill the gaps between larger coral heads.
   ctx.save();for(let q=0;q<Math.round(2+intensity*5);q++){const ax=px+(unit(seed+q*7)-.5)*72*scale,ay=py-(3+unit(seed+q*11)*8)*scale;ctx.fillStyle=pick(['#e5a66f','#b27eaf','#6ab9a5'],seed+q);ctx.beginPath();ctx.ellipse(ax,ay,2.2*scale,4.5*scale,0,0,Math.PI*2);ctx.fill()}ctx.restore();
  }
  if(h==='coral_reef'||h==='hydrothermal_vent'){for(let bubble=0;bubble<2; bubble++)window.NexusSprites?.drawProp?.(ctx,'bubble',px+(bubble?18:-16)*scale,py-(34+bubble*21+Math.sin(time+seed+bubble)*4)*scale,5*scale,5*scale,time,seed+bubble)}
  if(h==='sandy_seabed'||h==='seagrass'||h==='estuary'){ctx.save();ctx.strokeStyle='rgba(239,220,164,.16)';ctx.lineWidth=1*scale;for(let q=0;q<3;q++){const yy=py-(q+1)*4*scale;ctx.beginPath();ctx.moveTo(px-35*scale,yy);ctx.quadraticCurveTo(px,yy-3*scale,px+35*scale,yy);ctx.stroke()}ctx.restore()}
 }
}
window.NexusBiomeRenderer={draw,palettes};
})();