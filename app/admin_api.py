from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from datetime import datetime, timedelta

from .app import db
from .model import User, Course, Lesson, Quiz, QuizQuestion, QuizAttempt, StudentProgress, LiveClass, Feedback, Notification
from .admin_decorators import admin_required, founder_required


def create_admin_api_blueprint():
    """Create and return the admin API blueprint."""
    admin_api = Blueprint('admin_api', __name__, url_prefix='/api/admin')

    # ==================== Dashboard ====================

    @admin_api.route('/dashboard', methods=['GET'])
    @admin_required
    def get_dashboard_stats():
        """Get dashboard statistics."""
        try:
            total_students = User.query.filter_by(role='student').count()
            total_courses = Course.query.count()
            total_lessons = Lesson.query.count()
            total_videos = Lesson.query.filter(Lesson.video_url != '').count()
            total_quizzes = Quiz.query.count()
            total_quiz_attempts = QuizAttempt.query.count()
            completed_courses = StudentProgress.query.filter_by(
                completed=True,
                lesson_id=None  # Course-level completion
            ).count()
            upcoming_live_classes = LiveClass.query.filter(
                LiveClass.status == 'Upcoming'
            ).count()

            return jsonify({
                'ok': True,
                'data': {
                    'total_students': total_students,
                    'total_courses': total_courses,
                    'total_lessons': total_lessons,
                    'total_videos': total_videos,
                    'total_quizzes': total_quizzes,
                    'quiz_attempts': total_quiz_attempts,
                    'completed_courses': completed_courses,
                    'upcoming_live_classes': upcoming_live_classes
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Courses ====================

    @admin_api.route('/courses', methods=['GET'])
    @admin_required
    def list_courses():
        """List all courses."""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)

            query = Course.query
            if status:
                query = query.filter_by(status=status)

            pagination = query.order_by(Course.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            courses_data = []
            for course in pagination.items:
                lesson_count = Lesson.query.filter_by(course_id=course.id).count()
                courses_data.append({
                    'id': course.id,
                    'title': course.title,
                    'category': course.category,
                    'level': course.level,
                    'status': course.status,
                    'lessons': lesson_count,
                    'created_at': course.created_at.isoformat(),
                    'updated_at': course.updated_at.isoformat()
                })

            return jsonify({
                'ok': True,
                'data': courses_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/courses', methods=['POST'])
    @admin_required
    def create_course():
        """Create a new course."""
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['title', 'description']
            if not all(field in data for field in required_fields):
                return jsonify({'ok': False, 'message': 'Missing required fields'}), 400

            course = Course(
                title=data.get('title'),
                description=data.get('description'),
                category=data.get('category', 'General'),
                level=data.get('level', 'Beginner'),
                status=data.get('status', 'Draft'),
                thumbnail=data.get('thumbnail', '')
            )

            db.session.add(course)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Course created successfully',
                'data': {
                    'id': course.id,
                    'title': course.title,
                    'status': course.status
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/courses/<int:course_id>', methods=['GET'])
    @admin_required
    def get_course(course_id):
        """Get course details."""
        try:
            course = Course.query.get_or_404(course_id)
            lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()

            return jsonify({
                'ok': True,
                'data': {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'thumbnail': course.thumbnail,
                    'category': course.category,
                    'level': course.level,
                    'status': course.status,
                    'lessons': [{
                        'id': lesson.id,
                        'title': lesson.title,
                        'order': lesson.order,
                        'status': lesson.status
                    } for lesson in lessons],
                    'created_at': course.created_at.isoformat(),
                    'updated_at': course.updated_at.isoformat()
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/courses/<int:course_id>', methods=['PUT'])
    @admin_required
    def update_course(course_id):
        """Update a course."""
        try:
            course = Course.query.get_or_404(course_id)
            data = request.get_json()

            course.title = data.get('title', course.title)
            course.description = data.get('description', course.description)
            course.category = data.get('category', course.category)
            course.level = data.get('level', course.level)
            course.status = data.get('status', course.status)
            course.thumbnail = data.get('thumbnail', course.thumbnail)
            course.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Course updated successfully',
                'data': {
                    'id': course.id,
                    'title': course.title,
                    'status': course.status
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/courses/<int:course_id>', methods=['DELETE'])
    @admin_required
    def delete_course(course_id):
        """Delete a course."""
        try:
            course = Course.query.get_or_404(course_id)
            db.session.delete(course)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Course deleted successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Lessons ====================

    @admin_api.route('/courses/<int:course_id>/lessons', methods=['GET'])
    @admin_required
    def list_lessons(course_id):
        """List lessons for a course."""
        try:
            Course.query.get_or_404(course_id)
            lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order).all()

            return jsonify({
                'ok': True,
                'data': [{
                    'id': lesson.id,
                    'title': lesson.title,
                    'order': lesson.order,
                    'status': lesson.status,
                    'has_video': bool(lesson.video_url),
                    'created_at': lesson.created_at.isoformat()
                } for lesson in lessons]
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/courses/<int:course_id>/lessons', methods=['POST'])
    @admin_required
    def create_lesson(course_id):
        """Create a new lesson."""
        try:
            Course.query.get_or_404(course_id)
            data = request.get_json()

            if 'title' not in data:
                return jsonify({'ok': False, 'message': 'Title is required'}), 400

            # Get next order number
            max_order = db.session.query(func.max(Lesson.order)).filter_by(course_id=course_id).scalar() or 0
            next_order = max_order + 1

            lesson = Lesson(
                course_id=course_id,
                title=data.get('title'),
                content=data.get('content', ''),
                video_url=data.get('video_url', ''),
                order=next_order,
                status=data.get('status', 'Draft')
            )

            db.session.add(lesson)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Lesson created successfully',
                'data': {
                    'id': lesson.id,
                    'title': lesson.title,
                    'order': lesson.order
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/lessons/<int:lesson_id>', methods=['GET'])
    @admin_required
    def get_lesson(lesson_id):
        """Get lesson details for editing."""
        try:
            lesson = Lesson.query.get_or_404(lesson_id)
            return jsonify({
                'ok': True,
                'data': {
                    'id': lesson.id,
                    'course_id': lesson.course_id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'video_url': lesson.video_url,
                    'order': lesson.order,
                    'status': lesson.status,
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/lessons/<int:lesson_id>', methods=['PUT'])
    @admin_required
    def update_lesson(lesson_id):
        """Update a lesson."""
        try:
            lesson = Lesson.query.get_or_404(lesson_id)
            data = request.get_json()

            lesson.title = data.get('title', lesson.title)
            lesson.content = data.get('content', lesson.content)
            lesson.video_url = data.get('video_url', lesson.video_url)
            lesson.status = data.get('status', lesson.status)
            lesson.order = data.get('order', lesson.order)
            lesson.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Lesson updated successfully',
                'data': {
                    'id': lesson.id,
                    'title': lesson.title
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/lessons/<int:lesson_id>', methods=['DELETE'])
    @admin_required
    def delete_lesson(lesson_id):
        """Delete a lesson."""
        try:
            lesson = Lesson.query.get_or_404(lesson_id)
            db.session.delete(lesson)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Lesson deleted successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Quizzes ====================

    @admin_api.route('/quizzes', methods=['GET'])
    @admin_required
    def list_quizzes():
        """List all quizzes."""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)

            pagination = Quiz.query.order_by(Quiz.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            quizzes_data = []
            for quiz in pagination.items:
                questions_count = QuizQuestion.query.filter_by(quiz_id=quiz.id).count()
                attempts_count = QuizAttempt.query.filter_by(quiz_id=quiz.id).count()
                quizzes_data.append({
                    'id': quiz.id,
                    'title': quiz.title,
                    'course_id': quiz.course_id,
                    'questions': questions_count,
                    'attempts': attempts_count,
                    'status': quiz.status,
                    'passing_score': 49,
                    'created_at': quiz.created_at.isoformat()
                })

            return jsonify({
                'ok': True,
                'data': quizzes_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/quizzes', methods=['POST'])
    @admin_required
    def create_quiz():
        """Create a new quiz."""
        try:
            data = request.get_json()

            if 'title' not in data or 'course_id' not in data:
                return jsonify({'ok': False, 'message': 'Title and course_id are required'}), 400

            # Verify course exists
            Course.query.get_or_404(data['course_id'])

            quiz = Quiz(
                course_id=data.get('course_id'),
                title=data.get('title'),
                description=data.get('description', ''),
                status=data.get('status', 'Draft'),
                passing_score=49.0
            )

            db.session.add(quiz)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Quiz created successfully',
                'data': {
                    'id': quiz.id,
                    'title': quiz.title
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/quizzes/<int:quiz_id>', methods=['GET'])
    @admin_required
    def get_quiz(quiz_id):
        """Get quiz with all questions."""
        try:
            quiz = Quiz.query.get_or_404(quiz_id)
            questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.order).all()

            return jsonify({
                'ok': True,
                'data': {
                    'id': quiz.id,
                    'title': quiz.title,
                    'description': quiz.description,
                    'course_id': quiz.course_id,
                    'status': quiz.status,
                    'passing_score': 49,
                    'questions': [{
                        'id': q.id,
                        'question_text': q.question_text,
                        'option_a': q.option_a,
                        'option_b': q.option_b,
                        'option_c': q.option_c,
                        'option_d': q.option_d,
                        'correct_answer': q.correct_answer,
                        'order': q.order
                    } for q in questions],
                    'created_at': quiz.created_at.isoformat()
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/quizzes/<int:quiz_id>/attempts', methods=['GET'])
    @admin_required
    def list_quiz_attempts(quiz_id):
        """List student results for a quiz."""
        Quiz.query.get_or_404(quiz_id)
        attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).order_by(
            QuizAttempt.completed_at.desc()
        ).all()
        return jsonify({'ok': True, 'data': [{
            'id': attempt.id,
            'student': attempt.user.fullname,
            'email': attempt.user.email,
            'score': attempt.score,
            'passed': attempt.score >= 49,
            'completed_at': attempt.completed_at.isoformat(),
        } for attempt in attempts]})

    @admin_api.route('/quizzes/<int:quiz_id>', methods=['PUT'])
    @admin_required
    def update_quiz(quiz_id):
        """Update a quiz."""
        try:
            quiz = Quiz.query.get_or_404(quiz_id)
            data = request.get_json()

            quiz.title = data.get('title', quiz.title)
            quiz.description = data.get('description', quiz.description)
            quiz.status = data.get('status', quiz.status)
            quiz.passing_score = 49.0
            quiz.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Quiz updated successfully',
                'data': {'id': quiz.id, 'title': quiz.title}
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/quizzes/<int:quiz_id>', methods=['DELETE'])
    @admin_required
    def delete_quiz(quiz_id):
        """Delete a quiz."""
        try:
            quiz = Quiz.query.get_or_404(quiz_id)
            db.session.delete(quiz)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Quiz deleted successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Quiz Questions ====================

    @admin_api.route('/quizzes/<int:quiz_id>/questions', methods=['POST'])
    @admin_required
    def create_quiz_question(quiz_id):
        """Add a question to a quiz."""
        try:
            quiz = Quiz.query.get_or_404(quiz_id)
            data = request.get_json()

            required_fields = ['question_text', 'option_a', 'option_b', 'correct_answer']
            if not all(field in data for field in required_fields):
                return jsonify({'ok': False, 'message': 'Missing required fields'}), 400

            # Get next order
            max_order = db.session.query(func.max(QuizQuestion.order)).filter_by(quiz_id=quiz_id).scalar() or 0

            question = QuizQuestion(
                quiz_id=quiz_id,
                question_text=data.get('question_text'),
                option_a=data.get('option_a'),
                option_b=data.get('option_b'),
                option_c=data.get('option_c', ''),
                option_d=data.get('option_d', ''),
                correct_answer=data.get('correct_answer'),
                order=max_order + 1
            )

            db.session.add(question)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Question added successfully',
                'data': {'id': question.id}
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/questions/<int:question_id>', methods=['PUT'])
    @admin_required
    def update_quiz_question(question_id):
        """Update a quiz question."""
        try:
            question = QuizQuestion.query.get_or_404(question_id)
            data = request.get_json()

            question.question_text = data.get('question_text', question.question_text)
            question.option_a = data.get('option_a', question.option_a)
            question.option_b = data.get('option_b', question.option_b)
            question.option_c = data.get('option_c', question.option_c)
            question.option_d = data.get('option_d', question.option_d)
            question.correct_answer = data.get('correct_answer', question.correct_answer)
            question.order = data.get('order', question.order)

            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Question updated successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/questions/<int:question_id>', methods=['DELETE'])
    @admin_required
    def delete_quiz_question(question_id):
        """Delete a quiz question."""
        try:
            question = QuizQuestion.query.get_or_404(question_id)
            db.session.delete(question)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Question deleted successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Students ====================

    @admin_api.route('/students', methods=['GET'])
    @admin_required
    def list_students():
        """List all students."""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)

            pagination = User.query.filter_by(role='student').order_by(User.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            students_data = []
            for student in pagination.items:
                courses_enrolled = StudentProgress.query.filter_by(user_id=student.id).distinct(StudentProgress.course_id).count()
                quiz_attempts = QuizAttempt.query.filter_by(user_id=student.id).count()
                
                students_data.append({
                    'id': student.id,
                    'fullname': student.fullname,
                    'email': student.email,
                    'phone': student.phoneNumber,
                    'courses': courses_enrolled,
                    'quiz_attempts': quiz_attempts,
                    'joined_at': student.created_at.isoformat()
                })

            return jsonify({
                'ok': True,
                'data': students_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/students/<int:student_id>', methods=['GET'])
    @admin_required
    def get_student_detail(student_id):
        """Get detailed student information."""
        try:
            student = User.query.filter_by(id=student_id, role='student').first_or_404()

            # Get progress
            progress = StudentProgress.query.filter_by(user_id=student_id).all()
            quiz_attempts = QuizAttempt.query.filter_by(user_id=student_id).all()

            courses_data = {}
            for p in progress:
                if p.course_id not in courses_data:
                    course = Course.query.get(p.course_id)
                    courses_data[p.course_id] = {
                        'course_id': p.course_id,
                        'course_title': course.title if course else 'Unknown',
                        'lessons_completed': 0,
                        'total_lessons': Lesson.query.filter_by(course_id=p.course_id).count(),
                        'course_completed': False
                    }
                if p.lesson_id:
                    courses_data[p.course_id]['lessons_completed'] += 1
                if not p.lesson_id and p.completed:
                    courses_data[p.course_id]['course_completed'] = True

            for course_data in courses_data.values():
                total_lessons = course_data['total_lessons']
                course_data['progress'] = round(
                    course_data['lessons_completed'] / total_lessons * 100
                ) if total_lessons else 0

            return jsonify({
                'ok': True,
                'data': {
                    'id': student.id,
                    'fullname': student.fullname,
                    'email': student.email,
                    'phone': student.phoneNumber,
                    'gender': student.gender,
                    'joined_at': student.created_at.isoformat(),
                    'courses': list(courses_data.values()),
                    'quiz_stats': {
                        'total_attempts': len(quiz_attempts),
                        'average_score': round(sum(q.score for q in quiz_attempts) / len(quiz_attempts), 2) if quiz_attempts else 0,
                        'passed': sum(1 for attempt in quiz_attempts if attempt.score >= 49),
                    }
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Live Classes ====================

    @admin_api.route('/live-classes', methods=['GET'])
    @admin_required
    def list_live_classes():
        """List all live classes."""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)

            query = LiveClass.query
            if status:
                query = query.filter_by(status=status)

            pagination = query.order_by(LiveClass.scheduled_date.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            classes_data = []
            for lc in pagination.items:
                course = Course.query.get(lc.course_id)
                classes_data.append({
                    'id': lc.id,
                    'title': lc.title,
                    'course': course.title if course else 'Unknown',
                    'platform': lc.platform,
                    'status': lc.status,
                    'scheduled_date': lc.scheduled_date.isoformat(),
                    'has_recording': bool(lc.recording_url)
                })

            return jsonify({
                'ok': True,
                'data': classes_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/live-classes', methods=['POST'])
    @admin_required
    def create_live_class():
        """Create a new live class."""
        try:
            data = request.get_json()

            required_fields = ['title', 'course_id', 'scheduled_date', 'end_time', 'meeting_link']
            if not all(field in data for field in required_fields):
                return jsonify({'ok': False, 'message': 'Missing required fields'}), 400

            # Verify course exists
            Course.query.get_or_404(data['course_id'])

            live_class = LiveClass(
                course_id=data.get('course_id'),
                title=data.get('title'),
                description=data.get('description', ''),
                scheduled_date=datetime.fromisoformat(data.get('scheduled_date')),
                end_time=datetime.fromisoformat(data.get('end_time')),
                platform=data.get('platform', 'Google Meet'),
                meeting_link=data.get('meeting_link'),
                status=data.get('status', 'Upcoming')
            )

            db.session.add(live_class)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Live class created successfully',
                'data': {
                    'id': live_class.id,
                    'title': live_class.title
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/live-classes/<int:class_id>', methods=['GET'])
    @admin_required
    def get_live_class(class_id):
        """Get live class details for editing."""
        try:
            live_class = LiveClass.query.get_or_404(class_id)
            return jsonify({
                'ok': True,
                'data': {
                    'id': live_class.id,
                    'course_id': live_class.course_id,
                    'title': live_class.title,
                    'description': live_class.description,
                    'platform': live_class.platform,
                    'status': live_class.status,
                    'meeting_link': live_class.meeting_link,
                    'recording_url': live_class.recording_url,
                    'scheduled_date': live_class.scheduled_date.isoformat(),
                    'end_time': live_class.end_time.isoformat(),
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/live-classes/<int:class_id>', methods=['PUT'])
    @admin_required
    def update_live_class(class_id):
        """Update a live class."""
        try:
            live_class = LiveClass.query.get_or_404(class_id)
            data = request.get_json()

            live_class.title = data.get('title', live_class.title)
            live_class.description = data.get('description', live_class.description)
            live_class.status = data.get('status', live_class.status)
            live_class.meeting_link = data.get('meeting_link', live_class.meeting_link)
            live_class.recording_url = data.get('recording_url', live_class.recording_url)

            if 'scheduled_date' in data:
                live_class.scheduled_date = datetime.fromisoformat(data.get('scheduled_date'))
            if 'end_time' in data:
                live_class.end_time = datetime.fromisoformat(data.get('end_time'))

            live_class.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Live class updated successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/live-classes/<int:class_id>', methods=['DELETE'])
    @admin_required
    def delete_live_class(class_id):
        """Delete a live class."""
        try:
            live_class = LiveClass.query.get_or_404(class_id)
            db.session.delete(live_class)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Live class deleted successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Analytics ====================

    @admin_api.route('/analytics', methods=['GET'])
    @admin_required
    def get_analytics():
        """Get analytics data."""
        try:
            # Student registration trend (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = User.query.filter(
                User.created_at >= thirty_days_ago,
                User.role == 'student'
            ).count()

            # Active students (with activity in last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            active_students = User.query.filter(
                User.role == 'student',
                User.created_at <= datetime.utcnow()
            ).count()

            # Course stats
            avg_lessons_per_course = db.session.query(func.avg(
                db.session.query(func.count(Lesson.id)).filter(Lesson.course_id == Course.id).as_scalar()
            )).scalar() or 0

            # Quiz stats
            avg_quiz_score = db.session.query(func.avg(QuizAttempt.score)).scalar() or 0
            total_quiz_pass = QuizAttempt.query.filter(QuizAttempt.passed == True).count()
            total_quiz_fail = QuizAttempt.query.filter(QuizAttempt.passed == False).count()

            return jsonify({
                'ok': True,
                'data': {
                    'students': {
                        'total': User.query.filter_by(role='student').count(),
                        'recent': recent_registrations,
                        'active': active_students
                    },
                    'courses': {
                        'total': Course.query.count(),
                        'published': Course.query.filter_by(status='Published').count(),
                        'draft': Course.query.filter_by(status='Draft').count(),
                        'avg_lessons': round(avg_lessons_per_course, 2)
                    },
                    'lessons': {
                        'total': Lesson.query.count(),
                        'published': Lesson.query.filter_by(status='Published').count(),
                        'with_videos': Lesson.query.filter(Lesson.video_url != '').count()
                    },
                    'quizzes': {
                        'total': Quiz.query.count(),
                        'attempts': QuizAttempt.query.count(),
                        'avg_score': round(avg_quiz_score, 2),
                        'pass_rate': round((total_quiz_pass / (total_quiz_pass + total_quiz_fail) * 100) if (total_quiz_pass + total_quiz_fail) > 0 else 0, 2)
                    },
                    'live_classes': {
                        'total': LiveClass.query.count(),
                        'upcoming': LiveClass.query.filter_by(status='Upcoming').count(),
                        'completed': LiveClass.query.filter_by(status='Completed').count()
                    }
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Feedback ====================

    @admin_api.route('/feedback', methods=['GET'])
    @admin_required
    def list_feedback():
        """List all feedback."""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)

            query = Feedback.query
            if status:
                query = query.filter_by(status=status)

            pagination = query.order_by(Feedback.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            feedback_data = []
            for fb in pagination.items:
                user = User.query.get(fb.user_id)
                feedback_data.append({
                    'id': fb.id,
                    'from': user.fullname if user else 'Unknown',
                    'email': fb.email,
                    'message': fb.message[:100] + '...' if len(fb.message) > 100 else fb.message,
                    'status': fb.status,
                    'created_at': fb.created_at.isoformat()
                })

            return jsonify({
                'ok': True,
                'data': feedback_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }), 200
        except Exception as e:
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/feedback/<int:feedback_id>', methods=['PUT'])
    @admin_required
    def update_feedback_status(feedback_id):
        """Update feedback status."""
        try:
            fb = Feedback.query.get_or_404(feedback_id)
            data = request.get_json()

            fb.status = data.get('status', fb.status)
            fb.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Feedback updated successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    @admin_api.route('/feedback/<int:feedback_id>', methods=['DELETE'])
    @admin_required
    def delete_feedback(feedback_id):
        """Delete feedback."""
        try:
            fb = Feedback.query.get_or_404(feedback_id)
            db.session.delete(fb)
            db.session.commit()

            return jsonify({
                'ok': True,
                'message': 'Feedback deleted successfully'
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # ==================== Founder controls and announcements ====================

    @admin_api.route('/users', methods=['GET'])
    @founder_required
    def list_users_for_role_management():
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify({'ok': True, 'data': [{
            'id': user.id,
            'fullname': user.fullname,
            'email': user.email,
            'role': user.role,
        } for user in users]})

    @admin_api.route('/users/<int:user_id>/role', methods=['PUT'])
    @founder_required
    def update_user_role(user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}
        role = data.get('role')
        if role not in {'student', 'admin'}:
            return jsonify({'ok': False, 'message': 'Role must be student or admin.'}), 400
        if user.email.lower() == current_app.config['FOUNDER_EMAIL']:
            return jsonify({'ok': False, 'message': 'The founder account cannot be demoted.'}), 400
        user.role = role
        db.session.commit()
        return jsonify({'ok': True, 'message': 'User role updated.'})

    @admin_api.route('/announcements', methods=['POST'])
    @admin_required
    def send_announcement():
        data = request.get_json() or {}
        title = str(data.get('title', '')).strip()
        message = str(data.get('message', '')).strip()
        if not title or not message:
            return jsonify({'ok': False, 'message': 'Title and message are required.'}), 400
        notifications = [Notification(user_id=user.id, title=title, message=message) for user in User.query.filter_by(role='student')]
        db.session.add_all(notifications)
        db.session.commit()
        return jsonify({'ok': True, 'message': f'Announcement sent to {len(notifications)} students.'}), 201

    return admin_api
