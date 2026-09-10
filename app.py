from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import pymysql
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import tempfile
import os
from functools import wraps

load_dotenv()

IS_VERCEL = os.getenv("VERCEL", "0") == "1" or os.getenv("VERCEL_ENV") is not None
if IS_VERCEL:
    SQLITE_DB_PATH = os.path.join(tempfile.gettempdir(), "bloodfinder.db")
else:
    SQLITE_DB_PATH = "bloodfinder.db"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "bloodnet_super_secret_key_2026_safe")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "t")
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "")

mail = Mail(app)

CITY_COORDINATES = {
    "NASHIK": {"lat": 20.0059, "lng": 73.7898},
    "MUMBAI": {"lat": 19.0760, "lng": 72.8777},
    "PUNE": {"lat": 18.5204, "lng": 73.8567},
    "DELHI": {"lat": 28.6139, "lng": 77.2090},
    "BANGALORE": {"lat": 12.9716, "lng": 77.5946},
    "HYDERABAD": {"lat": 17.3850, "lng": 78.4867},
    "CHENNAI": {"lat": 13.0827, "lng": 80.2707},
    "KOLKATA": {"lat": 22.5726, "lng": 88.3639}
}

# SQLite Fallback Classes & Helpers
class SQLiteDictCursor:
    def __init__(self, conn):
        self.conn = conn
        self.cur = conn.cursor()
    def execute(self, query, params=()):
        query = query.replace('%s', '?').replace('current_timestamp()', 'CURRENT_TIMESTAMP')
        self.cur.execute(query, params)
        return self
    def fetchone(self):
        row = self.cur.fetchone()
        return dict(row) if row else None
    def fetchall(self):
        rows = self.cur.fetchall()
        return [dict(r) for r in rows]
    def close(self):
        self.cur.close()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class SQLiteConnectionWrapper:
    def __init__(self, db_path=None):
        target_path = db_path or SQLITE_DB_PATH
        self.conn = sqlite3.connect(target_path)
        self.conn.row_factory = sqlite3.Row

    def cursor(self):
        return SQLiteDictCursor(self.conn)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.close()

def init_sqlite_db(db_path=None):
    target_path = db_path or SQLITE_DB_PATH
    conn = sqlite3.connect(target_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        location TEXT NOT NULL,
        contact TEXT NOT NULL,
        verified INTEGER DEFAULT 0
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS blood_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requester_name TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        location TEXT NOT NULL,
        contact TEXT NOT NULL,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved INTEGER DEFAULT 0
    )""")
    
    # Seed default accounts if empty
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        pw_12345678 = generate_password_hash("12345678")
        admin_pw = generate_password_hash("admin")
        cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", admin_pw))
        cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin@admin", admin_pw))
        cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("hamizkhan@ggsf.edu.in", pw_12345678))
        
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        pw = generate_password_hash("12345678")
        sample_users = [
            ("Hamiz Khan", "hamizkhan@ggsf.edu.in", pw, "A+", "Nashik", "9876501234", 1),
            ("Rajesh Sharma", "rajesh.sharma@example.com", pw, "O+", "Mumbai", "9820012345", 1),
            ("Priya Patel", "priya.patel@example.com", pw, "B+", "Pune", "9890023456", 1),
            ("Amit Verma", "amit.verma@example.com", pw, "A-", "Delhi", "9811034567", 1),
            ("Sneha Reddy", "sneha.reddy@example.com", pw, "O-", "Bangalore", "9845045678", 1),
            ("Vikram Singh", "vikram.singh@example.com", pw, "AB+", "Hyderabad", "9849056789", 1),
            ("Ananya Sen", "ananya.sen@example.com", pw, "B-", "Kolkata", "9830067890", 1),
            ("Karthik Nair", "karthik.nair@example.com", pw, "A+", "Chennai", "9840078901", 1),
            ("Suresh Joshi", "suresh.joshi@example.com", pw, "O+", "Nashik", "9822089012", 1),
            ("Meera Deshmukh", "meera.d@example.com", pw, "AB-", "Pune", "9823090123", 1),
            ("Rohan Gupta", "rohan.g@example.com", pw, "B+", "Mumbai", "9820091234", 1),
            ("Pooja Kapoor", "pooja.k@example.com", pw, "A+", "Delhi", "9810092345", 1),
            ("Rahul Kumar", "rahul.k@example.com", pw, "O+", "Bangalore", "9845093456", 1),
            ("Kavita Roy", "kavita.r@example.com", pw, "A-", "Kolkata", "9830094567", 1),
            ("Manish Tiwari", "manish.t@example.com", pw, "B+", "Nashik", "9822095678", 0),
            ("Divya Shah", "divya.s@example.com", pw, "O-", "Mumbai", "9820096789", 0),
            ("Arjun Mehta", "arjun.m@example.com", pw, "AB+", "Pune", "9890097890", 0)
        ]
        cur.executemany(
            "INSERT INTO users (name, email, password, blood_group, location, contact, verified) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_users
        )

    cur.execute("SELECT COUNT(*) FROM blood_requests")
    if cur.fetchone()[0] == 0:
        sample_requests = [
            ("Ramesh Shinde", "O+", "Nashik City Hospital, Nashik", "9876543210", "Urgent O+ required for bypass surgery", 0),
            ("Sunita Patil", "A+", "Ruby Hall Clinic, Pune", "9823011223", "Emergency ICU blood transfusion request", 0),
            ("Mohammad Ali", "B+", "Lilavati Hospital, Mumbai", "9819055443", "Accident trauma recovery requirement", 1),
            ("Anita Sharma", "O-", "AIIMS, Delhi", "9910022334", "Universal donor needed urgently for surgery", 1),
            ("Deepak Kumar", "AB+", "Apollo Hospital, Bangalore", "9740011223", "Platelet & plasma transfusion request", 0)
        ]
        cur.executemany(
            "INSERT INTO blood_requests (requester_name, blood_group, location, contact, message, approved) VALUES (?, ?, ?, ?, ?, ?)",
            sample_requests
        )

    conn.commit()
    conn.close()

# Database Connection Router (MySQL with automatic SQLite Fallback)
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            db=os.getenv("DB_NAME", "bloodfinder"),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=2
        )
        return conn
    except Exception:
        init_sqlite_db(SQLITE_DB_PATH)
        return SQLiteConnectionWrapper(SQLITE_DB_PATH)

# Access Control Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session and "admin_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Admin authorization required.", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# Blood Compatibility Rules
VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

COMPATIBLE_DONORS = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
    "AB-": ["AB+", "AB-", "A-", "B-", "O-"],
    "O+": ["O+", "O-"],
    "O-": ["O-"]
}

def get_compatible_donor_groups(blood_group):
    bg = blood_group.strip().upper() if blood_group else ""
    return COMPATIBLE_DONORS.get(bg, [bg] if bg else [])

def get_request_by_id(req_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM blood_requests WHERE id=%s", (req_id,))
            return cur.fetchone()
    finally:
        conn.close()

def send_email_alert(to_email, subject, body):
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print(f"Simulation Mode: Email would be sent to {to_email} with subject '{subject}'")
        return
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to_email])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

# ---------------- USER HOME ----------------
@app.route('/')
def home():
    if "user_id" in session:
        # Fetch stats for home counters
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM users WHERE verified=1")
                total_donors = cur.fetchone()['cnt']
                cur.execute("SELECT COUNT(*) as cnt FROM blood_requests")
                total_requests = cur.fetchone()['cnt']
                cur.execute("SELECT COUNT(DISTINCT location) as cnt FROM users WHERE verified=1")
                cities_count = cur.fetchone()['cnt']
        finally:
            conn.close()
        return render_template(
            "home.html",
            name=session.get("name", "User"),
            total_donors=total_donors,
            total_requests=total_requests,
            cities_count=cities_count
        )
    elif "admin_id" in session:
        return redirect("/admin/dashboard")
    return redirect("/login")

# ---------- REGISTER ----------
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password_raw = request.form.get("password", "")
        blood_group = request.form.get("blood_group", "").strip().upper()
        location = request.form.get("location", "").strip()
        contact = request.form.get("contact", "").strip()

        if not name or not email or not password_raw or not blood_group:
            flash("Please fill in all required fields.", "warning")
            return render_template("register.html", valid_blood_groups=VALID_BLOOD_GROUPS)

        password = generate_password_hash(password_raw)
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, email, password, blood_group, location, contact) VALUES (%s,%s,%s,%s,%s,%s)",
                    (name, email, password, blood_group, location, contact)
                )
            conn.commit()
            flash("Registration successful! Please login after an admin verifies your profile.", "success")
            return redirect("/login")
        except Exception as e:
            if "UNIQUE" in str(e).upper() or "DUPLICATE" in str(e).upper() or "INTEGRITY" in str(e).upper():
                flash("An account with this email already exists.", "danger")
            else:
                flash("An unexpected error occurred during registration. Please try again.", "danger")
        finally:
            conn.close()
    return render_template("register.html", valid_blood_groups=VALID_BLOOD_GROUPS)

# ---------- LOGIN ----------
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email=%s", (email,))
                user = cur.fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html")

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/login")

# ---------- SEARCH DONORS ----------
@app.route('/search', methods=["GET", "POST"])
@login_required
def search():
    donors = None
    selected_group = ""
    location_query = ""

    if request.method == "POST":
        selected_group = request.form.get("blood_group", "").strip().upper()
        location_query = request.form.get("location", "").strip()

    compatible_groups = get_compatible_donor_groups(selected_group) if selected_group else []

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if compatible_groups:
                format_strings = ','.join(['%s'] * len(compatible_groups))
                query = f"""
                    SELECT name, blood_group, location, contact, email, verified 
                    FROM users 
                    WHERE verified=1 AND blood_group IN ({format_strings}) AND location LIKE %s
                """
                params = tuple(compatible_groups) + (f"%{location_query}%",)
                cur.execute(query, params)
            else:
                query = "SELECT name, blood_group, location, contact, email, verified FROM users WHERE verified=1 AND location LIKE %s"
                cur.execute(query, (f"%{location_query}%",))
            donors = cur.fetchall()
    finally:
        conn.close()

    return render_template("search.html", donors=donors, valid_blood_groups=VALID_BLOOD_GROUPS, selected_group=selected_group, location_query=location_query)

# ---------- REQUEST BLOOD ----------
@app.route('/request_blood', methods=["GET", "POST"])
@login_required
def request_blood():
    if request.method == "POST":
        requester_name = request.form.get("name", "").strip()
        blood_group = request.form.get("blood_group", "").strip().upper()
        location = request.form.get("location", "").strip()
        contact = request.form.get("contact", "").strip()
        message = request.form.get("message", "").strip()

        if not requester_name or not blood_group or not location or not contact:
            flash("Please fill in all required fields.", "warning")
            return render_template("request_blood.html", valid_blood_groups=VALID_BLOOD_GROUPS)

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO blood_requests (requester_name, blood_group, location, contact, message) VALUES (%s,%s,%s,%s,%s)",
                    (requester_name, blood_group, location, contact, message)
                )
            conn.commit()
            flash("Blood request submitted successfully! Admin will review your request.", "success")
            return redirect("/")
        except Exception:
            flash("Failed to submit blood request. Please try again.", "danger")
        finally:
            conn.close()

    return render_template("request_blood.html", valid_blood_groups=VALID_BLOOD_GROUPS)

# ---------- MY REQUESTS ----------
@app.route('/my_requests')
@login_required
def my_requests():
    user_name = session.get("name", "")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM blood_requests WHERE requester_name=%s ORDER BY created_at DESC", (user_name,))
            user_requests = cur.fetchall()
    finally:
        conn.close()
    return render_template("my_requests.html", requests=user_requests)

# ---------- ADMIN LOGIN ----------
@app.route('/admin/login', methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM admins WHERE username=%s", (username,))
                admin_user = cur.fetchone()
        finally:
            conn.close()

        if admin_user:
            authenticated = False
            db_pw = admin_user["password"]
            if db_pw.startswith("scrypt:") or db_pw.startswith("pbkdf2:"):
                authenticated = check_password_hash(db_pw, password)
            elif db_pw == password:
                authenticated = True
                new_hash = generate_password_hash(password)
                conn = get_db_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE admins SET password=%s WHERE id=%s", (new_hash, admin_user["id"]))
                    conn.commit()
                finally:
                    conn.close()

            if authenticated:
                session["admin_id"] = admin_user["id"]
                session["admin_name"] = admin_user["username"]
                flash("Admin login successful!", "success")
                return redirect("/admin/dashboard")

        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")

# ---------- ADMIN DASHBOARD ----------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE verified=0")
            pending_donors = cur.fetchall()

            cur.execute("SELECT * FROM users WHERE verified=1")
            verified_donors = cur.fetchall()

            cur.execute("SELECT * FROM blood_requests WHERE approved=0")
            pending_requests = cur.fetchall()

            cur.execute("SELECT * FROM blood_requests WHERE approved=1")
            approved_requests = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "admin_dashboard.html",
        donors=pending_donors,
        verified_donors=verified_donors,
        pending_requests=pending_requests,
        approved_requests=approved_requests
    )

# ---------- ADMIN ANALYTICS APIs ----------
@app.route('/api/admin/stats')
@admin_required
def admin_stats_api():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Blood group distribution among verified donors
            cur.execute("SELECT blood_group, COUNT(*) as count FROM users WHERE verified=1 GROUP BY blood_group")
            bg_data = {row['blood_group']: row['count'] for row in cur.fetchall()}
            
            # City distribution
            cur.execute("SELECT location, COUNT(*) as count FROM users WHERE verified=1 GROUP BY location")
            city_data = {row['location']: row['count'] for row in cur.fetchall()}

            # Requests status
            cur.execute("SELECT approved, COUNT(*) as count FROM blood_requests GROUP BY approved")
            req_data = {('Approved' if row['approved']==1 else 'Pending'): row['count'] for row in cur.fetchall()}
    finally:
        conn.close()

    full_bg = {bg: bg_data.get(bg, 0) for bg in VALID_BLOOD_GROUPS}

    return jsonify({
        "blood_groups": full_bg,
        "cities": city_data,
        "requests": req_data
    })

@app.route('/api/admin/geo_data')
@admin_required
def admin_geo_api():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name, blood_group, location, contact FROM users WHERE verified=1")
            donors = cur.fetchall()
    finally:
        conn.close()

    geo_points = []
    for d in donors:
        city_key = d['location'].strip().upper()
        # Find matching key in CITY_COORDINATES
        coords = None
        for k in CITY_COORDINATES:
            if k in city_key or city_key in k:
                coords = CITY_COORDINATES[k]
                break
        if not coords:
            coords = {"lat": 19.0760, "lng": 72.8777} # Default to Mumbai area

        geo_points.append({
            "name": d['name'],
            "blood_group": d['blood_group'],
            "location": d['location'],
            "contact": d['contact'],
            "lat": coords['lat'],
            "lng": coords['lng']
        })

    return jsonify(geo_points)

# ---------- VERIFY DONOR ----------
@app.route('/admin/verify_donor/<int:user_id>')
@admin_required
def verify_donor(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET verified=1 WHERE id=%s", (user_id,))
        conn.commit()
        flash("Donor verified successfully!", "success")
    finally:
        conn.close()
    return redirect("/admin/dashboard")

# ---------- APPROVE BLOOD REQUEST ----------
@app.route('/admin/approve_request/<int:request_id>')
@admin_required
def approve_request(request_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE blood_requests SET approved=1 WHERE id=%s", (request_id,))
        conn.commit()
        flash("Blood request approved successfully!", "success")
    finally:
        conn.close()
    return redirect("/admin/dashboard")

# ---------- REJECT BLOOD REQUEST ----------
@app.route('/admin/reject_request/<int:request_id>')
@admin_required
def reject_request(request_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM blood_requests WHERE id=%s", (request_id,))
        conn.commit()
        flash("Blood request rejected and removed.", "info")
    finally:
        conn.close()
    return redirect("/admin/dashboard")

# ---------- SEND ALERT ----------
@app.route("/send_alert/<int:req_id>")
@admin_required
def send_alert(req_id):
    req = get_request_by_id(req_id)
    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    subject = f"EMERGENCY: {req['blood_group']} Blood Needed!"
    body = f"""
Urgent request for {req['blood_group']} blood.
Patient: {req['requester_name']}
Location: {req['location']}
Contact: {req['contact']}
Message: {req['message']}
"""

    compatible_groups = get_compatible_donor_groups(req['blood_group'])

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if compatible_groups:
                format_strings = ','.join(['%s'] * len(compatible_groups))
                cur.execute(
                    f"SELECT email FROM users WHERE verified=1 AND blood_group IN ({format_strings})",
                    tuple(compatible_groups)
                )
            else:
                cur.execute("SELECT email FROM users WHERE verified=1")
            donors = cur.fetchall()
    finally:
        conn.close()

    if not donors:
        flash("No verified donors with compatible blood group found!", "warning")
        return redirect(url_for("admin_dashboard"))

    for donor in donors:
        email = donor.get('email')
        if email:
            send_email_alert(email.strip(), subject, body)

    flash(f"Emergency email alert sent to {len(donors)} verified donor(s)!", "success")
    return redirect(url_for("admin_dashboard"))

# ---------- RECOMMEND DONORS ----------
def recommend_donors_local(request_id, top_n=5):
    req = get_request_by_id(request_id)
    if not req:
        return []

    compatible_groups = get_compatible_donor_groups(req['blood_group'])

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if compatible_groups:
                format_strings = ','.join(['%s'] * len(compatible_groups))
                query = f"""
                    SELECT id, name, email, blood_group, location
                    FROM users
                    WHERE verified=1 AND blood_group IN ({format_strings})
                    ORDER BY CASE WHEN LOWER(location) LIKE LOWER(%s) THEN 1 ELSE 2 END
                    LIMIT %s
                """
                params = tuple(compatible_groups) + (f"%{req['location']}%", top_n)
                cur.execute(query, params)
            else:
                query = """
                    SELECT id, name, email, blood_group, location
                    FROM users
                    WHERE verified=1
                    ORDER BY CASE WHEN LOWER(location) LIKE LOWER(%s) THEN 1 ELSE 2 END
                    LIMIT %s
                """
                cur.execute(query, (f"%{req['location']}%", top_n))
            return cur.fetchall()
    finally:
        conn.close()

@app.route("/recommend_donors/<int:req_id>")
@admin_required
def recommend_donors(req_id):
    recommendations = recommend_donors_local(req_id)
    if not recommendations:
        flash("No suitable verified donors found for this request.", "warning")
    return render_template("recommendations.html", recommendations=recommendations, req_id=req_id)

# ---------- SEND EMAIL TO INDIVIDUAL DONOR ----------
@app.route("/send_email_to_donor/<int:req_id>/<int:donor_id>")
@admin_required
def send_email_to_donor(req_id, donor_id):
    req = get_request_by_id(req_id)
    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for("recommend_donors", req_id=req_id))

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s AND verified=1", (donor_id,))
            donor = cur.fetchone()
    finally:
        conn.close()

    if not donor:
        flash("Donor not found or not verified.", "warning")
        return redirect(url_for("recommend_donors", req_id=req_id))

    subject = f"Urgent Blood Request: {req['blood_group']} Needed!"
    body = f"""
Hello {donor['name']},

There is an urgent blood request matching your blood group.

Patient: {req['requester_name']}
Blood Group: {req['blood_group']}
Location: {req['location']}
Contact: {req['contact']}
Message: {req['message']}

Please reach out if you can donate.
"""

    send_email_alert(donor['email'], subject, body)
    flash(f"Email sent to {donor['name']}!", "success")
    return redirect(url_for("recommend_donors", req_id=req_id))


if __name__ == "__main__":
    app.run(debug=True)