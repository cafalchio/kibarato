(() => {
  const navigation = document.querySelector('.navigation');
  if (!navigation) return;
  const toggle = navigation.querySelector('.menu-toggle');
  const links = navigation.querySelector('.nav-links');
  const mobile = window.matchMedia('(max-width: 760px)');

  function setOpen(open) {
    navigation.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', String(open));
  }

  toggle.addEventListener('click', () => {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });
  links.addEventListener('click', (event) => {
    if (mobile.matches && event.target.closest('a')) {
      setOpen(false);
      toggle.focus({ preventScroll: true });
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && navigation.classList.contains('menu-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (!navigation.contains(event.target)) setOpen(false);
  });
  mobile.addEventListener('change', () => {
    if (mobile.matches && links.contains(document.activeElement)) toggle.focus();
    if (!mobile.matches && document.activeElement === toggle) links.querySelector('a').focus();
    setOpen(false);
  });
  navigation.classList.add('menu-ready');
  toggle.hidden = false;
})();
