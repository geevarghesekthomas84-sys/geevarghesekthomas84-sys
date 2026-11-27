(function(){
  var nav=document.querySelector('.nav');
  if(!nav)return;
  var links=[].slice.call(nav.querySelectorAll('nav a, .nav-links a')).filter(function(a){return !a.classList.contains('gh-link')});
  var gh=nav.querySelector('.pill, .gh-link');
  var ghHref=gh?gh.getAttribute('href'):'https://github.com/geevarghesekthomas84-sys';

  var btn=document.createElement('button');
  btn.className='menu-btn';btn.type='button';
  btn.setAttribute('aria-label','Open menu');btn.setAttribute('aria-expanded','false');btn.setAttribute('aria-controls','mobile-menu');
  btn.innerHTML='<span></span><span></span>';
  nav.appendChild(btn);

  var ov=document.createElement('div');
  ov.id='mobile-menu';ov.className='mm';ov.hidden=true;
  ov.setAttribute('role','dialog');ov.setAttribute('aria-modal','true');ov.setAttribute('aria-label','Menu');

  var top=document.createElement('div');top.className='mm-top';
  var brand=document.createElement('a');brand.className='mm-brand';brand.href='/';brand.innerHTML='<span>G</span>G.';
  var close=document.createElement('button');close.className='mm-close';close.type='button';close.setAttribute('aria-label','Close menu');close.innerHTML='<span></span><span></span>';
  top.appendChild(brand);top.appendChild(close);

  var list=document.createElement('nav');list.className='mm-links';list.setAttribute('aria-label','Mobile');
  links.forEach(function(a,i){
    var l=document.createElement('a');
    l.href=a.getAttribute('href');
    l.style.setProperty('--i',i);
    if(a.classList.contains('active'))l.className='active';
    var n=document.createElement('small');n.textContent=('0'+(i+1)).slice(-2);
    l.appendChild(n);l.appendChild(document.createTextNode(a.textContent.trim()));
    list.appendChild(l);
  });

  var foot=document.createElement('div');foot.className='mm-foot';
  foot.innerHTML='<p class="mm-hand">say hi</p><div><a href="mailto:geevarghesekthomas84@gmail.com">Email</a><a href="https://www.linkedin.com/in/geevarghese-k-thomas" target="_blank" rel="noreferrer">LinkedIn</a><a href="'+ghHref+'" target="_blank" rel="noreferrer">GitHub</a></div>';

  ov.appendChild(top);ov.appendChild(list);ov.appendChild(foot);
  document.body.appendChild(ov);

  var isOpen=false,timer=0;
  function open(){
    if(isOpen)return;isOpen=true;clearTimeout(timer);
    ov.hidden=false;
    requestAnimationFrame(function(){requestAnimationFrame(function(){ov.classList.add('open')})});
    document.body.classList.add('mm-lock');
    btn.setAttribute('aria-expanded','true');
    close.focus();
  }
  function shut(restore){
    if(!isOpen)return;isOpen=false;
    ov.classList.remove('open');
    document.body.classList.remove('mm-lock');
    btn.setAttribute('aria-expanded','false');
    timer=setTimeout(function(){ov.hidden=true},320);
    if(restore)btn.focus();
  }
  btn.addEventListener('click',open);
  close.addEventListener('click',function(){shut(true)});
  list.addEventListener('click',function(e){if(e.target.closest('a'))shut(false)});
  foot.addEventListener('click',function(e){if(e.target.closest('a'))shut(false)});
  brand.addEventListener('click',function(){shut(false)});
  document.addEventListener('keydown',function(e){
    if(!isOpen)return;
    if(e.key==='Escape'){shut(true);return}
    if(e.key==='Tab'){
      var f=[].slice.call(ov.querySelectorAll('a,button')).filter(function(x){return x.offsetParent!==null});
      if(!f.length)return;
      var first=f[0],last=f[f.length-1];
      if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
    }
  });
  window.addEventListener('resize',function(){if(window.innerWidth>760)shut(false)});
})();
