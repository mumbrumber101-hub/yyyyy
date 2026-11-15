/* Let the Wix About page grow with this document after a trusted handshake. */
(() => {
  'use strict';
  if (window.parent === window) return;
  const parentOrigins = new Set(['https://www.arriveateasterwine.com', 'https://arriveateasterwine.com']);
  const main = document.querySelector('main');
  if (!main) return;
  let hostOrigin = null;
  let queued = false;
  let lastHeight = 0;
  let pendingTarget = null;

  function send(type, data = {}) {
    if (hostOrigin) window.parent.postMessage({type, ...data}, hostOrigin);
  }

  function measure() {
    queued = false;
    if (!hostOrigin) return;
    // Measure content, not the viewport-sized document, so the frame can shrink.
    const rect = main.getBoundingClientRect();
    const height = Math.ceil(rect.bottom + window.scrollY + 2);
    if (Number.isFinite(height) && height > 0 && height !== lastHeight) {
      lastHeight = height;
      send('aae-about-height', {height});
    }
    if (pendingTarget) {
      const target = pendingTarget;
      pendingTarget = null;
      if (target.isConnected) send('aae-about-scroll', {
        top: Math.max(0, Math.round(target.getBoundingClientRect().top + window.scrollY))
      });
    }
  }

  function schedule() {
    if (!queued) {
      queued = true;
      requestAnimationFrame(measure);
    }
  }

  window.aaeAboutScrollTo = target => {
    if (!hostOrigin) {
      target.scrollIntoView({behavior: 'smooth', block: 'start'});
      return;
    }
    pendingTarget = target;
    schedule();
  };

  window.addEventListener('message', event => {
    if (event.source !== window.parent || !parentOrigins.has(event.origin) ||
        !event.data || event.data.type !== 'aae-about-measure') return;
    hostOrigin = event.origin;
    if (!document.getElementById('aae-about-flow-style')) {
      const style = document.createElement('style');
      style.id = 'aae-about-flow-style';
      style.textContent = '@media screen{html,body{height:auto!important;min-height:0!important;overflow-y:hidden!important}}';
      document.head.appendChild(style);
    }
    lastHeight = 0;
    schedule();
  });

  document.addEventListener('click', event => {
    if (!hostOrigin || event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href^="#"]');
    if (!link) return;
    let id;
    try { id = decodeURIComponent(link.getAttribute('href').slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    window.aaeAboutScrollTo(target);
  });

  if (window.ResizeObserver) new ResizeObserver(schedule).observe(main);
  new MutationObserver(schedule).observe(main, {
    childList: true, subtree: true, attributes: true,
    attributeFilter: ['open', 'hidden', 'style', 'class']
  });
  window.addEventListener('resize', schedule);
  window.addEventListener('load', schedule);
  document.addEventListener('toggle', schedule, true);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(schedule);
  for (const origin of parentOrigins) window.parent.postMessage({type: 'aae-about-ready'}, origin);
})();
