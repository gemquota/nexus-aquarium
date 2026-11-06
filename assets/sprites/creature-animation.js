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
function clipFor(o,time){
 const raw=norm(o.animation_state||o.behaviour||o.behavior||o.state||'swim');
 const aliases={turn:'turning',turning:'turning',feed:'feeding',feeding:'feeding',hunt:'hunting',hunting:'hunting',attack:'hunting',death:'dying',dead:'dying',dying:'dying',swim:'swim',idle:'idle'};
 const name=aliases[raw]||'swim',duration={turning:.9,feeding:1.25,hunting:1.1,dying:1.8,idle:2.8,swim:1}[name];
 const elapsed=Math.max(0,Number(o.animation_elapsed??o.state_elapsed??o.behaviour_elapsed??(Number.isFinite(Number(o.animation_started_at))?time-Number(o.animation_started_at):time%duration))||0);
 const progress=name==='swim'||name==='idle'?(time%duration)/duration:clamp(elapsed/duration,0,1);
 return {name,progress,active:name!=='swim'&&name!=='idle'};
}
function jointedLimb(ctx,root,angle,length,width,fill,outline,far=false){
 ctx.save();ctx.translate(root[0],root[1]);ctx.rotate(angle);
 ctx.globalAlpha=far?.56:1;
 ctx.strokeStyle=outline;ctx.fillStyle=fill;ctx.lineWidth=.022;
 ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(length*.34,-width*.1,length*.68,width*.08);
 ctx.stroke();
 shape(ctx,[[0,-width*.42],[length*.24,-width*.55],[length*.72,-width*.28],[length,width*.04],[length*.82,width*.38],[length*.28,width*.31]],fill,outline,.018);
 // Two visible joints make the pivot hierarchy inspectable and give the limb a hinge.
 ctx.beginPath();ctx.arc(0,0,width*.12,0,TAU);ctx.fillStyle=outline;ctx.fill();
 ctx.beginPath();ctx.arc(length*.27,0,width*.075,0,TAU);ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=outline;ctx.lineWidth=.012;ctx.stroke();
 ctx.restore();
}
function draw(ctx,o,x,y,w,h,time,opts={}){
 const species=norm(o.species),name=ALIASES[species]||species,p=PROFILES[name];
 if(!p)return false;
 const [top,belly,outline]=palette(p.type),speed=clamp(Math.hypot(Number(o.vx)||0,Number(o.vy)||0)/.35,0,1.4);
 const phase=phaseFor(o,time,p.rate),wave=Math.sin(phase),flap=Math.sin(phase+Math.PI*.5);
 const flip=Boolean(opts.flip),view=opts.view||'side',layer=opts.layer||'all';
 const clip=clipFor(o,time),u=clip.progress;
 const envelope=clip.name==='turning'?Math.sin(u*Math.PI):clip.name==='feeding'?Math.sin(u*Math.PI):clip.name==='hunting'?Math.sin(u*Math.PI):clip.name==='dying'?u:0;
 const turn=clip.name==='turning'?Math.sin(u*Math.PI*2)*.48:0;
 const lunge=clip.name==='hunting'?Math.sin(u*Math.PI)*.13:0;
 const jaw=clip.name==='feeding'?Math.sin(u*Math.PI)*.18:clip.name==='hunting'?Math.sin(u*Math.PI)*.1:0;
 const deathRoll=clip.name==='dying'?u*.9:0;
 const stroke=outline,line=.022;
 const tailAngle=wave*(p.tail||0)*(.42+speed*.14)+(clip.name==='hunting'?envelope*.32:0)+(clip.name==='dying'?-.12*envelope:0);
 const finPulse=Math.sin(phase+1.2),slow=flap;
 const horizontal=flip?-1:1;
 const far=layer==='far'||layer==='all',near=layer==='near'||layer==='all';
 ctx.save();ctx.translate(x,y);ctx.scale(horizontal,1);ctx.scale(w,h);
 ctx.lineJoin='round';ctx.lineCap='round';
 // Far-side appendages are intentionally lower contrast and are rendered before
 // the body. Near-side appendages are rendered after the body by sprite-runtime.
 if(far){
   if(p.type==='turtle'){
     jointedLimb(ctx,[-.32,.09],-.24+flap*.13,.34,.19,belly,stroke,true);
     jointedLimb(ctx,[.22,.09],-.2-flap*.13,.38,.22,belly,stroke,true);
   }else if(p.type==='shark'||p.type==='fish'){
     jointedLimb(ctx,[.08,.09],.28+flap*(p.pectoral||.2)*.12,.31,.12,belly,stroke,true);
   }else if(p.type==='whale'||p.type==='dolphin'||p.type==='pinniped'||p.type==='manatee'){
     jointedLimb(ctx,[.08,.10],.32+flap*(p.flipper||p.pectoral||.2)*.12,.34,.16,belly,stroke,true);
   }else if(p.type==='sunfish'){
     jointedLimb(ctx,[-.02,-.02],-.2+finPulse*.06,.38,.14,belly,stroke,true);
   }
 }
 // Rear/caudal appendage: two articulated links, with the distal section lagging.
 if(far&&p.type!=='jelly'&&p.type!=='seahorse'){
   ctx.save();ctx.translate(-.46,0);ctx.rotate(tailAngle);
   const tailFill=top;
   if(p.type==='whale'||p.type==='dolphin'){
     shape(ctx,[[0,0],[-.12,-.025],[-.24,-.22],[-.43,-.29],[-.36,-.05],[-.36,.05],[-.43,.29],[-.24,.22],[-.12,.025]],tailFill,stroke,line);
     ctx.translate(-.18,0);ctx.rotate(tailAngle*.22);
     ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(-.12,-.08,-.25,-.27);ctx.moveTo(0,0);ctx.quadraticCurveTo(-.12,.08,-.25,.27);ctx.strokeStyle=belly;ctx.lineWidth=.018;ctx.stroke();
   }else{
     shape(ctx,[[0,0],[-.1,-.035],[-.29,-.24],[-.38,-.18],[-.34,0],[-.38,.18],[-.29,.24],[-.1,.035]],tailFill,stroke,line);
   }
   ctx.restore();
 }
 if(p.type==='jelly'){
   const pulse=Math.sin(phase*.5),contract=1-.12*pulse;
   ctx.save();ctx.translate(0,-.1);ctx.scale(contract,1+.08*pulse);
   for(let i=0;i<8;i++){
     if(layer!=='all'&&((i<4&&!far)||(i>=4&&!near)))continue;
     const q=(i-3.5)/3.5,sway=Math.sin(phase*.32+i*.8)*(.04+Math.abs(q)*.025);
     ctx.beginPath();ctx.moveTo(q*.2,.2);ctx.bezierCurveTo(q*.23+sway,.38,q*.36-sway,.61,q*.25+Math.sin(phase*.6+i)*.035,.88);
     ctx.strokeStyle=stroke;ctx.lineWidth=.035;ctx.stroke();
     ctx.beginPath();ctx.moveTo(q*.2,.2);ctx.bezierCurveTo(q*.23+sway,.38,q*.36-sway,.61,q*.25+Math.sin(phase*.6+i)*.035,.88);
     ctx.strokeStyle=top;ctx.lineWidth=.017;ctx.stroke();
   }
   ctx.restore();
 }
 if(far&&p.type==='seahorse'){
   ctx.save();ctx.translate(-.3,.2);ctx.rotate(Math.sin(phase*.22)*.08);
   ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(-.2,.14,-.34,.38,-.18,.42);ctx.bezierCurveTo(-.04,.46,.02,.31,-.12,.29);
   ctx.strokeStyle=stroke;ctx.lineWidth=.105;ctx.stroke();ctx.strokeStyle=top;ctx.lineWidth=.07;ctx.stroke();ctx.restore();
 }
 // Near-side appendage layer. The pivots are fixed to the body rig and each limb
 // has a proximal hinge plus a distal articulation.
 if(near){
   if(p.type==='turtle'){
     jointedLimb(ctx,[-.28,.08],.16+flap*(p.flipper||.5)*.34,.5,.23,top,stroke,false);
     jointedLimb(ctx,[.23,.08],.12-flap*(p.flipper||.5)*.25,.4,.19,top,stroke,false);
     jointedLimb(ctx,[-.48,.02],tailAngle*.25,.2,.09,top,stroke,false);
   }else if(p.type==='shark'||p.type==='fish'){
     jointedLimb(ctx,[.12,.1],-.18+flap*(p.pectoral||.2)*.42,.43,.17,top,stroke,false);
     ctx.save();ctx.translate(-.05,-.16);ctx.rotate(-wave*(p.dorsal||p.fin||.15)*.16);
     shape(ctx,[[-.16,.12],[-.06,-.19],[.08,-.12],[.16,.12]],top,stroke,line);ctx.restore();
     if(p.type==='fish'){
       jointedLimb(ctx,[-.06,.12],.18+wave*(p.fin||.2)*.24,.2,.1,top,stroke,false);
     }
   }else if(p.type==='whale'||p.type==='dolphin'){
     jointedLimb(ctx,[.08,.11],-.12+flap*(p.pectoral||.2)*.35,p.type==='whale'?.48:.32,.2,top,stroke,false);
   }else if(p.type==='pinniped'||p.type==='manatee'){
     jointedLimb(ctx,[.08,.12],-.1+flap*(p.flipper||.2)*.38,.44,.22,top,stroke,false);
   }else if(p.type==='sunfish'){
     jointedLimb(ctx,[-.02,-.02],-.24+finPulse*.1,.43,.17,top,stroke,false);
     jointedLimb(ctx,[-.02,.02],.24-finPulse*.1,.4,.17,top,stroke,false);
   }else if(p.type==='seahorse'){
     ctx.save();ctx.translate(.02,-.04);ctx.rotate(finPulse*(p.fin||.5)*.15);
     shape(ctx,[[0,0],[.08,-.14],[.18,-.2],[.15,-.08],[.09,.02]],top,stroke,line*.8);ctx.restore();
   }
   // Feeding/hunting jaw cue, with an open-close arc attached to the head.
   if(jaw>0){
     ctx.save();ctx.translate(.42,.025);ctx.rotate(jaw);
     ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(.1,.1,.22,.06);
     ctx.strokeStyle=stroke;ctx.lineWidth=.035;ctx.stroke();ctx.restore();
   }
 }
 ctx.restore();
 const pulse=p.type==='jelly'?Math.sin(phase*.5):0;
 const death=clip.name==='dying'?u:0;
 return {phase,speed,bodyFlex:(p.bodyFlex||0)*wave*(1+speed*.4)+turn*.08+lunge*.18,
  bodyScaleX:p.type==='jelly'?1-.07*pulse:1-.08*death,
  bodyScaleY:p.type==='jelly'?1+.09*pulse:1-.05*death,
  tailAngle,finPulse,clip:clip.name,clipProgress:u,bodyRoll:deathRoll,bodyPitch:clip.name==='turning'?turn:0,
  bodyOpacity:clip.name==='dying'?1-.38*death:1};
}
function profile(species){const n=norm(species),key=ALIASES[n]||n,p=PROFILES[key];return p?{...p}:null}
window.NexusCreatureAnimation={draw,profile,species:Object.keys(PROFILES),version:1};
})();