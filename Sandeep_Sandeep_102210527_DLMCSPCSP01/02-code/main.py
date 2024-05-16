from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    mobile_number = db.Column(db.String(20), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/submit-signup-form', methods=['POST'])
def submit_signup_form():
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    mobile_number = request.form['mobile_number']

    if password != confirm_password:
        flash('Passwords do not match. Please try again.', 'error')
        return redirect(url_for('signup'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email already in use. Please choose another one.', 'error')
        return redirect(url_for('signup'))

    new_user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        mobile_number=mobile_number
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Automatically log in the user
    session['username'] = username
    flash('Successfully signed up and logged in!', 'success')
    return redirect(url_for('home'))


@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/submit-login-form', methods=['POST'])
def submit_login_form():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        flash('You have successfully logged in!', 'success')
        return redirect(url_for('home'))  # Or redirect to a user-specific dashboard
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))


@app.route('/tasks')
def tasks():
    if 'username' not in session:
        flash("You must be logged in to view this page.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for('login'))

    user_tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template('task.html', tasks=user_tasks)


@app.route('/submit-new-task', methods=['POST'])
def submit_new_task():
    if 'username' not in session:
        flash("You must be logged in to add tasks.", "warning")
        return redirect(url_for('login'))

    task_name = request.form['task_name']
    task_description = request.form['task_description']
    task_date_str = request.form['task_date']

    # Convert string to date object
    try:
        task_date = datetime.strptime(task_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD format.", "error")
        return redirect(url_for('tasks'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('login'))

    new_task = Task(
        name=task_name,
        description=task_description,
        due_date=task_date,
        user_id=user.id
    )
    db.session.add(new_task)
    try:
        db.session.commit()
        flash('Task added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash("Error adding task: " + str(e), 'error')

    return redirect(url_for('tasks'))


@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'username' not in session:
        flash("You must be logged in to perform this action.", "warning")
        return redirect(url_for('login'))

    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        flash('Task removed successfully!', 'success')
    else:
        flash('Task not found.', 'error')
    return redirect(url_for('tasks'))

@app.route('/edit_task/<int:task_id>', methods=['GET'])
def edit_task(task_id):
    if 'username' not in session:
        flash("You must be logged in to perform this action.", "warning")
        return redirect(url_for('login'))

    task = Task.query.get(task_id)
    if task:
        return render_template('edit_task.html', task=task)
    else:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'username' not in session:
        flash("You must be logged in to perform this action.", "warning")
        return redirect(url_for('login'))

    task = Task.query.get(task_id)
    if task:
        task.name = request.form['name']
        task.description = request.form['description']
        task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks'))
    else:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks'))



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables within the application context
    app.run(debug=True)