document.addEventListener('DOMContentLoaded', () => {
  const announcement = document.querySelector('#announcement-form');
  const announcementFeedback = document.querySelector('#announcement-feedback');
  if (announcement) announcement.addEventListener('submit', async event => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(announcement));
    try {
      const result = await adminApiCall('/api/admin/announcements', { method: 'POST', body: JSON.stringify(payload) });
      announcement.reset(); announcementFeedback.textContent = result.message;
    } catch (error) { announcementFeedback.textContent = error.message; announcementFeedback.classList.add('is-error'); }
  });

  const users = document.querySelector('#managed-users');
  if (!users) return;
  const founderEmail = users.dataset.founderEmail.toLowerCase();
  adminApiCall('/api/admin/users').then(result => {
    users.innerHTML = result.data.map(user => `<tr><td>${escapeHtml(user.fullname)}</td><td>${escapeHtml(user.email)}</td><td>${user.role}</td><td>${user.email.toLowerCase() === founderEmail ? 'Founder' : `<button class="admin-btn admin-btn-small" data-user-id="${user.id}" data-role="${user.role === 'admin' ? 'student' : 'admin'}">${user.role === 'admin' ? 'Remove admin' : 'Make admin'}</button>`}</td></tr>`).join('');
    users.addEventListener('click', async event => { const button = event.target.closest('button[data-user-id]'); if (!button) return; await adminApiCall(`/api/admin/users/${button.dataset.userId}/role`, { method: 'PUT', body: JSON.stringify({ role: button.dataset.role }) }); window.location.reload(); });
  }).catch(error => { users.innerHTML = `<tr><td colspan="4" class="admin-table-state">${escapeHtml(error.message)}</td></tr>`; });
});
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character])); }