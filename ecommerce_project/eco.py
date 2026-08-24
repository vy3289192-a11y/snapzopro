from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import random
import smtplib
from email.mime.text import MIMEText
import razorpay
import ast

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vistan_super_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ========================================================
# 1. RAZORPAY SETUP
# ========================================================
RAZORPAY_KEY_ID = 'rzp_test_SmR1NuUnO3yNhV'
RAZORPAY_KEY_SECRET = 'ZQyIPKANFwzUXwGcDa7ua5Gd'

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ========================================================
# 2. DATABASE MODELS
# ========================================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    role = db.Column(db.String(20), default='customer')
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    mrp = db.Column(db.Integer, nullable=False)
    selling_price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=10)
    
    image_url = db.Column(db.String(500), nullable=False)
    image_url2 = db.Column(db.String(500), nullable=True)
    image_url3 = db.Column(db.String(500), nullable=True)
    sizes = db.Column(db.String(100), nullable=True)
    
    @property
    def discount_percent(self):
        if self.mrp > self.selling_price:
            return int(((self.mrp - self.selling_price) / self.mrp) * 100)
        return 0

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    delivery_address = db.Column(db.Text)
    order_details = db.Column(db.Text) 
    total_amount = db.Column(db.Integer)
    status = db.Column(db.String(50), default='Pending')
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_name = db.Column(db.String(100), default='VISTAN')
    tagline = db.Column(db.String(200), default='')
    logo_url = db.Column(db.String(500), default='')
    upi_id = db.Column(db.String(100), default='vy3289192@okicici')
    delivery_charge = db.Column(db.Integer, default=0)
    enable_cod = db.Column(db.Boolean, default=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)   

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========================================================
# 3. EMAIL FUNCTIONS (OTP & ORDER CONFIRMATION)
# ========================================================
SENDER_EMAIL = "roliy6064@gmail.com"
SENDER_PASSWORD = "crvm rbrp otvt yuia"

def send_otp_email(receiver_email, otp):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; }}
            .header {{ background-color: #2874f0; padding: 25px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 26px; letter-spacing: 1.5px; text-transform: uppercase; }}
            .content {{ padding: 40px 30px; text-align: center; color: #333333; }}
            .content h2 {{ color: #212121; margin-top: 0; }}
            .content p {{ font-size: 15px; line-height: 1.6; color: #555555; margin-bottom: 20px; }}
            .otp-box {{ background-color: #f8f9fa; border: 2px dashed #2874f0; color: #2874f0; font-size: 34px; font-weight: bold; letter-spacing: 8px; padding: 15px 30px; margin: 25px auto; width: fit-content; border-radius: 8px; }}
            .footer {{ background-color: #f1f3f6; padding: 20px; text-align: center; font-size: 12px; color: #888888; border-top: 1px solid #e0e0e0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>VISTAN PREMIUM</h1>
            </div>
            <div class="content">
                <h2>Secure Login Verification</h2>
                <p>Hello,</p>
                <p>We received a request to log in to your VISTAN account. Please use the secure One-Time Password (OTP) below to access your account.</p>
                
                <div class="otp-box">{otp}</div>
                
                <p style="font-size: 13px; color: #888; margin-top: 30px;">
                    <i>If you did not request this OTP, please ignore this email. Do not share this code with anyone.</i>
                </p>
            </div>
            <div class="footer">
                &copy; 2026 VISTAN Premium | Varanasi, Uttar Pradesh.<br>
                This is an automated security email, please do not reply.
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = 'VISTAN Secure Login OTP'
    msg['From'] = f"VISTAN Premium <{SENDER_EMAIL}>"
    msg['To'] = receiver_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email Send Error:", e)
        return False

def send_order_email(receiver_email, order_id, user_name, total_amount, payment_method, full_address):
    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; background-color: #ffffff;">
        <div style="text-align: center; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; margin-bottom: 20px;">
            <h1 style="color: #2874f0; margin: 0; font-size: 28px; letter-spacing: 1px;">VISTAN</h1>
            <p style="color: #777; margin: 5px 0 0 0; font-size: 14px;">Premium Smart Shopping</p>
        </div>
        
        <h2 style="color: #333; text-align: center;">Order Successfully Placed! 🎉</h2>
        <p style="color: #555; font-size: 16px; line-height: 1.5;">Hi <strong>{user_name}</strong>,</p>
        <p style="color: #555; font-size: 16px; line-height: 1.5;">Thank you for shopping with us! We have received your order and are getting it ready for dispatch.</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #2874f0;">
            <h3 style="margin-top: 0; color: #333; font-size: 16px; border-bottom: 1px solid #ddd; padding-bottom: 10px;">Order Summary (#ORD-{order_id})</h3>
            <p style="margin: 10px 0 5px 0; color: #555;"><strong>Total Amount:</strong> <span style="color: #212121; font-size: 18px; font-weight: bold;">₹{total_amount}</span></p>
            <p style="margin: 5px 0; color: #555;"><strong>Payment Method:</strong> {payment_method}</p>
            <p style="margin: 5px 0; color: #555;"><strong>Delivery Address:</strong> {full_address}</p>
        </div>
        
        <p style="color: #777; font-size: 14px; text-align: center;">You can track your order status anytime by visiting the 'My Orders' section on our website.</p>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="http://127.0.0.1:5000/my_orders" style="background-color: #2874f0; color: #ffffff; text-decoration: none; padding: 12px 25px; border-radius: 5px; font-weight: bold; font-size: 15px;">View My Orders</a>
        </div>
        
        <p style="color: #999; font-size: 12px; text-align: center; margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
            &copy; 2026 Vistan Premium. All rights reserved.<br>Varanasi, UP, India
        </p>
    </div>
    """

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = f'Order Confirmed - VISTAN #ORD-{order_id}'
    msg['From'] = f"VISTAN Premium <{SENDER_EMAIL}>"
    msg['To'] = receiver_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email Send Error:", e)
        return False

# ========================================================
# 4. AUTHENTICATION (OTP LOGIN)
# ========================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        otp = str(random.randint(100000, 999999))
        
        if send_otp_email(email, otp):
            session['otp'] = otp
            session['login_email'] = email
            return redirect(url_for('verify_otp'))
        else:
            flash('Error sending email. Please check your credentials.', 'danger')
            
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'login_email' not in session:
        return redirect(url_for('login'))

    email = session.get('login_email')

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if user_otp == session.get('otp'):
            user = User.query.filter_by(email=email).first()
            
            if not user:
                username = email.split('@')[0]
                user = User(username=username, email=email, password='OTP_LOGIN', role='customer')
                db.session.add(user)
                db.session.commit()

            login_user(user)
            session.pop('otp', None)
            session.pop('login_email', None)
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            flash('Invalid OTP! Please try again.', 'danger')

    return render_template('verify_otp.html', email=email)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_name = request.form.get('username') or request.form.get('name')
        new_phone = request.form.get('phone')
        
        if new_name:
            current_user.username = new_name
        if new_phone:
            current_user.phone = new_phone
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ========================================================
# 5. USER STORE ROUTES
# ========================================================
@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products, current_category='Home')

@app.route('/category/<category_name>')
def category(category_name):
    if category_name == 'Men':
        products = Product.query.filter(Product.category.like('Men%')).all()
    elif category_name == 'Women':
        products = Product.query.filter(Product.category.like('Women%')).all()
    else:
        products = Product.query.filter_by(category=category_name).all()
        
    return render_template('index.html', products=products, current_category=category_name)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    cart_count = len(session.get('cart', []))
    
    # 1. Related Products nikalna
    related_products = Product.query.filter(
        Product.category == product.category, 
        Product.id != product.id
    ).limit(4).all() 
    
    # 2. Reviews nikalna
    reviews = Review.query.filter_by(product_id=product.id).order_by(Review.id.desc()).all()
    
    # 3. Average Rating nikalna
    avg_rating = 0
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
        
    return render_template('product_detail.html', 
                           product=product, 
                           cart_count=cart_count, 
                           related_products=related_products, 
                           reviews=reviews, 
                           avg_rating=avg_rating)

@app.route('/add_review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')
    
    if comment:
        new_review = Review(
            product_id=product_id,
            user_name=current_user.username,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        db.session.commit()
        flash("Review added successfully!", "success")
        
    return redirect(f'/product/{product_id}')

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    size = request.form.get('size', 'Free Size')
    quantity = int(request.form.get('quantity', 1))
    action = request.form.get('action') 
    
    if 'cart' not in session or not isinstance(session['cart'], list):
        session['cart'] = []
        
    cart = session['cart']
    cart = [item for item in cart if isinstance(item, dict)]
    
    found = False
    for item in cart:
        if item.get('id') == product_id and item.get('size') == size:
            item['quantity'] += quantity
            found = True
            break
            
    if not found:
        cart.append({
            'id': product.id,
            'name': product.name,
            'selling_price': product.selling_price,
            'mrp': product.mrp,
            'image_url': product.image_url,
            'size': size,
            'quantity': quantity
        })
        
    session['cart'] = cart
    session.modified = True
    
    if action == 'buy':
        return redirect('/checkout')
    
    return redirect(f'/product/{product_id}')

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return "<h1>Kachra Saaf! <a href='/'>Go to Home</a></h1>"

@app.route('/wishlist', methods=['GET'])
@login_required
def wishlist():
    wishlist_ids = session.get('wishlist', [])
    products = Product.query.filter(Product.id.in_(wishlist_ids)).all() if wishlist_ids else []
    return render_template('wishlist.html', products=products)

@app.route('/payment', methods=['POST'])
def payment_page():
    if request.method == 'POST':
        session['checkout_address'] = {
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'house': request.form.get('house'),
            'area': request.form.get('area'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'pincode': request.form.get('pincode')
        }
        return render_template('payment.html')

@app.route('/place_order', methods=['POST'])
def place_order():
    if request.method == 'POST':
        address_data = session.get('checkout_address')
        if not address_data:
            return redirect('/checkout') 
            
        payment_method = request.form.get('payment_method', 'COD')
        full_address = f"{address_data['house']}, {address_data['area']}, {address_data['city']}, {address_data['state']} - {address_data['pincode']}"
        
        cart = session.get('cart', [])
        total = sum(int(item['selling_price']) * int(item['quantity']) for item in cart if isinstance(item, dict))
        
        u_id = current_user.id if current_user.is_authenticated else None
        
        new_order = Order(
            user_id=u_id,
            customer_name=address_data['name'],
            customer_phone=address_data['phone'],
            delivery_address=full_address,
            order_details=f"Payment: {payment_method} | Items: {str(cart)}", 
            total_amount=total
        )
        db.session.add(new_order)
        db.session.commit() 
        
        # --- ORDER EMAIL DISPATCH ---
        if current_user.is_authenticated and current_user.email:
            send_order_email(
                receiver_email=current_user.email,
                order_id=new_order.id,
                user_name=address_data['name'],
                total_amount=total,
                payment_method=payment_method,
                full_address=full_address
            )
        
        session.pop('cart', None)
        session.pop('checkout_address', None)
        
        return render_template('success.html', name=address_data['name'])

@app.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    wishlist = session.get('wishlist', [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        flash('Removed from Wishlist', 'success')
    else:
        wishlist.append(product_id)
        flash('Added to Wishlist', 'success')
    session['wishlist'] = wishlist
    return redirect(request.referrer or url_for('home'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    clean_cart = [item for item in cart if isinstance(item, dict)]
    if len(cart) != len(clean_cart):
        session['cart'] = clean_cart
        session.modified = True
        
    total_amount = sum(int(item['selling_price']) * int(item['quantity']) for item in clean_cart)
    return render_template('cart.html', cart_items=clean_cart, total_amount=total_amount)

@app.route('/remove_item/<int:product_id>/<size>')
def remove_item(product_id, size):
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if not (item['id'] == product_id and item.get('size') == size)]
    session.modified = True
    return redirect('/cart')

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    if product_id in cart:
        cart.remove(product_id)
        session['cart'] = cart
        flash('Product removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', [])
    clean_cart = [item for item in cart if isinstance(item, dict)]
    
    if not clean_cart:
        flash("Your cart is empty!", "danger")
        return redirect('/cart')
        
    total_amount = sum(int(item['selling_price']) * int(item['quantity']) for item in clean_cart)
    total_mrp = sum(int(item.get('mrp', item['selling_price'])) * int(item['quantity']) for item in clean_cart)
    total_discount = total_mrp - total_amount
    
    return render_template('checkout.html', 
                           cart_items=clean_cart, 
                           total_amount=total_amount, 
                           total_mrp=total_mrp, 
                           discount=total_discount)

@app.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    flash('Payment Successful! Your order has been placed.', 'success')
    return redirect(url_for('my_orders'))

@app.route('/my_orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    for order in orders:
        try:
            items_str = order.order_details.split("Items: ")[1]
            order.parsed_items = ast.literal_eval(items_str)
            order.payment_mode = order.order_details.split(" | ")[0].replace("Payment: ", "")
        except:
            order.parsed_items = []
            order.payment_mode = "COD"
            
    return render_template('my_orders.html', orders=orders)

@app.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    try:
        items_str = order.order_details.split("Items: ")[1]
        order.parsed_items = ast.literal_eval(items_str)
        order.payment_mode = order.order_details.split(" | ")[0].replace("Payment: ", "")
    except:
        order.parsed_items = []
        order.payment_mode = "COD"
        
    return render_template('order_detail.html', order=order)

# ========================================================
# 6. ADMIN DASHBOARD ROUTES
# ========================================================
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    total_sales = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    total_orders = Order.query.count()
    total_products = Product.query.count()
    
    return render_template('admin/dashboard.html', total_sales=total_sales, total_orders=total_orders, total_products=total_products)

@app.route('/admin/products')
@login_required
def admin_products():
    if current_user.role != 'admin': return redirect(url_for('home'))
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

# --- ADMIN: MAGIC BUTTON (Generate 50 Fake Reviews) ---
@app.route('/admin/generate_reviews/<int:product_id>', methods=['POST'])
@login_required
def generate_fake_reviews(product_id):
    if current_user.role != 'admin': 
        return redirect('/')
        
    first_names = ["Rahul", "Amit", "Priya", "Sneha", "Vikram", "Neha", "Rohan", "Anjali", "Karan", "Pooja", "Vishal", "Ravi", "Kavita", "Suresh"]
    last_names = ["Kumar", "Sharma", "Singh", "Verma", "Gupta", "Yadav", "Patel", "Reddy", "Mishra", "Jain"]
    
    comments = [
        "Awesome product! Fit is perfect.", 
        "Loved the quality, definitely buying again.", 
        "Best purchase ever on this site.", 
        "Value for money. Go for it guys!", 
        "Looks exactly like the picture.", 
        "Fabric is very soft and comfortable.", 
        "Highly recommended!", 
        "Good fit and fast delivery.", 
        "Superb quality at this price point.", 
        "Not bad, pretty good for daily use.",
        "Premium feel, totally worth it.",
        "My brother loved it!"
    ]
    
    for _ in range(50):
        random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        random_rating = random.choice([4, 4, 5, 5, 5])
        random_comment = random.choice(comments)
        
        new_review = Review(
            product_id=product_id,
            user_name=random_name,
            rating=random_rating,
            comment=random_comment
        )
        db.session.add(new_review)
        
    db.session.commit()
    flash(f"50 Magic Reviews added to Product ID {product_id}!", "success")
    return redirect('/admin/products')

@app.route('/admin/bulk_delete', methods=['POST'])
def bulk_delete():
    product_ids = request.form.getlist('product_ids')
    if product_ids:
        for pid in product_ids:
            product = Product.query.get(pid)
            if product:
                db.session.delete(product)
        db.session.commit()
    return redirect('/admin/products')

@app.route('/admin/edit_product', methods=['POST'])
def edit_product():
    pid = request.form.get('product_id')
    product = Product.query.get(pid)
    
    if product:
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.mrp = request.form.get('mrp')
        product.selling_price = request.form.get('selling_price')
        product.stock = request.form.get('stock')
        product.image_url = request.form.get('image_url')
        db.session.commit()
        
    return redirect('/admin/products')

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        mrp = request.form.get('mrp')
        selling_price = request.form.get('selling_price')
        stock = request.form.get('stock')
        
        image_url = request.form.get('image_url')
        image_url2 = request.form.get('image_url2')
        image_url3 = request.form.get('image_url3')
        sizes = request.form.get('sizes')

        new_product = Product(
            name=name,
            category=category,
            mrp=int(mrp),
            selling_price=int(selling_price),
            stock=int(stock),
            image_url=image_url,
            image_url2=image_url2,
            image_url3=image_url3,
            sizes=sizes
        )
        db.session.add(new_product)
        db.session.commit()
        
        return redirect('/admin/products')

@app.route('/admin/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_product(id):
    if current_user.role != 'admin': return redirect(url_for('home'))
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
def admin_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    order = Order.query.get(order_id)
    if order:
        new_status = request.form.get('status')
        order.status = new_status
        db.session.commit()
    return redirect('/admin/orders')

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin': return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin': return redirect(url_for('home'))
    if id == current_user.id:
        flash("You cannot delete your own admin account!", "danger")
        return redirect(url_for('admin_users'))
        
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if current_user.role != 'admin': return redirect(url_for('home'))
    
    setting = Setting.query.first()
    if not setting:
        setting = Setting()
        db.session.add(setting)
        db.session.commit()
        
    if request.method == 'POST':
        setting.website_name = request.form.get('website_name')
        setting.tagline = request.form.get('tagline')
        setting.logo_url = request.form.get('logo_url')
        setting.upi_id = request.form.get('upi_id')
        setting.delivery_charge = request.form.get('delivery_charge') or 0
        setting.enable_cod = True if request.form.get('enable_cod') else False
        
        db.session.commit()
        flash('Settings Updated Successfully!', 'success')
        return redirect(url_for('admin_settings'))
        
    return render_template('admin/settings.html', setting=setting)

# ========================================================
# 7. APP RUN & DB INITIALIZATION
# ========================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            admin = User(username='Super Admin', email='vy3289192@gmail.com', password='OTP_LOGIN', role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Default Admin Created: admin@vistan.com")
            
    app.run(debug=True)