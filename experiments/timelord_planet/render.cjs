// Development-only observer: the browser loads ONLY reconstructed HTML.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const out=path.join(__dirname,'artifacts');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const context=await browser.newContext({viewport:{width:960,height:640},offline:true});
 const page=await context.newPage(),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>requests.push(r.url()));
 // Freeze the actual animation after initialization; explicit draw(t) tests endpoints.
 await page.addInitScript(()=>{window.realRAF=requestAnimationFrame.bind(window);window.requestAnimationFrame=fn=>{window.pendingFrame=fn;return 0;};});
 const target='file://'+path.resolve(process.argv[2]||out+'/planet.html');
 await page.goto(target);
 await page.waitForFunction('typeof draw=="function"',null,{polling:100});
 const diagnostic=await page.evaluate(()=>{
  window.g=document.querySelector('canvas').getContext('webgl');
  window.p=g.getParameter(g.CURRENT_PROGRAM);
  const debug=g.getExtension('WEBGL_debug_renderer_info');
  return {shaders:g.getAttachedShaders(p).map(s=>({ok:g.getShaderParameter(s,g.COMPILE_STATUS),log:g.getShaderInfoLog(s)})),linked:g.getProgramParameter(p,g.LINK_STATUS),renderer:debug?g.getParameter(debug.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER)};
 });
 assert(diagnostic.linked&&diagnostic.shaders.every(s=>s.ok),JSON.stringify(diagnostic));
 async function render(t){return await page.evaluate(async t=>{
  const view=draw(t);g.finish();let bytes=new Uint8Array(g.drawingBufferWidth*g.drawingBufferHeight*4);
  g.readPixels(0,0,g.drawingBufferWidth,g.drawingBufferHeight,g.RGBA,g.UNSIGNED_BYTE,bytes);
  // Hash exact RGBA pixels, including alpha, before the browser clears them.
  const digest=await crypto.subtle.digest('SHA-256',bytes);return {view,hash:Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,'0')).join('')};
 },t);}
 const start=await render(0),end=await render(40);
 assert.deepStrictEqual(start.view,end.view);assert.notEqual(start.hash,'');
 const initialHash=start.hash;
 assert.equal(initialHash,end.hash);
 await page.screenshot({path:out+'/A-return.png'});
 const captures={};
 for(const [name,t] of [['A',0],['globe',10],['B',20]]){
  const r=await render(t);captures[name]={time:t,view:r.view,sha256:r.hash};
  await page.screenshot({path:out+'/'+name+'.png'});
 }
 const states=await page.evaluate(()=>[0,5,10,15,20,25,30,35,40].map(t=>({time:t,view:camera(t)})));
 // Explicit endpoints, holds, and near-endpoint speed of the quintic easing.
 const motion=await page.evaluate(()=>{
  const delta=(a,b)=>Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
  return {holdA:delta(camera(0),camera(4)),holdB:delta(camera(20),camera(24)),endpointStep:Math.max(...[5,10,15,20,25,30,35,40].map(t=>delta(camera(t),camera(t+.001))))};
 });
 assert.equal(motion.holdA,0);assert.equal(motion.holdB,0);assert(motion.endpointStep<1e-8);
 // GPU field probes use the terrain function recovered from the transported shader.
 const field=await page.evaluate(()=>{
  const shaders=g.getAttachedShaders(p),frag=shaders.find(s=>g.getShaderParameter(s,g.SHADER_TYPE)==g.FRAGMENT_SHADER),vert=shaders.find(s=>g.getShaderParameter(s,g.SHADER_TYPE)==g.VERTEX_SHADER);
  const source=g.getShaderSource(frag).split('void main()')[0]+`uniform vec3 P;void main(){float h=clamp(terrain(P)+.5,0.,1.);float v=floor(h*65535.+.5);gl_FragColor=vec4(floor(v/256.)/255.,mod(v,256.)/255.,0,1);}`;
  const program=g.createProgram(),s=g.createShader(g.FRAGMENT_SHADER);
  g.shaderSource(s,source);g.compileShader(s);
  if(!g.getShaderParameter(s,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(s));
  g.attachShader(program,vert);g.attachShader(program,s);g.bindAttribLocation(program,0,'a');g.linkProgram(program);
  if(!g.getProgramParameter(program,g.LINK_STATUS))throw Error(g.getProgramInfoLog(program));
  g.useProgram(program);g.viewport(0,0,1,1);
  g.uniform2f(g.getUniformLocation(program,'R'),960,640);
  function sample(point,seed=1,zoom=.025){
   g.uniform3fv(g.getUniformLocation(program,'P'),point);
   g.uniform2f(g.getUniformLocation(program,'S'),seed&65535,seed>>>16);
   g.uniform4f(g.getUniformLocation(program,'V'),0,0,zoom,0);
   g.drawArrays(g.TRIANGLES,0,3);let v=new Uint8Array(4);g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,v);
   return (v[0]*256+v[1])/65535-.5;
  }
  const point=(x,y)=>[Math.sin(x)*Math.cos(y),Math.sin(y),Math.cos(x)*Math.cos(y)];
  // Predetermined coordinates, never searched for visual attractiveness.
  const coords=[[.4,.3],[2.2,-.45],[-1,.6],[0,0],[3,-1],[1,1.3],[0,Math.PI/2],[0,-Math.PI/2]];
  const samples=coords.map(([x,y])=>sample(point(x,y))),coarse=coords.map(([x,y])=>sample(point(x,y),1,1.2)),fine=coords.map(([x,y])=>sample(point(x,y),1,.006));
  const seeds=[0,1,2,42,65536,4294967295].map(seed=>({seed,values:coords.map(([x,y])=>sample(point(x,y),seed))}));
  const reverse=coords.slice().reverse().map(([x,y])=>sample(point(x,y))).reverse();
  const seam=Math.abs(sample(point(-Math.PI,.2))-sample(point(Math.PI,.2)));
  const poles=[-1,1].map(sign=>Math.max(...[-3,-1,0,1,3].map(x=>Math.abs(sample(point(x,sign*Math.PI/2))-sample([0,sign,0])))));
  const continuity=coords.map(([x,y])=>Math.abs(sample(point(x+1e-6,y))-sample(point(x,y))));
  g.useProgram(p);
  return {coords,samples,coarse,fine,seeds,reverse,seam,poles,continuity};
 });
 assert.deepStrictEqual(field.samples,field.reverse);
 assert.equal(new Set(field.seeds.map(x=>JSON.stringify(x.values))).size,field.seeds.length);
 assert(field.seam<=2/65535&&Math.max(...field.poles)<=2/65535);
 assert(Math.max(...field.continuity)<.001);
 const coarseError=Math.max(...field.samples.map((v,i)=>Math.abs(v-field.coarse[i])));
 const fineReveal=Math.max(...field.samples.map((v,i)=>Math.abs(v-field.fine[i])));
 assert(coarseError<.02);assert(fineReveal>1/65535);
 const seedRenders=[];
 for(const identity of field.seeds.map(x=>x.seed)){
  await page.evaluate(s=>planet(s,.4,.3,1.2),identity);
  const first=await render(0),again=await render(0);assert.equal(first.hash,again.hash);seedRenders.push({seed:identity,hash:first.hash});
 }
 assert.equal(new Set(seedRenders.map(x=>x.hash)).size,seedRenders.length);
 // Restore/leave/return through the delivered integration entry point.
 const extra=[];
 for(const [i,coord]of field.coords.entries()){
  await page.evaluate(([x,y])=>planet(1,x,y,.025),coord);
  const r=await render(0);extra.push({coordinate:coord,hash:r.hash});
  if(i>=2)await page.screenshot({path:out+'/location-'+i+'.png'});
 }
 await page.evaluate(()=>planet(1,.4,.3,.025));
 assert.equal((await render(0)).hash,initialHash);
 const controls=await page.evaluate(()=>{
  planet(42,.4,.3,.025);onwheel({deltaY:-100});const wheel=draw(0)[2];
  document.querySelector('canvas').onpointermove({buttons:1,movementX:30,movementY:10});const drag=[...draw(0)];
  let returned=null;window.parentPlanet=(...args)=>returned=args;onwheel({deltaY:100000});
  const leave=returned;onkeydown();const reset=draw(0);
  return {wheel,drag,leave,reset};
 });
 assert(controls.wheel<.025&&controls.drag[0]!=.4&&controls.leave[0]===42);
 assert.deepStrictEqual(controls.reset,[.4,.3,.025]);
 // Performance of the actual requestAnimationFrame loop, independent of captures.
 await page.evaluate(()=>{planet(1);onkeydown();});
 const timing=await page.evaluate(async()=>{
  let n=0,last=performance.now(),frames=[],pixel=new Uint8Array(4);
  await new Promise(resolve=>{
   function tick(now){draw(6+n/30);g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,pixel);frames.push(performance.now()-now);if(++n==60)resolve();else setTimeout(()=>tick(performance.now()),0);}
   tick(performance.now());
  });
  frames.sort((a,b)=>a-b);return {frames:n,synchronous_readback:true,total_ms:performance.now()-last,median_render_ms:frames[30],max_render_ms:frames[59]};
 });
 assert.equal(errors.length,0,errors.join('\n'));
 assert.equal(await page.evaluate(()=>g.getError()),0,'WebGL error');
 assert.equal(await page.evaluate(()=>g.isContextLost()),false,'WebGL context lost');
 assert(requests.every(url=>url===target),JSON.stringify(requests));
 const animation=await page.evaluate(async()=>{
  onkeydown();let count=0;const begin=performance.now();
  window.requestAnimationFrame=window.realRAF;window.realRAF(window.pendingFrame);
  await new Promise(resolve=>{function tick(now){count++;if(now-begin>=1500)resolve();else realRAF(tick);}realRAF(tick);});
  window.requestAnimationFrame=fn=>{window.pendingFrame=fn;return 0;};
  return {actual_application_callback_ran:true,frames:count,elapsed_ms:performance.now()-begin};
 });
 const report={seed_render_hashes:seedRenders,animation,browser:browser.version(),...diagnostic,offline:true,requests,errors,endpoint_state_equal:true,endpoint_rgba_sha256:initialHash,endpoint_frame_equal:true,captures,states,motion,field,coarse_max_error:coarseError,finer_detail_max_change:fineReveal,additional_locations:extra,restore_exact:true,controls,timing};
 fs.writeFileSync(out+'/browser-verification.json',JSON.stringify(report,null,2)+'\n');
 if(fs.existsSync(out+'/loop.mp4')||process.argv.includes('--video')){report.video={file:'loop.mp4',world_seed:1,seconds:40,sampling_fps:12,frames:480};fs.writeFileSync(out+'/browser-verification.json',JSON.stringify(report,null,2)+'\n');}
 console.log(JSON.stringify({offline:true,endpoint_frame_equal:true,coarseError,fineReveal,timing,framed_bytes:JSON.parse(fs.readFileSync(out+'/sizes.json')).total_framed_bytes}));
 // Encode a full deterministic 40-second loop if requested. Each image comes
 // from the reconstructed document, sampled at 12fps; no algorithm in a viewer.
 if(process.argv.includes('--video')){
  await page.waitForTimeout(100);
  await page.evaluate(()=>{planet(1);onkeydown();});
  const dir=path.join(out,'frames');fs.mkdirSync(dir,{recursive:true});
  for(let i=0;i<480;i++){
   await page.evaluate(t=>{draw(t);g.finish();},i/12);
   await page.screenshot({path:path.join(dir,String(i).padStart(4,'0')+'.png')});
  }
 }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
