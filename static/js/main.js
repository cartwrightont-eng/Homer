/* ============================================
   HOMERR — Main JS
   Scroll reveal, nav, skeleton, interactions
   ============================================ */

'use strict';

// --- Scroll reveal (scale + blur in) ---
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('revealed');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

// --- Nav scroll shadow ---
const nav = document.querySelector('.glass-nav');
if (nav) {
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });
}

// --- Mobile nav toggle ---
const hamburger = document.querySelector('.nav__hamburger');
const navLinks  = document.querySelector('.nav__links');
const navActions = document.querySelector('.nav__actions');

if (hamburger) {
  hamburger.addEventListener('click', () => {
    const expanded = hamburger.getAttribute('aria-expanded') === 'true';
    hamburger.setAttribute('aria-expanded', String(!expanded));

    if (!expanded) {
      // inject mobile drawer if not exists
      let drawer = document.querySelector('.nav__drawer');
      if (!drawer) {
        drawer = document.createElement('div');
        drawer.className = 'nav__drawer glass';
        drawer.innerHTML = `
          <ul class="nav__drawer-links">
            <li><a href="/listings" class="nav__link">Browse</a></li>
            <li><a href="#" class="nav__link">How it works</a></li>
            <li><a href="#" class="nav__link">Pricing</a></li>
          </ul>
          <div class="nav__drawer-actions">
            <a href="/login" class="btn btn--ghost" style="width:100%;justify-content:center;">Sign in</a>
            <a href="/register" class="btn btn--primary" style="width:100%;justify-content:center;">List a property</a>
          </div>
        `;
        Object.assign(drawer.style, {
          position: 'fixed',
          top: '68px', left: '16px', right: '16px',
          borderRadius: '16px',
          padding: '24px',
          zIndex: '99',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        });
        document.body.appendChild(drawer);
      }
      drawer.style.display = 'flex';
    } else {
      const drawer = document.querySelector('.nav__drawer');
      if (drawer) drawer.style.display = 'none';
    }
  });
}

// --- Skeleton → real content swap ---
// Simulates async data load; replace with real fetch in Flask context
function initSkeletons() {
  const skeletonContainers = document.querySelectorAll('[data-skeleton]');
  skeletonContainers.forEach(container => {
    const delay = parseInt(container.dataset.skeletonDelay || '1200', 10);
    setTimeout(() => {
      container.classList.add('skeleton-loaded');
      const skels = container.querySelectorAll('.property-card-skeleton');
      skels.forEach(skel => {
        skel.style.opacity = '0';
        skel.style.transition = 'opacity 300ms ease';
        setTimeout(() => skel.remove(), 300);
      });
      const realCards = container.querySelectorAll('.property-card[data-deferred]');
      realCards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'scale(0.96)';
        card.style.filter = 'blur(4px)';
        card.style.transition = 'opacity 400ms ease, transform 400ms ease, filter 400ms ease';
        card.removeAttribute('data-deferred');
        setTimeout(() => {
          card.style.opacity = '1';
          card.style.transform = 'scale(1)';
          card.style.filter = 'blur(0)';
        }, i * 80 + 50);
      });
    }, delay);
  });
}

initSkeletons();

// --- Save / heart toggle on property cards ---
document.addEventListener('click', e => {
  const saveBtn = e.target.closest('.property-card__save');
  if (!saveBtn) return;
  const saved = saveBtn.dataset.saved === 'true';
  saveBtn.dataset.saved = String(!saved);
  saveBtn.innerHTML = !saved
    ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="#E53E3E" stroke="#E53E3E" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`
    : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
});

// --- Filter chips toggle ---
document.addEventListener('click', e => {
  const chip = e.target.closest('.filter-chip');
  if (!chip) return;
  const group = chip.closest('.filter-chips');
  if (!group) return;
  const isMulti = group.dataset.multi === 'true';
  if (!isMulti) group.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  chip.classList.toggle('active');
});

// --- Role selector on register ---
document.addEventListener('click', e => {
  const option = e.target.closest('.role-option');
  if (!option) return;
  const group = option.closest('.role-selector');
  if (!group) return;
  group.querySelectorAll('.role-option').forEach(o => o.classList.remove('selected'));
  option.classList.add('selected');
  const input = document.querySelector('input[name="role"]');
  if (input) input.value = option.dataset.role;
});

// --- Gallery thumbnail switcher ---
document.addEventListener('click', e => {
  const thumb = e.target.closest('.detail-gallery__thumb');
  if (!thumb) return;
  const gallery = thumb.closest('.detail-gallery');
  if (!gallery) return;
  const mainImg = gallery.querySelector('.detail-gallery__main img');
  const thumbImg = thumb.querySelector('img');
  if (mainImg && thumbImg) {
    const tmp = mainImg.src;
    mainImg.style.opacity = '0';
    mainImg.style.transition = 'opacity 250ms ease';
    setTimeout(() => {
      mainImg.src = thumbImg.src;
      mainImg.style.opacity = '1';
    }, 200);
  }
});

// --- Inquiry form basic validation ---
const inquiryForm = document.querySelector('.inquiry-form');
if (inquiryForm) {
  inquiryForm.addEventListener('submit', e => {
    e.preventDefault();
    const btn = inquiryForm.querySelector('[type="submit"]');
    if (!btn) return;
    btn.textContent = 'Sending…';
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = 'Message sent';
      btn.style.background = '#27AE60';
      btn.style.borderColor = '#27AE60';
    }, 1400);
  });
}

// --- Price range display ---
const rangeInputs = document.querySelectorAll('.range-input');
rangeInputs.forEach(input => {
  const display = document.querySelector(`[data-range-display="${input.id}"]`);
  if (!display) return;
  input.addEventListener('input', () => {
    display.textContent = `KES ${parseInt(input.value).toLocaleString()}`;
  });
});
