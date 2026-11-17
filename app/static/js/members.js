const MAX_PLANTS = 62;
const USERS_API  = '/api/users';

// ── API helpers ───────────────────────────────────────────────────────────────

async function apiGet() {
  const res = await fetch(USERS_API);
  if (!res.ok) throw new Error('fetch failed');
  return res.json();
}

async function apiPost(data) {
  const res = await fetch(USERS_API, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(data),
  });
  return { ok: res.ok, status: res.status, data: await res.json() };
}

async function apiPut(id, data) {
  const res = await fetch(`${USERS_API}/${id}`, {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(data),
  });
  return { ok: res.ok, data: await res.json() };
}

async function apiDelete(id) {
  const res = await fetch(`${USERS_API}/${id}`, { method: 'DELETE' });
  return res.ok;
}

// ── State ─────────────────────────────────────────────────────────────────────

const state = { users: [], filter: 'all', search: '' };

// ── Helpers ───────────────────────────────────────────────────────────────────

function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function nameToInitials(name) {
  const parts = name.trim().split(/\s+/);
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : name.slice(0, 2).toUpperCase();
}

const PALETTES = [
  { bg: '#0d2e2e', fg: '#2dce89' }, { bg: '#1e1040', fg: '#8b6fdf' },
  { bg: '#0d1e30', fg: '#4a9eff' }, { bg: '#2e1040', fg: '#e07aff' },
  { bg: '#1a2010', fg: '#a3e050' }, { bg: '#301820', fg: '#ff8a70' },
];

function getVisible() {
  return state.users.filter(u => {
    if (state.filter !== 'all' && u.status !== state.filter) return false;
    if (state.search) {
      const q = state.search.toLowerCase();
      return u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
    }
    return true;
  });
}

// ── Render ────────────────────────────────────────────────────────────────────

function renderRow(u) {
  const pct    = Math.round((u.plants / MAX_PLANTS) * 100);
  const barCls = u.plants < 10 ? 'bar-fill low' : 'bar-fill';
  return `
    <tr data-id="${u.id}">
      <td>
        <div class="user-cell">
          <div class="avatar" style="background:${esc(u.bg)};color:${esc(u.fg)};">${esc(u.initials)}</div>
          <div>
            <div class="user-name">${esc(u.name)}</div>
            <div class="user-email">${esc(u.email)}</div>
          </div>
        </div>
      </td>
      <td>
        ${u.role === 'Admin'
          ? '<span class="role-badge" style="background:rgba(139,111,223,.18);color:#a78bfa;border:1px solid rgba(139,111,223,.3)">Admin</span>'
          : '<span class="role-badge">Member</span>'}
      </td>
      <td><span class="status-badge ${esc(u.status)}"><span class="dot"></span>${esc(cap(u.status))}</span></td>
      <td><div class="date-cell">${esc(u.joined)}</div></td>
      <td><div class="last-active">${esc(u.lastActive)}</div></td>
      <td>
        <div class="plants-cell">
          <div class="bar-track"><div class="${barCls}" style="width:${pct}%"></div></div>
          <span class="plants-count">${u.plants}</span>
        </div>
      </td>
      <td>
        <button class="more-btn" data-id="${u.id}" title="Actions">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
        </button>
      </td>
    </tr>`;
}

function renderTable() {
  const tbody   = document.getElementById('members-tbody');
  const visible = getVisible();
  tbody.innerHTML = visible.length
    ? visible.map(renderRow).join('')
    : '<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--muted);">No users found</td></tr>';

  tbody.querySelectorAll('.more-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      openDropdown(btn, Number(btn.dataset.id));
    });
  });
}

function renderStats() {
  const u = state.users;
  document.getElementById('stat-total-users').textContent     = u.length;
  document.getElementById('stat-active-users').textContent    = u.filter(x => x.status === 'active').length;
  document.getElementById('stat-suspended-users').textContent = u.filter(x => x.status === 'suspended').length;
}

// ── Dropdown ──────────────────────────────────────────────────────────────────

let dropdown = null;
let activeDropdownId = null;

function buildDropdown() {
  const el = document.createElement('div');
  el.style.cssText = [
    'position:fixed', 'background:var(--surface2)', 'border:1px solid var(--border2)',
    'border-radius:10px', 'padding:6px', 'z-index:9999', 'min-width:164px',
    'box-shadow:0 8px 24px rgba(0,0,0,.45)', 'display:none',
  ].join(';');

  const ddBtn = (id, label, svgPath, color) => `
    <button id="${id}" style="
      display:flex;align-items:center;gap:8px;width:100%;background:none;border:none;
      color:${color};padding:8px 12px;border-radius:7px;
      font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;
      cursor:pointer;text-align:left;transition:background .15s;">
      <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2.5;flex-shrink:0">${svgPath}</svg>
      ${label}
    </button>`;

  el.innerHTML =
    ddBtn('dd-toggle', '', '', 'var(--text)') +
    '<div style="height:1px;background:var(--border);margin:4px 0"></div>' +
    ddBtn('dd-delete', 'Delete User',
      '<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>',
      'var(--red)');

  document.body.appendChild(el);

  el.querySelector('#dd-toggle').addEventListener('click', async () => {
    const user = state.users.find(u => u.id === activeDropdownId);
    if (!user) return closeDropdown();
    const newStatus = user.status === 'suspended' ? 'active' : 'suspended';
    closeDropdown();
    const result = await apiPut(user.id, { status: newStatus });
    if (result.ok) { user.status = newStatus; renderTable(); renderStats(); showToast('User ' + newStatus + '.', 'success'); }
  });

  el.querySelector('#dd-delete').addEventListener('click', async () => {
    if (!(await confirmToast('Delete this user? This cannot be undone.'))) return;
    const id = activeDropdownId;
    closeDropdown();
    const ok = await apiDelete(id);
    if (ok) {
      state.users = state.users.filter(u => u.id !== id);
      renderTable();
      renderStats();
      showToast('Member deleted.', 'success');
    }
  });

  return el;
}

function openDropdown(btn, userId) {
  if (!dropdown) dropdown = buildDropdown();
  if (activeDropdownId === userId && dropdown.style.display !== 'none') {
    closeDropdown(); return;
  }

  activeDropdownId = userId;
  const user   = state.users.find(u => u.id === userId);
  const toggle = dropdown.querySelector('#dd-toggle');

  if (user.status === 'suspended') {
    toggle.style.color = 'var(--accent)';
    toggle.querySelector('svg').innerHTML = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>';
    toggle.lastChild.textContent = ' Activate User';
  } else {
    toggle.style.color = 'var(--orange)';
    toggle.querySelector('svg').innerHTML = '<circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>';
    toggle.lastChild.textContent = ' Suspend User';
  }

  const rect = btn.getBoundingClientRect();
  dropdown.style.display = 'block';
  dropdown.style.top  = (rect.bottom + 6) + 'px';
  dropdown.style.left = (rect.right - 164) + 'px';
}

function closeDropdown() {
  if (dropdown) dropdown.style.display = 'none';
  activeDropdownId = null;
}

document.addEventListener('click', closeDropdown);

// ── Search ────────────────────────────────────────────────────────────────────

document.getElementById('members-search').addEventListener('input', e => {
  state.search = e.target.value.trim();
  renderTable();
});

// ── Filter tabs ───────────────────────────────────────────────────────────────

document.querySelectorAll('#member-data .filter-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('#member-data .filter-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const label = tab.textContent.trim().toLowerCase();
    state.filter = label === 'all' ? 'all' : label;
    renderTable();
  });
});

// ── Export CSV ────────────────────────────────────────────────────────────────

document.getElementById('members-export').addEventListener('click', () => {
  const headers = ['Name', 'Email', 'Role', 'Status', 'Joined', 'Last Active', 'Plants'];
  const rows    = state.users.map(u => [
    `"${u.name}"`, `"${u.email}"`, u.role, cap(u.status), u.joined, u.lastActive, u.plants,
  ]);
  const csv  = [headers, ...rows].map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a    = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: 'greenscape-members.csv',
  });
  a.click();
  URL.revokeObjectURL(a.href);
});

// ── Add User Modal ────────────────────────────────────────────────────────────

function openAddModal() {
  document.getElementById('add-member-form').reset();
  document.getElementById('add-member-error').style.display = 'none';
  document.getElementById('add-member-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
  document.getElementById('am-name').focus();
}

function closeAddModal() {
  document.getElementById('add-member-modal').classList.remove('open');
  document.body.style.overflow = '';
}

document.getElementById('add-member-btn').addEventListener('click', openAddModal);
document.getElementById('add-member-close').addEventListener('click', closeAddModal);
document.getElementById('add-member-cancel').addEventListener('click', closeAddModal);
document.getElementById('add-member-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('add-member-modal')) closeAddModal();
});

document.getElementById('add-member-form').addEventListener('submit', async function (e) {
  e.preventDefault();

  const name     = document.getElementById('am-name').value.trim();
  const email    = document.getElementById('am-email').value.trim().toLowerCase();
  const password = document.getElementById('am-password').value;
  const role     = document.getElementById('am-role').value;
  const status   = document.getElementById('am-status').value;
  const errEl    = document.getElementById('add-member-error');
  const submitBtn = this.querySelector('[type="submit"]');

  function showErr(msg) { errEl.textContent = msg; errEl.style.display = 'block'; }
  errEl.style.display = 'none';

  if (!name)               return showErr('Please enter a full name.');
  if (!email)              return showErr('Please enter an email address.');
  if (password.length < 6) return showErr('Password must be at least 6 characters.');

  const joined  = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  const palette = role === 'Admin'
    ? { bg: '#1e1040', fg: '#a78bfa' }
    : PALETTES[state.users.length % PALETTES.length];

  submitBtn.disabled    = true;
  submitBtn.textContent = 'Adding…';

  const result = await apiPost({
    name, email, password,
    initials:   nameToInitials(name),
    bg:         palette.bg,
    fg:         palette.fg,
    role, status, joined,
    lastActive: '—',
    plants:     0,
  });

  submitBtn.disabled    = false;
  submitBtn.textContent = 'Add User';

  if (result.status === 409) return showErr('A user with this email already exists.');
  if (!result.ok)            return showErr('Failed to add user. Please try again.');

  state.users.push(result.data);
  closeAddModal();
  renderTable();
  renderStats();
});

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
  const tbody = document.getElementById('members-tbody');
  tbody.innerHTML = '<tr><td colspan="7"><div class="gs-spinner"><div class="gs-spinner-ring"></div><span class="gs-spinner-text">Loading members…</span></div></td></tr>';

  try {
    state.users = await apiGet();
  } catch {
    tbody.innerHTML = `
      <tr><td colspan="7" style="text-align:center;padding:40px;color:var(--muted)">
        ⚠ Server not running.<br>
        <span style="font-size:12px;margin-top:6px;display:block">
          Open a terminal and run:
          <code style="background:rgba(255,255,255,.1);padding:2px 8px;border-radius:4px;margin-left:4px">python main.py</code>
        </span>
      </td></tr>`;
    renderStats();
    return;
  }

  renderTable();
  renderStats();
}

init();
