import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-local-development")

def db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "food_donation_portal")
    )

def query(sql, params=(), fetch=False, commit=False):
    conn = db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        result = cur.fetchall() if fetch else None
        if commit:
            conn.commit()
        return result
    finally:
        cur.close()
        conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco

@app.context_processor
def inject_now():
    return {"current_year": datetime.now().year}

@app.route("/")
def index():
    donations = query("""SELECT d.*, u.name AS donor_name FROM donations d
                         JOIN users u ON u.id=d.donor_id
                         WHERE d.status='Available' AND d.safe_until > NOW()
                         ORDER BY d.created_at DESC LIMIT 6""", fetch=True)
    stats = {
        "available": query("SELECT COUNT(*) AS n FROM donations WHERE status='Available' AND safe_until > NOW()", fetch=True)[0]["n"],
        "completed": query("SELECT COUNT(*) AS n FROM deliveries WHERE status='Delivered'", fetch=True)[0]["n"],
        "donated": query("SELECT COALESCE(SUM(quantity),0) AS n FROM donations WHERE status IN ('Claimed','Picked up','Delivered')", fetch=True)[0]["n"]
    }
    return render_template("index.html", donations=donations, stats=stats)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "")
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8 or role not in ("Donor", "NGO", "Volunteer"):
            flash("Fill all fields. Password must be at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            query("INSERT INTO users(name,email,phone,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                  (name, email, phone, generate_password_hash(password), role), commit=True)
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))
        except Error:
            flash("Could not create account. The email may already be registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        users = query("SELECT * FROM users WHERE email=%s", (email,), fetch=True)
        if users and check_password_hash(users[0]["password_hash"], password):
            user = users[0]
            if user["role"] in ("NGO", "Volunteer") and not user["verified"]:
                flash("Your organization/account is awaiting admin verification.", "warning")
                return render_template("login.html")
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    if role == "Admin":
        donations = query("""SELECT d.*, u.name AS donor_name FROM donations d JOIN users u ON u.id=d.donor_id
                             ORDER BY d.created_at DESC""", fetch=True)
        users = query("SELECT id,name,email,role,verified FROM users ORDER BY created_at DESC", fetch=True)
        requests_list = query("""SELECT r.*, d.food_name, u.name AS ngo_name FROM donation_requests r
                                 JOIN donations d ON d.id=r.donation_id JOIN users u ON u.id=r.ngo_id
                                 ORDER BY r.created_at DESC""", fetch=True)
        return render_template("dashboard.html", role=role, donations=donations, users=users, requests_list=requests_list)
    if role == "Donor":
        donations = query("SELECT * FROM donations WHERE donor_id=%s ORDER BY created_at DESC", (session["user_id"],), fetch=True)
        requests_list = query("""SELECT r.*, d.food_name, u.name AS ngo_name FROM donation_requests r
                                 JOIN donations d ON d.id=r.donation_id JOIN users u ON u.id=r.ngo_id
                                 WHERE d.donor_id=%s ORDER BY r.created_at DESC""", (session["user_id"],), fetch=True)
    elif role == "NGO":
        donations = query("""SELECT d.*, u.name AS donor_name FROM donations d JOIN users u ON u.id=d.donor_id
                             WHERE d.status='Available' AND d.safe_until > NOW() ORDER BY d.safe_until""", fetch=True)
        requests_list = query("""SELECT r.*, d.food_name FROM donation_requests r JOIN donations d ON d.id=r.donation_id
                                 WHERE r.ngo_id=%s ORDER BY r.created_at DESC""", (session["user_id"],), fetch=True)
    else:
        donations = query("""SELECT d.*, u.name AS donor_name FROM donations d JOIN users u ON u.id=d.donor_id
                             WHERE d.status IN ('Claimed','Picked up') ORDER BY d.safe_until""", fetch=True)
        requests_list = query("""SELECT r.*, d.food_name, u.name AS ngo_name FROM donation_requests r
                                 JOIN donations d ON d.id=r.donation_id JOIN users u ON u.id=r.ngo_id
                                 WHERE r.status='Approved' ORDER BY r.created_at DESC""", fetch=True)
    return render_template("dashboard.html", role=role, donations=donations, requests_list=requests_list, users=[], )

@app.route("/donations/new", methods=["GET", "POST"])
@roles_required("Donor")
def new_donation():
    if request.method == "POST":
        food_name = request.form.get("food_name", "").strip()
        category = request.form.get("category", "")
        quantity = request.form.get("quantity", type=float)
        unit = request.form.get("unit", "servings")
        location = request.form.get("location", "").strip()
        prepared = request.form.get("prepared_at", "")
        safe_until = request.form.get("safe_until", "")
        notes = request.form.get("notes", "").strip()
        if not food_name or category not in ("Cooked meal", "Packaged", "Produce", "Bakery", "Other") or not quantity or quantity <= 0 or not location or not prepared or not safe_until:
            flash("Complete all required fields with a positive quantity.", "danger")
            return render_template("new_donation.html")
        try:
            prep_dt = datetime.fromisoformat(prepared)
            safe_dt = datetime.fromisoformat(safe_until)
            if safe_dt <= datetime.now() or safe_dt <= prep_dt:
                flash("The safe-consumption deadline must be in the future and after preparation time.", "danger")
                return render_template("new_donation.html")
            if prep_dt > datetime.now():
                flash("Preparation time cannot be in the future.", "danger")
                return render_template("new_donation.html")
            query("""INSERT INTO donations(donor_id,food_name,category,quantity,unit,location,prepared_at,safe_until,notes,status)
                     VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'Available')""",
                  (session["user_id"], food_name, category, quantity, unit, location, prep_dt, safe_dt, notes), commit=True)
            flash("Donation posted. Please keep food covered and at a safe temperature.", "success")
            return redirect(url_for("dashboard"))
        except ValueError:
            flash("Enter valid preparation and deadline times.", "danger")
    return render_template("new_donation.html")

@app.route("/donations")
def donations():
    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()
    sql = """SELECT d.*, u.name AS donor_name FROM donations d JOIN users u ON u.id=d.donor_id
             WHERE d.status='Available' AND d.safe_until > NOW()"""
    params = []
    if category:
        sql += " AND d.category=%s"
        params.append(category)
    if search:
        sql += " AND (d.food_name LIKE %s OR d.location LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    sql += " ORDER BY d.safe_until ASC"
    items = query(sql, tuple(params), fetch=True)
    return render_template("donations.html", donations=items)

@app.route("/donations/<int:donation_id>/request", methods=["POST"])
@roles_required("NGO")
def request_donation(donation_id):
    rows = query("SELECT * FROM donations WHERE id=%s AND status='Available' AND safe_until>NOW()", (donation_id,), fetch=True)
    if not rows:
        flash("This donation is no longer available or its safe deadline has passed.", "warning")
        return redirect(url_for("donations"))
    try:
        query("INSERT INTO donation_requests(donation_id,ngo_id,requested_quantity,status) VALUES(%s,%s,%s,'Pending')",
              (donation_id, session["user_id"], rows[0]["quantity"]), commit=True)
        flash("Request sent to the donor.", "success")
    except Error:
        flash("You may already have requested this donation.", "warning")
    return redirect(url_for("dashboard"))

@app.route("/requests/<int:request_id>/<action>", methods=["POST"])
@login_required
def update_request(request_id, action):
    reqs = query("""SELECT r.*, d.donor_id, d.status AS donation_status, d.safe_until FROM donation_requests r
                    JOIN donations d ON d.id=r.donation_id WHERE r.id=%s""", (request_id,), fetch=True)
    if not reqs:
        abort(404)
    r = reqs[0]
    is_admin = session["role"] == "Admin"
    is_donor = session["role"] == "Donor" and r["donor_id"] == session["user_id"]
    if action in ("approve", "reject") and (is_admin or is_donor):
        if action == "approve":
            if r["donation_status"] != "Available" or r["safe_until"] <= datetime.now():
                flash("Expired or unavailable food cannot be approved.", "danger")
                return redirect(url_for("dashboard"))
            query("UPDATE donation_requests SET status='Rejected' WHERE donation_id=%s AND id<>%s AND status='Pending'",
                  (r["donation_id"], request_id), commit=True)
            query("UPDATE donation_requests SET status='Approved' WHERE id=%s", (request_id,), commit=True)
            query("UPDATE donations SET status='Claimed' WHERE id=%s", (r["donation_id"],), commit=True)
            query("INSERT INTO deliveries(request_id,status) VALUES(%s,'Assigned')", (request_id,), commit=True)
            flash("Request approved. Food is now marked as claimed.", "success")
        else:
            query("UPDATE donation_requests SET status='Rejected' WHERE id=%s", (request_id,), commit=True)
            flash("Request rejected.", "info")
    elif action in ("pickup", "deliver") and (session["role"] == "Volunteer" or is_admin):
        if r["safe_until"] <= datetime.now():
            flash("Deadline passed. Do not distribute this food.", "danger")
            return redirect(url_for("dashboard"))
        new_status = "Picked up" if action == "pickup" else "Delivered"
        query("UPDATE deliveries SET status=%s, volunteer_id=%s WHERE request_id=%s",
              (new_status, session["user_id"], request_id), commit=True)
        query("UPDATE donations SET status=%s WHERE id=(SELECT donation_id FROM donation_requests WHERE id=%s)",
              (new_status, request_id), commit=True)
        if action == "deliver":
            query("UPDATE donation_requests SET status='Completed' WHERE id=%s", (request_id,), commit=True)
        flash("Delivery status updated.", "success")
    else:
        abort(403)
    return redirect(url_for("dashboard"))

@app.route("/admin/verify/<int:user_id>", methods=["POST"])
@roles_required("Admin")
def verify_user(user_id):
    query("UPDATE users SET verified=1 WHERE id=%s AND role IN ('NGO','Volunteer')", (user_id,), commit=True)
    flash("Account verified.", "success")
    return redirect(url_for("dashboard"))

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page or record could not be found."), 404

if __name__ == "__main__":
    app.run(debug=True)
