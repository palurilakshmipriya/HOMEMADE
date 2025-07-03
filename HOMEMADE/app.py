# Flask app with AWS DynamoDB, SNS, IAM (for EC2)
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
import uuid
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)
app.secret_key = '1q2w3e4r5t6y'

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# AWS setup
try:
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    sns = boto3.client('sns', region_name='ap-south-1')
    users_table = dynamodb.Table('Users')
    orders_table = dynamodb.Table('Orders')
except NoCredentialsError:
    print("AWS credentials not found.")

# Product database
products = {
    'veg_pickles': [
        {'id': 1, 'name': 'Andhra Mango Pickle', 'price': 150, 'description': 'Raw mango chunks in fiery red chili-garlic masala.', 'image': 'mango.jpg'},
        {'id': 2, 'name': 'Gongura Pickle', 'price': 140, 'description': 'Tangy gongura leaves pickled with spices & tradition.', 'image': 'gongura.jpg'},
        {'id': 3, 'name': 'Lemon Pickle', 'price': 130, 'description': 'Zesty lemons steeped in mustard, fenugreek & oil.', 'image': 'lemon.jpg'},
        {'id': 4, 'name': 'Tomato Pickle', 'price': 120, 'description': 'Rich, spicy, and bursting with flavor.', 'image': 'tomato.jpg'},
        {'id': 5, 'name': 'Amla Pickle', 'price': 150, 'description': 'Rich in vitamin C and bursting with flavor.', 'image': 'amla.jpg'}
    ],
    'non_veg_pickles': [
        {'id': 6, 'name': 'Boneless Chicken Pickle', 'price': 200, 'description': 'Juicy, tender boneless chicken cooked to perfection.', 'image': 'boneless_chicken_pickle.jpg'},
        {'id': 7, 'name': 'Mutton Pickle', 'price': 300, 'description': 'Mutton pickle with bold and spicy flavor.', 'image': 'mutton.jpg'},
        {'id': 8, 'name': 'Fish Pickle', 'price': 250, 'description': 'A coastal delicacy made with premium fish.', 'image': 'fish.jpg'},
        {'id': 9, 'name': 'Prawn Pickle', 'price': 250, 'description': 'Succulent prawns infused with mustard and chili.', 'image': 'prawns.jpg'},
        {'id': 10, 'name': 'Chicken Gongura Pickle', 'price': 210, 'description': 'Succulent Chicken Gongura Bites.', 'image': 'chicken_gongura.jpg'},
        {'id': 11, 'name': 'Mutton Gongura Pickle', 'price': 210, 'description': 'Where mutton meets gongura magic.', 'image': 'mutton_gongura.jpg'}
    ],
    'snacks': [
        {'id': 12, 'name': 'Masala Murukulu', 'price': 80, 'description': 'Spicy and crunchy spirals made from rice flour and urad dal.', 'image': 'masala_murukulu.jpg'},
        {'id': 13, 'name': 'Karam Boondi', 'price': 70, 'description': 'Golden crispy gram flour pearls seasoned with bold flavors.', 'image': 'karam_boondi.jpg'},
        {'id': 14, 'name': 'Popcorn', 'price': 30, 'description': 'Melt-in-your-mouth buttery goodness with every pop!', 'image': 'popcorn.jpg'},
        {'id': 15, 'name': 'Potato Chips', 'price': 60, 'description': 'Your favorite snack, now with extra crunch and flavor!', 'image': 'potato_chips.jpg'},
        {'id': 16, 'name': 'Mirchi Bajji', 'price': 80, 'description': 'Best enjoyed with a hot cup of chai and a rainy evening.', 'image': 'mirchi_bajji.jpg'},
        {'id': 17, 'name': 'Chekkalu', 'price': 60, 'description': 'Thin and savory rice crackers with hints of cumin and ginger.', 'image': 'chekkalu.jpg'}
    ]
}

# User database (for demo purposes - use a real database in production)
users = {
    'admin@example.com': {
        'name': 'Admin',
        'password': 'admin123',  # In production, use hashed passwords
        'cart': []
    }
}

# Initialize cart in session
@app.before_request
def before_request():
    if 'cart' not in session:
        session['cart'] = []
    if 'user' not in session:
        session['user'] = None

# Helper function for file uploads
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    featured_products = [
        products['veg_pickles'][0],  # Mango Pickle
        products['non_veg_pickles'][0],  # Chicken Pickle
        products['snacks'][0]  # Masala Murukulu
    ]
    return render_template('home.html', featured_products=featured_products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Here you would typically save this to a database or send an email
        print(f"New contact message from {name} ({email}): {message}")
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email in users and users[email]['password'] == password:
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif email in users:
            flash('Email already registered', 'danger')
        else:
            users[email] = {
                'name': name,
                'password': password,  # Remember to hash passwords in production
                'cart': []
            }
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html')
@app.route('/veg_pickles')
def veg_pickles():
    return render_template('veg_pickles.html', products=products['veg_pickles'])

@app.route('/non_veg_pickles')
def non_veg_pickles():
    return render_template('non_veg_pickles.html', products=products['non_veg_pickles'])

@app.route('/snacks')
def snacks():
    return render_template('snacks.html', products=products['snacks'])

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        flash('Please login to add items to cart', 'warning')
        return redirect(url_for('login'))
    
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    
    # Find the product in our database
    product = None
    for category in products.values():
        for p in category:
            if p['id'] == product_id:
                product = p
                break
        if product:
            break
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('home'))
    
    # Add to cart
    cart = session.get('cart', [])
    
    # Check if product already in cart
    found = False
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += quantity
            found = True
            break
    
    if not found:
        cart.append({
            'id': product_id,
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'image': product['image']
        })
    
    session['cart'] = cart
    flash(f'{product["name"]} added to cart', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'user' not in session:
        flash('Please login to modify your cart', 'warning')
        return redirect(url_for('login'))
    
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['id'] != product_id]
    flash('Item removed from cart', 'info')
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        flash('Please login to checkout', 'warning')
        return redirect(url_for('login'))
    
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Process order
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        notes = request.form.get('notes')
        
        # Here you would typically:
        # 1. Save the order to a database
        # 2. Process payment
        # 3. Send confirmation email
        
        order_id = str(uuid.uuid4())[:8].upper()
        flash(f'Order #{order_id} placed successfully!', 'success')
        
        # Clear the cart
        session['cart'] = []
        
        return redirect(url_for('success'))
    
    return render_template('checkout.html')

@app.route('/success')
def success():
    return render_template('success.html')

# Admin routes (protected)
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user' not in session or session['user'] != 'admin@example.com':
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        description = request.form.get('description')
        category = request.form.get('category')
        
        # Handle file upload
        if 'image' not in request.files:
            flash('No image uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['image']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Add to products
            new_id = max(p['id'] for p in products[category]) + 1 if products[category] else 1
            new_product = {
                'id': new_id,
                'name': name,
                'price': price,
                'description': description,
                'image': filename
            }
            products[category].append(new_product)
            
            flash('Product added successfully', 'success')
            return redirect(url_for('home'))
    
    return render_template('admin/add_product.html')

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
