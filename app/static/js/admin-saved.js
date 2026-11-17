function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function loadAdminSaved() {
  const tbody   = document.getElementById('admin-saved-tbody');
  const countEl = document.getElementById('admin-saved-count');
  if (!tbody) return;

  const allSaved = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!key.startsWith('gsSaved_')) continue;
    const email = key.slice('gsSaved_'.length);
    try {
      const plants = JSON.parse(localStorage.getItem(key) || '[]');
      plants.forEach(p => allSaved.push({ ...p, _savedBy: email }));
    } catch {}
  }

  if (countEl) countEl.textContent = allSaved.length;

  var counts = {};
  allSaved.forEach(function(p) {
    var name = p.plant_name || ('Plant #' + p.plant_id);
    counts[name] = (counts[name] || 0) + 1;
  });
  var best = null, bestCount = 0;
  for (var name in counts) {
    if (counts[name] > bestCount) { best = name; bestCount = counts[name]; }
  }
  var msName = document.getElementById('saved-most-name');
  var msCount = document.getElementById('saved-most-count');
  if (msName) msName.textContent = best || '—';
  if (msCount) msCount.textContent = best ? bestCount + ' saves' : 'No saves yet';

  if (allSaved.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6"
      style="text-align:center;padding:40px;color:var(--muted)">
      No plants have been saved yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = allSaved.map(p => {
    const toxColor = p.toxicity_level === 'Non-toxic' ? '#2dce89' : '#e85555';
    const toxBg    = p.toxicity_level === 'Non-toxic' ? 'rgba(45,206,137,.15)' : 'rgba(232,85,85,.15)';
    const careColor = p.maintenance_level === 'Low' ? '#2dce89' : '#f7a94a';
    const careBg    = p.maintenance_level === 'Low' ? 'rgba(45,206,137,.15)' : 'rgba(247,169,74,.15)';
    return `
      <tr>
        <td>
          <div class="plant-name">${esc(p.plant_name)}</div>
          <div class="plant-latin">${esc(p.category_name || 'General')}</div>
        </td>
        <td class="cell-text">${esc(p.light_requirement || '—')}</td>
        <td>
          <span style="display:inline-block;padding:3px 10px;border-radius:6px;
            font-size:12px;font-weight:600;background:${careBg};color:${careColor}">
            ${esc(p.maintenance_level || '—')}
          </span>
        </td>
        <td class="cell-text">${esc(p.watering_frequency || '—')}</td>
        <td>
          <span style="display:inline-block;padding:3px 10px;border-radius:20px;
            font-size:12px;font-weight:600;background:${toxBg};color:${toxColor}">
            ${esc(p.toxicity_level || '—')}
          </span>
        </td>
        <td><div class="user-email">${esc(p._savedBy)}</div></td>
      </tr>`;
  }).join('');
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  if (btn.dataset.tab === 'saved-data') {
    btn.addEventListener('click', loadAdminSaved);
  }
});
