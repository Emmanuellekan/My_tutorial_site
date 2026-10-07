import os
import tempfile

from app.app import create_app
from app.model import Notification, User


def build_app():
    temp_db = os.path.join(tempfile.gettempdir(), 'devrise_test.sqlite')
    os.environ['SQLITE_DATABASE_PATH'] = temp_db
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        from app.app import db
        db.drop_all()
        db.create_all()
    return app


def test_support_page_renders_and_notification_can_be_created():
    app = build_app()

    with app.app_context():
        from app.notifications import create_notification

        user = User(
            fullname='Ada Lovelace',
            email='ada@example.com',
            phoneNumber='08000000000',
            gender='Female',
            profile_image='',
            password='hashed',
            role='student',
        )
        from app.app import db
        db.session.add(user)
        db.session.commit()

        create_notification(user.id, 'Welcome to DevRise', 'Your account is ready to start learning.')

        assert Notification.query.filter_by(user_id=user.id).count() == 1

    with app.test_client() as client:
        response = client.get('/support')
        assert response.status_code == 200
        assert b'Support Program' in response.data
        assert b'Account Name' in response.data
