// ── Value mapping helpers ──────────────────────────────────────────────────────
const lightToBackend = { low: 'Low', indirect: 'Medium', direct: 'High' };
const careToBackend  = { low: 'Low', medium: 'Medium', high: 'High' };
const sizeToBackend  = { small: 'Small', medium: 'Medium', large: 'Large' };
const petsToBackend  = { yes: true, no: false };

const lightFromBackend = { Low: 'low', Medium: 'indirect', High: 'direct' };
const careFromBackend  = { Low: 'low', Medium: 'medium', High: 'high' };
const sizeFromBackend  = { Small: 'small', Medium: 'medium', Large: 'large' };

// ── UI helpers ────────────────────────────────────────────────────────────────
function prefillForm(prefs) {
  if (prefs.light && document.getElementById('light-select'))
    document.getElementById('light-select').value = prefs.light;
  if (prefs.size && document.getElementById('size-select'))
    document.getElementById('size-select').value = prefs.size;
  if (prefs.experience && document.getElementById('experience-select'))
    document.getElementById('experience-select').value = prefs.experience;

  ['care', 'pets'].forEach(name => {
    if (!prefs[name]) return;
    const radio = document.querySelector(`input[name="${name}"][value="${prefs[name]}"]`);
    if (radio) {
      radio.checked = true;
      radio.closest('.radio-option').classList.add('selected');
    }
  });
}

// ── Pre-fill from sessionStorage immediately (fast) ───────────────────────────
(function prefillLocal() {
  try {
    const prefs = JSON.parse(sessionStorage.getItem('plantPrefs') || '{}');
    if (Object.keys(prefs).length) prefillForm(prefs);
  } catch { /* ignore */ }
})();

// ── Load from backend (overrides sessionStorage for logged-in users) ──────────
(async function loadFromBackend() {
  let user;
  try { user = JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { return; }
  if (!user) return;

  try {
    const res = await fetch('/api/preferences');
    const data = await res.json();
    if (!data.success || !data.preference) return;

    const p = data.preference;
    const prefs = {
      light:      lightFromBackend[p.preferred_light] || '',
      care:       careFromBackend[p.preferred_maintenance] || '',
      size:       sizeFromBackend[p.preferred_size] || '',
      pets:       p.pet_friendly_required ? 'yes' : 'no',
      experience: '',  // experience is not stored in backend
    };
    sessionStorage.setItem('plantPrefs', JSON.stringify(prefs));
    prefillForm(prefs);
  } catch { /* offline or error — keep sessionStorage version */ }
})();

// ── Highlight radio-option rows when selected ─────────────────────────────────
document.querySelectorAll('.radio-options').forEach(group => {
  const options = group.querySelectorAll('.radio-option');
  options.forEach(option => {
    option.addEventListener('click', () => {
      const radio = option.querySelector('input[type="radio"]');
      radio.checked = true;
      options.forEach(o => o.classList.remove('selected'));
      option.classList.add('selected');
    });
  });
});

// ── Save preferences and navigate ─────────────────────────────────────────────
document.getElementById('get-recs-btn').addEventListener('click', async () => {
  const prefs = {
    light:      document.getElementById('light-select').value,
    care:       document.querySelector('input[name="care"]:checked')?.value || '',
    size:       document.getElementById('size-select').value,
    pets:       document.querySelector('input[name="pets"]:checked')?.value || '',
    experience: document.getElementById('experience-select').value,
  };

  // Always save to sessionStorage (works for guests too)
  sessionStorage.setItem('plantPrefs', JSON.stringify(prefs));

  // If logged in, also persist to backend database
  let user;
  try { user = JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { /* ignore */ }
  if (user && prefs.light && prefs.care && prefs.size) {
    try {
      await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferred_light:       lightToBackend[prefs.light] || prefs.light,
          preferred_maintenance: careToBackend[prefs.care] || prefs.care,
          preferred_size:        sizeToBackend[prefs.size] || prefs.size,
          pet_friendly_required: prefs.pets === 'yes',
        }),
      });
    } catch { /* save failed — sessionStorage still works for this session */ }
  }

  window.location.href = 'recommendations.html';
});
