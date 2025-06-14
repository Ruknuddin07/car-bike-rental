import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Khuzz%40123@localhost/car_bike_rental'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicit table name to match your DB
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


from sqlalchemy import ForeignKey
from datetime import datetime



class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100))
    type = db.Column(db.String(10))
    image = db.Column(db.String(200))
    is_rented = db.Column(db.Boolean, default=False)
    rented_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    price = db.Column(db.Integer)
    rent_time = db.Column(db.DateTime, nullable=True)





# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

import re
from flask import flash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate email
        if not username.endswith('@gmail.com'):
            flash('Only Gmail addresses are allowed.')
            return render_template('register.html')

        # Validate password strength
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password):
            flash('Password must be at least 8 characters and include an uppercase letter and a number.')
            return render_template('register.html')

        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('User already exists.')
            return render_template('register.html')

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route called")  # DEBUG
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid Credentials")
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', vehicles=vehicles)

@app.route('/add', methods=['POST'])
@login_required
def add():
    name = request.form['name']
    vtype = request.form['type']
    price = request.form['price']
    image = request.files['image']

    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        new_vehicle = Vehicle(
            user_id=current_user.id,
            name=name,
            type=vtype,
            price=price,
            image=filename,
            is_rented=False,
            rented_by=None,
            rent_time=None
        )

        db.session.add(new_vehicle)
        db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/delete/<int:vid>')
@login_required
def delete(vid):
    vehicle = Vehicle.query.get(vid)
    if vehicle and vehicle.user_id == current_user.id:
        db.session.delete(vehicle)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/rent/<int:vid>')
@login_required
def rent(vid):
    vehicle = Vehicle.query.get_or_404(vid)

    if not vehicle.is_rented:
        vehicle.is_rented = True
        vehicle.rented_by = current_user.id
        vehicle.rent_time = datetime.utcnow()
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/return/<int:vid>')
@login_required
def return_vehicle(vid):
    vehicle = Vehicle.query.get_or_404(vid)
    if vehicle.is_rented and vehicle.rented_by == current_user.id:
        vehicle.is_rented = False
        vehicle.rented_by = None
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

