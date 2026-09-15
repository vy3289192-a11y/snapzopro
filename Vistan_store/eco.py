import os
import random
import json
import urllib.request
import urllib.error

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

# Secret key Render Environment Variable से आएगी
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "vistan-development-secret-change-this"
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vistan.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)


# =========================================================
# EMAIL / OTP CONFIGURATION
# =========================================================

# Render Environment Variables में ये दोनों डालना है:
#
# RESEND_API_KEY = re_xxxxxxxxxxxxxxxxx
# SENDER_EMAIL = Vistan Store <noreply@yourdomain.com>
#
# SENDER_EMAIL में वही domain होना चाहिए जो Resend में verify है.

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get(
    "SENDER_EMAIL",
    "Vistan Store <noreply@yourdomain.com>"
)

OTP_EXPIRY_MINUTES = 10


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        default=""
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        default=""
    )

    gender = db.Column(
        db.String(20),
        default=""
    )

    address = db.Column(
        db.String(300),
        default=""
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )


class Product(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    price = db.Column(
        db.Integer,
        nullable=False
    )

    old_price = db.Column(
        db.Integer,
        nullable=False
    )

    description = db.Column(
        db.Text,
        default="Premium Quality Product"
    )

    category = db.Column(
        db.String(50),
        default="General"
    )

    stock = db.Column(
        db.Integer,
        default=10
    )

    image = db.Column(
        db.String(300),
        nullable=False
    )

    image2 = db.Column(
        db.String(300),
        default=""
    )

    image3 = db.Column(
        db.String(300),
        default=""
    )

    image4 = db.Column(
        db.String(300),
        default=""
    )


class Order(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    customer_name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    address = db.Column(
        db.String(300),
        nullable=False
    )

    cart_details = db.Column(
        db.Text,
        nullable=False
    )

    total_amount = db.Column(
        db.Integer,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# CONTEXT PROCESSOR
# =========================================================

@app.context_processor
def inject_user():
    return {
        "current_user_name": session.get("user_name")
    }


# =========================================================
# IMAGE UPLOAD
# =========================================================

def save_image(file):

    if file and file.filename != "":

        filename = secure_filename(file.filename)

        if not os.path.exists(
            app.config["UPLOAD_FOLDER"]
        ):
            os.makedirs(
                app.config["UPLOAD_FOLDER"]
            )

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(file_path)

        return "/" + file_path.replace(
            "\\",
            "/"
        )

    return ""


# =========================================================
# RESEND EMAIL FUNCTION
# =========================================================

def send_email(to_email, subject, html_content, text_content):

    if not RESEND_API_KEY:

        raise Exception(
            "RESEND_API_KEY Render Environment Variables में सेट नहीं है."
        )

    url = "https://api.resend.com/emails"

    payload = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
        "text": text_content
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    req.add_header(
        "Authorization",
        f"Bearer {RESEND_API_KEY}"
    )

    req.add_header(
        "Content-Type",
        "application/json"
    )

    try:

        with urllib.request.urlopen(
            req,
            timeout=15
        ) as response:

            response_body = response.read().decode(
                "utf-8"
            )

            return json.loads(
                response_body
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise Exception(
            f"Resend API Error {e.code}: {error_body}"
        )

    except urllib.error.URLError as e:

        raise Exception(
            f"Email network error: {str(e)}"
        )


# =========================================================
# SEND OTP API
# =========================================================

@app.route(
    "/api/send_otp",
    methods=["POST"]
)
def send_otp():

    data = request.get_json(
        silent=True
    ) or {}

    email_address = str(
        data.get("email", "")
    ).strip().lower()

    # Email check
    if not email_address:

        return jsonify({
            "status": "error",
            "message": "कृपया ईमेल भरें!"
        }), 400

    if "@" not in email_address:

        return jsonify({
            "status": "error",
            "message": "कृपया सही ईमेल डालें!"
        }), 400

    # =====================================================
    # GENERATE OTP
    # =====================================================

    otp = str(
        random.randint(
            1000,
            9999
        )
    )

    # Current time
    now = datetime.utcnow()

    expiry_time = (
        now +
        timedelta(
            minutes=OTP_EXPIRY_MINUTES
        )
    )

    # =====================================================
    # SAVE OTP IN SESSION
    # =====================================================

    session["current_otp"] = otp
    session["otp_email"] = email_address

    session["otp_created_at"] = now.isoformat()
    session["otp_expires_at"] = expiry_time.isoformat()

    # =====================================================
    # SERVER LOG
    # =====================================================

    print("========================================")
    print(
        f"OTP generated for: {email_address}"
    )
    print(
        f"OTP expires at: {expiry_time}"
    )
    print("========================================")

    # =====================================================
    # EMAIL HTML
    # =====================================================

    html_content = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <title>Vistan Store OTP</title>

    </head>

    <body
        style="
            margin:0;
            padding:0;
            background:#f5f5f5;
            font-family:Arial,Helvetica,sans-serif;
        "
    >

        <div
            style="
                max-width:520px;
                margin:40px auto;
                background:#ffffff;
                border-radius:14px;
                padding:30px;
                box-shadow:0 4px 20px rgba(0,0,0,0.08);
            "
        >

            <h1
                style="
                    text-align:center;
                    margin-bottom:10px;
                "
            >
                Vistan Store
            </h1>

            <p
                style="
                    text-align:center;
                    color:#555;
                    font-size:16px;
                "
            >
                Login Verification
            </p>

            <p
                style="
                    color:#333;
                    font-size:15px;
                    line-height:1.6;
                "
            >
                आपके Vistan Store account में login करने के लिए
                आपका OTP नीचे दिया गया है:
            </p>

            <div
                style="
                    margin:25px 0;
                    padding:20px;
                    background:#f2f2f2;
                    border-radius:12px;
                    text-align:center;
                "
            >

                <div
                    style="
                        font-size:36px;
                        font-weight:bold;
                        letter-spacing:10px;
                    "
                >
                    {otp}
                </div>

            </div>

            <p
                style="
                    text-align:center;
                    color:#666;
                    font-size:14px;
                "
            >
                यह OTP {OTP_EXPIRY_MINUTES} मिनट तक valid है।
            </p>

            <p
                style="
                    color:#333;
                    font-size:14px;
                    line-height:1.6;
                "
            >
                अगर आपने यह login request नहीं की है,
                तो इस email को ignore कर दें।
            </p>

            <hr>

            <p
                style="
                    text-align:center;
                    color:#888;
                    font-size:13px;
                "
            >
                © Vistan Store
            </p>

        </div>

    </body>

    </html>
    """

    text_content = f"""
Vistan Store - Login OTP

Your Vistan Store login OTP is:

{otp}

This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.

If you did not request this login, please ignore this email.

Regards,
Vistan Store
"""

    # =====================================================
    # SEND EMAIL
    # =====================================================

    try:

        response = send_email(
            to_email=email_address,
            subject="Vistan Store - Your Login OTP",
            html_content=html_content,
            text_content=text_content
        )

        print(
            "Email sent successfully:"
        )

        print(response)

        return jsonify({
            "status": "success",
            "message": "OTP आपके ईमेल पर भेज दिया गया है!"
        })

    except Exception as e:

        print(
            "========================================"
        )

        print(
            "EMAIL SEND ERROR:"
        )

        print(
            str(e)
        )

        print(
            "========================================"
        )

        # Email नहीं गया तो OTP session से भी हटा दो
        session.pop(
            "current_otp",
            None
        )

        session.pop(
            "otp_email",
            None
        )

        session.pop(
            "otp_created_at",
            None
        )

        session.pop(
            "otp_expires_at",
            None
        )

        return jsonify({
            "status": "error",
            "message": "OTP भेजा नहीं जा सका। कृपया कुछ देर बाद दोबारा कोशिश करें।"
        }), 500


# =========================================================
# VERIFY OTP API
# =========================================================

@app.route(
    "/api/verify_otp",
    methods=["POST"]
)
def verify_otp():

    data = request.get_json(
        silent=True
    ) or {}

    email = str(
        data.get("email", "")
    ).strip().lower()

    entered_otp = str(
        data.get("otp", "")
    ).strip()

    saved_otp = session.get(
        "current_otp"
    )

    saved_email = session.get(
        "otp_email"
    )

    expires_at_string = session.get(
        "otp_expires_at"
    )

    # =====================================================
    # CHECK OTP EXISTS
    # =====================================================

    if not saved_otp or not saved_email:

        return jsonify({
            "status": "error",
            "message": "OTP नहीं मिला या expire हो गया है। नया OTP मांगें।"
        }), 400

    # =====================================================
    # CHECK EMAIL
    # =====================================================

    if email != saved_email:

        return jsonify({
            "status": "error",
            "message": "ईमेल match नहीं कर रहा है!"
        }), 400

    # =====================================================
    # CHECK OTP EXPIRY
    # =====================================================

    if expires_at_string:

        try:

            expires_at = datetime.fromisoformat(
                expires_at_string
            )

            if datetime.utcnow() > expires_at:

                session.pop(
                    "current_otp",
                    None
                )

                session.pop(
                    "otp_email",
                    None
                )

                session.pop(
                    "otp_created_at",
                    None
                )

                session.pop(
                    "otp_expires_at",
                    None
                )

                return jsonify({
                    "status": "error",
                    "message": "OTP expire हो गया है। नया OTP मांगें।"
                }), 400

        except ValueError:

            return jsonify({
                "status": "error",
                "message": "OTP session invalid है। नया OTP मांगें।"
            }), 400

    # =====================================================
    # CHECK OTP
    # =====================================================

    if entered_otp != saved_otp:

        return jsonify({
            "status": "error",
            "message": "गलत OTP! कृपया दोबारा check करें।"
        }), 400

    # =====================================================
    # FIND USER
    # =====================================================

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        # OTP सही था लेकिन account नहीं मिला
        session.pop(
            "current_otp",
            None
        )

        session.pop(
            "otp_email",
            None
        )

        session.pop(
            "otp_created_at",
            None
        )

        session.pop(
            "otp_expires_at",
            None
        )

        return jsonify({
            "status": "error",
            "message": "इस ईमेल से कोई account नहीं मिला। पहले account बनाएं।"
        }), 404

    # =====================================================
    # LOGIN SUCCESS
    # =====================================================

    session["user_id"] = user.id
    session["user_name"] = user.name

    # =====================================================
    # DELETE OTP AFTER SUCCESSFUL LOGIN
    # =====================================================

    session.pop(
        "current_otp",
        None
    )

    session.pop(
        "otp_email",
        None
    )

    session.pop(
        "otp_created_at",
        None
    )

    session.pop(
        "otp_expires_at",
        None
    )

    print(
        f"Login successful for: {email}"
    )

    return jsonify({
        "status": "success",
        "message": "Login successful!",
        "redirect": url_for("home")
    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.pop(
        "user_id",
        None
    )

    session.pop(
        "user_name",
        None
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("home")
        )

    user = User.query.get(
        session["user_id"]
    )

    if user is None:

        session.pop(
            "user_id",
            None
        )

        session.pop(
            "user_name",
            None
        )

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        user.name = request.form[
            "first_name"
        ]

        user.last_name = request.form[
            "last_name"
        ]

        user.phone = request.form[
            "phone"
        ]

        user.gender = request.form.get(
            "gender",
            ""
        )

        user.address = request.form[
            "address"
        ]

        db.session.commit()

        session["user_name"] = user.name

        return redirect(
            url_for("profile")
        )

    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/my_orders")
def my_orders():

    if "user_id" not in session:

        return redirect(
            url_for("home")
        )

    user = User.query.get(
        session["user_id"]
    )

    if user is None:

        session.pop(
            "user_id",
            None
        )

        session.pop(
            "user_name",
            None
        )

        return redirect(
            url_for("home")
        )

    user_orders = (
        Order.query
        .filter_by(
            customer_name=user.name
        )
        .order_by(
            Order.date.desc()
        )
        .all()
    )

    return render_template(
        "my_orders.html",
        orders=user_orders,
        user=user
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        products=Product.query.all()
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route(
    "/product/<int:id>"
)
def product_detail(id):

    return render_template(
        "product.html",
        product=Product.query.get_or_404(id)
    )


# =========================================================
# PLACE ORDER
# =========================================================

@app.route(
    "/api/place_order",
    methods=["POST"]
)
def place_order():

    data = request.get_json(
        silent=True
    ) or {}

    db.session.add(
        Order(
            customer_name=data["name"],
            phone=data["phone"],
            address=data["address"],
            cart_details=data["cart_details"],
            total_amount=data["total"]
        )
    )

    db.session.commit()

    return jsonify({
        "status": "success"
    })


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin_login",
    methods=["GET", "POST"]
)
def admin_login():

    error = None

    if request.method == "POST":

        if (
            request.form["username"] == "admin"
            and
            request.form["password"] == "admin123"
        ):

            session[
                "admin_logged_in"
            ] = True

            return redirect(
                url_for("admin_dashboard")
            )

        else:

            error = (
                "Invalid Username or Password!"
            )

    return render_template(
        "admin_login.html",
        error=error
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin_logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    all_products = Product.query.all()

    all_orders = (
        Order.query
        .order_by(
            Order.date.desc()
        )
        .all()
    )

    total_users = User.query.count()

    total_revenue = sum(
        o.total_amount
        for o in all_orders
        if o.status != "Cancelled"
    )

    return render_template(
        "admin.html",
        products=all_products,
        orders=all_orders,
        total_revenue=total_revenue,
        total_orders=len(all_orders),
        total_users=total_users
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route(
    "/add",
    methods=["GET", "POST"]
)
def add_product():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":

        img1 = save_image(
            request.files.get("image1")
        )

        img2 = save_image(
            request.files.get("image2")
        )

        img3 = save_image(
            request.files.get("image3")
        )

        img4 = save_image(
            request.files.get("image4")
        )

        new_prod = Product(

            name=request.form["name"],

            price=request.form["price"],

            old_price=request.form["old_price"],

            description=request.form[
                "description"
            ],

            category=request.form[
                "category"
            ],

            stock=request.form[
                "stock"
            ],

            image=img1,

            image2=img2,

            image3=img3,

            image4=img4
        )

        db.session.add(
            new_prod
        )

        db.session.commit()

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "add.html"
    )


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route(
    "/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_product(id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    p = Product.query.get_or_404(id)

    if request.method == "POST":

        p.name = request.form[
            "name"
        ]

        p.price = request.form[
            "price"
        ]

        p.old_price = request.form[
            "old_price"
        ]

        p.description = request.form[
            "description"
        ]

        p.category = request.form[
            "category"
        ]

        p.stock = request.form[
            "stock"
        ]

        img1 = save_image(
            request.files.get("image1")
        )

        if img1:
            p.image = img1

        img2 = save_image(
            request.files.get("image2")
        )

        if img2:
            p.image2 = img2

        img3 = save_image(
            request.files.get("image3")
        )

        if img3:
            p.image3 = img3

        img4 = save_image(
            request.files.get("image4")
        )

        if img4:
            p.image4 = img4

        db.session.commit()

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "edit.html",
        p=p
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route(
    "/delete/<int:id>"
)
def delete_product(id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    product = Product.query.get_or_404(
        id
    )

    db.session.delete(
        product
    )

    db.session.commit()

    return redirect(
        url_for("admin_dashboard")
    )


# =========================================================
# UPDATE ORDER
# =========================================================

@app.route(
    "/update_order/<int:id>",
    methods=["POST"]
)
def update_order(id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    order = Order.query.get_or_404(
        id
    )

    order.status = request.form[
        "status"
    ]

    db.session.commit()

    return redirect(
        url_for("admin_dashboard")
    )


# =========================================================
# DELETE ORDER
# =========================================================

@app.route(
    "/delete_order/<int:id>"
)
def delete_order(id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )

    order = Order.query.get_or_404(
        id
    )

    db.session.delete(
        order
    )

    db.session.commit()

    return redirect(
        url_for("admin_dashboard")
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
