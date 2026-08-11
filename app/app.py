import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import inspect, text


db = SQLAlchemy()


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

    db.session.commit()


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devdb.db'
    app.config['PROFILE_IMAGE_UPLOAD_FOLDER'] = os.path.join(
        app.static_folder,
        'uploads',
        'profile_images'
    )
    app.secret_key = 'devsecretkey'

    os.makedirs(app.config['PROFILE_IMAGE_UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'main.signup'
    login_manager.init_app(app)

    from .model import User
    from .route import register_app
    register_app(app, db)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        ensure_user_schema()


    migrate = Migrate(app, db)

    return app
