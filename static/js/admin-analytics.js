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

    const chart = document.querySelector('#usage-chart');
    const usage = data.students.usage || [];
    const peak = Math.max(1, ...usage.map(day => Number(day.value) || 0));
    chart.innerHTML = usage.map(day => {
      const value = Number(day.value) || 0;
      const height = value ? Math.max(8, value / peak * 100) : 3;
      return `<div class="admin-usage-day" title="${day.date}: ${value} actions, ${day.lesson_completions} lessons and ${day.quiz_attempts} quizzes">
        <span class="admin-usage-count">${value}</span>
        <span class="admin-usage-track"><span class="admin-usage-bar" style="height: ${height}%"></span></span>
        <span class="admin-usage-label">${day.label}</span>
      </div>`;
    }).join('');
  } catch (error) { feedback.textContent = error.message; feedback.classList.add('is-error'); }
});
