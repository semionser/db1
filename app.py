import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# Настройка SQLite

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Используем SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/var/www/db1/static/uploads'  # Полный путь для загрузки
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Замените на свой секретный ключ

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Модель пользователя
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


# Создание пользователя 'admin'
def create_admin_user():
    user = User.query.filter_by(username='adm').first()
    if not user:
        hashed_password = generate_password_hash('1234')
        new_user = User(username='adm', password=hashed_password)
        db.session.add(new_user)
        db.session.commit()


# Главная страница
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
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = 'Неверный логин или пароль'

    return render_template('login.html', error=error)


# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Страница аналитики
@app.route('/analytics')
@login_required
def analytics():
    products = Product.query.all()
    total_quantity = sum(product.quantity for product in products)
    added_quantity = len(products)
    return render_template('analytics.html', total_quantity=total_quantity, added_quantity=added_quantity)


# Скачивание данных в Excel
@app.route('/download_excel')
@login_required
def download_excel():
    products = Product.query.all()
    df = pd.DataFrame([(product.name, product.quantity) for product in products], columns=['Название', 'Количество'])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="products.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# Инициализация базы данных и создание администратора
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
        create_admin_user()
    app.run(host='0.0.0.0', port=5000)