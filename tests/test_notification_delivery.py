import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

from app.app import create_app, db
from app.model import Course, Lesson, Quiz, QuizAttempt, StudentProgress, User
from app.notifications import create_bulk_notifications, create_notification


class NotificationDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_database_path = os.environ.get('SQLITE_DATABASE_PATH')
        os.environ['SQLITE_DATABASE_PATH'] = os.path.join(self.temp_dir.name, 'test.sqlite')
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            MAIL_SERVER='smtp.example.test',
            ONESIGNAL_APP_ID='test-app-id',
            ONESIGNAL_API_KEY='test-api-key',
        )
        with self.app.app_context():
            db.create_all()
            user = User(
                fullname='Test Student',
                email='student@example.test',
                phoneNumber='08000000000',
                gender='Other',
                password='test-hash',
            )
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
        if self.previous_database_path is None:
            os.environ.pop('SQLITE_DATABASE_PATH', None)
        else:
            os.environ['SQLITE_DATABASE_PATH'] = self.previous_database_path
        self.temp_dir.cleanup()

    @patch('app.notifications._send_email_notification', return_value=True)
    @patch('app.notifications._send_onesignal_notification', return_value=True)
    def test_single_notification_attempts_push_and_email(self, push, email):
        with self.app.app_context():
            create_notification(self.user_id, 'Welcome', 'Welcome to DevRise.')

        push.assert_called_once()
        email.assert_called_once()

    @patch('app.notifications._send_email_notification', return_value=True)
    @patch('app.notifications._send_onesignal_notification', return_value=False)
    def test_bulk_notification_reports_each_channel(self, push, email):
        with self.app.app_context():
            notifications, delivery_counts = create_bulk_notifications(
                [self.user_id], 'Update', 'A course update is available.'
            )

        self.assertEqual(len(notifications), 1)
        self.assertEqual(delivery_counts, {'push': 0, 'email': 1})
        push.assert_called_once()
        email.assert_called_once()

    def test_analytics_counts_lessons_and_quizzes_by_day(self):
        with self.app.app_context():
            course = Course(title='Test course', description='', status='Published')
            admin = User(
                fullname='Test Admin',
                email='admin@example.test',
                phoneNumber='08000000001',
                gender='Other',
                password='test-hash',
                role='admin',
            )
            db.session.add_all([course, admin])
            db.session.flush()
            lesson = Lesson(course_id=course.id, title='Test lesson', status='Published')
            quiz = Quiz(course_id=course.id, title='Test quiz', status='Published')
            db.session.add_all([lesson, quiz])
            db.session.flush()
            db.session.add_all([
                StudentProgress(
                    user_id=self.user_id,
                    course_id=course.id,
                    lesson_id=lesson.id,
                    completed=True,
                    completed_at=datetime.utcnow(),
                ),
                QuizAttempt(user_id=self.user_id, quiz_id=quiz.id, score=100, passed=True),
            ])
            db.session.commit()
            admin_id = admin.id

        with self.app.test_client() as client:
            with client.session_transaction() as session:
                session['_user_id'] = str(admin_id)
                session['_fresh'] = True
            response = client.get('/api/admin/analytics')

        self.assertEqual(response.status_code, 200)
        today = response.get_json()['data']['students']['usage'][-1]
        self.assertEqual(today['value'], 2)
        self.assertEqual(today['lesson_completions'], 1)
        self.assertEqual(today['quiz_attempts'], 1)