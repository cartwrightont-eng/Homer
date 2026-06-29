/* ============================================
   HOMERR — API Client v2
   ============================================ */

const API_BASE = '';

const Auth = {
  getToken:     ()              => localStorage.getItem('homerr_token'),
  getUser:      ()              => JSON.parse(localStorage.getItem('homerr_user') || 'null'),
  setSession:   (token, user)   => {
    localStorage.setItem('homerr_token', token);
    localStorage.setItem('homerr_user', JSON.stringify(user));
  },
  clearSession: ()              => {
    localStorage.removeItem('homerr_token');
    localStorage.removeItem('homerr_user');
  },
  isLoggedIn:   ()              => !!localStorage.getItem('homerr_token'),
  getRole:      ()              => { const u = Auth.getUser(); return u ? u.role : null; },
};

async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) { Auth.clearSession(); window.location.href = 'login.html'; return null; }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.error || `Request failed (${res.status})`);
  return data;
}

function requireAuth(redirectTo = 'login.html') {
  if (!Auth.isLoggedIn()) { window.location.href = redirectTo; return false; }
  return true;
}
function requireRole(role, redirectTo = 'index.html') {
  if (!requireAuth()) return false;
  if (Auth.getRole() !== role) { window.location.href = redirectTo; return false; }
  return true;
}
function redirectIfLoggedIn(to = 'index.html') {
  if (Auth.isLoggedIn()) window.location.href = to;
}

const API = {
  // Auth
  login:    (email, password) =>
    apiFetch('/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (name, email, password, role) =>
    apiFetch('/register', { method: 'POST', body: JSON.stringify({ name, email, password, role }) }),

  // Listings
  getListings:  (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([,v]) => v != null))
    ).toString();
    return apiFetch(`/accommodations${qs ? '?' + qs : ''}`);
  },
  getListing:    (id)   => apiFetch(`/accommodations/${id}`),
  createListing: (data) => apiFetch('/accommodations', { method: 'POST', body: JSON.stringify(data) }),
  getMyListings: ()     => apiFetch('/accommodations/landlord'),

  // Favourites
  getFavourites:    ()    => apiFetch('/favourites'),
  addFavourite:     (id)  => apiFetch(`/favourites/${id}`, { method: 'POST' }),
  removeFavourite:  (id)  => apiFetch(`/favourites/${id}`, { method: 'DELETE' }),

  // Applications
  getApplications:  ()     => apiFetch('/applications'),
  apply:            (accommodation_id, message) =>
    apiFetch('/applications', { method: 'POST', body: JSON.stringify({ accommodation_id, message }) }),

  // Chat
  getConversations: ()     => apiFetch('/conversations'),
  startConversation:(landlord_id, accommodation_id) =>
    apiFetch('/conversations', { method: 'POST', body: JSON.stringify({ landlord_id, accommodation_id }) }),
  getMessages:      (id)   => apiFetch(`/conversations/${id}/messages`),
  sendMessage:      (id, content) =>
    apiFetch(`/conversations/${id}/messages`, { method: 'POST', body: JSON.stringify({ content }) }),

  // Landlord wallet
  getWallet:        ()     => apiFetch('/wallet'),

  // Tours
  bookTour: (accommodation_id, tour_type, scheduled_at) =>
    apiFetch('/tours', { method: 'POST', body: JSON.stringify({ accommodation_id, tour_type, scheduled_at }) }),
};

// --- UI helpers ---
function showError(containerEl, message) {
  containerEl.innerHTML = `
    <div style="padding:12px 16px;background:#FEE2E2;border:1px solid #FECACA;border-radius:10px;font-size:0.83rem;color:#DC2626;margin-top:12px;">
      ${message}
    </div>`;
}
function showSuccess(containerEl, message) {
  containerEl.innerHTML = `
    <div style="padding:12px 16px;background:#DCFCE7;border:1px solid #BBF7D0;border-radius:10px;font-size:0.83rem;color:#16A34A;margin-top:12px;">
      ${message}
    </div>`;
}
function setLoading(btn, loading, originalText) {
  btn.disabled = loading;
  btn.textContent = loading ? 'Please wait…' : originalText;
}

function renderSkeletons(container, count = 3) {
  container.innerHTML = Array(count).fill(`
    <div class="property-card-skeleton">
      <div class="skeleton sk-image"></div>
      <div class="sk-body">
        <div class="skeleton sk-title"></div>
        <div class="skeleton sk-sub"></div>
        <div class="skeleton sk-price"></div>
        <div class="sk-tags">
          <div class="skeleton sk-tag"></div>
          <div class="skeleton sk-tag"></div>
        </div>
      </div>
    </div>`).join('');
}

function renderPropertyCard(p) {
  const img = (p.photos && p.photos[0])
    ? p.photos[0].photo_url
    : 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&q=80';
  const tags = [
    p.vacancy_status === 'available' ? 'Available' : 'Occupied',
    p.is_student_accommodation ? 'Student' : 'Standard',
  ].filter(Boolean);

  return `
    <a href="property.html?id=${p.id}" class="property-card reveal" style="text-decoration:none;">
      <div class="property-card__image">
        <img src="${img}" alt="${p.name}" loading="lazy" />
        <div class="property-card__badge">Verified</div>
        <button class="property-card__save" aria-label="Save property" data-id="${p.id}"
          onclick="event.preventDefault();toggleFavourite(this,${p.id})">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>
      </div>
      <div class="property-card__body">
        <div class="property-card__title">${p.name}</div>
        <div class="property-card__location">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
          </svg>
          ${p.location}
        </div>
        <div class="property-card__price">KES ${Number(p.price).toLocaleString()} <span>/ month</span></div>
        <div class="property-card__tags">
          ${tags.map(t => `<span class="tag">${t}</span>`).join('')}
        </div>
      </div>
    </a>`;
}

async function toggleFavourite(btn, id) {
  if (!Auth.isLoggedIn()) { window.location.href = 'login.html'; return; }
  const saved = btn.dataset.saved === 'true';
  try {
    if (saved) {
      await API.removeFavourite(id);
      btn.dataset.saved = 'false';
      btn.style.color = '';
    } else {
      await API.addFavourite(id);
      btn.dataset.saved = 'true';
      btn.style.color = 'var(--color-sage-deep)';
    }
  } catch(e) { console.error(e); }
}

function initNav() {
  const actionsEl = document.querySelector('.nav__actions');
  if (!actionsEl) return;
  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    const dashHref = user?.role === 'landlord' ? 'landlord-dashboard.html' : 'tenant-dashboard.html';
    actionsEl.innerHTML = `
      <a href="${dashHref}" class="btn btn--ghost">Dashboard</a>
      <button class="btn btn--primary" id="logout-btn">Sign out</button>`;
    document.getElementById('logout-btn')?.addEventListener('click', () => {
      Auth.clearSession();
      window.location.href = 'index.html';
    });
  }
}

function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('revealed'); observer.unobserve(e.target); }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.reveal:not(.revealed)').forEach(el => observer.observe(el));
}

window.apiFetch = apiFetch;
API.getLandlordAnalytics = () => apiFetch('/landlord/analytics');
API.getWallet = () => apiFetch('/wallet');
