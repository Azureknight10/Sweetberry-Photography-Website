/* ============================================================
   Sweet Berry Photography — Main JavaScript
   ============================================================ */

/* ── Sticky Nav ── */
(function(){
  const nav = document.querySelector('.site-nav');
  if (!nav) return;

  function onScroll(){
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Hamburger
  const toggle = nav.querySelector('.nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      nav.classList.toggle('mobile-open');
    });
  }

  // Mobile dropdown toggles
  const dropdownParents = nav.querySelectorAll('.has-dropdown > .nav-link');
  dropdownParents.forEach(link => {
    link.addEventListener('click', e => {
      if (window.innerWidth <= 768) {
        e.preventDefault();
        link.closest('.has-dropdown').classList.toggle('open');
      }
    });
  });
})();

/* ── Scroll Fade In ── */
(function(){
  const els = document.querySelectorAll('.fade-in');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  els.forEach(el => io.observe(el));
})();

/* ── Testimonials Carousel ── */
(function(){
  const carousel = document.querySelector('.testimonials-carousel');
  if (!carousel) return;

  const track    = carousel.querySelector('.testimonials-track');
  const cards    = carousel.querySelectorAll('.testimonial-card');
  const prevBtn  = carousel.closest('.testimonials-section')?.querySelector('.carousel-btn-prev') ||
                   document.querySelector('.carousel-btn-prev');
  const nextBtn  = carousel.closest('.testimonials-section')?.querySelector('.carousel-btn-next') ||
                   document.querySelector('.carousel-btn-next');
  const dotsWrap = document.querySelector('.carousel-dots');

  let current = 0;
  const total = cards.length;

  // Build dots
  if (dotsWrap && total) {
    dotsWrap.innerHTML = '';
    cards.forEach((_, i) => {
      const d = document.createElement('div');
      d.className = 'carousel-dot' + (i === 0 ? ' active' : '');
      d.addEventListener('click', () => goTo(i));
      dotsWrap.appendChild(d);
    });
  }

  function goTo(n){
    current = (n + total) % total;
    track.style.transform = `translateX(-${current * 100}%)`;
    dotsWrap?.querySelectorAll('.carousel-dot').forEach((d,i) => d.classList.toggle('active', i === current));
  }

  prevBtn?.addEventListener('click', () => goTo(current - 1));
  nextBtn?.addEventListener('click', () => goTo(current + 1));

  // Auto-advance
  let timer = setInterval(() => goTo(current + 1), 5500);
  carousel.addEventListener('mouseenter', () => clearInterval(timer));
  carousel.addEventListener('mouseleave', () => { timer = setInterval(() => goTo(current + 1), 5500); });
})();

/* ── FAQ Accordion ── */
(function(){
  const items = document.querySelectorAll('.faq-item');
  items.forEach(item => {
    const btn    = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');
    if (!btn || !answer) return;

    btn.addEventListener('click', () => {
      const isOpen = btn.classList.contains('active');
      // Close all
      items.forEach(i => {
        i.querySelector('.faq-question')?.classList.remove('active');
        const a = i.querySelector('.faq-answer');
        if (a) a.style.maxHeight = '0';
      });
      // Open clicked if it was closed
      if (!isOpen) {
        btn.classList.add('active');
        answer.style.maxHeight = answer.scrollHeight + 'px';
      }
    });
  });
})();

/* ── Lightbox ── */
(function(){
  const lb      = document.querySelector('.lightbox');
  if (!lb) return;
  const lbImg   = lb.querySelector('img');
  const lbClose = lb.querySelector('.lb-close');
  const lbPrev  = lb.querySelector('.lb-prev');
  const lbNext  = lb.querySelector('.lb-next');

  let images = [];
  let cur    = 0;

  function buildImageList(){
    images = Array.from(document.querySelectorAll('.gallery-item[data-src]')).map(el => el.dataset.src);
  }

  function open(idx){
    buildImageList();
    cur = idx;
    lbImg.src = images[cur];
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function close(){
    lb.classList.remove('open');
    document.body.style.overflow = '';
  }

  function nav(dir){
    cur = (cur + dir + images.length) % images.length;
    lbImg.src = images[cur];
  }

  document.querySelectorAll('.gallery-item[data-src]').forEach((el, i) => {
    el.addEventListener('click', () => open(i));
  });

  lbClose?.addEventListener('click', close);
  lbPrev?.addEventListener('click', () => nav(-1));
  lbNext?.addEventListener('click', () => nav(1));
  lb.addEventListener('click', e => { if (e.target === lb) close(); });
  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') nav(-1);
    if (e.key === 'ArrowRight') nav(1);
  });
})();

/* ── Contact Form ── */
(function(){
  const form = document.getElementById('contact-form');
  if (!form) return;

  form.addEventListener('submit', function(e){
    e.preventDefault();
    let valid = true;

    // Clear errors
    form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
    form.querySelectorAll('.form-error').forEach(el => el.remove());

    const required = form.querySelectorAll('[required]');
    required.forEach(field => {
      if (!field.value.trim()) {
        field.classList.add('error');
        const err = document.createElement('span');
        err.className = 'form-error';
        err.textContent = 'This field is required.';
        field.parentNode.appendChild(err);
        valid = false;
      }
    });

    // Email validation
    const email = form.querySelector('[type="email"]');
    if (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
      email.classList.add('error');
      const err = document.createElement('span');
      err.className = 'form-error';
      err.textContent = 'Please enter a valid email address.';
      email.parentNode.appendChild(err);
      valid = false;
    }

    if (!valid) return;

    // Show success
    const success = document.querySelector('.form-success');
    if (success) success.style.display = 'block';
    form.reset();
    form.querySelector('button[type="submit"]').disabled = true;
  });
})();
