(function () {
  let user;
  try { user = JSON.parse(sessionStorage.getItem('gsUser') || 'null'); } catch { return; }

  if (user) {
    // Check if session is still valid (not suspended/deleted)
    fetch('/api/auth/check', { credentials: 'same-origin' })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.authenticated) {
          sessionStorage.removeItem('gsUser');
          sessionStorage.removeItem('plantPrefs');
          if (data.reason === 'suspended') {
            sessionStorage.setItem('suspendToast', '1');
          }
          location.href = 'signin.html';
          return;
        }
        if (data.role !== 'Admin' && location.pathname.indexOf('adminpanel') !== -1) {
          location.href = 'dashboard.html';
        }
      })
      .catch(function () { /* offline — let them use the site */ });

    // Avatar initials
    document.querySelectorAll('.gs-initial').forEach(function (el) { el.textContent = user.initial; });

    // "Hi, Name!" greeting
    document.querySelectorAll('.gs-greeting').forEach(function (el) { el.textContent = 'Hi, ' + user.name + '!'; });

    // Profile page — card
    var pa = document.getElementById('gs-profile-avatar');
    if (pa) pa.textContent = user.initial;
    var pn = document.getElementById('gs-profile-name');
    if (pn) pn.textContent = user.name;
    var pe = document.getElementById('gs-profile-email');
    if (pe) pe.textContent = user.email;

    // Profile page — edit form pre-fill
    var peName = document.getElementById('p-name');
    if (peName) peName.value = user.name;
    var peEmail = document.getElementById('p-email');
    if (peEmail) peEmail.value = user.email;

    // Dashboard welcome heading
    var dw = document.getElementById('gs-dash-welcome');
    if (dw) dw.textContent = 'Welcome back, ' + user.name + '! 🌿';

    // Auth-state toggle: show logged-in elements, hide guest elements
    document.querySelectorAll('.nav-auth').forEach(function (el) { el.style.display = ''; });
    document.querySelectorAll('.nav-guest').forEach(function (el) { el.style.display = 'none'; });
  }

  // Logout — works whether button is always-visible or nav-auth-toggled
  var logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function (e) {
      e.preventDefault();
      sessionStorage.removeItem('gsUser');
      sessionStorage.removeItem('plantPrefs');
      location.href = 'index.html';
    });
  }
})();
