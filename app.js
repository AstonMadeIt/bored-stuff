// =========================
// Utility
// =========================
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

const state = {
  theme: (localStorage.getItem('theme') || 'light'),
  hydratedTikToks: new WeakSet()
};

// Apply persisted theme early
document.documentElement.setAttribute('data-theme', state.theme);
const themeRadios = $$('input[name="theme"]');
themeRadios.forEach(r => { r.checked = (r.value === state.theme); });

// =========================
// Loader (elevated)
// =========================
const loader = $('#loader');
const loaderProgress = $('.loader-progress');
let loaderPct = 0;
const loaderSim = setInterval(() => {
  loaderPct = Math.min(loaderPct + Math.random() * 12, 95);
  loaderProgress.style.width = `${loaderPct}%`;
}, 280);

window.addEventListener('load', () => {
  clearInterval(loaderSim);
  loaderProgress.style.width = '100%';
  setTimeout(() => loader.classList.add('hidden'), 450);
});

// =========================
// Progress bar on scroll
// =========================
const prog = $('.progress-bar');
const onScroll = () => {
  const h = document.documentElement;
  const scrolled = (h.scrollTop) / (h.scrollHeight - h.clientHeight);
  prog.style.transform = `scaleX(${scrolled})`;
};
document.addEventListener('scroll', onScroll, { passive: true });

// =========================
/* Back to top with circular progress */
// =========================
const backToTop = $('.back-to-top');
const ring = $('.progress-ring-progress');
const R = 24, C = 2 * Math.PI * R;
ring.style.strokeDasharray = `${C} ${C}`;
const backProgress = () => {
  const h = document.documentElement;
  const t = h.scrollTop;
  const m = h.scrollHeight - h.clientHeight;
  const p = m ? t / m : 0;
  ring.style.strokeDashoffset = `${C - p * C}`;
  if (t > 480) backToTop.classList.add('visible'); else backToTop.classList.remove('visible');
};
document.addEventListener('scroll', backProgress, { passive: true });
backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// =========================
/* Music (Tone.js or Howler.js not required) */
// =========================
const musicBtn = $('#music-toggle');
const volumeCtl = $('#volume-control');
const volSlider = $('#volume-slider');
let audioCtx, osc, gain;

function ensureAudio() {
  if (audioCtx) return;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  osc = audioCtx.createOscillator();
  gain = audioCtx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(222, audioCtx.currentTime);
  gain.gain.value = 0.0;
  osc.connect(gain).connect(audioCtx.destination);
  osc.start();
}

musicBtn.addEventListener('click', async () => {
  ensureAudio();
  const active = musicBtn.classList.toggle('active');
  musicBtn.setAttribute('aria-pressed', String(active));
  $('.music-toggle-text').textContent = active ? 'Music On' : 'Music Off';
  volumeCtl.classList.toggle('visible', active);
  if (active) {
    await audioCtx.resume();
    gain.gain.linearRampToValueAtTime(volSlider.value / 100 * 0.15, audioCtx.currentTime + 0.15);
  } else {
    gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.1);
  }
});
volSlider.addEventListener('input', () => {
  if (!gain) return;
  gain.gain.value = (volSlider.value / 100) * 0.15;
});

// =========================
/* Theme toggle (1% radio) */
// =========================
themeRadios.forEach(r => {
  r.addEventListener('change', (e) => {
    const val = e.target.value;
    document.documentElement.setAttribute('data-theme', val);
    localStorage.setItem('theme', val);
  });
});

// =========================
/* TikTok: poster-first hydration + in-viewport play/pause */
// =========================
function buildIframe(videoId) {
  const url = `https://www.tiktok.com/embed/v2/video/${videoId}?lang=en-US&autoplay=1&controls=1&muted=1`;
  const iframe = document.createElement('iframe');
  iframe.src = url;
  iframe.loading = 'lazy';
  iframe.title = 'TikTok video';
  iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
  iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
  iframe.setAttribute('allowfullscreen', '');
  return iframe;
}

function hydrateTikTok(card) {
  if (state.hydratedTikToks.has(card)) return;
  state.hydratedTikToks.add(card);

  const url = card.dataset.tiktokUrl || '';
  const vid = (url.match(/video\/(\d+)/) || [])[1];
  const posterBtn = card.querySelector('.ttk__poster');
  const posterImg = card.querySelector('.ttk__poster-img');
  const frame = card.querySelector('.ttk__frame');
  const err = card.querySelector('.ttk__error');
  posterImg.src = card.dataset.poster || '';

  if (!vid) {
    err.hidden = false;
    err.innerHTML = `<p>Couldn’t load video.</p><a href="${url}" target="_blank" rel="noopener">Open on TikTok</a>`;
    return;
  }

  // Swap poster → iframe
  posterBtn.hidden = true;
  frame.hidden = false;
  const iframe = buildIframe(vid);
  frame.appendChild(iframe);

  // Intersection play/pause (simulate loop by refresh on re-enter if needed)
  const LOOP_MS = 0; // set >0 (e.g., 60000) to “refresh loop” every minute
  let lastEnter = 0;
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        // play: reload src to ensure autoplay within viewport
        if (Date.now() - lastEnter > 2000) {
          const s = iframe.src;
          iframe.src = s; // idempotent “re-init”
          lastEnter = Date.now();
        }
      } else {
        // pause: navigate to about:blank then back (TikTok doesn’t expose pause API)
        const s = iframe.src;
        iframe.src = 'about:blank';
        requestAnimationFrame(() => { iframe.src = s; });
      }
    }
  }, { rootMargin: '50px 0px' });
  io.observe(iframe);

  if (LOOP_MS > 0) {
    setInterval(() => {
      const s = iframe.src;
      iframe.src = s; // refresh
    }, LOOP_MS);
  }
}

function initTikTok() {
  const cards = $$('.ttk');
  const prefersReduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Click to hydrate
  cards.forEach(card => {
    const posterBtn = card.querySelector('.ttk__poster');
    posterBtn.addEventListener('click', () => hydrateTikTok(card));
  });

  // Optional: auto-hydrate when entering viewport (exec-safe)
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) {
        if (!prefersReduced) hydrateTikTok(e.target);
      }
    }
  }, { rootMargin: '50px 0px' });

  cards.forEach(c => io.observe(c));
}
document.addEventListener('DOMContentLoaded', initTikTok);

// =========================
/* Fancy cursor hover states (optional, preserved) */
// =========================
(() => {
  const cursor = $('#custom-cursor');
  if (!cursor) return;
  let ticking = false;

  document.addEventListener('mousemove', (ev) => {
    if (ticking) return;
    window.requestAnimationFrame(() => {
      cursor.style.transform = `translate(${ev.clientX - 10}px, ${ev.clientY - 10}px)`;
      ticking = false;
    });
    ticking = true;
  }, { passive: true });

  ['a','button','input','[role="button"]','.press-link','.ttk__poster'].forEach(sel => {
    document.addEventListener('mouseover', e => { if (e.target.closest(sel)) cursor.classList.add('hover'); });
    document.addEventListener('mouseout',  e => { if (e.target.closest(sel)) cursor.classList.remove('hover'); });
  });
})();
