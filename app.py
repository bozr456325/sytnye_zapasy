from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sytnye_zapasy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель для пользователей
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Модель для продуктов
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.String(20), nullable=False)  # Новое поле: объём
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=False)

# Модель для заказов
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='Новый')

# Создаём таблицы в базе данных
with app.app_context():
    print("Создаём таблицы в базе данных...")
    db.create_all()
    print("Таблицы созданы.")

# Пример данных для продуктов (можно удалить после наполнения базы)
def add_sample_products():
    try:
        with app.app_context():  # Добавляем контекст приложения
            if not Product.query.first():
                products = [
                    # Мясная продукция
                    Product(name="Говядина тушёная", description="Нежное мясо, приготовленное по традиционным рецептам.", price=550, volume="500 мл.", category="meat", image="meat1.jpg"),
                    Product(name="Свинина тушёная", description="Сочная свинина, идеальная для бутербродов и салатов.", price=380, volume="500 мл", category="meat", image="meat2.jpg"),
                    Product(name="Курица тушёная", description="Нежная курица в собственном соку, без костей.", price=360, volume="500 мл", category="meat", image="meat3.jpg"),
                    Product(name="Индейка тушёная", description="Изысканное и питательное блюдо с нежным вкусом и ароматом.", price=530, volume="500 мл", category="meat", image="meat4.jpg"),

                    # Рыбная продукция
                    Product(name="Шпроты в масле", description="Классические шпроты с насыщенным вкусом.", price=250, volume="240 г", category="fish", image="fish1.jpg"),
                    Product(name="Скумбрия копчёная", description="Ароматная копчёная скумбрия для настоящих гурманов.", price=280, volume="300 г", category="fish", image="fish2.jpg"),
                    Product(name="Сардины в томатном соусе", description="Сардины в пикантном томатном соусе.", price=220, volume="240 г", category="fish", image="fish3.jpg"),
                    Product(name="Кальмары в масле", description="Нежные кальмары в ароматном масле.", price=270, volume="300 г", category="fish", image="fish4.jpg"),

                    # Супы
                    Product(name="Борщ консервированный", description="Настоящий украинский борщ в банке.", price=200, volume="0.5 л", category="soups", image="soup1.jpg"),
                    Product(name="Суп гороховый", description="Сытный и ароматный гороховый суп.", price=180, volume="0.5 л", category="soups", image="soup2.jpg"),
                    Product(name="Суп грибной", description="Ароматный грибный суп с натуральными грибами.", price=190, volume="0.5 л", category="soups", image="soup3.jpg"),
                    Product(name="Суп куриный", description="Наваристый куриный суп с овощами.", price=210, volume="0.5 л", category="soups", image="soup4.jpg"),

                    # Паштеты и рийеты
                    Product(name="Паштет из куриной печени", description="Нежный паштет с насыщенным вкусом.", price=150, volume="200 г", category="pates", image="pate1.jpg"),
                    Product(name="Рийет из утки", description="Изысканный рийет для настоящих гурманов.", price=300, volume="200 г", category="pates", image="pate2.jpg"),
                    Product(name="Паштет из лосося", description="Нежный паштет с лососем и зеленью.", price=250, volume="200 г", category="pates", image="pate3.jpg"),
                    Product(name="Рийет из кролика", description="Ароматный рийет с нежным мясом кролика.", price=280, volume="200 г", category="pates", image="pate4.jpg"),
                ]
                db.session.bulk_save_objects(products)
                db.session.commit()
                print("Примерные продукты добавлены в базу данных.")
            else:
                print("Продукты уже существуют в базе данных.")
    except Exception as e:
        print(f"Ошибка при добавлении продуктов: {e}")

# Добавляем пример продуктов (вызовите эту функцию один раз)
add_sample_products()

# Маршруты и логика приложения
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products_page():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Проверяем, авторизован ли пользователь
    if 'user_id' not in session:
        flash('Для добавления товара в корзину необходимо войти в систему.', 'error')
        return redirect(url_for('login'))  # Перенаправляем на страницу входа

    product_id = request.form.get('product_id')
    if 'cart' not in session:
        session['cart'] = {}

    if product_id in session['cart']:
        session['cart'][product_id]['quantity'] += 1
    else:
        product = Product.query.get(product_id)
        session['cart'][product_id] = {
            'quantity': 1,
            'name': product.name,
            'price': product.price,
            'image': product.image
        }

    session.modified = True
    flash('Товар добавлен в корзину!', 'success')
    return redirect(url_for('products_page'))

@app.route('/check_auth')
def check_auth():
    return jsonify({'isLoggedIn': 'user_id' in session})

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    total_price = sum(item['price'] * item['quantity'] for item in cart_items.values())
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return redirect(url_for('register'))

        # Проверяем, существует ли пользователь с таким именем или email
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Пользователь с таким именем или email уже существует!', 'error')
            return redirect(url_for('register'))

        # Создаём нового пользователя
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Маршрут для входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Маршрут для выхода
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Вы успешно вышли из системы!', 'success')
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True
    return redirect(url_for('cart'))

if __name__ == '__main__':
    app.run(debug=True)