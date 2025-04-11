import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Настройка SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Используем SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Замените на свой секретный ключ

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Модель пользователя для авторизации
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


# Модель товара
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    image = db.Column(db.String(100), nullable=True)


# Загрузка пользователя по ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание пользователя 'admin' с паролем
def create_admin_user():
    user = User.query.filter_by(username='admin').first()
    if not user:
        # Хешируем пароль перед сохранением в базе данных
        hashed_password = generate_password_hash('adminpassword')
        new_user = User(username='admin', password=hashed_password)
        db.session.add(new_user)
        db.session.commit()


# Главная страница (с доступом только для авторизованных пользователей)
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)


# Обновление количества
@app.route('/update/<int:product_id>', methods=['POST'])
@login_required
def update_quantity(product_id):
    product = Product.query.get_or_404(product_id)
    new_quantity = request.form.get('quantity')
    if new_quantity.isdigit():
        product.quantity = int(new_quantity)
        db.session.commit()
    return redirect(url_for('index'))


# Удаление товара
@app.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('index'))


# Добавление товара
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        image_file = request.files['image']

        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        new_product = Product(name=name, quantity=quantity, image=filename)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add_product.html')


# Вход в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')

    return render_template('login.html')


# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Инициализация базы данных и создание администратора
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
        create_admin_user()  # Создаем администратора при старте приложения
    app.run(host='0.0.0.0', port=5000)