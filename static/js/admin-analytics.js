document.addEventListener('DOMContentLoaded', async () => {
  const cards = document.querySelector('#analytics-cards');
  const feedback = document.querySelector('#analytics-feedback');
  try {
    const data = (await adminApiCall('/api/admin/analytics')).data;
    const values = [
      ['Students', `${data.students.total} total / ${data.students.active} active`],
      ['Registrations', `${data.students.recent} in the last 30 days`],
      ['Courses', `${data.courses.published} published / ${data.courses.draft} draft`],
      ['Lessons', `${data.lessons.total} total / ${data.lessons.with_videos} with video`],
      ['Quiz attempts', data.quizzes.attempts],
      ['Average quiz score', `${data.quizzes.avg_score}%`],
      ['Quiz pass rate', `${data.quizzes.pass_rate}%`],
      ['Live classes', `${data.live_classes.upcoming} upcoming / ${data.live_classes.completed} completed`]
    ];
    cards.innerHTML = values.map(([label, value]) => `<div class="admin-stat-card"><div class="admin-stat-content"><div class="admin-stat-value">${value}</div><div class="admin-stat-label">${label}</div></div></div>`).join('');
  } catch (error) { feedback.textContent = error.message; feedback.classList.add('is-error'); }
});
