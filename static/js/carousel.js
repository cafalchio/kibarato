(() => {
  const carousel = document.querySelector('[data-carousel]');
  if (!carousel) return;
  const slides = [...carousel.querySelectorAll('[data-slide]')];
  if (slides.length < 2) return;
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let current = 0;
  let timer;

  function show(index) {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => { slide.hidden = i !== current; });
  }
  function schedule() {
    window.clearInterval(timer);
    if (!motion.matches && !document.hidden) {
      timer = window.setInterval(() => show(current + 1), 5000);
    }
  }
  document.addEventListener('visibilitychange', schedule);
  motion.addEventListener('change', schedule);
  show(0);
  schedule();
})();
