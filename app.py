from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cambia-esta-clave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wjr_tecnosoluciones.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/products'

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
DEFAULT_WHATSAPP_LINK = 'https://wa.me/573246060069'
DEFAULT_FACEBOOK_LINK = 'https://www.facebook.com/share/1G95SmYMcL/'
DEFAULT_INSTAGRAM_LINK = 'https://www.instagram.com/wjrtecnosoluciones_c?igsh=MTBndDZ0a29jenlpOA=='


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    cart_items = db.relationship('CartItem', backref='usuario', cascade='all, delete-orphan')

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    tipo = db.Column(db.String(20), nullable=False)  # reparacion | mayor
    imagen_url = db.Column(db.String(255), nullable=True)


class SiteContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    about_title = db.Column(db.String(120), default='Acerca de nosotros')
    about_body = db.Column(
        db.Text,
        default='Somos WJR Tecnosoluciones. Aquí puedes contar quiénes son, qué hacen y cuál es su propósito.',
    )
    whatsapp_link = db.Column(db.String(255), default=DEFAULT_WHATSAPP_LINK)
    facebook_link = db.Column(db.String(255), default=DEFAULT_FACEBOOK_LINK)
    instagram_link = db.Column(db.String(255), default=DEFAULT_INSTAGRAM_LINK)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)

    product = db.relationship('Product')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acceso restringido al panel administrativo.', 'danger')
            return redirect(url_for('home'))
        return func(*args, **kwargs)

    return wrapper


def get_site_content() -> SiteContent:
    content = SiteContent.query.first()
    if not content:
        content = SiteContent()
        db.session.add(content)
        db.session.commit()
    return content


@app.context_processor
def inject_site_content():
    return {'global_site_content': get_site_content()}


def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_image(image_file):
    if not image_file or not image_file.filename:
        return None

    if not allowed_file(image_file.filename):
        flash('Formato de imagen no permitido. Usa PNG, JPG, WEBP o GIF.', 'warning')
        return None

    extension = image_file.filename.rsplit('.', 1)[1].lower()
    safe_name = secure_filename(image_file.filename.rsplit('.', 1)[0])
    filename = f"{safe_name}-{uuid4().hex[:8]}.{extension}"

    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / filename
    image_file.save(destination)

    return f"uploads/products/{filename}"


def migrate_existing_schema():
    with db.engine.begin() as connection:
        columns = {row[1] for row in connection.execute(text('PRAGMA table_info(product)'))}
        if 'imagen_url' not in columns:
            connection.execute(text('ALTER TABLE product ADD COLUMN imagen_url VARCHAR(255)'))


@app.route('/')
def home():
    site_content = get_site_content()
    return render_template('home.html', site_content=site_content)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if not nombre or not email or not password:
            flash('Completa todos los campos.', 'warning')
            return redirect(url_for('registro'))

        if User.query.filter_by(email=email).first():
            flash('Este correo ya está registrado.', 'warning')
            return redirect(url_for('registro'))

        nuevo_usuario = User(nombre=nombre, email=email)
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Bienvenido a WJR Tecnosoluciones.', 'success')
            return redirect(url_for('home'))

        flash('Credenciales inválidas.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada con éxito.', 'info')
    return redirect(url_for('home'))


@app.route('/servicios-reparacion')
def servicios_reparacion():
    productos = Product.query.filter_by(tipo='reparacion').all()
    return render_template('catalogo.html', titulo='Reparación y repuestos', productos=productos)


@app.route('/venta-mayor')
def venta_mayor():
    productos = Product.query.filter_by(tipo='mayor').all()
    return render_template('catalogo.html', titulo='Accesorios y productos al mayor', productos=productos)


@app.post('/agregar-carrito/<int:producto_id>')
@login_required
def agregar_carrito(producto_id):
    producto = Product.query.get_or_404(producto_id)
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=producto.id).first()

    if item:
        item.cantidad += 1
    else:
        item = CartItem(user_id=current_user.id, product_id=producto.id, cantidad=1)
        db.session.add(item)

    db.session.commit()
    flash(f'Se agregó {producto.nombre} al carrito.', 'success')
    return redirect(request.referrer or url_for('home'))


@app.route('/carrito')
@login_required
def carrito():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.precio * item.cantidad for item in items)
    return render_template('carrito.html', items=items, total=total)


@app.post('/carrito/eliminar/<int:item_id>')
@login_required
def eliminar_del_carrito(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('No autorizado.', 'danger')
        return redirect(url_for('carrito'))

    db.session.delete(item)
    db.session.commit()
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('carrito'))


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        telefono = request.form['telefono'].strip()
        mensaje = request.form['mensaje'].strip()
        if not nombre or not telefono or not mensaje:
            flash('Todos los campos de contacto son obligatorios.', 'warning')
        else:
            flash('Gracias por escribirnos. Pronto te responderemos.', 'success')
        return redirect(url_for('contacto'))

    return render_template('contacto.html')


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    usuarios = User.query.order_by(User.id.desc()).all()
    productos = Product.query.order_by(Product.id.desc()).all()
    site_content = get_site_content()
    return render_template('admin.html', usuarios=usuarios, productos=productos, site_content=site_content)


@app.post('/admin/usuarios/eliminar/<int:user_id>')
@login_required
@admin_required
def eliminar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'warning')
        return redirect(url_for('admin_dashboard'))

    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.post('/admin/productos/crear')
@login_required
@admin_required
def crear_producto():
    nombre = request.form['nombre'].strip()
    descripcion = request.form['descripcion'].strip()
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    tipo = request.form['tipo']

    imagen_url = request.form.get('imagen_url', '').strip()
    uploaded_image = save_uploaded_image(request.files.get('imagen_archivo'))
    if uploaded_image:
        imagen_url = uploaded_image

    producto = Product(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        tipo=tipo,
        imagen_url=imagen_url or None,
    )
    db.session.add(producto)
    db.session.commit()

    flash('Producto creado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.post('/admin/productos/actualizar/<int:producto_id>')
@login_required
@admin_required
def actualizar_producto(producto_id):
    producto = Product.query.get_or_404(producto_id)
    producto.nombre = request.form['nombre'].strip()
    producto.descripcion = request.form['descripcion'].strip()
    producto.precio = float(request.form['precio'])
    producto.stock = int(request.form['stock'])
    producto.tipo = request.form['tipo']
    producto.imagen_url = request.form.get('imagen_url', '').strip() or producto.imagen_url

    uploaded_image = save_uploaded_image(request.files.get('imagen_archivo'))
    if uploaded_image:
        producto.imagen_url = uploaded_image

    db.session.commit()
    flash('Producto actualizado correctamente.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.post('/admin/productos/eliminar/<int:producto_id>')
@login_required
@admin_required
def eliminar_producto(producto_id):
    producto = Product.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.post('/admin/acerca-de')
@login_required
@admin_required
def actualizar_acerca_de():
    site_content = get_site_content()
    site_content.about_title = request.form.get('about_title', '').strip() or 'Acerca de nosotros'
    site_content.about_body = request.form.get('about_body', '').strip() or site_content.about_body
    site_content.whatsapp_link = request.form.get('whatsapp_link', '').strip() or site_content.whatsapp_link
    site_content.facebook_link = request.form.get('facebook_link', '').strip() or site_content.facebook_link
    site_content.instagram_link = request.form.get('instagram_link', '').strip() or site_content.instagram_link

    db.session.commit()
    flash('Se actualizó la sección "Acerca de nosotros" y los enlaces de contacto.', 'success')
    return redirect(url_for('admin_dashboard'))


def seed_data():
    if not User.query.filter_by(email='admin@wjr.com').first():
        admin = User(nombre='Administrador WJR', email='admin@wjr.com', is_admin=True)
        admin.set_password('Admin123*')
        db.session.add(admin)

    if Product.query.count() == 0:
        db.session.add_all([
            Product(nombre='Cambio de pantalla', descripcion='Servicio técnico para pantallas de laptop y celular.', precio=45.00, stock=20, tipo='reparacion'),
            Product(nombre='Batería original', descripcion='Repuesto para laptops de varias marcas.', precio=35.00, stock=15, tipo='reparacion'),
            Product(nombre='Mouse inalámbrico', descripcion='Accesorio ergonómico para oficina y hogar.', precio=12.50, stock=150, tipo='mayor'),
            Product(nombre='Teclado mecánico', descripcion='Producto gamer al mayor para distribuidores.', precio=29.99, stock=70, tipo='mayor'),
        ])

    site_content = get_site_content()
    if not site_content.whatsapp_link or site_content.whatsapp_link == 'https://wa.me/0000000000':
        site_content.whatsapp_link = DEFAULT_WHATSAPP_LINK
    if not site_content.facebook_link or site_content.facebook_link == 'https://facebook.com':
        site_content.facebook_link = DEFAULT_FACEBOOK_LINK
    if not site_content.instagram_link or site_content.instagram_link == 'https://instagram.com':
        site_content.instagram_link = DEFAULT_INSTAGRAM_LINK

    db.session.commit()


with app.app_context():
    db.create_all()
    migrate_existing_schema()
    seed_data()


if __name__ == '__main__':
    app.run(debug=True)
