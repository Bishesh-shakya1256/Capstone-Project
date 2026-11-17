/* ── Toast notifications ──────────────────────────────────────────────────── */
(function () {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const ICONS = {
    success: '&#10003;',
    error:   '&#10007;',
    info:    '&#8505;',
  };

  window.showToast = function (message, type = 'info', duration = 3500) {
    const toast = document.createElement('div');
    toast.className = 'gs-toast gs-toast--' + type;
    toast.innerHTML =
      '<span class="gs-toast-icon">' + (ICONS[type] || ICONS.info) + '</span>' +
      '<span class="gs-toast-msg">' + message + '</span>' +
      '<button class="gs-toast-close" aria-label="Close">&times;</button>';

    container.appendChild(toast);

    /* trigger enter animation */
    requestAnimationFrame(function () { toast.classList.add('gs-toast--show'); });

    function dismiss() {
      toast.classList.remove('gs-toast--show');
      toast.classList.add('gs-toast--hide');
      toast.addEventListener('transitionend', function () { toast.remove(); });
    }

    toast.querySelector('.gs-toast-close').addEventListener('click', dismiss);
    if (duration > 0) setTimeout(dismiss, duration);
  };
})();

/* ── Confirm modal (replaces window.confirm) ────────────────────────────── */
window.confirmToast = function (message) {
  return new Promise(function (resolve) {
    const overlay = document.createElement('div');
    overlay.className = 'gs-confirm-overlay';
    overlay.innerHTML =
      '<div class="gs-confirm-box">' +
        '<p class="gs-confirm-msg">' + message + '</p>' +
        '<div class="gs-confirm-actions">' +
          '<button class="btn btn-dark btn-sm" data-action="cancel">Cancel</button>' +
          '<button class="btn btn-green btn-sm" data-action="confirm">Confirm</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);
    requestAnimationFrame(function () { overlay.classList.add('gs-confirm-overlay--show'); });

    function close(val) {
      overlay.classList.remove('gs-confirm-overlay--show');
      overlay.addEventListener('transitionend', function () { overlay.remove(); });
      resolve(val);
    }

    overlay.querySelector('[data-action="cancel"]').addEventListener('click', function () { close(false); });
    overlay.querySelector('[data-action="confirm"]').addEventListener('click', function () { close(true); });
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(false); });
  });
};

/* ── Prompt modal (replaces window.prompt) ──────────────────────────────── */
window.promptToast = function (message, defaultValue) {
  defaultValue = defaultValue || '';
  return new Promise(function (resolve) {
    var overlay = document.createElement('div');
    overlay.className = 'gs-confirm-overlay';
    overlay.innerHTML =
      '<div class="gs-confirm-box">' +
        '<p class="gs-confirm-msg">' + message + '</p>' +
        '<input type="text" class="gs-prompt-input" value="' + defaultValue.replace(/"/g, '&quot;') + '" />' +
        '<div class="gs-confirm-actions">' +
          '<button class="btn btn-dark btn-sm" data-action="cancel">Cancel</button>' +
          '<button class="btn btn-green btn-sm" data-action="confirm">OK</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);
    requestAnimationFrame(function () { overlay.classList.add('gs-confirm-overlay--show'); });

    var input = overlay.querySelector('.gs-prompt-input');
    input.focus();
    input.select();

    function close(val) {
      overlay.classList.remove('gs-confirm-overlay--show');
      overlay.addEventListener('transitionend', function () { overlay.remove(); });
      resolve(val);
    }

    overlay.querySelector('[data-action="cancel"]').addEventListener('click', function () { close(null); });
    overlay.querySelector('[data-action="confirm"]').addEventListener('click', function () { close(input.value); });
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(null); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') close(input.value); });
  });
};
