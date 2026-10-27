// Test-only observation of reconstructed HTML. No runtime algorithms live here.
const engines=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const out=path.join(__dirname,'artifacts');
const engine=process.argv.includes('--webkit')?'webkit':'chromium';
(async()=>{
 const browser=await engines[engine].launch(engine==='chromium'?{args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']}:{});
 try{
 const context=await browser.newContext({viewport:{width:960,height:640},offline:engine==='chromium'});
 // WebKit's network-offline switch rejects file: navigation on this host.
 if(engine==='webkit')await context.route(/^https?:\/\//,route=>route.abort());
 const page=await context.newPage(),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>requests.push(r.url()));
 await page.addInitScript(()=>{
  window.realRAF=requestAnimationFrame.bind(window);
  window.requestAnimationFrame=fn=>{window.pendingFrame=fn;return 0;};
 });
 const target='file://'+path.resolve(process.argv[2]||out+'/planet.html');
 await page.goto(target);await page.waitForFunction('typeof draw=="function"',null,{polling:100});
 const diagnostic=await page.evaluate(()=>{
  const vertex=g.getAttachedShaders(p).find(s=>g.getShaderParameter(s,g.SHADER_TYPE)===g.VERTEX_SHADER);
  const fragment=g.getAttachedShaders(p).find(s=>g.getShaderParameter(s,g.SHADER_TYPE)===g.FRAGMENT_SHADER);
  function compile(source){
   const program=g.createProgram(),s=g.createShader(g.FRAGMENT_SHADER);
   g.shaderSource(s,source);g.compileShader(s);
   if(!g.getShaderParameter(s,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(s));
   g.attachShader(program,vertex);g.attachShader(program,s);g.bindAttribLocation(program,0,'a');g.linkProgram(program);
   if(!g.getProgramParameter(program,g.LINK_STATUS))throw Error(g.getProgramInfoLog(program));
   return program;
  }
  const source=g.getShaderSource(fragment);
  // Remove the shell, shadow and composite block ONLY, retaining actual ground rendering.
  const groundSource=source.replace(/vec3 shell=[\s\S]*?(?=gl_FragColor=)/,'');
  if(groundSource===source||groundSource.includes('col*=1.-.23'))throw Error('ground extraction failed');
  const frozenGround=groundSource.replace('sunDirection(V.w)','sunDirection(0.)');
  const noGlint=frozenGround.replace(/col\+=vec3\(1\.,\.8,\.5\)[^;]+;/,'');
  const noFlash=source.replace(/col\+=vec3\(\.3,\.4,\.7\)[^;]+;/,'');
  if(noFlash===source||noGlint===frozenGround)throw Error('effect extraction failed');
  window.obs={app:p,source,compile,ground:compile(frozenGround),groundActual:compile(groundSource),noGlint:compile(noGlint),noFlash:compile(noFlash)};
  const debug=g.getExtension('WEBGL_debug_renderer_info');
  return {shaders:g.getAttachedShaders(p).map(s=>({ok:g.getShaderParameter(s,g.COMPILE_STATUS),log:g.getShaderInfoLog(s)})),linked:g.getProgramParameter(p,g.LINK_STATUS),renderer:debug?g.getParameter(debug.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER)};
 });
 assert(diagnostic.linked&&diagnostic.shaders.every(s=>s.ok));
 async function render(time,ground=false){
  return await page.evaluate(async({time,ground})=>{
   p=ground==='actual'?obs.groundActual:ground==='no-glint'?obs.noGlint:ground==='no-flash'?obs.noFlash:ground?obs.ground:obs.app;g.useProgram(p);
   const view=[...draw(time)],bytes=new Uint8Array(g.drawingBufferWidth*g.drawingBufferHeight*4);
   g.readPixels(0,0,g.drawingBufferWidth,g.drawingBufferHeight,g.RGBA,g.UNSIGNED_BYTE,bytes);
   const digest=await crypto.subtle.digest('SHA-256',bytes);
   const hash=Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,'0')).join('');
   let luminance=0,count=0;const w=g.drawingBufferWidth,h=g.drawingBufferHeight;
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const qx=(2*x+1-w)/h*view[2],qy=(2*y+1-h)/h*view[2];
    if(qx*qx+qy*qy<.81){const i=(y*w+x)*4;luminance+=.2126*bytes[i]+.7152*bytes[i+1]+.0722*bytes[i+2];count++;}
   }
   p=obs.app;g.useProgram(p);return {view,hash,mean_luminance:luminance/count};
  },{time,ground});
 }
 const initial=await render(0),returned=await render(40);
 assert.deepStrictEqual(initial.view,returned.view);assert.notEqual(initial.hash,returned.hash,'weather should have evolved');
 const groundInitial=await render(0,true),groundReturn=await render(40,true);
 assert.equal(groundInitial.hash,groundReturn.hash,'exact terrain return with solar time held fixed');
 const solarReturn=await render(40,'actual');assert.notEqual(groundInitial.hash,solarReturn.hash,'solar illumination must advance');
 if(engine==='chromium')await page.screenshot({path:out+'/ground-A-return.png'});
 const captures={};
 for(const [name,t]of [['A',0],['globe',10],['B',20],['A-return',40],['orbit-start',48],['orbit',60],['orbit-later',75],['terminator',80],['night',100],['dawn',120]]){
  captures[name]={time:t,...await render(t)};
  if(engine==='chromium')await page.screenshot({path:out+'/'+name+'.png'});
 }
 const choreography=await page.evaluate(()=>{
  const delta=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i]))),dt=.001;
  const zero=[5,10,15,20,25,30,35,40,43,48].map(t=>({time:t,left:delta(camera(t-dt),camera(t))/dt,right:delta(camera(t+dt),camera(t))/dt}));
  const speed=t=>(camera(t+dt)[0]-camera(t)[0])/dt;
  return {states:[0,5,10,15,20,25,30,35,40,43,48,52,60,70,80,160].map(time=>({time,view:camera(time)})),zero,
   holdA:delta(camera(0),camera(4)),holdB:delta(camera(20),camera(24)),returnHold:delta(camera(40),camera(42.9)),
   rampLeft:speed(52-dt),rampRight:speed(52),steady:[60,70,80,160].map(t=>({time:t,speed:speed(t),z:camera(t)[2]}))};
 });
 assert.equal(choreography.holdA,0);assert.equal(choreography.holdB,0);assert.equal(choreography.returnHold,0);
 assert(choreography.zero.every(x=>Math.max(x.left,x.right)<1e-5));
 assert(Math.abs(choreography.rampLeft-choreography.rampRight)<1e-6);
 assert(choreography.steady.every(x=>Math.abs(x.speed-.08)<1e-8&&Math.abs(x.z-1.2)<1e-12));
 // Probe the actual transported terrain/cloud functions, changing only output encoding.
 const field=await page.evaluate(()=>{
  const prefix=obs.source.split('void main()')[0];
  const probes=[obs.compile(prefix+`uniform vec3 P;void main(){float v=floor(clamp(terrain(P)+.5,0.,1.)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`),
                obs.compile(prefix+`uniform vec3 P;void main(){float v=floor(clamp(cloud(P),0.,1.)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`),
                obs.compile(prefix+`uniform vec3 P;void main(){float v=floor((wind(P.y)*16.+.5)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`),
                obs.compile(prefix+`uniform vec3 P;void main(){float v=floor(N(P*3.+91.)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`),
                obs.compile(prefix+`uniform vec3 P;void main(){float v=floor(clamp(cloud(advect(P,-V.w)),0.,1.)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`),
                ...['x','y','z'].map(axis=>obs.compile(prefix+`uniform vec3 P;void main(){float v=floor((sunDirection(V.w).${axis}*.5+.5)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`)),
                obs.compile(prefix+`uniform vec3 P;void main(){float v=floor(flash(P)*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`)];
  function sample(point,weather=false,seed=1,zoom=.025,time=0,kind=+weather){
   const prog=probes[kind];g.useProgram(prog);g.viewport(0,0,1,1);
   const uniform=n=>g.getUniformLocation(prog,n);
   g.uniform3fv(uniform('P'),point);g.uniform2f(uniform('R'),960,640);
   g.uniform2f(uniform('S'),seed&65535,seed>>>16);g.uniform4f(uniform('V'),0,0,zoom,time);
   g.drawArrays(g.TRIANGLES,0,3);const bytes=new Uint8Array(4);g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,bytes);
   const value=(bytes[0]*256+bytes[1])/65535;return kind===0?value-.5:kind===2?(value-.5)/16:kind>=5&&kind<=7?2*value-1:value;
  }
  const point=(x,y)=>[Math.sin(x)*Math.cos(y),Math.sin(y),Math.cos(x)*Math.cos(y)];
  const coords=[[.4,.3],[2.2,-.45],[-1,.6],[0,0],[3,-1],[1,1.3],[0,Math.PI/2],[0,-Math.PI/2]];
  const points=coords.map(([x,y])=>point(x,y));
  const ground=points.map(v=>sample(v)),cloud=points.map(v=>sample(v,true));
  const groundTime=[0,20,40,80].map(t=>points.map(v=>sample(v,false,1,.025,t)));
  const groundReverse=points.slice().reverse().map(v=>sample(v)).reverse();
  const cloudReverse=points.slice().reverse().map(v=>sample(v,true)).reverse();
  const coarse=points.map(v=>sample(v,false,1,1.2)),fine=points.map(v=>sample(v,false,1,.006));
  const cloudCoarse=points.map(v=>sample(v,true,1,1.2)),cloudFine=points.map(v=>sample(v,true,1,.006));
  const seeds=[0,1,2,42,65536,4294967295].map(seed=>({seed,ground:points.map(v=>sample(v,false,seed)),cloud:points.map(v=>sample(v,true,seed))}));
  const weatherTimes=[0,.001,1,20,39.999,40,40.001,43,48,52,80].map(time=>({time,values:points.map(v=>sample(v,true,1,.025,time))}));
  const seam=[false,true].map(weather=>Math.abs(sample(point(-Math.PI,.2),weather)-sample(point(Math.PI,.2),weather)));
  const poles=[false,true].map(weather=>[-1,1].map(sign=>Math.max(...[-3,-1,0,1,3].map(x=>Math.abs(sample(point(x,sign*Math.PI/2),weather)-sample([0,sign,0],weather))))));
  const spatial=[false,true].map(weather=>coords.map(([x,y])=>Math.abs(sample(point(x+1e-6,y),weather)-sample(point(x,y),weather))));
  const windRates=[-1,-Math.SQRT1_2,0,Math.SQRT1_2,1].map(y=>({y,rate:sample([0,y,0],true,1,.025,0,2)}));
  const handoffs=points.map(v=>{
   const phase=sample(v,true,1,.025,0,3),time=12*(1-phase);
   return {time,before:sample(v,true,1,.025,time-.001),after:sample(v,true,1,.025,time+.001)};
  });
  const materialTimes=[0,3,12,40].map(time=>({time,values:points.map(v=>sample(v,true,1,.025,time,4))}));
  const purelyAdvected=cloud,evolved=materialTimes[3].values;
  const suns=[0,40,400].map(time=>({time,vector:[5,6,7].map(kind=>sample([0,0,0],true,1,.025,time,kind))}));
  const stormClocks=Array.from({length:120},(_,i)=>points.map(v=>sample(v,true,1,.025,i/5,8)));
  g.useProgram(obs.app);
  return {stormClocks,suns,coords,ground,cloud,groundTime,groundReverse,cloudReverse,coarse,fine,cloudCoarse,cloudFine,seeds,weatherTimes,seam,poles,spatial,purelyAdvected,evolved,windRates,handoffs,materialTimes};
 });
 assert.deepStrictEqual(field.ground,field.groundReverse);assert.deepStrictEqual(field.cloud,field.cloudReverse);
 assert(field.groundTime.every(values=>JSON.stringify(values)===JSON.stringify(field.ground)));
 for(const kind of ['ground','cloud'])assert.equal(new Set(field.seeds.map(x=>JSON.stringify(x[kind]))).size,6);
 assert(field.seam.every(x=>x<=2/65535));assert(field.poles.flat().every(x=>x<=2/65535));
 assert(field.spatial.flat().every(x=>x<.001));
 const maxDelta=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
 const coarseError=maxDelta(field.ground,field.coarse),fineReveal=maxDelta(field.ground,field.fine);
 assert(coarseError<.02&&fineReveal>1/65535);
 assert(maxDelta(field.cloud,field.weatherTimes[1].values)<.001);
 assert(maxDelta(field.weatherTimes[4].values,field.weatherTimes[6].values)<.001);
 const evolution=maxDelta(field.purelyAdvected,field.evolved);assert(evolution>.001,'formation/evolution beyond wind alone');
 assert(maxDelta(field.cloud,field.evolved)>.01);
 assert(field.windRates[0].rate<0&&field.windRates[1].rate>0&&field.windRates[2].rate<0&&field.windRates[3].rate>0&&field.windRates[4].rate<0);
 assert(Math.abs(field.windRates[0].rate-field.windRates[4].rate)<2/65535);
 assert(Math.abs(field.windRates[1].rate-field.windRates[3].rate)<2/65535);
 assert(field.handoffs.every(x=>Math.abs(x.before-x.after)<.001),'smooth cloud-generation handoff');
 assert(maxDelta(field.materialTimes[0].values,field.materialTimes[1].values)>.01,'visible evolution in three seconds, not advection alone');
 const seedRenders=[];
 for(const identity of field.seeds.map(x=>x.seed)){
  await page.evaluate(s=>planet(s,.4,.3,1.2),identity);
  const first=await render(37),second=await render(37);assert.equal(first.hash,second.hash);
  seedRenders.push({seed:identity,hash:first.hash});
 }
 assert.equal(new Set(seedRenders.map(x=>x.hash)).size,6);
 const locations=[];
 for(const [i,coord]of field.coords.entries()){
  await page.evaluate(([x,y])=>planet(1,x,y,.025),coord);const r=await render(17);
  locations.push({coordinate:coord,...r});if(engine==='chromium'&&i>=2)await page.screenshot({path:out+'/location-'+i+'.png'});
 }
 await page.evaluate(()=>planet(1,.4,.3,.025));assert.equal((await render(0)).hash,initial.hash);
 const fixedSun=field.suns[0].vector;
 assert(maxDelta(field.suns[0].vector,field.suns[1].vector)>.1,'terminator advances over the film');
 assert(Math.abs(field.suns[0].vector[1]-field.suns[2].vector[1])<2/65535);
 const sunView=[Math.atan2(fixedSun[0],fixedSun[2]),Math.atan2(fixedSun[1],Math.hypot(fixedSun[0],fixedSun[2]))];
 const lighting={sun_direction:fixedSun};
 await page.evaluate(([x,y])=>planet(1,x,y,1.2),sunView);
 lighting.dayGround=await render(0,true);lighting.dayClouds=await render(0);
 await page.evaluate(([x,y])=>planet(1,x+Math.PI,-y,1.2),sunView);
 lighting.nightGround=await render(0,true);lighting.nightClouds=await render(0);
 assert(lighting.dayGround.mean_luminance>8*lighting.nightGround.mean_luminance);
 assert(lighting.dayClouds.mean_luminance>8*lighting.nightClouds.mean_luminance);
 assert(lighting.nightClouds.mean_luminance<10,'night clouds must not remain white');
 const glints=[];
 for(const longitude of [-1,0,1,2,3,4]){
  await page.evaluate(x=>planet(1,x,.3,1.2),longitude);
  const on=await render(0,true),off=await render(0,'no-glint');
  glints.push({longitude,added_luminance:on.mean_luminance-off.mean_luminance});
 }
 assert(glints.some(x=>x.added_luminance>.01),'ocean reflection must contribute visibly');
 const flashes=[];
 await page.evaluate(()=>planet(1,4.4,.1,1.2));
 for(const time of [80,84.3,86,90,93.3,95,99.3,102,104.3,108,111.3,115,120]){
  const on=await render(time),off=await render(time,'no-flash');
  flashes.push({time,added_luminance:on.mean_luminance-off.mean_luminance});
 }
 assert(flashes.some(x=>x.added_luminance>0),'occasional night lightning must be visible');
 assert(Math.max(...flashes.map(x=>x.added_luminance))>2*Math.min(...flashes.map(x=>x.added_luminance)),'storm emission must vary with time');
 const peaks=field.coords.map((_,i)=>field.stormClocks.reduce((best,row,t)=>row[i]>field.stormClocks[best][i]?t:best,0));
 assert(new Set(peaks).size>=6,'separate storm cells must peak at independent times');
 assert(field.stormClocks.some(row=>row.some(v=>v>.5)&&row.some(v=>v<.001)),'local flashes must coexist with unlit cells');
 const controls=await page.evaluate(()=>{
  planet(42,.4,.3,.025);onwheel({deltaY:-100});const wheel=[...draw(8)];
  document.querySelector('canvas').onpointermove({buttons:1,movementX:30,movementY:10});const drag=[...draw(9)];
  let leave=null;window.parentPlanet=(...args)=>leave=args;onwheel({deltaY:100000});
  onkeydown({code:'KeyA'});const ignoredKey=[...draw(10)];
  onkeydown({code:'Space',preventDefault(){}});const reset=[...draw(0)];
  return {wheel,drag,leave,ignoredKey,reset,weatherUniform:Array.from(g.getUniform(p,g.getUniformLocation(p,'V')))};
 });
 assert(controls.wheel[2]<.025&&controls.drag[0]!==.4&&controls.leave[0]===42);
 assert.equal(controls.ignoredKey[2],1.5);assert.deepStrictEqual(controls.reset,[.4,.3,.025]);assert.equal(controls.weatherUniform[3],0);
 await page.evaluate(()=>planet(1));await page.keyboard.press('Space');
 // The actual application passes a single continuous elapsed-time value to the shader.
 const clock=await page.evaluate(()=>[39.999,40,40.001,43,48,52].map(time=>{draw(time);return {time,weather:g.getUniform(p,g.getUniformLocation(p,'V'))[3]};}));
 assert(clock.every(x=>Math.abs(x.time-x.weather)<5e-6));
 const openingChanged=(await render(0)).hash!==(await render(1)).hash;
 // An ordinary local view can be clear on a different GPU; inspect the whole shell too.
 await page.evaluate(()=>planet(1,.4,.3,1.2));
 const globeWeatherMoves=(await render(0)).hash!==(await render(1)).hash;assert(globeWeatherMoves);
 await page.evaluate(()=>planet(1));await page.keyboard.press('Space');
 const timing=await page.evaluate(async()=>{
  const frames=[],pixel=new Uint8Array(4);
  for(let i=0;i<30;i++){let begin=performance.now();draw(6+i/30);g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,pixel);frames.push(performance.now()-begin);await new Promise(r=>setTimeout(r,0));}
  frames.sort((a,b)=>a-b);return {frames:30,synchronous_readback:true,median_render_ms:frames[15],max_render_ms:frames[29]};
 });
 // Run native requestAnimationFrame callbacks; the camera is intentionally holding.
 const animation=await page.evaluate(async()=>{
  onkeydown({code:'Space',preventDefault(){}});const begin=performance.now();let count=0;
  requestAnimationFrame=realRAF;realRAF(window.pendingFrame);
  await new Promise(resolve=>{function tick(now){count++;if(now-begin>=1000)resolve();else realRAF(tick);}realRAF(tick);});
  requestAnimationFrame=fn=>{window.pendingFrame=fn;return 0;};
  return {actual_application_callback_ran:true,frames:count,elapsed_ms:performance.now()-begin};
 });
 await page.waitForTimeout(100);
 // Also open the independently recovered stripped distribution, offline.
 const distributionSmoke=[];
 for(const file of [process.argv[3]].filter(x=>x&&!x.startsWith('--'))){
  const smoke=await context.newPage();const seen=[],smokeErrors=[];
  smoke.on('request',r=>seen.push(r.url()));smoke.on('pageerror',e=>smokeErrors.push(String(e)));
  await smoke.addInitScript(()=>requestAnimationFrame=()=>0);const url='file://'+path.resolve(file);
  await smoke.goto(url);await smoke.waitForFunction('typeof draw=="function"',null,{polling:100});
  const hash=await smoke.evaluate(async()=>{draw(0);const bytes=new Uint8Array(g.drawingBufferWidth*g.drawingBufferHeight*4);g.readPixels(0,0,g.drawingBufferWidth,g.drawingBufferHeight,g.RGBA,g.UNSIGNED_BYTE,bytes);return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');});
  assert.equal(hash,initial.hash);assert.deepStrictEqual(smokeErrors,[]);assert(seen.every(x=>x===url));
  distributionSmoke.push({distribution:'stripped',hash,requests:seen,errors:smokeErrors});await smoke.close();
 }
 assert.deepStrictEqual(errors,[]);assert(requests.every(url=>url===target));
 assert.equal(await page.evaluate(()=>g.getError()),0);assert.equal(await page.evaluate(()=>g.isContextLost()),false);
 const report={engine,browser:browser.version(),...diagnostic,offline:true,network_protection:engine==='chromium'?'browser offline':'HTTP(S) routes aborted',requests,errors,initial,returned,groundInitial,groundReturn,solarReturn,ground_endpoint_frame_equal_with_frozen_sun:true,composite_endpoint_frame_equal:false,captures,choreography,field,coarse_max_error:coarseError,finer_detail_max_change:fineReveal,evolution_beyond_advection:evolution,seedRenders,locations,lighting,glints,flashes,controls,clock,opening_cloud_motion:openingChanged,globe_cloud_motion:globeWeatherMoves,timing,animation,distributionSmoke};
 fs.writeFileSync(out+'/'+(engine==='chromium'?'browser-verification.json':'webkit-verification.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({engine,ground_endpoint_equal_with_frozen_sun:true,clouds_evolve:true,coarseError,fineReveal,timing,framed_bytes:JSON.parse(fs.readFileSync(out+'/sizes.json')).total_framed_bytes}));
 if(process.argv.includes('--video')){
  await page.evaluate(()=>planet(1));await page.keyboard.press('Space');
  const dir=path.join(out,'frames');fs.mkdirSync(dir,{recursive:true});
  for(let i=0;i<1560;i++){await page.evaluate(t=>{draw(t);g.finish()},i/12);await page.screenshot({path:path.join(dir,String(i).padStart(4,'0')+'.png')});}
  // Fixed ground and camera make formation/dissipation easy to distinguish from wind.
  await page.evaluate(()=>planet(1,1.28,-.095,1.2));
  const weatherDir=path.join(out,'weather-frames');fs.mkdirSync(weatherDir,{recursive:true});
  for(let i=0;i<288;i++){await page.evaluate(t=>{draw(t);g.finish()},i/12);await page.screenshot({path:path.join(weatherDir,String(i).padStart(4,'0')+'.png')});}
 }
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1)});
