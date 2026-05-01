import os
from uuid import uuid4

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .app import db
from .model import User


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
    def home():
        return render_template('home.html')


    @main.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html')


    @main.route('/courses')
    def courses():
        return render_template('courses.html')


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
            fullname = request.form.get('fullname', '').strip()
            email = request.form.get('email', '').strip()
            gender = request.form.get('gender', '').strip().lower()
            phoneNumber = request.form.get('phoneNumber', '').strip()
            password = request.form.get('password', '')
            profile_image_file = request.files.get('profile_image')

            if len(fullname) < 2:
                return auth_error('Full name must be at least 2 characters.', 'main.signup')

            if len(email) < 4:
                return auth_error('Email must be at least 4 characters.', 'main.signup')
            
            if len(phoneNumber) < 7 or phoneNumber == '1234567890' or phoneNumber == '0000000000':
                return auth_error('Please enter a valid phone number.', 'main.signup')
            
            if not phoneNumber.isdigit():
                return auth_error('Phone number must contain only digits.', 'main.signup')
            
            if len(phoneNumber) > 15:
                return auth_error('Phone number must be less than 15 digits.', 'main.signup')
            
            existing_phone_user = User.query.filter_by(phoneNumber=phoneNumber).first()
            if existing_phone_user:
                return auth_error('Phone number already exists.', 'main.signup')
            
            
            if gender not in ['male', 'female', 'other']:
                return auth_error('Please select a valid gender.', 'main.signup')

            if len(password) < 4:
                return auth_error('Password must be at least 4 characters.', 'main.signup')

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return auth_error('Email already exists.', 'main.signup')

            profile_image = save_profile_image(profile_image_file)
            if profile_image is None:
                return auth_error('Please upload a valid image file.', 'main.signup')

            new_user = User(
                fullname=fullname,
                phoneNumber=phoneNumber,
                email=email,
                gender=gender.capitalize(),
                profile_image=profile_image,
                password=generate_password_hash(password)
            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True)
            return auth_success('Account created successfully.', 'main.login')

        return render_template('signup.html', user=current_user)


    @main.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            user = User.query.filter_by(email=email).first()

            if not user:
                return auth_error('Email does not exist.', 'main.login')

            if not password:
                return auth_error("You didn't enter any password.", 'main.login')

            if not check_password_hash(user.password, password):
                return auth_error('Incorrect password.', 'main.login')

            login_user(user, remember=True)
            return auth_success('Login successful.', 'main.home')

        return render_template('login.html', user=current_user)


    @main.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('main.login'))

    app.register_blueprint(main)
