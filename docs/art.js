(function(){
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const RAMP=' .:-=+*#%@',ASPECT=1.75,COLS=64;
  const ALPHA=Array.from({length:10},(_,i)=>'rgba(200,255,74,'+(0.3+0.7*i/9).toFixed(2)+')');
  const hash=(c,r)=>((c*73856093)^(r*19349663))>>>0;

  function stage(cv,frame){
    const ctx=cv.getContext('2d');
    const rows=Math.round(COLS/ASPECT);
    const R=Math.min(COLS/2,rows/2*ASPECT)-0.5;
    let cw=1,chh=1,raf=0,visible=false;
    function size(){
      const w=Math.min(cv.parentElement.clientWidth-36||290,290),dpr=window.devicePixelRatio||1;
      cw=w/COLS;chh=cw*ASPECT;
      cv.style.width=w+'px';cv.style.height=chh*rows+'px';
      cv.width=Math.round(w*dpr);cv.height=Math.round(chh*rows*dpr);
      ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.font='500 '+(chh*0.92)+'px "DM Mono",monospace';
      ctx.textBaseline='top';
    }
    function render(t){
      const buf=new Float32Array(COLS*rows);
      frame(t,buf,COLS,rows,R,ASPECT);
      ctx.clearRect(0,0,cv.width,cv.height);
      for(let r=0;r<rows;r++)for(let c=0;c<COLS;c++){
        const v=buf[r*COLS+c];if(v<=0.04)continue;
        const i=Math.min(9,Math.round(v*9));if(i<1)continue;
        ctx.fillStyle=ALPHA[i];ctx.fillText(RAMP[i],c*cw,r*chh);
      }
    }
    function loop(now){render(now);raf=visible?requestAnimationFrame(loop):0}
    size();render(1200);
    window.addEventListener('resize',()=>{size();render(performance.now())});
    if(reduce)return;
    new IntersectionObserver(es=>{
      visible=es[0].isIntersecting;
      if(visible&&!raf)raf=requestAnimationFrame(loop);
    },{threshold:0.1}).observe(cv);
  }

  /* ── GLOBE ── */
  const rad=d=>d*Math.PI/180;
  const ll=(lat,lon)=>[Math.cos(rad(lat))*Math.sin(rad(lon)),Math.sin(rad(lat)),Math.cos(rad(lat))*Math.cos(rad(lon))];
  const CITIES={kochi:[9.9,76.3],london:[51.5,-0.1],nyc:[40.7,-74],sf:[37.8,-122.4],tokyo:[35.7,139.7],sydney:[-33.9,151.2],
    saopaulo:[-23.5,-46.6],capetown:[-33.9,18.4],dubai:[25.2,55.3],singapore:[1.35,103.8],moscow:[55.7,37.6],lagos:[6.5,3.4]};
  const NODES=Object.values(CITIES).map(([a,b])=>ll(a,b));
  const ARCS=[['kochi','london'],['kochi','singapore'],['kochi','dubai'],['nyc','london'],['sf','tokyo'],['saopaulo','lagos'],['dubai','moscow'],['singapore','sydney'],['london','capetown'],['nyc','saopaulo']]
    .map(([a,b])=>{
      const A=ll(...CITIES[a]),B=ll(...CITIES[b]);
      const w=Math.acos(Math.min(1,A[0]*B[0]+A[1]*B[1]+A[2]*B[2])),s=Math.sin(w);
      const pts=[];for(let i=0;i<=40;i++){
        const t=i/40,k=1+0.2*Math.sin(Math.PI*t),p0=Math.sin((1-t)*w)/s,p1=Math.sin(t*w)/s;
        pts.push([(p0*A[0]+p1*B[0])*k,(p0*A[1]+p1*B[1])*k,(p0*A[2]+p1*B[2])*k]);
      }
      return pts;
    });

  function globe(t,buf,cols,rows,R,asp){
    const th=t*0.00032,ct=Math.cos(th),st=Math.sin(th),TL=0.38,cT=Math.cos(TL),sT=Math.sin(TL);
    for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){
      const px=c+0.5-cols/2,py=(r+0.5-rows/2)*asp;
      const d2=(px*px+py*py)/(R*R);if(d2>1)continue;
      const nx=px/R,ny=-py/R,nz=Math.sqrt(1-d2);
      const y1=ny*cT-nz*sT,z1=ny*sT+nz*cT;
      const x=nx*ct+z1*st,z=-nx*st+z1*ct;
      const lat=Math.asin(Math.max(-1,Math.min(1,y1)))*180/Math.PI,lon=Math.atan2(x,z)*180/Math.PI;
      let m=((lat%20)+20)%20;const dl=Math.min(m,20-m);
      m=((lon%20)+20)%20;const dn=Math.min(m,20-m)*Math.cos(rad(lat));
      let v=0;
      if(dl<0.9||dn<0.8)v=0.2+0.3*nz;
      else if((hash(c,r)%100)/100<0.2*nz)v=0.16;
      if(nz<0.14)v=Math.max(v,0.5);
      buf[r*cols+c]=v;
    }
    const put=(P,val)=>{
      const x1=P[0]*ct-P[2]*st,z1=P[0]*st+P[2]*ct;
      const xs=x1,ys=P[1]*cT+z1*sT,zs=-P[1]*sT+z1*cT;
      if(zs<0.03)return;
      const c=Math.round(cols/2+xs*R-0.5),r=Math.round(rows/2-ys*R/asp-0.5);
      if(c<0||r<0||c>=cols||r>=rows)return;
      const i=r*cols+c;if(buf[i]<val)buf[i]=val;
    };
    ARCS.forEach((pts,i)=>{
      pts.forEach(p=>put(p,0.42));
      const u=(t*0.00022+i*0.137)%1;
      pts.forEach((p,j)=>{const dd=Math.abs(j/40-u);if(dd<0.05)put(p,1-dd*10)});
    });
    NODES.forEach((P,i)=>put(P,0.72+0.28*Math.sin(t*0.004+i*1.7)));
  }

  /* ── RADAR ── */
  const BLIPS=[[0.9,0.62],[2.1,0.38],[3.3,0.8],[4.4,0.5],[5.4,0.72],[1.5,0.9],[3.9,0.25]];
  function radar(t,buf,cols,rows,R,asp){
    const sw=(t*0.0017)%(Math.PI*2);
    for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){
      const px=c+0.5-cols/2,py=(r+0.5-rows/2)*asp;
      const d=Math.hypot(px,py)/R;if(d>1)continue;
      let v=0;
      const ring=Math.min(Math.abs(d-1),Math.abs(d-0.66),Math.abs(d-0.33));
      if(ring<0.025)v=d>0.95?0.55:0.28;
      if((Math.abs(px)<=0.5||Math.abs(py)<=0.5*asp*0.5)&&d>0.04)v=Math.max(v,0.18);
      const a=Math.atan2(-py,px);
      let diff=(sw-a)%(Math.PI*2);if(diff<0)diff+=Math.PI*2;
      if(diff<1.2)v=Math.max(v,Math.pow(1-diff/1.2,1.6)*0.85);
      buf[r*cols+c]=v;
    }
    BLIPS.forEach(([a,rad_])=>{
      let diff=(sw-a)%(Math.PI*2);if(diff<0)diff+=Math.PI*2;
      const v=Math.max(0,1-diff/3.2);if(v<0.08)return;
      const c=Math.round(cols/2+Math.cos(a)*rad_*R-0.5),r=Math.round(rows/2-Math.sin(a)*rad_*R/asp-0.5);
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
        const cc=c+dx,rr=r+dy;if(cc<0||rr<0||cc>=cols||rr>=rows)continue;
        const i=rr*cols+cc,val=(dx||dy)?v*0.45:v;if(buf[i]<val)buf[i]=val;
      }
    });
  }

  const g=document.getElementById('globe'),rd=document.getElementById('radar');
  if(g)stage(g,globe);
  if(rd)stage(rd,radar);
})();
