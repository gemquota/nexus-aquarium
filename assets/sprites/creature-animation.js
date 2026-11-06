/* Species-specific articulated creature animation for the NEXUS side-view renderer.
 * Appendages are drawn behind the painted turnaround body. Phase is deterministic per
 * organism and advances from simulation time and swim speed, not frame count. */
(()=>{'use strict';
const TAU=Math.PI*2;
const PROFILES={
 great_white_shark:{type:'shark',rate:5.1,tail:1.0,bodyFlex:.055,pectoral:.22,dorsal:.18},
 hammerhead_shark:{type:'shark',rate:5.4,tail:1.0,bodyFlex:.06,pectoral:.24,dorsal:.16},
 whale_shark:{type:'shark',rate:2.7,tail:.72,bodyFlex:.035,pectoral:.18,dorsal:.12},
 humpback_whale:{type:'whale',rate:1.8,tail:1.0,bodyFlex:.035,pectoral:.48},
 orca:{type:'whale',rate:3.0,tail:.9,bodyFlex:.045,pectoral:.2},
 bottlenose_dolphin:{type:'dolphin',rate:4.5,tail:.9,bodyFlex:.075,pectoral:.18},
 harbor_seal:{type:'pinniped',rate:3.4,tail:.4,bodyFlex:.07,flipper:.32},
 california_sea_lion:{type:'pinniped',rate:4.0,tail:.45,bodyFlex:.075,flipper:.42},
 west_indian_manatee:{type:'manatee',rate:1.35,tail:.22,bodyFlex:.025,flipper:.13},
 ocean_sunfish:{type:'sunfish',rate:2.0,tail:.12,bodyFlex:.015,fin:.5},
 pacific_seahorse:{type:'seahorse',rate:8.5,tail:.12,bodyFlex:.025,fin:.6},
 moon_jellyfish:{type:'jelly',rate:1.15,tail:.0,bodyFlex:.0},
 green_sea_turtle:{type:'turtle',rate:2.6,tail:.08,bodyFlex:.018,flipper:.52},
 clownfish:{type:'fish',rate:7.0,tail:1,bodyFlex:.045,pectoral:.3,fin:.2},
 yellow_tang:{type:'fish',rate:6.5,tail:1,bodyFlex:.04,pectoral:.32,fin:.18},
 angelfish:{type:'fish',rate:5.2,tail:.8,bodyFlex:.035,pectoral:.28,fin:.28}
};
const ALIASES={shark:'great_white_shark',whale:'humpback_whale',dolphin:'bottlenose_dolphin',seal:'harbor_seal',sea_lion:'california_sea_lion',manatee:'west_indian_manatee',sunfish:'ocean_sunfish',seahorse:'pacific_seahorse',jellyfish:'moon_jellyfish',turtle:'green_sea_turtle',sea_turtle:'green_sea_turtle',clown_fish:'clownfish',tang:'yellow_tang'};
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_|_$/g,'');
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function phaseFor(o,time,rate){
 const id=Number(o.id)||0, speed=Math.hypot(Number(o.vx)||0,Number(o.vy)||0);
 const speedFactor=.28+clamp(speed/.35,0,1.4)*.72;
 return (Number(time)||0)*rate*speedFactor+(id*2.399963229728653);
}
function palette(type){
 if(type==='shark')return ['#667f86','#b8c9c5','#203b45'];
 if(type==='whale'||type==='dolphin')return ['#426d83','#9ab9c3','#1e3948'];
 if(type==='pinniped'||type==='manatee')return ['#708c8c','#b1c4b9','#29434a'];
 if(type==='jelly')return ['#bd8be6','#e4c8f1','#74539c'];
 if(type==='turtle')return ['#568e71','#b4c98d','#294c43'];
 if(type==='seahorse')return ['#d8a34e','#f1d08a','#72502e'];
 if(type==='sunfish')return ['#718b9b','#c3d0ca','#334c5a'];
 return ['#4b9b91','#b9d9c2','#24514d'];
}
function shape(ctx,points,fill,stroke,line){
 ctx.beginPath();ctx.moveTo(points[0][0],points[0][1]);
 for(let i=1;i<points.length;i++)ctx.lineTo(points[i][0],points[i][1]);
 ctx.closePath();ctx.fillStyle=fill;ctx.fill();
 if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=line||.025;ctx.stroke()}
}
function draw(ctx,o,x,y,w,h,time,opts={}){
 const species=norm(o.species),name=ALIASES[species]||species,p=PROFILES[name];
 if(!p)return false;
 const [top,belly,outline]=palette(p.type),speed=clamp(Math.hypot(Number(o.vx)||0,Number(o.vy)||0)/.35,0,1.4);
 const phase=phaseFor(o,time,p.rate),wave=Math.sin(phase),slow=Math.sin(phase*.5);
 const flip=Boolean(opts.flip),view=opts.view||'side';
 const horizontal=flip?-1:1;
 ctx.save();ctx.translate(x,y);ctx.scale(horizontal,1);
 // Rig space is normalised to the rendered body dimensions. All moving parts pivot
 // around fixed attachment points, so no per-frame allocations or DOM animation exist.
 ctx.scale(w,h);ctx.lineJoin='round';ctx.lineCap='round';
 const stroke=outline,line=.022;
 const tailAngle=wave*(p.tail||0)*.42;
 const finPulse=Math.sin(phase+1.2),flap=Math.sin(phase+Math.PI*.5);
 const isFront=view==='front'||view==='rear';
 if(p.type==='jelly'){
   const contract=.86+.14*Math.sin(phase*.5);
   ctx.save();ctx.scale(contract,1/contract);
   for(let i=0;i<7;i++){
     const u=(i-3)/3, sway=Math.sin(phase*.34+i*.8)*(.045+Math.abs(u)*.025);
     ctx.beginPath();ctx.moveTo(u*.18,.18);
     ctx.bezierCurveTo(u*.22+sway,.36,u*.38-sway,.58,u*.25+Math.sin(phase*.6+i)*.04,.82);
     ctx.strokeStyle=outline;ctx.lineWidth=.035;ctx.stroke();
     ctx.beginPath();ctx.moveTo(u*.18,.18);ctx.bezierCurveTo(u*.22+sway,.36,u*.38-sway,.58,u*.25+Math.sin(phase*.6+i)*.04,.82);
     ctx.strokeStyle=top;ctx.lineWidth=.018;ctx.stroke();
   }
   ctx.restore();
 }else if(p.type==='turtle'){
   // Foreflippers sweep in opposition; hind flippers stabilise with a smaller phase.
   for(const side of [-1,1]){
     const a=side*flap*(p.flipper||.4)*.32;
     ctx.save();ctx.translate(side*.28,.08);ctx.rotate(a);
     shape(ctx,[[0,0],[side*.08,.04],[side*.48,.18],[side*.58,.11],[side*.42,-.03],[side*.12,-.12]],top,stroke,line);
     ctx.restore();
     ctx.save();ctx.translate(side*-.34,.12);ctx.rotate(-a*.32);
     shape(ctx,[[0,0],[side*.12,.03],[side*.27,.13],[side*.3,.08],[side*.13,-.04]],belly,stroke,line*.8);
     ctx.restore();
   }
   ctx.save();ctx.translate(-.48,.03);ctx.rotate(tailAngle*.25);
   shape(ctx,[[0,0],[-.16,-.045],[-.23,0],[-.16,.045]],top,stroke,line*.8);ctx.restore();
 }else if(p.type==='seahorse'){
   // Fin flutter and curled prehensile tail are independent of translation.
   ctx.save();ctx.translate(-.34,.22);ctx.rotate(Math.sin(phase*.22)*.09);
   ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(-.23,.16,-.34,.38,-.18,.42);
   ctx.bezierCurveTo(-.04,.46,.02,.31,-.12,.29);ctx.strokeStyle=top;ctx.lineWidth=.075;ctx.stroke();ctx.restore();
   ctx.save();ctx.translate(.02,-.04);ctx.rotate(finPulse*(p.fin||.5)*.13);
   shape(ctx,[[0,0],[.08,-.14],[.18,-.2],[.15,-.08],[.09,.02]],top,stroke,line*.8);ctx.restore();
 }else if(p.type==='sunfish'){
   // Tall dorsal/anal fins undulate like a paired oscillating foil.
   for(const side of [-1,1]){
     ctx.save();ctx.translate(-side*.04,side*.0);ctx.rotate(side*finPulse*(p.fin||.4)*.08);
     shape(ctx,[[-.25,side*.05],[-.12,side*.22],[.08,side*.31],[.28,side*.18],[.16,side*.04]],top,stroke,line);ctx.restore();
   }
   ctx.save();ctx.translate(-.47,0);ctx.rotate(tailAngle*.18);
   shape(ctx,[[0,0],[-.16,-.2],[-.22,0],[-.16,.2]],top,stroke,line);ctx.restore();
 }else{
   // Caudal peduncle and lunate/fan tail. The tail stroke is the primary thrust source.
   ctx.save();ctx.translate(-.47,0);ctx.rotate(tailAngle);
   if(p.type==='whale'||p.type==='dolphin'){
     shape(ctx,[[0,0],[-.12,-.025],[-.23,-.23],[-.43,-.3],[-.36,-.06],[-.36,.06],[-.43,.3],[-.23,.23],[-.12,.025]],top,stroke,line);
     if(p.type==='whale'){
       ctx.beginPath();ctx.moveTo(-.2,0);ctx.quadraticCurveTo(-.39,-.1,-.43,-.3);ctx.moveTo(-.2,0);ctx.quadraticCurveTo(-.39,.1,-.43,.3);ctx.strokeStyle=belly;ctx.lineWidth=.012;ctx.stroke();
     }
   }else{
     shape(ctx,[[0,0],[-.1,-.035],[-.29,-.24],[-.38,-.18],[-.34,0],[-.38,.18],[-.29,.24],[-.1,.035]],top,stroke,line);
   }
   ctx.restore();
   if(p.type==='whale'||p.type==='dolphin'){
     for(const side of [-1,1]){
       ctx.save();ctx.translate(.08,side*.105);ctx.rotate(side*flap*(p.pectoral||.2)*.2);
       const reach=p.type==='whale'?.48:.3;
       shape(ctx,[[0,0],[.12,side*.025],[reach,side*.18],[reach*.88,side*.22],[.1,side*.095]],top,stroke,line);
       ctx.restore();
     }
   }
   if(p.type==='shark'||p.type==='fish'){
     // Dorsal fin rocks slightly with the travelling body wave.
     ctx.save();ctx.translate(-.05,-.16);ctx.rotate(-wave*(p.dorsal||p.fin||.15)*.12);
     shape(ctx,[[-.16,.12],[-.06,-.19],[.08,-.12],[.16,.12]],top,stroke,line);ctx.restore();
     // Paired pectorals are offset in phase to suggest near/far fin depth.
     for(const side of [-1,1]){
       ctx.save();ctx.translate(.12,side*.11);ctx.rotate(side*(flap*(p.pectoral||.2)*.24));
       shape(ctx,[[0,0],[.12,side*.04],[.42,side*.25],[.29,side*.12],[.08,-side*.035]],side<0?belly:top,stroke,line*.8);ctx.restore();
     }
     if(p.type==='fish'){
       ctx.save();ctx.translate(-.06,.12);ctx.rotate(wave*(p.fin||.2)*.22);
       shape(ctx,[[-.1,0],[.02,.16],[.18,.19],[.1,.03]],top,stroke,line*.7);ctx.restore();
     }
   }else if(p.type==='pinniped'||p.type==='manatee'){
     for(const side of [-1,1]){
       ctx.save();ctx.translate(.1,side*.13);ctx.rotate(side*flap*(p.flipper||.2)*.28);
       shape(ctx,[[0,0],[.14,side*.02],[.43,side*.17],[.37,side*.24],[.12,side*.11]],top,stroke,line);ctx.restore();
     }
   }
 }
 // Subtle travelling body wave is applied to the sprite by the caller. This layer
 // only contributes articulated appendages and their motion.
 ctx.restore();
 const pulse=p.type==='jelly'?Math.sin(phase*.5):0;
 return {phase,speed,bodyFlex:(p.bodyFlex||0)*wave,bodyScaleX:p.type==='jelly'?1-.07*pulse:1,bodyScaleY:p.type==='jelly'?1+.09*pulse:1,tailAngle,finPulse};
}
function profile(species){const n=norm(species),key=ALIASES[n]||n,p=PROFILES[key];return p?{...p}:null}
window.NexusCreatureAnimation={draw,profile,species:Object.keys(PROFILES),version:1};
})();