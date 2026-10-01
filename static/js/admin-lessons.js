document.addEventListener('DOMContentLoaded', () => {
  const courseFilter = document.querySelector('#lesson-course-filter');
  const courseField = document.querySelector('#lesson-course');
  const list = document.querySelector('#lesson-list');
  const dialog = document.querySelector('#lesson-dialog');
  const form = document.querySelector('#lesson-form');
  const feedback = document.querySelector('#lesson-feedback');
  const requestedCourse = new URLSearchParams(window.location.search).get('course_id');

  const setFeedback = (message, isError = false) => {
    feedback.textContent = message;
    feedback.className = `admin-inline-feedback${isError ? ' is-error' : ''}`;
  };

  const loadCourses = async () => {
    try {
      const response = await adminApiCall('/api/admin/courses?per_page=100');
      const courses = response.data || [];
      const options = courses.map(course => `<option value="${course.id}">${escapeHtml(course.title)}</option>`).join('');
      courseFilter.insertAdjacentHTML('beforeend', options);
      courseField.innerHTML = options;
      if (requestedCourse && courses.some(course => String(course.id) === requestedCourse)) {
        courseFilter.value = requestedCourse;
      }
      if (courseFilter.value) loadLessons();
    } catch (error) {
      setFeedback(error.message, true);
    }
  };

  const loadLessons = async () => {
    const courseId = courseFilter.value;
    if (!courseId) {
      list.innerHTML = '<tr><td colspan="6" class="admin-table-state">Select a course to load lessons.</td></tr>';
      return;
    }
    list.innerHTML = '<tr><td colspan="6" class="admin-table-state">Loading lessons...</td></tr>';
    try {
      const response = await adminApiCall(`/api/admin/courses/${courseId}/lessons`);
      renderLessons(response.data || []);
    } catch (error) {
      list.innerHTML = '<tr><td colspan="6" class="admin-table-state">Unable to load lessons.</td></tr>';
      setFeedback(error.message, true);
    }
  };

  const renderLessons = (lessons) => {
    if (!lessons.length) {
      list.innerHTML = '<tr><td colspan="6" class="admin-table-state">No lessons found for this course.</td></tr>';
      return;
    }
    list.innerHTML = lessons.map(lesson => `
      <tr>
        <td>${lesson.order}</td>
        <td><strong>${escapeHtml(lesson.title)}</strong></td>
        <td>${lesson.has_video ? 'Attached' : 'None'}</td>
        <td><span class="admin-status admin-status-${lesson.status.toLowerCase()}">${escapeHtml(lesson.status)}</span></td>
        <td>${new Date(lesson.created_at).toLocaleDateString()}</td>
        <td class="admin-table-actions">
          <button class="admin-btn admin-btn-small" data-action="edit" data-id="${lesson.id}">Edit</button>
          <button class="admin-btn admin-btn-small admin-btn-danger" data-action="delete" data-id="${lesson.id}">Delete</button>
        </td>
      </tr>
    `).join('');
  };

  const openLessonDialog = async (lessonId = null) => {
    form.reset();
    document.querySelector('#lesson-id').value = lessonId || '';
    document.querySelector('#lesson-dialog-title').textContent = lessonId ? 'Edit Lesson' : 'New Lesson';
    courseField.value = courseFilter.value;
    if (lessonId) {
      const response = await adminApiCall(`/api/admin/lessons/${lessonId}`);
      const lesson = response.data;
      courseField.value = lesson.course_id;
      document.querySelector('#lesson-title').value = lesson.title;
      document.querySelector('#lesson-content').value = lesson.content;
      document.querySelector('#lesson-video-url').value = lesson.video_url;
      document.querySelector('#lesson-order').value = lesson.order;
      document.querySelector('#lesson-status').value = lesson.status;
    }
    dialog.showModal();
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const lessonId = document.querySelector('#lesson-id').value;
    const courseId = courseField.value;
    const payload = Object.fromEntries(new FormData(form));
    payload.order = Number(payload.order || 0);
    try {
      await adminApiCall(lessonId ? `/api/admin/lessons/${lessonId}` : `/api/admin/courses/${courseId}/lessons`, {
        method: lessonId ? 'PUT' : 'POST',
        body: JSON.stringify(payload)
      });
      dialog.close();
      courseFilter.value = courseId;
      setFeedback(lessonId ? 'Lesson updated.' : 'Lesson created.');
      loadLessons();
    } catch (error) {
      setFeedback(error.message, true);
    }
  });

  list.addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    try {
      if (button.dataset.action === 'edit') await openLessonDialog(button.dataset.id);
      if (button.dataset.action === 'delete' && window.confirm('Delete this lesson?')) {
        await adminApiCall(`/api/admin/lessons/${button.dataset.id}`, { method: 'DELETE' });
        setFeedback('Lesson deleted.');
        loadLessons();
      }
    } catch (error) {
      setFeedback(error.message, true);
    }
  });

  document.querySelector('#new-lesson-button').addEventListener('click', () => {
    if (courseFilter.value) openLessonDialog();
    else setFeedback('Select a course first.', true);
  });
  document.querySelector('#close-lesson-dialog').addEventListener('click', () => dialog.close());
  document.querySelector('#cancel-lesson-dialog').addEventListener('click', () => dialog.close());
  courseFilter.addEventListener('change', loadLessons);
  loadCourses();
});

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}
