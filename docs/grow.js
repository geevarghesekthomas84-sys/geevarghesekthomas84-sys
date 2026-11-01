(function(){
  const G=window.GROW;
  if(!G)return;
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SCR='01<>/\\{}[]#$%&*+=:;.';
  const RAMP=' .:-=+*#%@';
  const cells=[];
  G.art.forEach((row,y)=>{for(let x=0;x<row.length;x++){const c=row[x];if(c!==' ')cells.push({x,y,c,t:(1-y/G.rows)*0.82+Math.random()*0.18,d:RAMP.indexOf(c)})}});
  const END=1.12;

  window.growChar=function(cv,o){
    const ctx=cv.getContext('2d');
    const dur=o.dur||4200;
    let cw=1,chh=1,start=null,raf=0,last=-1;

    function size(){
      const w=o.width(),dpr=window.devicePixelRatio||1;
      cw=w/G.cols;chh=cw*G.cellAspect;
      cv.style.width=w+'px';cv.style.height=chh*G.rows+'px';
      cv.width=Math.round(w*dpr);cv.height=Math.round(chh*G.rows*dpr);
      ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.font='500 '+(chh*0.92)+'px "DM Mono",monospace';
      ctx.textBaseline='top';
    }

    function draw(p){
      last=p;
      ctx.clearRect(0,0,cv.width,cv.height);
      for(const k of cells){
        if(p<k.t)continue;
        let ch=k.c,a=0.6+k.d*0.045;
        if(p-k.t<0.07){ch=SCR[(Math.random()*SCR.length)|0];a=1}
        ctx.fillStyle='rgba(200,255,74,'+Math.min(1,a)+')';
        ctx.fillText(ch,k.x*cw,k.y*chh);
      }
    }

    function tick(now){
      if(start===null)start=now;
      const p=Math.min((now-start)/dur*END,END);
      draw(p);
      if(o.onProgress)o.onProgress(Math.min(p/END,1));
      if(p<END)raf=requestAnimationFrame(tick);
      else{raf=0;if(o.onDone)o.onDone()}
    }

    function play(){
      cancelAnimationFrame(raf);
      if(reduce){draw(2);if(o.onProgress)o.onProgress(1);if(o.onDone)o.onDone();return}
      start=null;raf=requestAnimationFrame(tick);
    }

    function finish(){cancelAnimationFrame(raf);raf=0;draw(2);if(o.onProgress)o.onProgress(1)}

    size();draw(-1);
    window.addEventListener('resize',()=>{size();draw(raf?Math.max(last,0):2)});
    return {play,finish};
  };

  const sec=document.getElementById('grow');
  if(sec){
    const a=window.growChar(sec,{width:()=>Math.min(sec.parentElement.clientWidth-36,640)});
    let played=false;
    new IntersectionObserver((es,ob)=>{
      es.forEach(e=>{if(e.isIntersecting&&!played){played=true;a.play();ob.disconnect()}})
    },{threshold:0.35}).observe(sec);
    sec.addEventListener('click',a.play);
    const rb=document.querySelector('.panel-replay');if(rb)rb.addEventListener('click',a.play);
  }
})();
