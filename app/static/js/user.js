// Show suspension toast if redirected from session check
(function () {
  if (sessionStorage.getItem('suspendToast') === '1') {
    sessionStorage.removeItem('suspendToast');
    setTimeout(function () { showToast('Your account has been suspended.', 'error'); }, 200);
  }
})();

document.getElementById('signin-form').addEventListener('submit', async function (e) {
  e.preventDefault();

  const email    = document.querySelector('#email').value.trim().toLowerCase();
  const password = document.querySelector('#password').value;
  const btn      = this.querySelector('[type="submit"]');

  btn.disabled    = true;
  btn.textContent = 'Signing in…';

  try {
    const res = await fetch('/api/users/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email, password }),
    });

    const body = await res.json();

    if (res.status === 401) { showToast(body.error || 'Invalid email or password.', 'error'); return; }
    if (res.status === 403) { showToast(body.error || 'Account suspended.', 'error'); return; }
    if (!res.ok)            { showToast('Login failed. Please try again.', 'error'); return; }

    sessionStorage.setItem('gsUser', JSON.stringify({
      name:    body.name,
      initial: body.name[0].toUpperCase(),
      email:   body.email,
      role:    body.role,
    }));

    window.location.href = body.role === 'Admin' ? 'adminpanel.html' : 'index.html';

  } catch {
    showToast('Cannot connect to server. Please try again.', 'error');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Sign In';
  }
});
