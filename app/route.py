import os
import json
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from pydantic import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .app import db
from .model import Course, LiveClass, Lesson, Notification, Quiz, QuizAttempt, QuizQuestion, StudentProgress, User
from .validation import LoginData, SignupData, first_validation_error
from .admin_routes import create_admin_blueprint
from .admin_api import create_admin_api_blueprint


def register_app(app, db):
    main = Blueprint('main', __name__)
    allowed_image_extensions = {'jpg', 'jpeg', 'png', 'webp', 'gif'}


    def wants_json_response():
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


    def auth_error(message, redirect_endpoint):
        if wants_json_response():
            return jsonify({'ok': False, 'category': 'error', 'message': message}), 400

        flash(message, category='error')
        return redirect(url_for(redirect_endpoint))


    def auth_success(message, redirect_endpoint):
        target_url = url_for(redirect_endpoint)

        if wants_json_response():
            return jsonify({
                'ok': True,
                'category': 'success',
                'message': message,
                'redirect_url': target_url,
            })

        flash(message, category='success')
        return redirect(target_url)


    def save_profile_image(image_file):
        if not image_file or not image_file.filename:
            return ''

        extension = image_file.filename.rsplit('.', 1)[-1].lower()
        if '.' not in image_file.filename or extension not in allowed_image_extensions:
            return None

        filename = secure_filename(f'{uuid4().hex}.{extension}')
        image_file.save(os.path.join(app.config['PROFILE_IMAGE_UPLOAD_FOLDER'], filename))
        return f'uploads/profile_images/{filename}'


    @main.route('/')
    @login_required
    def index():
        return render_template('index.html')


    @main.route('/dashboard')
    @login_required
    def student_dashboard():
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))

        courses = Course.query.filter_by(status='Published').order_by(Course.created_at.desc()).all()
        course_cards = []
        for course in courses:
            total_lessons = Lesson.query.filter_by(course_id=course.id, status='Published').count()
            completed_lessons = StudentProgress.query.filter_by(
                user_id=current_user.id,
                course_id=course.id,
                completed=True,
            ).filter(StudentProgress.lesson_id.isnot(None)).count()
            course_cards.append({
                'course': course,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress': round(completed_lessons / total_lessons * 100) if total_lessons else 0,
            })
        upcoming_classes = LiveClass.query.filter(
            LiveClass.status == 'Upcoming',
            LiveClass.scheduled_date >= datetime.utcnow(),
        ).order_by(LiveClass.scheduled_date).limit(5).all()
        recent_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(
            QuizAttempt.completed_at.desc()
        ).limit(5).all()
        current_user_quizzes = Quiz.query.join(Course).filter(
            Quiz.status == 'Published',
            Course.status == 'Published',
        ).order_by(Quiz.created_at.desc()).all()
        return render_template(
            'student-dashboard.html',
            course_cards=course_cards,
            upcoming_classes=upcoming_classes,
            recent_attempts=recent_attempts,
            current_user_quizzes=current_user_quizzes,
        )


    @main.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')


    @main.route('/notifications')
    @login_required
    def notifications():
        user_notifications = Notification.query.filter_by(
            user_id=current_user.id
        ).order_by(Notification.created_at.desc()).all()
        return render_template('notifications.html', notifications=user_notifications)


    @main.route('/live-classes')
    @login_required
    def student_live_classes():
        upcoming_classes = LiveClass.query.filter(
            LiveClass.status.in_(['Upcoming', 'Ongoing'])
        ).order_by(LiveClass.scheduled_date).all()
        past_classes = LiveClass.query.filter(
            LiveClass.status == 'Completed'
        ).order_by(LiveClass.scheduled_date.desc()).all()
        return render_template(
            'student-live-classes.html',
            upcoming_classes=upcoming_classes,
            past_classes=past_classes,
        )


    @main.route('/notifications/<int:notification_id>/read', methods=['POST'])
    @login_required
    def mark_notification_read(notification_id):
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first_or_404()
        notification.read_at = notification.read_at or datetime.utcnow()
        db.session.commit()
        return redirect(url_for('main.notifications'))


    @main.route('/learn/courses/<int:course_id>')
    @login_required
    def learn_course(course_id):
        course = Course.query.filter_by(id=course_id, status='Published').first_or_404()
        lessons = Lesson.query.filter_by(
            course_id=course.id,
            status='Published',
        ).order_by(Lesson.order).all()
        completed_ids = {
            progress.lesson_id for progress in StudentProgress.query.filter_by(
                user_id=current_user.id,
                course_id=course.id,
                completed=True,
            ).filter(StudentProgress.lesson_id.isnot(None)).all()
        }
        quizzes = Quiz.query.filter_by(course_id=course.id, status='Published').all()
        return render_template(
            'learn-course.html',
            course=course,
            lessons=lessons,
            completed_ids=completed_ids,
            quizzes=quizzes,
        )


    @main.route('/learn/lessons/<int:lesson_id>/complete', methods=['POST'])
    @login_required
    def complete_lesson(lesson_id):
        lesson = Lesson.query.join(Course).filter(
            Lesson.id == lesson_id,
            Lesson.status == 'Published',
            Course.status == 'Published',
        ).first_or_404()
        progress = StudentProgress.query.filter_by(
            user_id=current_user.id,
            course_id=lesson.course_id,
            lesson_id=lesson.id,
        ).first()
        if progress is None:
            progress = StudentProgress(
                user_id=current_user.id,
                course_id=lesson.course_id,
                lesson_id=lesson.id,
            )
            db.session.add(progress)
        progress.completed = True
        progress.completed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('main.learn_course', course_id=lesson.course_id))


    @main.route('/quizzes/<int:quiz_id>', methods=['GET', 'POST'])
    @login_required
    def take_quiz(quiz_id):
        quiz = Quiz.query.join(Course).filter(
            Quiz.id == quiz_id,
            Quiz.status == 'Published',
            Course.status == 'Published',
        ).first_or_404()
        questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()
        if request.method == 'POST':
            if not questions:
                flash('This quiz does not have any questions yet.', 'error')
                return redirect(url_for('main.student_dashboard'))
            correct = sum(
                request.form.get(f'question_{question.id}') == question.correct_answer
                for question in questions
            )
            score = round(correct / len(questions) * 100, 2)
            answers = {
                str(question.id): request.form.get(f'question_{question.id}')
                for question in questions
            }
            attempt = QuizAttempt(
                user_id=current_user.id,
                quiz_id=quiz.id,
                score=score,
                passed=score >= 49,
                answers_json=json.dumps(answers),
            )
            db.session.add(attempt)
            db.session.commit()
            return redirect(url_for('main.quiz_review', attempt_id=attempt.id))
        return render_template('take-quiz.html', quiz=quiz, questions=questions)


    @main.route('/quiz-attempts/<int:attempt_id>')
    @login_required
    def quiz_review(attempt_id):
        attempt = QuizAttempt.query.filter_by(
            id=attempt_id,
            user_id=current_user.id,
        ).first_or_404()
        questions = QuizQuestion.query.filter_by(quiz_id=attempt.quiz_id).order_by(
            QuizQuestion.order
        ).all()
        answers = json.loads(attempt.answers_json or '{}')
        review = [{
            'question': question,
            'selected': answers.get(str(question.id)),
            'selected_text': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }.get(answers.get(str(question.id))),
            'correct_text': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }.get(question.correct_answer),
            'correct': answers.get(str(question.id)) == question.correct_answer,
        } for question in questions]
        return render_template('quiz-review.html', attempt=attempt, review=review)


    @main.route('/courses')
    def courses():
        published_courses = Course.query.filter_by(status='Published').order_by(Course.created_at.desc()).all()
        return render_template('courses.html', published_courses=published_courses)


    @main.route('/start-learning')
    def start_learning():
        return render_template('start-learning.html')


    @main.route('/courses/html')
    def html_course():
        return render_template('html-course.html')


    @main.route('/courses/css')
    def css_course():
        return render_template('css-course.html')


    @main.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            profile_image_file = request.files.get('profile_image')

            try:
                signup_data = SignupData(**request.form)
            except ValidationError as error:
                return auth_error(first_validation_error(error), 'main.signup')

            existing_phone_user = User.query.filter_by(phoneNumber=signup_data.phoneNumber).first()
            if existing_phone_user:
                return auth_error('Phone number already exists.', 'main.signup')

            existing_user = User.query.filter_by(email=signup_data.email).first()
            if existing_user:
                return auth_error('Email already exists.', 'main.signup')

            profile_image = save_profile_image(profile_image_file)
            if profile_image is None:
                return auth_error('Please upload a valid image file.', 'main.signup')

            new_user = User(
                fullname=signup_data.fullname,
                phoneNumber=signup_data.phoneNumber,
                email=signup_data.email,
                gender=signup_data.gender.capitalize(),
                profile_image=profile_image,
                password=generate_password_hash(signup_data.password)
            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return auth_success('Account created successfully.', 'main.index')

        return render_template('signup.html', user=current_user)


    @main.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            try:
                login_data = LoginData(**request.form)
            except ValidationError as error:
                return auth_error(first_validation_error(error), 'main.login')

            user = User.query.filter_by(email=login_data.email).first()

            if not user:
                return auth_error('Email does not exist.', 'main.login')

            if not check_password_hash(user.password, login_data.password):
                return auth_error('Incorrect password.', 'main.login')

            login_user(user)
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                if wants_json_response():
                    return jsonify({
                        'ok': True,
                        'category': 'success',
                        'message': 'Login successful.',
                        'redirect_url': next_url,
                    })
                flash('Login successful.', category='success')
                return redirect(next_url)
            return auth_success('Login successful.', 'main.index')

        return render_template('login.html', user=current_user)


    @main.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('main.login'))

    app.register_blueprint(main)
    
    # Register admin blueprint
    admin_blueprint = create_admin_blueprint()
    app.register_blueprint(admin_blueprint)
    
    # Register admin API blueprint
    admin_api_blueprint = create_admin_api_blueprint()
    app.register_blueprint(admin_api_blueprint)
