from flask_login import UserMixin
from datetime import datetime

from .app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    profile_image = db.Column(db.String(255), nullable=False, default='')
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    progress = db.relationship('StudentProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade='all, delete-orphan')

    def is_admin(self):
        return self.role == 'admin'


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    thumbnail = db.Column(db.String(255), nullable=False, default='')
    category = db.Column(db.String(100), nullable=False, default='General')
    level = db.Column(db.String(50), nullable=False, default='Beginner')  # Beginner, Intermediate, Advanced
    status = db.Column(db.String(20), nullable=False, default='Draft')  # Draft, Published
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lessons = db.relationship('Lesson', backref='course', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy=True, cascade='all, delete-orphan')
    live_classes = db.relationship('LiveClass', backref='course', lazy=True, cascade='all, delete-orphan')
    progress_records = db.relationship('StudentProgress', backref='course', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Course {self.title}>'


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False, default='')
    video_url = db.Column(db.String(500), nullable=False, default='')  # URL to external video (YouTube, Vimeo, etc.)
    order = db.Column(db.Integer, nullable=False, default=0)  # For ordering lessons within a course
    status = db.Column(db.String(20), nullable=False, default='Draft')  # Draft, Published
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    progress_records = db.relationship('StudentProgress', backref='lesson', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Lesson {self.title}>'


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    status = db.Column(db.String(20), nullable=False, default='Draft')  # Draft, Published
    passing_score = db.Column(db.Float, nullable=False, default=49.0)  # 49% or higher passes
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quiz {self.title}>'


class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False, default='')
    option_d = db.Column(db.String(500), nullable=False, default='')
    correct_answer = db.Column(db.String(1), nullable=False)  # A, B, C, or D
    order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuizQuestion {self.id}>'


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Float, nullable=False, default=0.0)  # Percentage score
    passed = db.Column(db.Boolean, nullable=False, default=False)
    answers_json = db.Column(db.Text, nullable=False, default='{}')
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuizAttempt user={self.user_id} quiz={self.quiz_id} score={self.score}>'


class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudentProgress user={self.user_id} course={self.course_id}>'


class LiveClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    scheduled_date = db.Column(db.DateTime, nullable=False)  # Date and time of the live class
    end_time = db.Column(db.DateTime, nullable=False)  # When the class ends
    platform = db.Column(db.String(100), nullable=False, default='Google Meet')  # Google Meet, Zoom, etc.
    meeting_link = db.Column(db.String(500), nullable=False)  # Direct link to the meeting
    status = db.Column(db.String(20), nullable=False, default='Upcoming')  # Upcoming, Ongoing, Completed
    recording_url = db.Column(db.String(500), nullable=False, default='')  # URL to recording if available
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<LiveClass {self.title}>'


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Unread')  # Unread, Read, Archived
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Feedback {self.id}>'


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Notification {self.id}>'

class PlatformSetting(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False, default='')

    def __repr__(self):
        return f'<PlatformSetting {self.key}>'
