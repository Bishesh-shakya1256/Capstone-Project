function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function starsHTML(rating) {
  if (!rating) return '<span style="color:var(--muted)">—</span>';
  var out = '';
  for (var i = 1; i <= 5; i++) {
    out += '<span style="color:' + (i <= rating ? '#22c55e' : 'var(--muted)') + ';font-size:13px">&#9733;</span>';
  }
  return out;
}

async function loadFeedback() {
  var tbody = document.getElementById('feedback-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="5"><div class="gs-spinner"><div class="gs-spinner-ring"></div><span class="gs-spinner-text">Loading feedback…</span></div></td></tr>';

  try {
    var res = await fetch('/api/feedback', { credentials: 'same-origin' });
    if (!res.ok) {
      var msg = res.status === 403 ? 'Admin login required.' : 'Failed to load feedback.';
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--muted)">' + esc(msg) + '</td></tr>';
      return;
    }
    var data = await res.json();

    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--muted)">No feedback submitted yet.</td></tr>';
      return;
    }

    tbody.innerHTML = data.map(function(f) {
      return '<tr>' +
        '<td>' +
          '<div style="font-weight:600;font-size:13px">' + esc(f.user_name) + '</div>' +
          '<div style="font-size:11px;color:var(--muted)">' + esc(f.user_email) + '</div>' +
        '</td>' +
        '<td style="font-size:13px">' + esc(f.category) + '</td>' +
        '<td style="font-size:13px">' + starsHTML(f.rating) + '</td>' +
        '<td style="font-size:13px;max-width:400px;line-height:1.5">' + esc(f.comment) + '</td>' +
        '<td style="font-size:12px;color:var(--muted);white-space:nowrap">' + esc(f.created_at) + '</td>' +
      '</tr>';
    }).join('');

  } catch {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--muted)">Failed to load feedback.</td></tr>';
  }
}

document.querySelectorAll('.tab-btn').forEach(function(btn) {
  if (btn.dataset.tab === 'feedback-data') {
    btn.addEventListener('click', loadFeedback);
  }
});
