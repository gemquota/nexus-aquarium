/* NEXUS biome scenery: deterministic, clustered side-view habitat dressing. */
(()=>{'use strict';
const palettes={
 coral_reef:{rock:'#344d50',light:'#73958a',plants:['#e879a7','#ffad72','#9c8bd7','#54c5a0'],density:1.25,hotspot:2.65,spread:1.0},
 kelp_forest:{rock:'#354a43',light:'#718b68',plants:['#4caa70','#76bd62','#a3c879'],density:1.3,hotspot:2.75,spread:.86},
 seagrass:{rock:'#9a8c69',light:'#c5b58a',plants:['#6dbb83','#9cce81','#4c9e76'],density:1.4,hotspot:2.7,spread:1.15},
 sandy_seabed:{rock:'#9a8c69',light:'#c5b58a',plants:['#80a878','#b2c987'],density:.22,hotspot:1.35,spread:.5},
 rocky_seabed:{rock:'#3b4a49',light:'#7d8980',plants:['#7ca77b','#a4b57b','#8b8da9'],density:.72,hotspot:1.9,spread:.8},
 deep_sea:{rock:'#172a35',light:'#344c55',plants:['#6a78a8','#8275a8','#58a5a0'],density:.12,hotspot:1.1,spread:.35},
 hydrothermal_vent:{rock:'#202d35',light:'#46565a',plants:['#d58a52','#a7a06d','#7c9b82'],density:.25,hotspot:1.25,spread:.45},
 open_ocean:{rock:'#455b57',light:'#84958a',plants:['#8caf85','#a9b987'],density:.06,hotspot:1.0,spread:.25},
 mangrove_forest:{rock:'#665c46',light:'#a49a70',plants:['#4f9361','#79ad68','#b5bd72'],density:1.25,hotspot:2.55,spread:1.2},
 estuary:{rock:'#77745a',light:'#b5a77b',plants:['#75aa75','#9bbf7c','#c0b66d'],density:1.05,hotspot:2.35,spread:1.0},
 polar_shelf:{rock:'#667d82',light:'#b5d0cf',plants:['#79a7a1','#b1c7ad'],density:.18,hotspot:1.2,spread:.45},
 seamount:{rock:'#3a4a52',light:'#71868a',plants:['#a78b77','#8d9c8d','#7b88a9'],density:.58,hotspot:1.75,spread:.7},
 abyssal_plain:{rock:'#17242d',light:'#35434a',plants:['#657b8a','#766f98'],density:.04,hotspot:1.0,spread:.2}
};
const hash=n=>{let x=(n|0)^0x9e3779b9;x=Math.imul(x^(x>>>16),0x21f0aaad);x=Math.imul(x^(x>>>15),0x735a2d97);return (x^(x>>>15))>>>0};
const rand=(n)=>hash(n)/4294967296;
const pick=(a,n)=>a[hash(n)%a.length];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function drawRock(ctx,px,py,scale,p,cluster,seed,time){
 const mound=8+cluster*34;
 ctx.save();
 const hasRock=window.NexusSprites?.drawProp?.(ctx,'rock',px,py,82*scale,44*scale,time,seed);
 ctx.fillStyle=p.rock;ctx.globalAlpha=hasRock?.18:.76;
 ctx.beginPath();ctx.moveTo(px-49*scale,py);ctx.quadraticCurveTo(px-35*scale,py-mound*scale,px-10*scale,py-mound*.72*scale);ctx.quadraticCurveTo(px+16*scale,py-mound*1.35*scale,px+49*scale,py);ctx.closePath();ctx.fill();
 ctx.globalAlpha=.22;ctx.strokeStyle=p.light;ctx.lineWidth=2*scale;ctx.beginPath();ctx.moveTo(px-22*scale,py-8*scale);ctx.quadraticCurveTo(px,py-mound*scale,px+24*scale,py-7*scale);ctx.stroke();ctx.restore();
}
function drawCoral(ctx,x,y,tall,scale,colour,id){
 ctx.save();ctx.translate(x,y);ctx.strokeStyle=colour;ctx.fillStyle=colour;ctx.lineWidth=(1.5+(hash(id+5)%3)*.5)*scale;ctx.lineCap='round';
 const arms=4+hash(id+9)%5;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-tall*.5);
 for(let a=0;a<arms;a++){const side=a%2?1:-1,yy=-tall*(.18+a/arms*.68),reach=tall*(.15+rand(id+a)*.15);ctx.moveTo(0,yy);ctx.quadraticCurveTo(side*reach*.55,yy-tall*.08,side*reach,yy-tall*.2);ctx.moveTo(0,yy-tall*.1);ctx.lineTo(-side*reach*.45,yy-tall*.25)}
 ctx.stroke();ctx.globalAlpha=.8;for(let q=0;q<4;q++){ctx.beginPath();ctx.arc((q-1.5)*tall*.11,-tall*(.55+q*.075),Math.max(1.1,2.1*scale),0,Math.PI*2);ctx.fill()}ctx.restore();
}
function drawKelp(ctx,x,y,tall,scale,colour,id,time){
 ctx.save();ctx.translate(x,y);ctx.strokeStyle=colour;ctx.lineWidth=(1.4+rand(id)*1.1)*scale;ctx.lineCap='round';
 const stipes=2+hash(id+3)%3;
 for(let b=0;b<stipes;b++){const offset=(b-(stipes-1)/2)*4*scale,phase=id*.01+b;
  ctx.beginPath();ctx.moveTo(offset,0);
  for(let q=1;q<=5;q++){const t=q/5,sway=Math.sin(time*.72+phase+t*2)*tall*.12;ctx.lineTo(offset+sway,-tall*t)}
  ctx.stroke();
  for(let q=1;q<=4;q++){const t=q/5,sway=Math.sin(time*.72+phase+t*2)*tall*.12;ctx.beginPath();ctx.ellipse(offset+sway+((q%2)?1:-1)*tall*.055,-tall*t,tall*.07,tall*.14,(q%2)*.35,0,Math.PI*2);ctx.fill()}
 }
 ctx.restore();
}
function drawGrass(ctx,x,y,tall,scale,colour,id,time,blades=8){
 ctx.save();ctx.translate(x,y);ctx.strokeStyle=colour;ctx.lineWidth=(1.0+rand(id)*.9)*scale;ctx.lineCap='round';
 for(let b=0;b<blades;b++){const f=(b-(blades-1)/2)/Math.max(1,blades),h=tall*(.55+rand(id+b)*.48),sway=Math.sin(time*1.1+id+b)*h*.09;
  ctx.beginPath();ctx.moveTo(f*4*scale,0);ctx.quadraticCurveTo(f*h*.1+sway,-h*.55,f*h*.16+sway,-h);ctx.stroke()}
 ctx.restore();
}
function drawMangrove(ctx,x,y,tall,scale,colour,id,time){
 ctx.save();ctx.translate(x,y);ctx.strokeStyle=colour;ctx.lineWidth=(1.5+rand(id)*1.3)*scale;ctx.lineCap='round';
 ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-tall);ctx.stroke();
 for(let r=0;r<5;r++){const side=r%2?1:-1,spread=(.18+rand(id+r)*.2)*tall;ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(side*spread*.45,-tall*.12,side*spread,-tall*(.25+rand(id+r+8)*.18));ctx.stroke()}
 for(let q=0;q<7;q++){const lx=(rand(id+q+20)-.5)*tall*.5,ly=-tall*(.68+rand(id+q+30)*.3);ctx.fillStyle=colour;ctx.beginPath();ctx.ellipse(lx,ly,tall*.09,tall*.035,rand(id+q)*2,0,Math.PI*2);ctx.fill()}
 ctx.restore();
}
function drawRockAlgae(ctx,x,y,tall,scale,colour,id){
 ctx.save();ctx.translate(x,y);ctx.fillStyle=colour;ctx.globalAlpha=.85;
 for(let q=0;q<5;q++){const a=rand(id+q)*Math.PI*2,rr=rand(id+q+9)*tall*.22;ctx.beginPath();ctx.ellipse(Math.cos(a)*rr,-tall*.25+Math.sin(a)*rr,tall*(.08+rand(id+q+18)*.07),tall*.13,a,0,Math.PI*2);ctx.fill()}
 ctx.restore();
}
function draw(ctx,o){
 const {ox,oy,sx,sy,width,height,worldWidth,worldHeight,bathymetry,time,zoom,habitatMap,defaultHabitat}=o;
 if(!sx||!sy||!bathymetry)return;
 const tiles=habitatMap?.tiles||[],cell=Number(habitatMap?.cell_size)||0,tileIndex=new Map(tiles.map(q=>[q.x+','+q.y,q.habitat]));
 const habitatAt=x=>{if(cell&&tileIndex.size){const tx=Math.max(0,Math.floor(x/cell)),ty=Math.max(0,Math.floor((worldHeight*.91)/cell));return tileIndex.get(tx+','+ty)||defaultHabitat||'coral_reef'}return defaultHabitat||'coral_reef'};
 const left=Math.max(0,(0-ox)/sx),right=Math.min(worldWidth,(width-ox)/sx),stride=Math.max(worldWidth/110,900);
 for(let x=Math.floor(left/stride)*stride;x<right;x+=stride){
  const h=habitatAt(x),p=palettes[h]||palettes.coral_reef,seed=Math.floor(x/stride),r=hash(seed),base=bathymetry(x),px=ox+x*sx,py=oy+base*sy;
  const scale=clamp(zoom,.55,1.8),cluster=rand(seed),hotspot=rand(seed+7919)>.62,patch=hotspot?p.hotspot:(.38+rand(seed+17)*.48),density=p.density*patch;
  if(h==='hydrothermal_vent'||h==='deep_sea'||h==='abyssal_plain'){
   ctx.save();ctx.globalAlpha=h==='hydrothermal_vent'?.72:.34;ctx.fillStyle=p.rock;
   ctx.beginPath();ctx.moveTo(px-42*scale,py);ctx.lineTo(px-25*scale,py-18*scale);ctx.lineTo(px-12*scale,py-52*scale);ctx.lineTo(px+1*scale,py-58*scale);ctx.lineTo(px+12*scale,py-23*scale);ctx.lineTo(px+36*scale,py);ctx.closePath();ctx.fill();
   if(h==='hydrothermal_vent'){ctx.strokeStyle='rgba(228,142,83,.7)';ctx.lineWidth=2*scale;ctx.beginPath();ctx.moveTo(px,py-55*scale);ctx.quadraticCurveTo(px+10*scale,py-82*scale+Math.sin(time+seed)*4,px+18*scale,py-102*scale);ctx.stroke();ctx.fillStyle='rgba(205,157,111,.22)';for(let q=0;q<4;q++){const bx=px+Math.sin(time*.5+seed+q)*9*scale,by=py-105*scale-q*16*scale;ctx.beginPath();ctx.arc(bx,by,4*scale+q,0,Math.PI*2);ctx.fill()}}
   if(h==='deep_sea'||h==='abyssal_plain'){ctx.fillStyle='rgba(118,150,191,.55)';for(let q=0;q<5;q++){const dx=(hash(seed+q)%90-45)*scale,dy=(hash(seed+q+77)%20-30)*scale;ctx.beginPath();ctx.arc(px+dx,py+dy,1.1*scale,0,Math.PI*2);ctx.fill()}}
   if(h==='deep_sea'&&rand(seed+31)>.55){drawRockAlgae(ctx,px+(rand(seed+32)-.5)*60*scale,py,12*scale,scale,pick(p.plants,seed),seed)}
   ctx.restore();continue;
  }
  drawRock(ctx,px,py,scale,p,cluster,seed,time);
  // Each biome has its own growth form and a dense centre with ragged edges.
  const baseCounts={coral_reef:17,kelp_forest:19,seagrass:23,sandy_seabed:3,rocky_seabed:9,open_ocean:1,mangrove_forest:17,estuary:14,polar_shelf:4,seamount:8};
  const count=Math.round((baseCounts[h]||2)*density);
  const centre=(rand(seed+101)-.5)*.42;
  for(let n=0;n<count;n++){
   const id=seed*131+n*29,offset=(rand(id)-.5)*stride*p.spread;
   const plantX=px+centre*stride+offset*(hotspot?.46:1),plantY=py-(rand(id+8)*9+rand(id+9)*5)*scale;
   const tall=(h==='kelp_forest'?70+rand(id+10)*115:h==='mangrove_forest'?48+rand(id+10)*78:h==='seagrass'?17+rand(id+10)*34:h==='coral_reef'?20+rand(id+10)*58:h==='estuary'?35+rand(id+10)*65:12+rand(id+10)*38)*scale;
   const colour=pick(p.plants,id);
   if(h==='coral_reef')drawCoral(ctx,plantX,plantY,tall,scale,colour,id);
   else if(h==='kelp_forest'){
    drawKelp(ctx,plantX,plantY,tall,scale,colour,id,time);
    if(rand(id+55)>.42)window.NexusSprites?.drawPlant?.(ctx,plantX,plantY,Math.max(12,tall*.23),Math.max(20,tall*.9),time,id);
   }else if(h==='seagrass'||h==='sandy_seabed')drawGrass(ctx,plantX,plantY,tall,scale,colour,id,time,h==='seagrass'?9:4);
   else if(h==='mangrove_forest')drawMangrove(ctx,plantX,plantY,tall,scale,colour,id,time);
   else if(h==='estuary'){drawGrass(ctx,plantX,plantY,tall,scale,colour,id,time,6);if(rand(id+77)>.45)drawMangrove(ctx,plantX,plantY,tall*.8,scale,colour,id,time)}
   else drawRockAlgae(ctx,plantX,plantY,tall,scale,colour,id);
  }
  if(h==='coral_reef'||h==='hydrothermal_vent'){for(let bubble=0;bubble<2; bubble++)window.NexusSprites?.drawProp?.(ctx,'bubble',px+(bubble?18:-16)*scale,py-(34+bubble*21+Math.sin(time+seed+bubble)*4)*scale,5*scale,5*scale,time,seed+bubble)}
  if(h==='sandy_seabed'||h==='seagrass'||h==='estuary'){ctx.save();ctx.strokeStyle='rgba(239,220,164,.16)';ctx.lineWidth=1*scale;for(let q=0;q<3;q++){const yy=py-(q+1)*4*scale;ctx.beginPath();ctx.moveTo(px-35*scale,yy);ctx.quadraticCurveTo(px,yy-3*scale,px+35*scale,yy);ctx.stroke()}ctx.restore()}
 }
}
window.NexusBiomeRenderer={draw,palettes};
})();