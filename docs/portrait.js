(function(){
  const P=window.PORTRAIT,box=document.querySelector('.hero-portrait');
  if(!P||!box)return;
  const img=box.querySelector('img');
  const cv=document.createElement('canvas');
  cv.className='portrait-canvas';cv.setAttribute('role','img');
  cv.setAttribute('aria-label',img?img.alt:'Halftone dot portrait');
  box.insertBefore(cv,img||box.firstChild);
  if(img)img.style.display='none';
  const ctx=cv.getContext('2d');
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const BRIGHT=[232,228,220],MID=[140,137,130],DIM=[65,63,58];
  const mix=(a,b,t)=>a.map((v,i)=>Math.round(v+t*(b[i]-v)));
  const levelColor=l=>{
    const b=l/35;
    const c=b>0.5?BRIGHT:b>0.22?mix(MID,BRIGHT,(b-0.22)/0.28):mix(DIM,MID,b/0.22);
    return 'rgb('+c[0]+','+c[1]+','+c[2]+')';
  };
  const COLORS=Array.from({length:36},(_,l)=>levelColor(l));
  const dots=[];
  P.art.forEach((row,ry)=>{for(let rx=0;rx<row.length;rx++){
    const l=parseInt(row[rx],36);
    if(l>0)dots.push({x:rx,y:ry,l,t:(1-ry/P.rows)*0.8+Math.random()*0.2});
  }});
  const byLevel=Array.from({length:36},()=>[]);
  dots.forEach(d=>byLevel[d.l].push(d));
  const WIN=0.14,END=1.0+WIN,DUR=2800;
  let s=1,raf=0,start=null;

  function size(){
    const w=Math.min(box.clientWidth||520,window.innerWidth<=760?300:520),dpr=window.devicePixelRatio||1;
    s=w/(P.cols*P.sp);
    const h=P.rows*P.sp*s;
    cv.style.width=w+'px';cv.style.height=h+'px';
    cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  const back=t=>{const c=1.70158;return 1+(c+1)*Math.pow(t-1,3)+c*Math.pow(t-1,2)};

  function draw(p){
    ctx.clearRect(0,0,cv.width,cv.height);
    for(let l=1;l<36;l++){
      const arr=byLevel[l];if(!arr.length)continue;
      ctx.fillStyle=COLORS[l];ctx.beginPath();
      const full=l/35*P.sp*0.47*s;
      for(const d of arr){
        if(p<d.t)continue;
        const k=p>=d.t+WIN?1:back((p-d.t)/WIN);
        const r=full*k;if(r<=0)continue;
        const x=(d.x*P.sp+P.sp/2)*s,y=(d.y*P.sp+P.sp/2)*s;
        ctx.moveTo(x+r,y);ctx.arc(x,y,r,0,6.2832);
      }
      ctx.fill();
    }
  }
  function tick(now){
    if(start===null)start=now;
    const p=Math.min((now-start)/DUR*END,END);
    draw(p);
    raf=p<END?requestAnimationFrame(tick):0;
  }
  function play(){
    cancelAnimationFrame(raf);
    if(reduce){draw(2);return}
    start=null;raf=requestAnimationFrame(tick);
  }

  size();draw(-1);
  window.addEventListener('resize',()=>{size();draw(raf?0.6:2)});
  let started=false;
  function go(){if(started)return;started=true;play()}
  if(document.body.classList.contains('ready'))go();
  else{document.addEventListener('intro-done',go,{once:true});setTimeout(go,9000)}
  cv.addEventListener('click',play);
})();
