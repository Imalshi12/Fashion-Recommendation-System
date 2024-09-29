from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.context import CryptContext 
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
import pickle

app = Flask(__name__)
app.secret_key = 'fb61cde08f3e661126dc127f5b39e739616b7ce3057f159e0e11b8a644ae0cf4'


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/body_shape_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)  
    age = db.Column(db.Integer, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to User
    dress_size = db.Column(db.Float, nullable=False)
    breasts = db.Column(db.Float, nullable=False)
    waist = db.Column(db.Float, nullable=False)
    hips = db.Column(db.Float, nullable=False)
    shoe = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    body_shape = db.Column(db.String(50), nullable=False)

    user = db.relationship('User', backref=db.backref('predictions', lazy=True))


class FashionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body_shape = db.Column(db.String(50), nullable=False) 
    name = db.Column(db.String(100), nullable=False)  
    image = db.Column(db.String(200), nullable=False)  
    price = db.Column(db.String(20), nullable=False)  

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fashion_item_id = db.Column(db.Integer, db.ForeignKey('fashion_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1) 

class UpdateProfileForm(FlaskForm):
    username = StringField('Username')
    email = StringField('Email')
    age = IntegerField('Age')
    password = PasswordField('New Password')
    submit = SubmitField('Update Profile')


model = pickle.load(open('best_model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        user = User.query.filter_by(username=username).first()
        if user and pwd_context.verify(password, user.password):
            login_user(user)
            
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    
    user_predictions = Prediction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user_predictions=user_predictions)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    all_users = User.query.all()
    return render_template('admin_dashboard.html', users=all_users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login')) 

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    body_shape_result = None
    
    if request.method == 'POST':
        dress_size = float(request.form['Dress_size'])
        breasts = float(request.form['Breasts'])
        waist = float(request.form['Waist'])
        hips = float(request.form['Hips'])
        shoe = float(request.form['Shoe'])
        height = float(request.form['Height'])
        weight = float(request.form['Weight'])
        
        features = [[dress_size, breasts, waist, hips, shoe, height, weight]]
        result = model.predict(features)[0]
        body_shapes = ['Banana', 'Hourglass', 'Pear', 'Apple', 'Inverted Triangle', 'Rectangle']
        body_shape_result = body_shapes[result]
        prediction = Prediction(dress_size=dress_size, breasts=breasts, waist=waist, hips=hips,
                                shoe=shoe, height=height, weight=weight, body_shape=body_shape_result,
                                user_id=current_user.id)
        db.session.add(prediction)
        db.session.commit()
        
        return render_template('body_display.html', body_shape=body_shape_result)

    return render_template('predict.html', body_shape=None)


pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        age = request.form['age']
        is_admin = request.form.get('is_admin', 'off') == 'on'

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists! Please choose another one.')
            return redirect(url_for('register'))

        hashed_password = pwd_context.hash(password)

        new_user = User(username=username, password=hashed_password,
                         email=email, age=age, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/predictions')
@login_required
def predictions():
    all_predictions = Prediction.query.all()
    return render_template('predictions.html', predictions=all_predictions)

@app.route('/fashion/<body_shape>')
@login_required
def fashion_recommendation(body_shape):
    items = FashionItem.query.filter_by(body_shape=body_shape).all()
    return render_template('fashion_recommendation.html', body_shape=body_shape, items=items)


@app.route('/admin/fashion', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_fashion():
    if request.method == 'POST':
        body_shape = request.form['body_shape']
        name = request.form['name']
        image = request.form['image']
        price = request.form['price']
       
        
        new_item = FashionItem(body_shape=body_shape, name=name, image=image, price=price )
        db.session.add(new_item)
        db.session.commit()
        
        
        return redirect(url_for('manage_fashion'))
    
    fashion_items = FashionItem.query.all()
    return render_template('admin_fashion.html', fashion_items=fashion_items)


@app.route('/admin/fashion/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_fashion_item(item_id):
    item = FashionItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.body_shape = request.form['body_shape']
        item.name = request.form['name']
        item.image = request.form['image']
        item.price = request.form['price']
       
        
        db.session.commit()
       
        return redirect(url_for('manage_fashion'))
    
    return render_template('edit_fashion_item.html', item=item)


@app.route('/admin/fashion/delete/<int:item_id>')
@login_required
@admin_required
def delete_fashion_item(item_id):
    item = FashionItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return redirect(url_for('manage_fashion'))

@app.route('/cart/add/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(item_id):
    existing_item = CartItem.query.filter_by(user_id=current_user.id, fashion_item_id=item_id).first()
    if existing_item:
        existing_item.quantity += 1 
    else:
        new_cart_item = CartItem(user_id=current_user.id, fashion_item_id=item_id, quantity=1)
        db.session.add(new_cart_item)
    
    db.session.commit()
    
    return redirect(url_for('fashion_recommendation', body_shape='Banana'))  


@app.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total_price = sum(float(FashionItem.query.get(item.fashion_item_id).price) * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/cart/checkout', methods=['GET'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
       
        return redirect(url_for('view_cart'))
    
    return render_template('payment.html')


@app.route('/cart/process_payment', methods=['POST'])
@login_required
def process_payment():
    
    name = request.form['name']
    address = request.form['address']
    card_number = request.form['card']
    expiry = request.form['expiry']
    cvv = request.form['cvv']

   
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

   
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    
    
    return redirect(url_for('home'))

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.age = form.age.data
        
        
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)

        db.session.commit()
        
        return redirect(url_for('dashboard'))

    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.age.data = current_user.age

    return render_template('update_profile.html', form=form)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)