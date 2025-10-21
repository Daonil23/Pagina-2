from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# --- Configuración ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'una-clave-secreta-muy-dificil-de-adivinar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

# --- Modelos de Base de Datos ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modelo para las sugerencias
class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Modelo para los productos
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price_val = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    materials = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=10)

# Modelo para los artículos del carrito
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True, cascade="all, delete-orphan"))
    product = db.relationship('Product')

# --- Datos de Productos (simulados) ---
PRODUCTS_DATA = [
    {"id": 1, "name": "Collar de Diamantes", "price_val": 1200, "description": "Un collar deslumbrante con un diamante central de corte brillante, engastado en oro blanco de 18k.", "materials": "Oro blanco 18k, Diamante", "stock": 5},
    {"id": 2, "name": "Anillo de Zafiro", "price_val": 850, "description": "Elegante anillo con un zafiro azul profundo rodeado de pequeños diamantes, perfecto para cualquier ocasión.", "materials": "Plata de ley, Zafiro, Diamantes", "stock": 8},
    {"id": 3, "name": "Pendientes de Perlas", "price_val": 450, "description": "Clásicos y atemporales, estos pendientes cuentan con perlas de agua dulce de alta calidad.", "materials": "Oro amarillo 14k, Perlas de agua dulce", "stock": 15},
    {"id": 4, "name": "Pulsera de Oro", "price_val": 750, "description": "Una pulsera de eslabones finos en oro macizo de 18k, un básico indispensable en cualquier joyero.", "materials": "Oro macizo 18k", "stock": 12},
    {"id": 5, "name": "Anillo de Esmeralda", "price_val": 950, "description": "Anillo de cóctel con una esmeralda colombiana de talla ovalada, una pieza que no pasará desapercibida.", "materials": "Oro amarillo 18k, Esmeralda", "stock": 7},
    {"id": 6, "name": "Gargantilla de Plata", "price_val": 300, "description": "Moderna y minimalista, esta gargantilla de plata de ley es el complemento perfecto para el día a día.", "materials": "Plata de ley 925", "stock": 20},
    {"id": 7, "name": "Broche de Rubí", "price_val": 600, "description": "Un broche vintage con un diseño floral y un rubí central que añade un toque de color y distinción.", "materials": "Bronce chapado en oro, Rubí", "stock": 4},
    {"id": 8, "name": "Pendientes de Topacio", "price_val": 420, "description": "Pendientes largos con topacios azules que capturan la luz con cada movimiento.", "materials": "Oro blanco 14k, Topacio azul", "stock": 18},
    {"id": 9, "name": "Collar de Luna Dorada", "price_val": 550, "description": "Delicado collar con un colgante en forma de luna creciente, adornado con circonitas.", "materials": "Oro vermeil, Circonitas", "stock": 25},
    {"id": 10, "name": "Anillo Solitario", "price_val": 1100, "description": "El clásico anillo solitario, con un diamante de 0.5 quilates que simboliza el amor eterno.", "materials": "Platino, Diamante", "stock": 10},
    {"id": 11, "name": "Pulsera de Cuarzo Rosa", "price_val": 280, "description": "Pulsera de cuentas de cuarzo rosa natural, conocida por sus propiedades calmantes.", "materials": "Cuarzo rosa, Hilo elástico", "stock": 30},
    {"id": 12, "name": "Pendientes de Amatista", "price_val": 390, "description": "Pequeños pendientes de botón con amatistas de un intenso color púrpura.", "materials": "Oro rosa 14k, Amatista", "stock": 22},
    {"id": 13, "name": "Anillo de Compromiso", "price_val": 2500, "description": "Un espectacular anillo de compromiso con un diamante de 1 quilate y una banda de platino.", "materials": "Platino, Diamante 1ct", "stock": 3},
    {"id": 14, "name": "Collar de Estrellas", "price_val": 480, "description": "Un collar juguetón con múltiples dijes en forma de estrella, perfecto para un look casual.", "materials": "Plata de ley, Circonitas", "stock": 15},
    {"id": 15, "name": "Pulsera de Infinito", "price_val": 320, "description": "Simboliza la eternidad con esta delicada pulsera con el símbolo del infinito.", "materials": "Plata chapada en rodio", "stock": 18},
    {"id": 16, "name": "Pendientes de Aro de Oro", "price_val": 500, "description": "Aros de oro de tamaño mediano, un clásico versátil que nunca pasa de moda.", "materials": "Oro 18k", "stock": 14}
]

# --- Rutas Principales ---
@app.route('/')
def index():
    # He añadido un 'id' a cada producto para que funcione el enlace de "Ver Detalles"
    products = Product.query.limit(4).all()
    return render_template('index.html', products=products)

# --- Rutas que necesitas agregar ---

@app.route('/catalog')
def catalog():
    # Ahora los productos vienen de la base de datos
    products = Product.query.limit(12).all()
    return render_template('catalog.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        new_suggestion = Suggestion(name=name, email=email, message=message)
        db.session.add(new_suggestion)
        db.session.commit()
        flash('¡Gracias por tu sugerencia! La hemos recibido.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Esta ruta recibe el ID del producto para mostrar sus detalles
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

# --- Rutas de Autenticación ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_by_email = User.query.filter_by(email=email).first()
        user_by_name = User.query.filter_by(username=username).first()

        if user_by_email or user_by_name:
            flash('El nombre de usuario o el correo ya existen.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        # Inicia sesión automáticamente después del registro
        login_user(new_user)
        flash('¡Registro exitoso! Has iniciado sesión automáticamente.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

# --- Rutas de Administrador ---
@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/suggestions')
@login_required
def admin_suggestions():
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    
    suggestions = Suggestion.query.order_by(Suggestion.id.desc()).all()
    return render_template('admin_suggestions.html', suggestions=suggestions)

@app.route('/admin/user_cart/<int:user_id>')
@login_required
def admin_user_cart(user_id):
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    return render_template('admin_user_cart.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('index'))

    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('admin_users'))

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f'El usuario "{user_to_delete.username}" ha sido eliminado.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')

        # Validar que el nuevo nombre de usuario o email no estén ya en uso por otro usuario
        if username != current_user.username and User.query.filter_by(username=username).first():
            flash('Ese nombre de usuario ya está en uso.', 'danger')
            return redirect(url_for('profile'))
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('Ese correo electrónico ya está en uso.', 'danger')
            return redirect(url_for('profile'))

        current_user.username = username
        current_user.email = email
        current_user.phone_number = phone_number
        db.session.commit()
        flash('Tu perfil ha sido actualizado con éxito.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

# --- Rutas del Carrito ---
@app.route('/add_to_cart', methods=['POST'])
def handle_add_to_cart(product_id):
    if not current_user.is_authenticated:
        flash('Por favor, regístrate o inicia sesión para añadir productos a tu carrito.', 'danger')
        return redirect(url_for('register'))
    
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    return add_to_cart(product_id, quantity)


@login_required
def add_to_cart(product_id, quantity=1):
    product = Product.query.get_or_404(product_id)
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if product.stock < quantity:
        flash(f'No hay suficiente stock para "{product.name}". Solo quedan {product.stock} unidades.', 'danger')
        return redirect(request.referrer or url_for('index'))

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'"{product.name}" ha sido añadido a tu carrito.', 'success')

    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
@login_required
def cart():
    # Los items del carrito ahora vienen de la base de datos
    cart_items = current_user.cart_items
    total_price = 0
    for item in cart_items:
        total_price += item.product.price_val * item.quantity

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        product_name = cart_item.product.name
        db.session.delete(cart_item)
        db.session.commit()
        flash(f'"{product_name}" ha sido eliminado de tu carrito.', 'success')
    else:
        flash('El producto no se encontró en tu carrito.', 'danger')

    return redirect(url_for('cart'))

if __name__ == '__main__':
    # Se usa el puerto 5001 para evitar conflictos con otros servidores
    with app.app_context():
        # Crea todas las tablas de la base de datos
        db.create_all()

        # Popula la tabla de productos si está vacía
        if Product.query.count() == 0:
            for p_data in PRODUCTS_DATA:
                product = Product(**p_data)
                db.session.add(product)
            db.session.commit()

        # Crea el usuario administrador si no existe
        if not User.query.filter_by(username='daonil').first():
            admin_user = User(
                username='daonil',
                email='admin@asteriamoon.com', # Puedes cambiar este email si lo deseas
                is_admin=True,
                phone_number=None
            )
            admin_user.set_password('1234')
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True, port=5001)