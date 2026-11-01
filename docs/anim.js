document.addEventListener('DOMContentLoaded',()=>{
  const obs=new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){e.target.classList.add('visible');obs.unobserve(e.target)}
    })
  },{threshold:0.15,rootMargin:'0px 0px -40px 0px'});
  document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));

  document.querySelectorAll('.reveal-stagger').forEach(group=>{
    const items=group.children;
    const gObs=new IntersectionObserver((entries)=>{
      entries.forEach(e=>{
        if(e.isIntersecting){
          Array.from(items).forEach((item,i)=>{
            item.style.transitionDelay=i*80+'ms';
            item.classList.add('visible');
          });
          gObs.unobserve(e.target);
        }
      })
    },{threshold:0.1});
    gObs.observe(group);
  });
});
