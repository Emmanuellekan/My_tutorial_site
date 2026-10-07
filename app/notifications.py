import json
import smtplib
from email.message import EmailMessage
from urllib import request, error as urllib_error

from flask import current_app

from .app import db
from .model import Notification, User


def _send_email_notification(user, title, message):
    mail_server = current_app.config.get('MAIL_SERVER')
    if not mail_server:
        return False

    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME') or 'no-reply@devrise.local'
    subject = title
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = user.email
    msg.set_content(message)

    try:
        with smtplib.SMTP(current_app.config.get('MAIL_SERVER'), current_app.config.get('MAIL_PORT', 587)) as smtp:
            username = current_app.config.get('MAIL_USERNAME')
            password = current_app.config.get('MAIL_PASSWORD')
            if username and password:
                smtp.starttls()
                smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def _send_onesignal_notification(user, title, message):
    app_id = current_app.config.get('ONESIGNAL_APP_ID')
    api_key = current_app.config.get('ONESIGNAL_API_KEY')
    if not app_id or not api_key:
        return False

    payload = json.dumps({
        'app_id': app_id,
        'include_external_user_ids': [str(user.id)],
        'headings': {'en': title},
        'contents': {'en': message},
    }).encode('utf-8')

    req = request.Request(
        'https://onesignal.com/api/v1/notifications',
        data=payload,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Basic {api_key}',
        },
        method='POST',
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            return response.status == 200 or response.status == 201
    except urllib_error.URLError:
        return False


def deliver_notification(user, title, message):
    if user is None:
        return {'push': False, 'email': False}

    delivery = {'push': False, 'email': False}
    if current_app.config.get('ONESIGNAL_APP_ID') and current_app.config.get('ONESIGNAL_API_KEY'):
        delivery['push'] = _send_onesignal_notification(user, title, message)
    if current_app.config.get('MAIL_SERVER'):
        delivery['email'] = _send_email_notification(user, title, message)
    return delivery


def create_notification(user_id, title, message, notify=True):
    user = User.query.get(user_id)
    if user is None:
        return None

    notification = Notification(user_id=user.id, title=title, message=message)
    db.session.add(notification)
    db.session.commit()

    if notify:
        deliver_notification(user, title, message)

    return notification


def create_bulk_notifications(user_ids, title, message):
    created = []
    delivery_counts = {'push': 0, 'email': 0}
    for user_id in user_ids:
        notification = create_notification(user_id, title, message, notify=False)
        if notification is not None:
            created.append(notification)
            user = User.query.get(notification.user_id)
            delivery = deliver_notification(user, title, message)
            for channel, sent in delivery.items():
                delivery_counts[channel] += int(sent)
    return created, delivery_counts
