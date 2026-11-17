const stars  = document.querySelectorAll('.star');
const label  = document.getElementById('rating-label');
const labels = ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'];
let selected = 0;

stars.forEach(star => {
  const val = Number(star.dataset.star);

  star.addEventListener('mouseenter', () => highlight(val));
  star.addEventListener('mouseleave', () => highlight(selected));
  star.addEventListener('click', () => {
    selected = val;
    label.textContent = labels[val];
    highlight(val);
  });
});

function highlight(upTo) {
  stars.forEach(s => {
    s.classList.toggle('active', Number(s.dataset.star) <= upTo);
  });
}

async function submitFeedback(e) {
  e.preventDefault();
  if (!selected) { showToast('Please select a rating.', 'error'); return; }

  const comment = document.getElementById('message');
  const category = document.getElementById('category');
  const catText = category && category.value ? '[' + category.value + '] ' : '';
  const text = catText + labels[selected] + (comment && comment.value.trim() ? ': ' + comment.value.trim() : '');

  try {
    const res = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error('Failed');
  } catch {
    showToast('Failed to submit feedback.', 'error');
    return;
  }

  document.getElementById('feedback-form').classList.add('hidden');
  document.getElementById('success-msg').classList.remove('hidden');
  showToast('Thank you for your feedback!', 'success');
}
