const editPanel = document.getElementById('edit-panel');
const viewPanel = document.getElementById('view-panel');
const editBtn   = document.querySelector('[onclick="toggleEdit()"]');

function toggleEdit() {
  const editing = !editPanel.classList.contains('hidden');
  editPanel.classList.toggle('hidden', editing);
  viewPanel.classList.toggle('hidden', !editing);
  editBtn.textContent = editing ? 'Edit Profile' : 'Cancel Editing';
}

function saveEdit() {
  const newName = document.getElementById('p-name').value.trim();
  if (!newName) { showToast('Name cannot be empty.', 'error'); return; }

  try {
    const raw  = sessionStorage.getItem('gsUser');
    const user = raw ? JSON.parse(raw) : null;
    if (user) {
      user.name    = newName;
      user.initial = newName[0].toUpperCase();
      sessionStorage.setItem('gsUser', JSON.stringify(user));

      document.querySelectorAll('.gs-initial').forEach(el => { el.textContent = user.initial; });
      const pn = document.getElementById('gs-profile-name');
      if (pn) pn.textContent = newName;
      const pa = document.getElementById('gs-profile-avatar');
      if (pa) pa.textContent = user.initial;
    }
  } catch { /* sessionStorage unavailable */ }

  toggleEdit();
  showToast('Profile updated.', 'success');
}

// ── Saved Plants ──────────────────────────────────────────────────────────────

const GRADS  = ['grad-1','grad-2','grad-3','grad-4','grad-5','grad-6'];
const EMOJIS = ['🌿','🌱','🌾','🍃','🌺','🌸','🌻','🌼','🌵','🎋','🪴','🌳'];

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderSavedGrid() {
  const grid       = document.querySelector('.saved-grid');
  const countBadge = document.getElementById('saved-count');
  if (!grid) return;

  const saved = getSavedPlants();
  if (countBadge) countBadge.textContent = saved.length;

  if (saved.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;padding:24px 0;text-align:center">
        <p class="text-muted" style="margin-bottom:16px">No saved plants yet.</p>
        <a href="recommendations.html" class="btn btn-green btn-sm">Browse Plants</a>
      </div>`;
    return;
  }

  grid.innerHTML = saved.map((plant, i) => {
    const hasImg = plant.image_url;
    const imgSection = hasImg
      ? `<img src="${esc(plant.image_url)}" alt="${esc(plant.plant_name)}"
              style="width:100%;height:112px;object-fit:cover;border-radius:12px 12px 0 0"
              onerror="this.parentElement.className='plant-card-img ${GRADS[i % GRADS.length]}';this.style.display='none';this.parentElement.innerHTML+='<span style=\\'font-size:48px\\'>${EMOJIS[i % EMOJIS.length]}</span>'">`
      : `<span style="font-size:48px">${EMOJIS[i % EMOJIS.length]}</span>`;
    const imgClass = hasImg ? '' : GRADS[i % GRADS.length];

    return `
    <div class="card plant-card">
      <div class="plant-card-img ${imgClass}" style="height:112px;display:flex;align-items:center;justify-content:center;overflow:hidden">
        ${imgSection}
      </div>
      <div class="plant-card-body" style="padding:16px">
        <div class="plant-card-top">
          <h3 style="font-size:14px">${esc(plant.plant_name)}</h3>
          <span class="plant-tag" style="font-size:11px">${esc(plant.light_requirement || '')}</span>
        </div>
        <div class="plant-tags" style="margin:8px 0">
          <span class="plant-tag">${esc(plant.maintenance_level || '')} Care</span>
          ${plant.toxicity_level === 'Non-toxic' ? '<span class="plant-tag">Pet-Safe</span>' : ''}
        </div>
        <div class="plant-actions" style="margin-top:8px">
          <button class="btn btn-dark btn-sm remove-btn"
            data-id="${plant.plant_id}" style="flex:1;font-size:12px">Remove</button>
          <button class="btn btn-green btn-sm view-btn"
            data-id="${plant.plant_id}" style="flex:1;font-size:12px">Details</button>
        </div>
      </div>
    </div>`;
  }).join('');

  grid.querySelectorAll('.remove-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      removeSaved(parseInt(btn.dataset.id));
      renderSavedGrid();
      showToast('Plant removed from saved list.', 'success');
    });
  });

  grid.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const plant = saved.find(p => p.plant_id === parseInt(btn.dataset.id));
      if (plant) showPlantModal(plant);
    });
  });
}

// ── Modal ─────────────────────────────────────────────────────────────────────

function showPlantModal(plant) {
  let overlay = document.getElementById('profile-modal');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'profile-modal';
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal-box">
        <button class="modal-close-btn" id="profile-modal-close">✕</button>
        <div id="profile-modal-content"></div>
      </div>`;
    document.body.appendChild(overlay);
    document.getElementById('profile-modal-close')
      .addEventListener('click', () => {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
      });
    overlay.addEventListener('click', e => {
      if (e.target === overlay) {
        overlay.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  }

  const toxColor = plant.toxicity_level === 'Non-toxic' ? 'var(--green)' : '#f87171';
  const toxBg    = plant.toxicity_level === 'Non-toxic' ? 'rgba(16,185,129,.15)' : 'rgba(248,113,113,.15)';

  const fields = [
    ['Growth Rate',  plant.growth_rate],
    ['Light',        plant.light_requirement],
    ['Watering',     plant.watering_frequency],
    ['Maintenance',  plant.maintenance_level],
    ['Size',         plant.size_category],
    ['Humidity',     plant.humidity_requirement],
    ['Temperature',  plant.temperature_range],
    ['Category',     plant.category_name],
  ];

  document.getElementById('profile-modal-content').innerHTML = `
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
      ${fields.map(([l, v]) => `
        <div class="modal-detail">
          <div class="modal-detail-label">${esc(l)}</div>
          <div class="modal-detail-value">${esc(v) || '—'}</div>
        </div>`).join('')}
    </div>`;

  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

renderSavedGrid();

// ── Load preferences from backend ─────────────────────────────────────────────
const lightLabels = { Low: 'Low', Medium: 'Indirect', High: 'Direct' };
const careLabels  = { Low: 'Low', Medium: 'Medium', High: 'High' };
const sizeLabels  = { Small: 'Small', Medium: 'Medium', Large: 'Large' };

(async function loadPrefs() {
  let user;
  try { user = JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { /* ignore */ }
  if (!user) return;

  try {
    const res  = await fetch('/api/preferences', { credentials: 'same-origin' });
    const data = await res.json();
    if (data.success && data.preference) {
      const p = data.preference;
      document.getElementById('pref-light').textContent = lightLabels[p.preferred_light] || p.preferred_light;
      document.getElementById('pref-care').textContent  = careLabels[p.preferred_maintenance] || p.preferred_maintenance;
      document.getElementById('pref-size').textContent   = sizeLabels[p.preferred_size] || p.preferred_size;
      document.getElementById('pref-pets').textContent   = p.pet_friendly_required ? 'Yes' : 'No';
      if (p.experience_level) document.getElementById('pref-exp').textContent = p.experience_level;
      return;
    }
  } catch { /* offline */ }

  try {
    const prefs = JSON.parse(sessionStorage.getItem('plantPrefs') || '{}');
    const lightMap = { low: 'Low', indirect: 'Indirect', direct: 'Direct' };
    const careMap  = { low: 'Low', medium: 'Medium', high: 'High' };
    const sizeMap  = { small: 'Small', medium: 'Medium', large: 'Large' };
    if (prefs.light)      document.getElementById('pref-light').textContent = lightMap[prefs.light] || prefs.light;
    if (prefs.care)       document.getElementById('pref-care').textContent  = careMap[prefs.care] || prefs.care;
    if (prefs.size)       document.getElementById('pref-size').textContent   = sizeMap[prefs.size] || prefs.size;
    if (prefs.pets)       document.getElementById('pref-pets').textContent   = prefs.pets === 'yes' ? 'Yes' : 'No';
    if (prefs.experience) document.getElementById('pref-exp').textContent    = prefs.experience.charAt(0).toUpperCase() + prefs.experience.slice(1);
  } catch { /* ignore */ }
})();
