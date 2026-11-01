(function(){
  const G=window.GROW,cv=document.getElementById('grow');
  if(!G||!cv)return;
  const ctx=cv.getContext('2d');
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SCR='01<>/\\{}[]#$%&*+=:;.';
  const DUR=4200,cells=[];
  G.art.forEach((row,y)=>{for(let x=0;x<row.length;x++){const c=row[x];if(c!==' ')cells.push({x,y,c,t:(1-y/G.rows)*0.82+Math.random()*0.18,d:' .:-=+*#%@'.indexOf(c)})}});
  let cw=1,chh=1,start=null,raf=0,played=false;

  function size(){
    const w=Math.min(cv.parentElement.clientWidth,640),dpr=window.devicePixelRatio||1;
    cw=w/G.cols;chh=cw*G.cellAspect;
    cv.style.width=w+'px';cv.style.height=chh*G.rows+'px';
    cv.width=Math.round(w*dpr);cv.height=Math.round(chh*G.rows*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.font='500 '+(chh*0.92)+'px "DM Mono",monospace';
    ctx.textBaseline='top';
  }

  function draw(p){
    ctx.clearRect(0,0,cv.width,cv.height);
    for(const k of cells){
      if(p<k.t)continue;
      const age=p-k.t;
      let ch=k.c,a=0.6+k.d*0.045;
      if(age<0.07){ch=SCR[(Math.random()*SCR.length)|0];a=1}
      ctx.fillStyle='rgba(200,255,74,'+Math.min(1,a)+')';
      ctx.fillText(ch,k.x*cw,k.y*chh);
    }
  }

  function tick(now){
    if(start===null)start=now;
    const p=Math.min((now-start)/DUR,1.12);
    draw(p);
    if(p<1.12)raf=requestAnimationFrame(tick);else raf=0;
  }

  function play(){
    cancelAnimationFrame(raf);
    if(reduce){draw(2);return}
    start=null;raf=requestAnimationFrame(tick);
  }

  size();draw(-1);
  window.addEventListener('resize',()=>{size();draw(raf?0.5:2)});
  new IntersectionObserver((es,o)=>{
    es.forEach(e=>{if(e.isIntersecting&&!played){played=true;play();o.disconnect()}})
  },{threshold:0.35}).observe(cv);
  cv.addEventListener('click',play);
})();
