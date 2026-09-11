import os
from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


db = SQLAlchemy()


def get_database_url(is_vercel):
    database_url = next(
        (
            os.getenv(name, '').strip().strip('"').strip("'")
            for name in (
                'DATABASE_URL',
                'POSTGRES_URL',
                'POSTGRES_PRISMA_URL',
                'POSTGRES_URL_NON_POOLING',
            )
            if os.getenv(name, '').strip()
        ),
        '',
    )

    if not database_url:
        if is_vercel:
            raise RuntimeError(
                'Set DATABASE_URL in Vercel to a valid PostgreSQL connection URL.'
            )
        return 'sqlite:///devdb.db'

    normalized_url = database_url.replace('postgres://', 'postgresql://', 1)
    try:
        parsed_url = make_url(normalized_url)
    except ArgumentError as error:
        raise RuntimeError(
            'DATABASE_URL must be a complete URL such as '
            'postgresql://user:password@host/database?sslmode=require.'
        ) from error

    if parsed_url.drivername in ('postgres', 'postgresql'):
        parsed_url = parsed_url.set(drivername='postgresql+psycopg')

    return str(parsed_url)


def ensure_user_schema():
    inspector = inspect(db.engine)

    if 'user' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('user')}

    if 'gender' not in columns:
        db.session.execute(
            text("ALTER TABLE user ADD COLUMN gender VARCHAR(20) NOT NULL DEFAULT 'Other'")
        )

    if 'phoneNumber' not in columns:
        db.session.execute(
            text("ALTER TABLE user ADD COLUMN phoneNumber VARCHAR(20) NOT NULL DEFAULT ''")
        )

    if 'profile_image' not in columns:
        db.session.execute(
            text("ALTER TABLE user ADD COLUMN profile_image VARCHAR(255) NOT NULL DEFAULT ''")
        )

    if 'role' not in columns:
        db.session.execute(
            text("ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'student'")
        )

    if 'created_at' not in columns:
        created_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.execute(
            text(
                "ALTER TABLE user ADD COLUMN created_at DATETIME "
                f"NOT NULL DEFAULT '{created_at}'"
            )
        )

    quiz_attempt_columns = {
        column['name'] for column in inspector.get_columns('quiz_attempt')
    }
    if 'answers_json' not in quiz_attempt_columns:
        db.session.execute(
            text("ALTER TABLE quiz_attempt ADD COLUMN answers_json TEXT NOT NULL DEFAULT '{}'")
        )

    db.session.execute(
        text("UPDATE quiz_attempt SET passed = CASE WHEN score >= 49 THEN 1 ELSE 0 END")
    )

    db.session.commit()


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )

    is_vercel = any(
        os.getenv(name)
        for name in ('VERCEL', 'VERCEL_ENV', 'VERCEL_URL', 'AWS_LAMBDA_FUNCTION_VERSION')
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url(is_vercel)

    app.config['FOUNDER_EMAIL'] = os.getenv('FOUNDER_EMAIL', 'emmanuellekan30@gmail.com').strip().lower()
    app.config['DEFAULT_SUPPORT_WHATSAPP'] = '2348106775065'
    app.config['PROFILE_IMAGE_UPLOAD_FOLDER'] = os.path.join(
        '/tmp' if is_vercel else app.static_folder,
        'uploads',
        'profile_images'
    )
    app.secret_key = os.getenv('SECRET_KEY', 'devsecretkey')
    app.config['SESSION_COOKIE_SECURE'] = is_vercel
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    os.makedirs(app.config['PROFILE_IMAGE_UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    @app.context_processor
    def inject_platform_settings():
        from .model import PlatformSetting

        values = {
            setting.key: setting.value
            for setting in PlatformSetting.query.all()
        }
        return {
            'platform_settings': values,
            'support_whatsapp': values.get(
                'support_whatsapp', app.config['DEFAULT_SUPPORT_WHATSAPP']
            ),
        }

    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.init_app(app)

    from .model import User
    from .route import register_app
    register_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()


    migrate = Migrate(app, db)

    return app
