import os
import random
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vistan_super_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vistan.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), default="")
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), default="")
    gender = db.Column(db.String(20), default="")
    address = db.Column(db.String(300), default="")
    password = db.Column(db.String(100), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    old_price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, default="Premium Quality Product")
    category = db.Column(db.String(50), default="General")
    stock = db.Column(db.Integer, default=10)
    image = db.Column(db.String(300), nullable=False)
    image2 = db.Column(db.String(300), default="")
    image3 = db.Column(db.String(300), default="")
    image4 = db.Column(db.String(300), default="")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    cart_details = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.context_processor
def inject_user():
    return dict(current_user_name=session.get('user_name'))

def save_image(file):
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return '/' + file_path.replace('\\', '/')
    return ""

# ==================== ठीक किया गया OTP API (Port 465 SSL के साथ) ====================
SENDER_EMAIL = "roliy6064@gmail.com" 
SENDER_PASSWORD = "tjub srnv vhug nbiy" 

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    email_address = data.get('email')
    if not email_address: 
        return jsonify({"status": "error", "message": "कृपया ईमेल भरें!"})
    
    otp = str(random.randint(1000, 9999))
    session['current_otp'] = otp
    session['otp_email'] = email_address
    
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Vistan Store - Your Login OTP'
        msg['From'] = f"Vistan Store <{SENDER_EMAIL}>"
        msg['To'] = email_address
        html_content = f"""
        <!DOCTYPE html><html><body style="background-color: #f1f3f6; font-family: sans-serif; padding: 40px 0; margin: 0;">
          <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <div style="background-color: #282c3f; padding: 25px; text-align: center;"><h1 style="color: #ffffff; margin: 0; font-size: 28px;">VISTAN<span style="color: #ff3f6c;">.STORE</span></h1></div>
            <div style="padding: 35px 30px;"><p style="font-size: 16px; color: #333; margin-bottom: 20px; font-weight: bold;">Hello,</p><p style="font-size: 15px; color: #555; margin-bottom: 30px;">Your OTP for Vistan Store account is:</p>
              <div style="text-align: center; margin-bottom: 35px;"><span style="font-size: 38px; font-weight: 800; color: #282c3f; background-color: #f5f5f6; padding: 15px 35px; border-radius: 8px; letter-spacing: 8px;">{otp}</span></div>
              <p style="font-size: 14px; color: #777; background: #fff0f4; padding: 15px; border-left: 4px solid #ff3f6c;"><strong>Security Alert:</strong> Please do not share this OTP with anyone.</p>
            </div></div></body></html>
        """
        msg.add_alternative(html_content, subtype='html')
        
        # 🔥 यहाँ बदलाव किया है: Port 465 और SMTP_SSL का इस्तेमाल (Render के लिए बेस्ट)
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return jsonify({"status": "success", "message": "OTP आपके ईमेल पर भेज दिया गया है!"})
    except Exception as e:
        print("SMTP Error:", str(e)) # Render लॉग्स में असली एरर देखने के लिए
        return jsonify({"status": "error", "message": "ईमेल भेजने में समस्या हुई। कृपया पुनः प्रयास करें!"})

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    user_otp = data.get('otp')
    if session.get('current_otp') == user_otp and session.get('otp_email'] == email:
        session.pop('current_otp', None)
        user = User.query.filter_by(email=email).first()
        if not user:
            name_part = email.split('@')[0].capitalize()
            user = User(name=name_part, email=email, password="real_otp_user")
            db.session.add(user)
            db.session.commit()
        session['user_id'] = user.id
        session['user_name'] = user.name
        return jsonify({"status": "success"})
    else: return jsonify({"status": "error", "message": "गलत OTP!"})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    if user is None:
        session.pop('user_id', None)
        session.pop('user_name', None)
        return redirect(url_for('home'))
    if request.method == 'POST':
        user.name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.phone = request.form['phone']
        user.gender = request.form.get('gender', '')
        user.address = request.form['address']
        db.session.commit()
        session['user_name'] = user.name
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session: return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    user_orders = Order.query.filter_by(customer_name=user.name).order_by(Order.date.desc()).all()
    return render_template('my_orders.html', orders=user_orders, user=user)

@app.route('/')
def home():
    return render_template('index.html', products=Product.query.all())

@app.route('/product/<int:id>')
def product_detail(id):
    return render_template('product.html', product=Product.query.get_or_404(id))

@app.route('/api/place_order', methods=['POST'])
def place_order():
    data = request.json
    db.session.add(Order(customer_name=data['name'], phone=data['phone'], address=data['address'], cart_details=data['cart_details'], total_amount=data['total']))
    db.session.commit()
    return jsonify({"status": "success"})

# ==================== ADVANCED ADMIN PANEL ====================
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid Username or Password!"
    return render_template('admin_login.html', error=error)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    all_products = Product.query.all()
    all_orders = Order.query.order_by(Order.date.desc()).all()
    total_users = User.query.count()
    total_revenue = sum(o.total_amount for o in all_orders if o.status != 'Cancelled')
    return render_template('admin.html', products=all_products, orders=all_orders, total_revenue=total_revenue, total_orders=len(all_orders), total_users=total_users)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    if request.method == 'POST':
        img1 = save_image(request.files.get('image1'))
        img2 = save_image(request.files.get('image2'))
        img3 = save_image(request.files.get('image3'))
        img4 = save_image(request.files.get('image4'))
        
        new_prod = Product(
            name=request.form['name'], price=request.form['price'], old_price=request.form['old_price'],
            description=request.form['description'], category=request.form['category'], stock=request.form['stock'],
            image=img1, image2=img2, image3=img3, image4=img4
        )
        db.session.add(new_prod)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    p = Product.query.get_or_404(id)
    if request.method == 'POST':
        p.name = request.form['name']
        p.price = request.form['price']
        p.old_price = request.form['old_price']
        p.description = request.form['description']
        p.category = request.form['category']
        p.stock = request.form['stock']
        
        img1 = save_image(request.files.get('image1'))
        if img1: p.image = img1
        img2 = save_image(request.files.get('image2'))
        if img2: p.image2 = img2
        img3 = save_image(request.files.get('image3'))
        if img3: p.image3 = img3
        img4 = save_image(request.files.get('image4'))
        if img4: p.image4 = img4
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('edit.html', p=p)

@app.route('/delete/<int:id>')
def delete_product(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db.session.delete(Product.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_order/<int:id>', methods=['POST'])
def update_order(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    order = Order.query.get_or_404(id)
    order.status = request.form['status']
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_order/<int:id>')
def delete_order(id):
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    db.session.delete(Order.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
