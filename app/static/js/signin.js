document.querySelectorAll('.toggle-pw').forEach(toggleBtn => {
  toggleBtn.addEventListener('click', () => {
    const pwInput = toggleBtn.parentElement.querySelector('input');

    if (!pwInput) return;

    const isPassword = pwInput.type === 'password';

    pwInput.type = isPassword ? 'text' : 'password';
    toggleBtn.textContent = isPassword ? '🙈' : '👁';
  });
});