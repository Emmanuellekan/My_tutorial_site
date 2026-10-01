from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .app import db
from .admin_decorators import admin_required
from .model import User, Course, Lesson, Quiz, QuizAttempt, StudentProgress, LiveClass, Notification, PlatformSetting


def create_admin_blueprint():
    """Create and return the admin blueprint."""
    admin = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates/admin')

    @admin.route('/')
    @admin_required
    def dashboard():
        """Admin dashboard home page."""
        stats = {
            'total_students': User.query.filter_by(role='student').count(),
            'total_courses': Course.query.count(),
            'total_lessons': Lesson.query.count(),
            'total_videos': Lesson.query.filter(Lesson.video_url != '').count(),
            'total_quizzes': Quiz.query.count(),
            'quiz_attempts': QuizAttempt.query.count(),
            'completed_courses': StudentProgress.query.filter_by(
                completed=True,
                lesson_id=None
            ).count(),
            'upcoming_live_classes': LiveClass.query.filter_by(status='Upcoming').count(),
        }

        activities = []
        for student in User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5):
            activities.append({
                'type': 'student',
                'title': 'New student registered',
                'description': f'{student.fullname} joined DevRise',
                'timestamp': student.created_at,
            })

        completed_progress = StudentProgress.query.filter_by(completed=True).order_by(
            StudentProgress.completed_at.desc()
        ).limit(5).all()
        for progress in completed_progress:
            if progress.lesson_id:
                activities.append({
                    'type': 'lesson',
                    'title': 'Student completed a lesson',
                    'description': f'{progress.user.fullname} completed "{progress.lesson.title}"',
                    'timestamp': progress.completed_at,
                })
            else:
                activities.append({
                    'type': 'course',
                    'title': 'Student completed a course',
                    'description': f'{progress.user.fullname} completed "{progress.course.title}"',
                    'timestamp': progress.completed_at,
                })

        for attempt in QuizAttempt.query.order_by(QuizAttempt.completed_at.desc()).limit(5):
            activities.append({
                'type': 'quiz',
                'title': 'Student attempted a quiz',
                'description': f'{attempt.user.fullname} attempted "{attempt.quiz.title}" and scored {attempt.score:g}%',
                'timestamp': attempt.completed_at,
            })

        activities.sort(key=lambda activity: activity['timestamp'], reverse=True)
        return render_template(
            'dashboard.html',
            user=current_user,
            stats=stats,
            activities=activities[:5],
        )

    @admin.route('/courses')
    @admin_required
    def courses():
        """Courses management page."""
        return render_template('courses/list.html', user=current_user)

    @admin.route('/lessons')
    @admin_required
    def lessons():
        """Lessons management page."""
        return render_template('lessons/list.html', user=current_user)

    @admin.route('/quizzes')
    @admin_required
    def quizzes():
        """Quizzes management page."""
        return render_template('quizzes/list.html', user=current_user)

    @admin.route('/students')
    @admin_required
    def students():
        """Students management page."""
        return render_template('students/list.html', user=current_user)

    @admin.route('/live-classes')
    @admin_required
    def live_classes():
        """Live classes management page."""
        return render_template('live-classes/list.html', user=current_user)

    @admin.route('/analytics')
    @admin_required
    def analytics():
        """Analytics page."""
        return render_template('analytics.html', user=current_user)

    @admin.route('/feedback')
    @admin_required
    def feedback():
        """Feedback page."""
        return render_template('feedback.html', user=current_user)

    @admin.route('/settings', methods=['GET', 'POST'])
    @admin_required
    def settings():
        """Settings page."""
        setting_values = {
            setting.key: setting.value for setting in PlatformSetting.query.all()
        }
        if request.method == 'POST':
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip().lower()
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')

            if not fullname or not email:
                flash('Name and email are required.', 'error')
            elif email != current_user.email and User.query.filter_by(email=email).first():
                flash('That email is already in use.', 'error')
            elif new_password and not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect.', 'error')
            else:
                current_user.fullname = fullname
                current_user.email = email
                if new_password:
                    current_user.password = generate_password_hash(new_password)
                for key in ('site_name', 'site_description', 'support_whatsapp'):
                    value = request.form.get(key, '').strip()
                    setting = PlatformSetting.query.get(key)
                    if setting is None:
                        setting = PlatformSetting(key=key)
                        db.session.add(setting)
                    setting.value = value
                db.session.commit()
                flash('Settings updated.', 'success')
                return redirect(url_for('admin.settings'))
        return render_template('settings.html', user=current_user, settings=setting_values)

    @admin.route('/users')
    @admin_required
    def users():
        """Founder-controlled administrator management page."""
        return render_template('users.html', user=current_user)

    return admin
