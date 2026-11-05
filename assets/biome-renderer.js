/* NEXUS biome scenery: deterministic, layered side-view habitat dressing. */
(()=>{'use strict';
const palettes={
 coral_reef:{rock:'#344d50',light:'#73958a',plants:['#e879a7','#ffad72','#9c8bd7','#54c5a0'],density:1.0},
 kelp_forest:{rock:'#354a43',light:'#718b68',plants:['#4caa70','#76bd62','#a3c879'],density:.92},
 seagrass:{rock:'#9a8c69',light:'#c5b58a',plants:['#6dbb83','#9cce81','#4c9e76'],density:.85},
 sandy_seabed:{rock:'#9a8c69',light:'#c5b58a',plants:['#80a878','#b2c987'],density:.22},
 rocky_seabed:{rock:'#3b4a49',light:'#7d8980',plants:['#7ca77b','#a4b57b','#8b8da9'],density:.48},
 deep_sea:{rock:'#172a35',light:'#344c55',plants:['#6a78a8','#8275a8','#58a5a0'],density:.12},
 hydrothermal_vent:{rock:'#202d35',light:'#46565a',plants:['#d58a52','#a7a06d','#7c9b82'],density:.18},
 open_ocean:{rock:'#455b57',light:'#84958a',plants:['#8caf85','#a9b987'],density:.08},
 mangrove_forest:{rock:'#665c46',light:'#a49a70',plants:['#4f9361','#79ad68','#b5bd72'],density:.92},
 estuary:{rock:'#77745a',light:'#b5a77b',plants:['#75aa75','#9bbf7c','#c0b66d'],density:.72},
 polar_shelf:{rock:'#667d82',light:'#b5d0cf',plants:['#79a7a1','#b1c7ad'],density:.12},
 seamount:{rock:'#3a4a52',light:'#71868a',plants:['#a78b77','#8d9c8d','#7b88a9'],density:.35},
 abyssal_plain:{rock:'#17242d',light:'#35434a',plants:['#657b8a','#766f98'],density:.04}
};
const hash=n=>{let x=(n|0)^0x9e3779b9;x=Math.imul(x^(x>>>16),0x21f0aaad);x=Math.imul(x^(x>>>15),0x735a2d97);return (x^(x>>>15))>>>0};
const pick=(a,n)=>a[hash(n)%a.length];
function draw(ctx,o){
 const {ox,oy,sx,sy,width,height,worldWidth,worldHeight,bathymetry,time,zoom,habitatMap,defaultHabitat}=o;
 if(!sx||!sy||!bathymetry)return;
 const tiles=habitatMap?.tiles||[],cell=Number(habitatMap?.cell_size)||0,tileIndex=new Map(tiles.map(q=>[q.x+','+q.y,q.habitat]));
 const habitatAt=x=>{if(cell&&tileIndex.size){const tx=Math.max(0,Math.floor(x/cell)),ty=Math.max(0,Math.floor((worldHeight*.91)/cell));return tileIndex.get(tx+','+ty)||defaultHabitat||'coral_reef'}return defaultHabitat||'coral_reef'};
 const left=Math.max(0,(0-ox)/sx),right=Math.min(worldWidth,(width-ox)/sx);
 const stride=Math.max(worldWidth/100,900);
 for(let x=Math.floor(left/stride)*stride;x<right;x+=stride){
  const h=habitatAt(x),p=palettes[h]||palettes.coral_reef,seed=Math.floor(x/stride),r=hash(seed),base=bathymetry(x),px=ox+x*sx,py=oy+base*sy;
  const scale=Math.max(.55,Math.min(1.8,zoom)),cluster=(r%1000)/1000;
  if(h==='hydrothermal_vent'||h==='deep_sea'||h==='abyssal_plain'){
   ctx.save();ctx.globalAlpha=h==='hydrothermal_vent'?.72:.34;ctx.fillStyle=p.rock;
   ctx.beginPath();ctx.moveTo(px-42*scale,py);ctx.lineTo(px-25*scale,py-18*scale);ctx.lineTo(px-12*scale,py-52*scale);ctx.lineTo(px+1*scale,py-58*scale);ctx.lineTo(px+12*scale,py-23*scale);ctx.lineTo(px+36*scale,py);ctx.closePath();ctx.fill();
   if(h==='hydrothermal_vent'){ctx.strokeStyle='rgba(228,142,83,.7)';ctx.lineWidth=2*scale;ctx.beginPath();ctx.moveTo(px,py-55*scale);ctx.quadraticCurveTo(px+10*scale,py-82*scale+Math.sin(time+seed)*4,px+18*scale,py-102*scale);ctx.stroke();ctx.fillStyle='rgba(205,157,111,.22)';for(let q=0;q<4;q++){const bx=px+Math.sin(time*.5+seed+q)*9*scale,by=py-105*scale-q*16*scale;ctx.beginPath();ctx.arc(bx,by,4*scale+q,0,Math.PI*2);ctx.fill()}}
   if(h==='deep_sea'||h==='abyssal_plain'){ctx.fillStyle='rgba(118,150,191,.55)';for(let q=0;q<5;q++){const dx=(hash(seed+q)%90-45)*scale,dy=(hash(seed+q+77)%20-30)*scale;ctx.beginPath();ctx.arc(px+dx,py+dy,1.1*scale,0,Math.PI*2);ctx.fill()}}
   ctx.restore();continue;
  }
  const mound=10+cluster*32;
  ctx.save();const hasRock=window.NexusSprites?.drawProp?.(ctx,'rock',px,py,78*scale,42*scale,time,seed);ctx.fillStyle=p.rock;ctx.globalAlpha=hasRock?0.18:.75;ctx.beginPath();ctx.moveTo(px-48*scale,py);ctx.quadraticCurveTo(px-35*scale,py-mound*scale,px-10*scale,py-mound*.72*scale);ctx.quadraticCurveTo(px+16*scale,py-mound*1.35*scale,px+48*scale,py);ctx.closePath();ctx.fill();
  ctx.globalAlpha=.22;ctx.strokeStyle=p.light;ctx.lineWidth=2*scale;ctx.beginPath();ctx.moveTo(px-22*scale,py-8*scale);ctx.quadraticCurveTo(px,py-mound*scale,px+24*scale,py-7*scale);ctx.stroke();ctx.restore();
  const count=Math.round(p.density*(h==='coral_reef'?5:4));
  for(let n=0;n<count;n++){
   const id=seed*13+n*29,dx=(hash(id)%86-43)*scale,plantX=px+dx,plantY=py-(hash(id+4)%12)*scale;
   const tall=(18+(hash(id+8)%50))*scale,colour=pick(p.plants,id);
   ctx.save();ctx.translate(plantX,plantY);ctx.strokeStyle=colour;ctx.fillStyle=colour;ctx.lineWidth=(1.2+(hash(id+5)%3)*.45)*scale;ctx.lineCap='round';
   if(h==='coral_reef'){
    const arms=3+hash(id+9)%4;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-tall*.45);
    for(let a=0;a<arms;a++){const side=a%2?1:-1,yy=-tall*(.24+a/arms*.65);ctx.moveTo(0,yy);ctx.quadraticCurveTo(side*tall*.18,yy-tall*.12,side*tall*.28,yy-tall*.25);ctx.moveTo(0,yy-tall*.12);ctx.lineTo(-side*tall*.12,yy-tall*.27)}ctx.stroke();
    ctx.globalAlpha=.75;for(let q=0;q<3;q++){ctx.beginPath();ctx.arc((q-1)*tall*.13,-tall*(.55+q*.11),Math.max(1.2,2.4*scale),0,Math.PI*2);ctx.fill()}
   }else if(h==='kelp_forest'||h==='mangrove_forest'||h==='estuary'){
    const blades=h==='mangrove_forest'?4:3;for(let b=0;b<blades;b++){const sway=Math.sin(time*.8+id+b)*tall*.11;ctx.beginPath();ctx.moveTo((b-1)*2*scale,0);ctx.quadraticCurveTo((b-1)*tall*.09+sway,-tall*.5,(b-1)*tall*.12+sway,-tall);ctx.stroke()}
   }else if(h==='seagrass'||h==='sandy_seabed'){
    for(let b=0;b<5;b++){const sway=Math.sin(time+id+b)*tall*.08;ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo((b-2)*tall*.08+sway,-tall*.55,(b-2)*tall*.12+sway,-tall*(.65+(b%2)*.25));ctx.stroke()}
   }else{
    ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-tall*.65);ctx.stroke();ctx.beginPath();ctx.ellipse(0,-tall*.7,3*scale,7*scale,0,0,Math.PI*2);ctx.fill()
   }
   ctx.restore();
  }
  if(h==='coral_reef'||h==='hydrothermal_vent'){for(let bubble=0;bubble<2;bubble++)window.NexusSprites?.drawProp?.(ctx,'bubble',px+(bubble?18:-16)*scale,py-(34+bubble*21+Math.sin(time+seed+bubble)*4)*scale,5*scale,5*scale,time,seed+bubble)}
  if(h==='sandy_seabed'||h==='seagrass'||h==='estuary'){ctx.save();ctx.strokeStyle='rgba(239,220,164,.16)';ctx.lineWidth=1*scale;for(let q=0;q<3;q++){const yy=py-(q+1)*4*scale;ctx.beginPath();ctx.moveTo(px-35*scale,yy);ctx.quadraticCurveTo(px,yy-3*scale,px+35*scale,yy);ctx.stroke()}ctx.restore()}
 }
}
window.NexusBiomeRenderer={draw,palettes};
})();