# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, session, abort
from models import db, User, Task

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/taskflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def get_current_user():
    user_id = session.get('user_id')
    return User.query.get(user_id) if user_id else None

@app.route('/')
def index():
    return render_template('index.html', user=get_current_user())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if get_current_user():
        return redirect(url_for('tasks'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not username or len(username) < 3:
            flash('Имя пользователя должно быть не короче 3 символов.')
        elif not email or '@' not in email:
            flash('Некорректный email.')
        elif not password or len(password) < 6:
            flash('Пароль должен быть не короче 6 символов.')
        elif password != password2:
            flash('Пароли не совпадают.')
        elif User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.')
        elif User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован.')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Войдите в систему.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        return redirect(url_for('tasks'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Добро пожаловать, {user.username}!')
            return redirect(url_for('tasks'))
        else:
            flash('Неверное имя пользователя или пароль.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы.')
    return redirect(url_for('index'))

@app.route('/tasks')
def tasks():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    user_tasks = Task.query.filter_by(user_id=user.id).all()
    return render_template('tasks.html', tasks=user_tasks, user=user)

@app.route('/task/<int:id>')
def task_detail(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session.get('user_id'):
        abort(403)
    return render_template('task_detail.html', task=task, user=get_current_user())

@app.route('/task/new', methods=['GET', 'POST'])
def task_create():
    if not get_current_user():
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        if not title:
            flash('Заголовок задачи обязателен.')
        else:
            task = Task(title=title, description=description, user_id=get_current_user().id)
            db.session.add(task)
            db.session.commit()
            flash('Задача создана!')
            return redirect(url_for('tasks'))
    return render_template('task_form.html', editing=False)

@app.route('/task/<int:id>/edit', methods=['GET', 'POST'])
def task_edit(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session.get('user_id'):
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        if not title:
            flash('Заголовок задачи обязателен.')
        else:
            task.title = title
            task.description = description
            db.session.commit()
            flash('Задача обновлена!')
            return redirect(url_for('task_detail', id=task.id))
    return render_template('task_form.html', task=task, editing=True)

@app.route('/task/<int:id>/delete', methods=['POST'])
def task_delete(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session.get('user_id'):
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash('Задача удалена.')
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)