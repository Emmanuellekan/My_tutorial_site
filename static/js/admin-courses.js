document.addEventListener('DOMContentLoaded', () => {
  const list = document.querySelector('#course-list');
  const dialog = document.querySelector('#course-dialog');
  const form = document.querySelector('#course-form');
  const feedback = document.querySelector('#course-feedback');
  const filter = document.querySelector('#course-status-filter');

  const setFeedback = (message, isError = false) => {
    feedback.textContent = message;
    feedback.className = `admin-inline-feedback${isError ? ' is-error' : ''}`;
  };

  const loadCourses = async () => {
    list.innerHTML = '<tr><td colspan="6" class="admin-table-state">Loading courses...</td></tr>';
    try {
      const status = filter.value ? `?status=${encodeURIComponent(filter.value)}` : '';
      const response = await adminApiCall(`/api/admin/courses${status}`);
      renderCourses(response.data || []);
    } catch (error) {
      list.innerHTML = '<tr><td colspan="6" class="admin-table-state">Unable to load courses.</td></tr>';
      setFeedback(error.message, true);
    }
  };

  const renderCourses = (courses) => {
    if (!courses.length) {
      list.innerHTML = '<tr><td colspan="6" class="admin-table-state">No courses found.</td></tr>';
      return;
    }
    list.innerHTML = courses.map(course => `
      <tr>
        <td><strong>${escapeHtml(course.title)}</strong></td>
        <td>${escapeHtml(course.category)}</td>
        <td>${escapeHtml(course.level)}</td>
        <td>${course.lessons}</td>
        <td><span class="admin-status admin-status-${course.status.toLowerCase()}">${escapeHtml(course.status)}</span></td>
        <td class="admin-table-actions">
          <a class="admin-btn admin-btn-small" href="/admin/lessons?course_id=${course.id}">Lessons</a>
          <button class="admin-btn admin-btn-small" data-action="edit" data-id="${course.id}">Edit</button>
          <button class="admin-btn admin-btn-small" data-action="toggle" data-id="${course.id}" data-status="${course.status}">${course.status === 'Published' ? 'Unpublish' : 'Publish'}</button>
          <button class="admin-btn admin-btn-small admin-btn-danger" data-action="delete" data-id="${course.id}">Delete</button>
        </td>
      </tr>
    `).join('');
  };

  const openCourseDialog = async (courseId = null) => {
    form.reset();
    document.querySelector('#course-id').value = courseId || '';
    document.querySelector('#course-dialog-title').textContent = courseId ? 'Edit Course' : 'New Course';
    if (courseId) {
      const response = await adminApiCall(`/api/admin/courses/${courseId}`);
      const course = response.data;
      document.querySelector('#course-title').value = course.title;
      document.querySelector('#course-description').value = course.description;
      document.querySelector('#course-category').value = course.category;
      document.querySelector('#course-level').value = course.level;
      document.querySelector('#course-thumbnail').value = course.thumbnail;
      document.querySelector('#course-status').value = course.status;
    }
    dialog.showModal();
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const id = document.querySelector('#course-id').value;
    const payload = Object.fromEntries(new FormData(form));
    try {
      await adminApiCall(id ? `/api/admin/courses/${id}` : '/api/admin/courses', {
        method: id ? 'PUT' : 'POST',
        body: JSON.stringify(payload)
      });
      dialog.close();
      setFeedback(id ? 'Course updated.' : 'Course created.');
      loadCourses();
    } catch (error) {
      setFeedback(error.message, true);
    }
  });

  list.addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    const { action, id, status } = button.dataset;
    try {
      if (action === 'edit') await openCourseDialog(id);
      if (action === 'toggle') {
        await adminApiCall(`/api/admin/courses/${id}`, { method: 'PUT', body: JSON.stringify({ status: status === 'Published' ? 'Draft' : 'Published' }) });
        loadCourses();
      }
      if (action === 'delete' && window.confirm('Delete this course and its lessons?')) {
        await adminApiCall(`/api/admin/courses/${id}`, { method: 'DELETE' });
        setFeedback('Course deleted.');
        loadCourses();
      }
    } catch (error) {
      setFeedback(error.message, true);
    }
  });

  document.querySelector('#new-course-button').addEventListener('click', () => openCourseDialog());
  document.querySelector('#close-course-dialog').addEventListener('click', () => dialog.close());
  document.querySelector('#cancel-course-dialog').addEventListener('click', () => dialog.close());
  filter.addEventListener('change', loadCourses);
  loadCourses();
});

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}
