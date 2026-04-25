// ═══════════════════════════════════════
//  ĐẬU DƯƠNG — Portfolio Script
// ═══════════════════════════════════════
(function () {
  'use strict';

  /* ── CURSOR ── */
  var cur  = document.getElementById('cur');
  var curR = document.getElementById('curR');
  var mx = 0, my = 0, cx = 0, cy = 0;

  document.addEventListener('mousemove', function (e) {
    mx = e.clientX; my = e.clientY;
    curR.style.left = mx + 'px';
    curR.style.top  = my + 'px';
  });

  (function tick() {
    cx += (mx - cx) * 0.13;
    cy += (my - cy) * 0.13;
    cur.style.left = cx + 'px';
    cur.style.top  = cy + 'px';
    requestAnimationFrame(tick);
  }());

  /* ── NAV SCROLL ── */
  var nav = document.getElementById('nav');
  window.addEventListener('scroll', function () {
    nav.classList.toggle('scrolled', window.scrollY > 30);
  }, { passive: true });

  /* ── MOBILE MENU ── */
  var burger = document.getElementById('burger');
  var mob    = document.getElementById('mob');
  var mLinks = document.querySelectorAll('.ml');

  burger.addEventListener('click', function () {
    var open = mob.classList.toggle('open');
    document.body.style.overflow = open ? 'hidden' : '';
  });
  mLinks.forEach(function (l) {
    l.addEventListener('click', function () {
      mob.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  /* ── SMOOTH SCROLL ── */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); }
    });
  });

  /* ── SKILL BARS ── */
  var fills = document.querySelectorAll('.sfill');
  var barIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) {
        en.target.style.width = en.target.dataset.p + '%';
        barIO.unobserve(en.target);
      }
    });
  }, { threshold: 0.5 });
  fills.forEach(function (f) { barIO.observe(f); });

  /* ── SCROLL REVEAL ── */
  var revEls = document.querySelectorAll('.sk, .sc, .pc, .tl, .cc, .vlist li');
  revEls.forEach(function (el) { el.classList.add('rev'); });

  var revIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) {
        var idx = Array.from(en.target.parentElement.children).indexOf(en.target);
        en.target.style.transitionDelay = (idx * 0.055) + 's';
        en.target.classList.add('in');
        revIO.unobserve(en.target);
      }
    });
  }, { threshold: 0.12 });
  revEls.forEach(function (el) { revIO.observe(el); });

  /* ── ACTIVE NAV ── */
  var secs  = document.querySelectorAll('section[id]');
  var navAs = document.querySelectorAll('.nav-links a');
  var secIO = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) {
        navAs.forEach(function (a) {
          a.style.color = (a.getAttribute('href') === '#' + en.target.id)
            ? 'var(--ink)' : '';
        });
      }
    });
  }, { threshold: 0.45 });
  secs.forEach(function (s) { secIO.observe(s); });

  /* ── BADGE PARALLAX ── */
  var badge = document.getElementById('heroBadge');
  if (badge) {
    window.addEventListener('scroll', function () {
      badge.style.transform = 'translateY(calc(-50% + ' + (window.scrollY * 0.07) + 'px))';
    }, { passive: true });
  }

  console.log('%c ĐD. %c Portfolio ready',
    'background:#111110;color:#f9f8f6;padding:3px 8px;border-radius:4px;font-family:serif;letter-spacing:.05em;',
    'color:#111110;');
}());
