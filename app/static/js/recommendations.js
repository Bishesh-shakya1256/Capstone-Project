const API_URL   = '/api/plants';
const GRADIENTS = ['grad-1','grad-2','grad-3','grad-4','grad-5','grad-6'];
const EMOJIS    = ['🌿','🌱','🌾','🍃','🌺','🌸','🌻','🌼','🌵','🎋','🪴','🌳'];

// Map of plant_id → plant object for fast lookup
const plantMap = {};

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function isLoggedIn() {
  try { return !!JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { return false; }
}

// ── Prefs / filtering ─────────────────────────────────────────────────────────

function getPrefs() {
  try { return JSON.parse(sessionStorage.getItem('plantPrefs') || '{}'); } catch { return {}; }
}

function mapLight(v) { return v==='direct'?'High':v==='indirect'?'Medium':v==='low'?'Low':null; }
function mapCare(v)  { return v==='low'?'Low':v==='medium'?'Medium':v==='high'?'High':null; }
function mapSize(v)  { return v==='small'?'Small':v==='medium'?'Medium':v==='large'?'Large':null; }
function mapExp(v)   { return v==='beginner'?'Low':v==='some'?'Medium':null; }

function scorePlant(plant, prefs) {
  let matches = 0, total = 0;
  if (prefs.light) { total++; if (plant.light_requirement === mapLight(prefs.light)) matches++; }
  if (prefs.care)  { total++; if (plant.maintenance_level  === mapCare(prefs.care))  matches++; }
  if (prefs.size)  { total++; if (plant.size_category       === mapSize(prefs.size))  matches++; }
  if (prefs.pets)  { total++; if (prefs.pets==='yes'&&plant.toxicity_level==='Non-toxic') matches++; if (prefs.pets==='no') matches++; }
  // Experience is a scoring bonus (not a hard filter) to avoid conflicts with care
  if (prefs.experience === 'beginner' && plant.maintenance_level === 'Low') matches++;
  if (prefs.experience === 'some' && plant.maintenance_level !== 'High') matches++;
  if (prefs.experience) total++;
  return total === 0 ? 100 : Math.round((matches / total) * 100);
}

function filterAndRank(plants, prefs) {
  let list = plants;

  // Hard filters — only show plants that match every selected preference
  if (prefs.pets  === 'yes')            list = list.filter(p => p.toxicity_level    === 'Non-toxic');
  if (prefs.light)                       list = list.filter(p => p.light_requirement === mapLight(prefs.light));
  if (prefs.care)                        list = list.filter(p => p.maintenance_level  === mapCare(prefs.care));
  if (prefs.size)                        list = list.filter(p => p.size_category      === mapSize(prefs.size));

  // Score remaining plants (experience boosts ranking but doesn't exclude) and sort
  return list
    .map(p => ({ ...p, _score: scorePlant(p, prefs) }))
    .sort((a, b) => b._score - a._score || a.plant_name.localeCompare(b.plant_name));
}

// ── Card rendering ────────────────────────────────────────────────────────────

function buildTags(plant) {
  const t = [];
  if (plant.light_requirement) t.push(plant.light_requirement + ' Light');
  if (plant.maintenance_level) t.push(plant.maintenance_level + ' Care');
  if (plant.growth_rate)       t.push(plant.growth_rate + ' Growth');
  if (plant.toxicity_level === 'Non-toxic') t.push('Pet-Safe');
  return t.slice(0, 3);
}

function buildDesc(plant) {
  const light  = (plant.light_requirement || 'moderate').toLowerCase();
  const water  = (plant.watering_frequency || 'weekly').toLowerCase();
  const growth = (plant.growth_rate || 'moderate').toLowerCase();
  const safe   = plant.toxicity_level === 'Non-toxic' ? 'Safe for pets.' : 'Keep away from pets.';
  return `A ${growth} growing plant that thrives in ${light} light. Water ${water}. ${safe}`;
}

function renderCard(plant, index) {
  const grad  = GRADIENTS[index % GRADIENTS.length];
  const emoji = EMOJIS[index % EMOJIS.length];
  const saved = isSaved(plant.plant_id);
  const hasImg = plant.image_url;

  return `
    <div class="card plant-card">
      <div class="plant-card-img ${hasImg ? '' : grad}" style="${hasImg ? 'padding:0;overflow:hidden' : ''}">
        ${hasImg
          ? `<img src="${esc(plant.image_url)}" alt="${esc(plant.plant_name)}"
                  style="width:100%;height:100%;object-fit:cover"
                  onerror="this.parentElement.classList.add('${grad}');this.style.display='none';this.parentElement.innerHTML+='<span style=\\'font-size:72px;line-height:1\\'>${emoji}</span>'">`
          : `<span style="font-size:72px;line-height:1">${emoji}</span>`}
      </div>
      <div class="plant-card-body">
        <div class="plant-card-top">
          <h3>${esc(plant.plant_name)}</h3>
          <span class="match-badge">${plant._score}% Match</span>
        </div>
        <p class="plant-desc">${esc(buildDesc(plant))}</p>
        <div class="plant-tags">
          ${buildTags(plant).map(t => `<span class="plant-tag">${esc(t)}</span>`).join('')}
        </div>
        <div class="plant-actions">
          ${isLoggedIn() ? `<button class="btn ${saved?'btn-green':'btn-dark'} btn-sm save-btn"
            data-id="${plant.plant_id}" style="flex:1">
            ${saved ? '✓ Saved' : 'Save'}
          </button>` : ''}
          <button class="btn btn-green btn-sm details-btn"
            data-id="${plant.plant_id}" style="flex:1">
            View Details
          </button>
        </div>
      </div>
    </div>`;
}

// ── Modal ─────────────────────────────────────────────────────────────────────

let modalEl = null;

function getModal() {
  if (modalEl) return modalEl;

  modalEl = document.createElement('div');
  modalEl.className = 'modal-overlay';
  modalEl.innerHTML = `
    <div class="modal-box">
      <button class="modal-close-btn" id="modal-close">✕</button>
      <div id="modal-content"></div>
    </div>`;
  document.body.appendChild(modalEl);

  document.getElementById('modal-close').addEventListener('click', closeModal);
  modalEl.addEventListener('click', e => { if (e.target === modalEl) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  return modalEl;
}

function showModal(plant) {
  const modal   = getModal();
  const content = document.getElementById('modal-content');
  const saved   = isSaved(plant.plant_id);

  const toxColor = plant.toxicity_level === 'Non-toxic' ? 'var(--green)' : '#f87171';
  const toxBg    = plant.toxicity_level === 'Non-toxic' ? 'rgba(16,185,129,.15)' : 'rgba(248,113,113,.15)';

  const fields = [
    ['Growth Rate',     plant.growth_rate],
    ['Light',           plant.light_requirement],
    ['Watering',        plant.watering_frequency],
    ['Maintenance',     plant.maintenance_level],
    ['Size',            plant.size_category],
    ['Humidity',        plant.humidity_requirement],
    ['Temperature',     plant.temperature_range],
    ['Category',        plant.category_name],
  ];

  content.innerHTML = `
    <div class="modal-header">
      <div>
        <h2 class="modal-plant-name">${esc(plant.plant_name)}</h2>
        <p class="modal-plant-sub">${esc(plant.category_name || 'General')}</p>
      </div>
      <span style="padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700;
                   background:${toxBg};color:${toxColor};white-space:nowrap;flex-shrink:0">
        ${esc(plant.toxicity_level || 'Unknown')}
      </span>
    </div>
    ${plant.image_url ? `<img class="modal-plant-img" src="${esc(plant.image_url)}" alt="${esc(plant.plant_name)}" onerror="this.style.display='none'">` : ''}
    <div class="modal-grid">
      ${fields.map(([label, val]) => `
        <div class="modal-detail">
          <div class="modal-detail-label">${esc(label)}</div>
          <div class="modal-detail-value">${esc(val) || '—'}</div>
        </div>`).join('')}
    </div>
    <div class="plant-actions" style="margin-top:24px">
      ${isLoggedIn() ? `<button id="modal-save-btn" data-id="${plant.plant_id}"
        class="btn ${saved?'btn-green':'btn-dark'} btn-sm" style="flex:1">
        ${saved ? '✓ Saved' : 'Save Plant'}
      </button>` : ''}
    </div>`;

  modal.classList.add('open');
  document.body.style.overflow = 'hidden';

  var modalSaveBtn = document.getElementById('modal-save-btn');
  if (modalSaveBtn) {
    modalSaveBtn.addEventListener('click', () => {
      const nowSaved = toggleSaved(plant);
      syncSaveState(plant.plant_id, nowSaved);
      showToast(nowSaved ? 'Plant saved!' : 'Plant removed.', 'success');
    });
  }
}

function closeModal() {
  if (modalEl) modalEl.classList.remove('open');
  document.body.style.overflow = '';
}

// Sync save button state across card + modal
function syncSaveState(plantId, saved) {
  // Card button
  const cardBtn = document.querySelector(`.save-btn[data-id="${plantId}"]`);
  if (cardBtn) {
    cardBtn.textContent   = saved ? '✓ Saved' : 'Save';
    cardBtn.className     = `btn ${saved?'btn-green':'btn-dark'} btn-sm save-btn`;
    cardBtn.style.flex    = '1';
  }
  // Modal button
  const modalBtn = document.getElementById('modal-save-btn');
  if (modalBtn && String(modalBtn.dataset.id) === String(plantId)) {
    modalBtn.textContent  = saved ? '✓ Saved' : 'Save Plant';
    modalBtn.className    = `btn ${saved?'btn-green':'btn-dark'} btn-sm`;
    modalBtn.style.flex   = '1';
  }
}

// ── Event wiring ──────────────────────────────────────────────────────────────

function wireButtons(grid) {
  grid.querySelectorAll('.save-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const plant = plantMap[parseInt(btn.dataset.id)];
      if (!plant) return;
      const nowSaved = toggleSaved(plant);
      syncSaveState(plant.plant_id, nowSaved);
      showToast(nowSaved ? 'Plant saved!' : 'Plant removed.', 'success');
    });
  });

  grid.querySelectorAll('.details-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const plant = plantMap[parseInt(btn.dataset.id)];
      if (plant) showModal(plant);
    });
  });
}

// ── Pagination + Search ───────────────────────────────────────────────────────

const PER_PAGE = 12;
let allRanked    = [];
let filtered     = [];
let currentPage  = 1;
let searchQuery  = '';

function applySearch() {
  const q = searchQuery.trim().toLowerCase();
  filtered = q ? allRanked.filter(p => p.plant_name.toLowerCase().includes(q)) : allRanked;
  currentPage = 1;
  renderPage(currentPage);
  renderPagination(filtered.length);
}

function renderPage(page) {
  const grid  = document.getElementById('recs-grid');
  const start = (page - 1) * PER_PAGE;
  const items = filtered.slice(start, start + PER_PAGE);

  if (items.length === 0) {
    const safeQ = searchQuery.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:48px 0">
      <p class="text-muted">No plants found for "<strong>${safeQ}</strong>".</p></div>`;
    return;
  }

  grid.innerHTML = items.map((p, i) => renderCard(p, start + i)).join('');
  wireButtons(grid);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderPagination(total) {
  const container = document.getElementById('recs-pagination');
  const totalPages = Math.ceil(total / PER_PAGE);

  if (totalPages <= 1) { container.innerHTML = ''; return; }

  const pages = [];

  // Build page number list: always show first, last, current ±2, with ellipsis
  const range = new Set([1, totalPages]);
  for (let i = Math.max(2, currentPage - 2); i <= Math.min(totalPages - 1, currentPage + 2); i++) range.add(i);
  const sorted = [...range].sort((a, b) => a - b);

  sorted.forEach((p, idx) => {
    if (idx > 0 && sorted[idx - 1] !== p - 1) {
      pages.push(`<button disabled>…</button>`);
    }
    pages.push(`<button class="${p === currentPage ? 'active' : ''}" data-page="${p}">${p}</button>`);
  });

  container.innerHTML = `
    <button id="pg-prev" ${currentPage === 1 ? 'disabled' : ''}>&larr; Prev</button>
    ${pages.join('')}
    <button id="pg-next" ${currentPage === totalPages ? 'disabled' : ''}>Next &rarr;</button>
    <span class="page-info">Page ${currentPage} of ${totalPages} &nbsp;&middot;&nbsp; ${total} plant${total !== 1 ? 's' : ''}</span>`;

  container.querySelectorAll('[data-page]').forEach(btn => {
    btn.addEventListener('click', () => {
      currentPage = parseInt(btn.dataset.page);
      renderPage(currentPage);
      renderPagination(total);
    });
  });

  document.getElementById('pg-prev').addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; renderPage(currentPage); renderPagination(total); }
  });
  document.getElementById('pg-next').addEventListener('click', () => {
    if (currentPage < totalPages) { currentPage++; renderPage(currentPage); renderPagination(total); }
  });
}

// ── Active filter chips ───────────────────────────────────────────────────────

const PREF_LABELS = {
  light:      { direct: 'Direct Light', indirect: 'Indirect Light', low: 'Low Light' },
  care:       { low: 'Low Care', medium: 'Medium Care', high: 'High Care' },
  size:       { small: 'Small Plants', medium: 'Medium Plants', large: 'Large Plants' },
  pets:       { yes: 'Pet-Safe Only', no: 'No Pets' },
  experience: { beginner: 'Beginner', some: 'Some Experience', expert: 'Expert' },
};

function removeFilter(key) {
  const prefs = getPrefs();
  prefs[key] = '';
  sessionStorage.setItem('plantPrefs', JSON.stringify(prefs));
  syncPrefsToBackend(prefs);
  location.reload();
}

function clearAllFilters() {
  sessionStorage.removeItem('plantPrefs');
  syncPrefsToBackend({});
  location.reload();
}

function syncPrefsToBackend(prefs) {
  let user;
  try { user = JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { return; }
  if (!user) return;
  if (prefs.light && prefs.care && prefs.size) {
    const lightToBackend = { low: 'Low', indirect: 'Medium', direct: 'High' };
    const careToBackend  = { low: 'Low', medium: 'Medium', high: 'High' };
    const sizeToBackend  = { small: 'Small', medium: 'Medium', large: 'Large' };
    fetch('/api/preferences', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        preferred_light:       lightToBackend[prefs.light] || prefs.light,
        preferred_maintenance: careToBackend[prefs.care] || prefs.care,
        preferred_size:        sizeToBackend[prefs.size] || prefs.size,
        pet_friendly_required: prefs.pets === 'yes',
      }),
    }).catch(() => {});
  } else {
    fetch('/api/preferences', { method: 'DELETE', credentials: 'same-origin' }).catch(() => {});
  }
}

function renderActiveFilters(prefs) {
  const container = document.getElementById('active-filters');
  const chips = Object.entries(prefs)
    .filter(([, v]) => v)
    .map(([key, val]) => {
      const label = PREF_LABELS[key]?.[val] || val;
      return `<span class="filter-chip">${label}
        <button data-key="${key}" title="Remove filter">✕</button>
      </span>`;
    });

  if (chips.length === 0) { container.innerHTML = ''; return; }

  container.innerHTML = chips.join('') +
    `<button class="btn btn-dark btn-sm" id="clear-all-filters" style="font-size:12px;padding:4px 12px">Clear All</button>`;

  container.querySelectorAll('[data-key]').forEach(btn => {
    btn.addEventListener('click', () => removeFilter(btn.dataset.key));
  });

  document.getElementById('clear-all-filters').addEventListener('click', clearAllFilters);
}

// ── Search wiring ─────────────────────────────────────────────────────────────

function wireSearch() {
  const input = document.getElementById('plant-search');
  const clear = document.getElementById('search-clear');

  input.addEventListener('input', () => {
    searchQuery = input.value;
    clear.style.display = searchQuery ? 'block' : 'none';
    applySearch();
  });

  clear.addEventListener('click', () => {
    input.value = '';
    searchQuery = '';
    clear.style.display = 'none';
    applySearch();
    input.focus();
  });
}

// ── Load ──────────────────────────────────────────────────────────────────────

const lightFromBackend = { Low: 'low', Medium: 'indirect', High: 'direct' };
const careFromBackend  = { Low: 'low', Medium: 'medium', High: 'high' };
const sizeFromBackend  = { Small: 'small', Medium: 'medium', Large: 'large' };

async function loadRecommendations() {
  const grid     = document.getElementById('recs-grid');
  const subtitle = document.getElementById('recs-subtitle');

  grid.innerHTML = `<div class="gs-spinner" style="grid-column:1/-1">
    <div class="gs-spinner-ring"></div>
    <span class="gs-spinner-text">Loading plants…</span>
  </div>`;

  // If logged in, sync prefs from backend into sessionStorage
  try {
    let user;
    try { user = JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { /* ignore */ }
    if (user) {
      const prefRes = await fetch('/api/preferences');
      const prefData = await prefRes.json();
      if (prefData.success && prefData.preference) {
        const p = prefData.preference;
        const prefs = {
          light:      lightFromBackend[p.preferred_light] || '',
          care:       careFromBackend[p.preferred_maintenance] || '',
          size:       sizeFromBackend[p.preferred_size] || '',
          pets:       p.pet_friendly_required ? 'yes' : 'no',
          experience: (getPrefs().experience || ''),
        };
        sessionStorage.setItem('plantPrefs', JSON.stringify(prefs));
      }
    }
  } catch { /* offline — keep sessionStorage version */ }

  try {
    const res    = await fetch(API_URL);
    const data   = await res.json();
    const plants = Array.isArray(data) ? data : (data.plants ?? []);
    const prefs  = getPrefs();
    allRanked    = filterAndRank(plants, prefs);
    filtered     = allRanked;

    allRanked.forEach(p => { plantMap[p.plant_id] = p; });

    if (allRanked.length === 0) {
      subtitle.textContent = 'No plants matched your filters — try adjusting your preferences.';
      grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:48px 0">
          <p class="text-muted" style="margin-bottom:16px">No plants matched your criteria.</p>
          <a href="query.html" class="btn btn-green btn-sm">Refine Search</a>
        </div>`;
      return;
    }

    const hasPrefs = Object.values(prefs).some(v => v !== '');
    subtitle.textContent = hasPrefs
      ? `${allRanked.length} plant${allRanked.length !== 1 ? 's' : ''} matched your preferences`
      : `Showing all ${allRanked.length} plants — use Refine Search to filter by your space and lifestyle`;

    renderActiveFilters(prefs);
    wireSearch();

    currentPage = 1;
    renderPage(currentPage);
    renderPagination(filtered.length);

  } catch (err) {
    console.error(err);
    subtitle.textContent = 'Could not load plants.';
    grid.innerHTML = `<p class="text-muted"
      style="grid-column:1/-1;text-align:center;padding:48px 0">
      Failed to load plants. Please check your connection and try again.</p>`;
  }
}

loadRecommendations();
