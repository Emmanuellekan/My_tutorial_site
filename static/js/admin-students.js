document.addEventListener('DOMContentLoaded', async () => {
  const list = document.querySelector('#student-list');
  const feedback = document.querySelector('#student-feedback');
  try {
    const response = await adminApiCall('/api/admin/students?per_page=100');
    list.innerHTML = response.data.length ? response.data.map(student => `<tr><td><strong>${escapeHtml(student.fullname)}</strong></td><td>${escapeHtml(student.email)}</td><td>${student.courses}</td><td>${student.quiz_attempts}</td><td>${new Date(student.joined_at).toLocaleDateString()}</td><td><button class="admin-btn admin-btn-small" data-id="${student.id}">View details</button></td></tr>`).join('') : '<tr><td colspan="6" class="admin-table-state">No students found.</td></tr>';
    list.addEventListener('click', async event => {
      const button = event.target.closest('button[data-id]');
      if (!button) return;
      const student = (await adminApiCall(`/api/admin/students/${button.dataset.id}`)).data;
      document.querySelector('#student-dialog-title').textContent = student.fullname;
      document.querySelector('#student-dialog-meta').textContent = `${student.email} | Joined ${new Date(student.joined_at).toLocaleDateString()}`;
      document.querySelector('#student-summary').innerHTML = `<strong>${student.quiz_stats.total_attempts}</strong> quiz attempts <span>${student.quiz_stats.passed} passed</span> <span>Average score ${student.quiz_stats.average_score.toFixed(2)}%</span>`;
      document.querySelector('#student-progress-list').innerHTML = student.courses.length ? student.courses.map(course => `<tr><td>${escapeHtml(course.course_title)}</td><td>${course.lessons_completed}/${course.total_lessons}</td><td><div class="student-progress"><span style="width: ${course.progress}%"></span></div>${course.progress}%</td><td>${course.course_completed ? 'Yes' : 'No'}</td></tr>`).join('') : '<tr><td colspan="4" class="admin-table-state">No course progress yet.</td></tr>';
      document.querySelector('#student-dialog').showModal();
    });
  } catch (error) { feedback.textContent = error.message; feedback.classList.add('is-error'); }
});
document.querySelector('#close-student-dialog').addEventListener('click', () => document.querySelector('#student-dialog').close());
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character])); }
