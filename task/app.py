from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer
from random import randint
from twilio.rest import Client
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:root@localhost/newdb"
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]
        password = request.form["password"]
        id = "ANFA" + str(randint(100, 999))
        user = User(id=id, name=name, email=email, phone_number=phone_number, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please verify your email and phone number.")
        return redirect(url_for("verify_email", id=id))
    return render_template("register.html")

@app.route("/verify_email/<id>")
def verify_email(id):
    user = User.query.get(id)
    if user:
        token = generate_token(user.email)
        flash("Email verification link sent to your email. Please verify your email.")
        return render_template("verify_email.html", token=token)
    return "User not found", 404

@app.route("/verify_email/<token>")
def verify_email_token(token):
    email = confirm_token(token)
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            user.email_verified = True
            db.session.commit()
            flash("Email verified successfully!")
            return redirect(url_for("verify_phone", id=user.id))
    return "Invalid token", 404
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
client = Client(account_sid, auth_token)

@app.route("/verify_phone/<id>")
def verify_phone(id):
    user = User.query.get(id)
    if user:
        otp = randint(100000, 999999)
        phone_number = request.form.get('phone_number')
        # Generate a random OTP

    message = client.messages.create(
        body=f'Your OTP is {otp}',
        from_='your_twilio_phone_number',
        to=phone_number
    )

    if message.sid:
        return jsonify({'message': 'OTP sent successfully'})
    else:
        return jsonify({'message': 'Failed to send OTP'})

        # Send OTP to user's phone number
        flash("Phone verification OTP sent to your phone number. Please enter the OTP.")
        return render_template("verify_phone.html", id=id, otp=otp)
    return "User not found", 404

@app.route("/verify_phone/<id>", methods=["POST"])
def verify_phone_post(id):
    user = User.query.get(id)
    if user:
        otp = request.form["otp"]
        if otp == user.phone_number:  # Replace with actual OTP verification
            user.phone_verified = True
            db.session.commit()
            flash("Phone number verified successfully!")
            return redirect(url_for("login"))
    return "Invalid OTP", 404

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        id = request.form["id"]
        password = request.form["password"]
        user = User.query.get(id)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirmation")

def confirm_token(token):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="email-confirmation", max_age=3600)
        return email
    except:
        return False

if __name__ == "__main__":
    app.run(debug=True)