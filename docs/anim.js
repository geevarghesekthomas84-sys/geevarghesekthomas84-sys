document.addEventListener('DOMContentLoaded',()=>{

  // ── PRELOADER ──
  const pre=document.getElementById('preloader');
  let seen=false;
  try{seen=sessionStorage.getItem('introSeen')==='1'}catch(e){}
  function endIntro(){
    if(!pre||pre.classList.contains('done'))return;
    pre.classList.add('done');document.body.classList.add('ready');
    document.dispatchEvent(new Event('intro-done'));
    try{sessionStorage.setItem('introSeen','1')}catch(e){}
  }
  if(pre){
    const fill=pre.querySelector('.pre-fill'),num=document.getElementById('preNum');
    const setP=p=>{if(fill)fill.style.width=(p*100)+'%';if(num)num.textContent=('00'+Math.round(p*100)).slice(-3)};
    const skip=pre.querySelector('.pre-skip');
    let t0=null;const D=seen?850:2300;
    (function tick(now){if(t0===null)t0=now;const p=Math.min((now-t0)/D,1);setP(p);if(p<1)requestAnimationFrame(tick);else setTimeout(endIntro,seen?150:350)})(performance.now());
    if(skip)skip.addEventListener('click',()=>{setP(1);endIntro()});
  } else{document.body.classList.add('ready');document.dispatchEvent(new Event('intro-done'))}

  // ── HERO TERMINAL + RETICLE ──
  const term=document.getElementById('heroTerm');
  if(term){
    const L=[["p","$ "],["w","whoami\n"],["","geevarghese k thomas  (gg)\n\n"],["p","$ "],["w","cat role.txt\n"],["","offensive security researcher\nred team ops · AI offense · builder\n\n"],["p","$ "],["w","ls ~/projects\n"],["","redpilot  gria-ai  cyberforge  ghostkit\nnetpulse  +6 more\n\n"],["p","$ "],["w","./redpilot --status\n"],["k","[+] "],["","access granted. welcome.\n"],["p","$ "]];
    const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const esc=t=>t.replace(/&/g,'&amp;').replace(/</g,'&lt;');
    let html='',li=0,ci=0;
    const render=()=>{term.innerHTML=html+'<span class="cur"></span>'};
    const step=()=>{
      if(li>=L.length){render();return}
      const [cls,txt]=L[li];
      const slow=cls==='w';
      const n=slow?1:Math.min(txt.length-ci,6);
      const part=esc(txt.slice(ci,ci+n));ci+=n;
      html+=cls?'<span class="'+cls+'">'+part+'</span>':part;
      if(ci>=txt.length){li++;ci=0}
      render();
      setTimeout(step,slow?55+Math.random()*60:18);
    };
    if(reduce){L.forEach(([c,t])=>html+=c?'<span class="'+c+'">'+esc(t)+'</span>':esc(t));render()}
    else{const go=()=>setTimeout(step,700);document.body.classList.contains('ready')?go():document.addEventListener('intro-done',go,{once:true})}
  }
  const hero=document.querySelector('.hero2'),ret=document.querySelector('.reticle');
  if(hero&&ret){
    let tx=0,ty=0,x=0,y=0,raf=0;
    const loop=()=>{x+=(tx-x)*.18;y+=(ty-y)*.18;ret.style.transform='translate('+x+'px,'+y+'px)';raf=Math.abs(tx-x)+Math.abs(ty-y)>.3?requestAnimationFrame(loop):0};
    hero.addEventListener('mousemove',e=>{const r=hero.getBoundingClientRect();tx=e.clientX-r.left;ty=e.clientY-r.top;if(!raf)raf=requestAnimationFrame(loop)});
  }

  // ── CUSTOM CURSOR ──
  const cross=document.querySelector('.cursor-cross');
  if(cross){
    document.addEventListener('mousemove',e=>{cross.style.left=e.clientX+'px';cross.style.top=e.clientY+'px'});
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
    const img=portrait.querySelector('.portrait-canvas')||portrait.querySelector('img');
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
