function nameToInitials(name) {
  const parts = name.trim().split(/\s+/);
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : name.slice(0, 2).toUpperCase();
}

function showError(msg) {
  const el = document.getElementById('signup-error');
  if (el) { el.textContent = msg; el.style.display = 'block'; }
}

function clearError() {
  const el = document.getElementById('signup-error');
  if (el) el.style.display = 'none';
}

document.querySelectorAll('.toggle-pw').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = btn.closest('.input-wrap').querySelector('input');
    const showing = input.type === 'password';
    input.type    = showing ? 'text' : 'password';
    btn.textContent = showing ? '🙈' : '👁';
  });
});

document.getElementById('signup-form').addEventListener('submit', async function (e) {
  e.preventDefault();
  clearError();

  const name     = document.getElementById('su-name').value.trim();
  const email    = document.getElementById('su-email').value.trim().toLowerCase();
  const password = document.getElementById('su-password').value;
  const confirm  = document.getElementById('su-confirm').value;
  const terms    = document.getElementById('su-terms').checked;
  const btn      = this.querySelector('[type="submit"]');

  if (!name)                return showError('Please enter your full name.');
  if (!email)               return showError('Please enter your email address.');
  if (!password)            return showError('Please create a password.');
  if (password.length < 6)  return showError('Password must be at least 6 characters.');
  if (password !== confirm)  return showError('Passwords do not match.');
  if (!terms)               return showError('Please agree to the Terms of Service.');

  btn.disabled    = true;
  btn.textContent = 'Creating account…';

  try {
    const res = await fetch('/api/users', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        password,
        initials:   nameToInitials(name),
        bg:         '#0d2e2e',
        fg:         '#2dce89',
        role:       'Member',
        status:     'active',
        joined:     new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
        lastActive: 'Today',
        plants:     0,
      }),
    });

    const body = await res.json();

    if (res.status === 409) return showError(body.error || 'Email already registered.');
    if (!res.ok)            return showError('Registration failed. Please try again.');

    sessionStorage.setItem('gsUser', JSON.stringify({
      name:    body.name,
      initial: body.name[0].toUpperCase(),
      email:   body.email,
    }));

    window.location.href = 'index.html';

  } catch {
    showError('Cannot connect to server. Please try again.');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Create Account';
  }
});
