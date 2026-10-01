document.addEventListener('DOMContentLoaded', async () => {
  const list = document.querySelector('#feedback-list');
  const feedback = document.querySelector('#feedback-feedback');
  const load = async () => {
    const response = await adminApiCall('/api/admin/feedback?per_page=100');
    list.innerHTML = response.data.length ? response.data.map(item => `<tr><td><strong>${escapeHtml(item.from)}</strong></td><td>${escapeHtml(item.email)}</td><td>${escapeHtml(item.message)}</td><td><span class="admin-status admin-status-${item.status.toLowerCase()}">${escapeHtml(item.status)}</span></td><td>${new Date(item.created_at).toLocaleDateString()}</td><td class="admin-table-actions"><button class="admin-btn admin-btn-small" data-action="read" data-id="${item.id}" data-status="${item.status}">${item.status === 'Read' ? 'Mark unread' : 'Mark read'}</button><button class="admin-btn admin-btn-small admin-btn-danger" data-action="delete" data-id="${item.id}">Delete</button></td></tr>`).join('') : '<tr><td colspan="6" class="admin-table-state">No feedback found.</td></tr>';
  };
  try { await load(); } catch (error) { feedback.textContent = error.message; feedback.classList.add('is-error'); }
  list.addEventListener('click', async event => { const button = event.target.closest('button[data-action]'); if (!button) return; try { if (button.dataset.action === 'read') await adminApiCall(`/api/admin/feedback/${button.dataset.id}`, { method: 'PUT', body: JSON.stringify({ status: button.dataset.status === 'Read' ? 'Unread' : 'Read' }) }); if (button.dataset.action === 'delete' && confirm('Delete this feedback?')) await adminApiCall(`/api/admin/feedback/${button.dataset.id}`, { method: 'DELETE' }); await load(); } catch (error) { feedback.textContent = error.message; feedback.classList.add('is-error'); } });
});
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character])); }
