document.addEventListener('DOMContentLoaded',()=>{

  // ── PRELOADER ──
  const pre=document.getElementById('preloader');
  if(pre){setTimeout(()=>pre.classList.add('done'),1400)}

  // ── CUSTOM CURSOR ──
  const dot=document.querySelector('.cursor-dot');
  const ring=document.querySelector('.cursor-ring');
  if(dot&&ring){
    let mx=0,my=0,rx=0,ry=0;
    document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY;dot.style.left=mx+'px';dot.style.top=my+'px'});
    (function moveRing(){rx+=(mx-rx)*.15;ry+=(my-ry)*.15;ring.style.left=rx+'px';ring.style.top=ry+'px';requestAnimationFrame(moveRing)})();
    document.querySelectorAll('a,button,.pill,.btn-primary,.btn-outline,.project,.grid-link article').forEach(el=>{
      el.addEventListener('mouseenter',()=>document.body.classList.add('cursor-hover'));
      el.addEventListener('mouseleave',()=>document.body.classList.remove('cursor-hover'));
    });
  }

  // ── TYPEWRITER ──
  const tw=document.querySelector('.typewriter');
  if(tw){
    const text="Hello, I'm";
    let i=0;
    setTimeout(()=>{
      const iv=setInterval(()=>{tw.textContent=text.slice(0,++i);if(i>=text.length)clearInterval(iv)},80);
    },800);
  }

  // ── PARTICLES ──
  const canvas=document.getElementById('particles');
  if(canvas){
    const ctx=canvas.getContext('2d');
    let W,H;
    function resize(){W=canvas.width=canvas.offsetWidth;H=canvas.height=canvas.offsetHeight}
    resize();window.addEventListener('resize',resize);
    const dots=Array.from({length:50},()=>({x:Math.random()*W,y:Math.random()*H,r:Math.random()*2+.5,vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,o:Math.random()*.3+.1}));
    (function draw(){ctx.clearRect(0,0,W,H);dots.forEach(d=>{d.x+=d.vx;d.y+=d.vy;if(d.x<0)d.x=W;if(d.x>W)d.x=0;if(d.y<0)d.y=H;if(d.y>H)d.y=0;ctx.beginPath();ctx.arc(d.x,d.y,d.r,0,Math.PI*2);ctx.fillStyle='rgba(200,255,74,'+d.o+')';ctx.fill()});requestAnimationFrame(draw)})();
  }

  // ── SCROLL REVEAL ──
  const obs=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');obs.unobserve(e.target)}})
  },{threshold:0.15,rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));

  document.querySelectorAll('.reveal-stagger').forEach(group=>{
    const items=group.children;
    const gObs=new IntersectionObserver(entries=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          Array.from(items).forEach((item,i)=>{item.style.transitionDelay=i*80+'ms';item.classList.add('visible')});
          gObs.unobserve(e.target);
        }
      })
    },{threshold:0.1});
    gObs.observe(group);
  });

  // ── STATS COUNTER ──
  const statObs=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.querySelectorAll('.stat-num').forEach(num=>{
          const target=+num.dataset.target;
          const dur=1200;
          const start=performance.now();
          (function tick(now){
            const t=Math.min((now-start)/dur,1);
            const ease=1-Math.pow(1-t,3);
            num.textContent=Math.floor(ease*target);
            if(t<1)requestAnimationFrame(tick);else num.textContent=target;
          })(start);
        });
        statObs.unobserve(e.target);
      }
    })
  },{threshold:0.3});
  const statsEl=document.querySelector('.stats');
  if(statsEl)statObs.observe(statsEl);

  // ── PORTRAIT TILT ──
  const portrait=document.querySelector('.hero-portrait');
  if(portrait){
    const img=portrait.querySelector('img');
    const glow=portrait.querySelector('.glow');
    portrait.addEventListener('mousemove',e=>{
      const r=portrait.getBoundingClientRect();
      const x=(e.clientX-r.left)/r.width;
      const y=(e.clientY-r.top)/r.height;
      img.style.transform='rotateX('+((y-.5)*-14)+'deg) rotateY('+((x-.5)*14)+'deg) scale(1.03)';
      if(glow){glow.style.left=e.clientX-r.left+'px';glow.style.top=e.clientY-r.top+'px'}
    });
    portrait.addEventListener('mouseleave',()=>{img.style.transform='rotateX(0) rotateY(0) scale(1)'});
  }

  // ── BACK TO TOP ──
  const btt=document.querySelector('.back-top');
  if(btt){window.addEventListener('scroll',()=>{btt.classList.toggle('show',window.scrollY>600)},{passive:true})}
});
