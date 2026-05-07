import os
from flask import Flask, render_template, request, redirect, url_for, Response, session, jsonify, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, validators, HiddenField
from werkzeug.security import generate_password_hash, check_password_hash
from database import *
from dotenv import load_dotenv
import time
import re
from datetime import datetime


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

app.config['PREFERRED_URL_SCHEME'] = 'https'

csrf = CSRFProtect(app)

# Session security
app.config['SESSION_COOKIE_HTTPONLY'] = True
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Brute force protection
login_attempts = {}

class LoginForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired(), validators.Length(min=3, max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=6)])
    # csrf_token = HiddenField()  # Temporarily disabled

@app.route("/admin")
def admin_redirect():
    return redirect("/bhakti-secure-admin-portal-84729/login")

@app.before_request
def initialize_database():
    if not hasattr(app, 'db_initialized'):
        init()
        app.db_initialized = True

@app.route("/db-test")
def db_test():
    conn = get_db_connection()

    if conn:
        conn.close()
        return "DB CONNECTED"

    return "DB FAILED"

@app.route("/bhakti-secure-admin-portal-84729/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Basic validation
        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("admin_login.html")

        # Brute force protection
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        current_time = time.time()

        if client_ip in login_attempts:
            attempts, last_attempt = login_attempts[client_ip]
            if attempts >= 5 and current_time - last_attempt < 300:  # 5 min lockout
                flash("Too many failed attempts. Try again later.", "error")
                return render_template("admin_login.html")

        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed. Please try again later.", "error")
            return render_template("admin_login.html")

        try:
            cursor = conn.cursor(buffered=True)
            placeholder = get_param_style(conn)

            cursor.execute(
                f"SELECT password FROM admin WHERE username = {placeholder}",
                (username,)
            )

            result = cursor.fetchone()
            conn.close()

            if result and check_password_hash(result[0], password):
                session["admin"] = username
                # Reset attempts on success
                if client_ip in login_attempts:
                    del login_attempts[client_ip]
                return redirect("/bhakti-secure-admin-portal-84729/dashboard")
            else:
                # Increment attempts
                if client_ip not in login_attempts:
                    login_attempts[client_ip] = [0, current_time]
                login_attempts[client_ip][0] += 1
                login_attempts[client_ip][1] = current_time
                flash("Invalid username or password", "error")

        except Exception as e:
            print(f"Database error: {e}")
            flash("An error occurred. Please try again.", "error")

    return render_template("admin_login.html")

@app.route("/bhakti-secure-admin-portal-84729/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")

    conn = get_db_connection()
    if conn is None:
    
        return render_template("admin_dashboard.html",
                             bookings=[],
                             total_bookings=0,
                             pending_bookings=0,
                             confirmed_bookings=0,
                             completed_bookings=0,
                             db_status="Database not connected")

    try:
        cursor = conn.cursor(buffered=True)

     
        cursor.execute("SELECT COUNT(*) FROM bookings")
        total_bookings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Pending'")
        pending_bookings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'")
        confirmed_bookings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status='Completed'")
        completed_bookings = cursor.fetchone()[0]

      
        cursor.execute("SELECT * FROM bookings ORDER BY created_at ASC")
        bookings_raw = cursor.fetchall()

        bookings = []
        for b in bookings_raw:
            b = list(b)
            if b[6]:  # created_at
                if hasattr(b[6], 'strftime'):
                    b[6] = b[6].strftime('%Y-%m-%d %H:%M')
                else:
                    # sqlite str
                    try:
                        b[6] = datetime.strptime(b[6], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        b[6] = str(b[6])
            bookings.append(b)

        conn.close()

        return render_template("admin_dashboard.html",
                             bookings=bookings,
                             total_bookings=total_bookings,
                             pending_bookings=pending_bookings,
                             confirmed_bookings=confirmed_bookings,
                             completed_bookings=completed_bookings,
                             db_status="Connected")

    except Exception as e:
        print(f"Database error: {e}")
        return render_template("admin_dashboard.html",
                             bookings=[],
                             total_bookings=0,
                             pending_bookings=0,
                             confirmed_bookings=0,
                             completed_bookings=0,
                             db_status="Database error")

@app.route("/bhakti-secure-admin-portal-84729/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/bhakti-secure-admin-portal-84729/login")

@app.route("/update-status/<int:booking_id>/<status>", methods=["POST"])
def update_status(booking_id, status):
    if "admin" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if status not in ['Pending', 'Confirmed', 'Completed', 'Rejected']:
        return jsonify({"success": False, "message": "Invalid status"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "Database not available"}), 500

    try:
        cursor = conn.cursor(buffered=True)
        placeholder = get_param_style(conn)

        cursor.execute(
            f"UPDATE bookings SET status = {placeholder} WHERE id = {placeholder}",
            (status, booking_id)
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Booking {status.lower()} successfully"})

    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500



@app.route("/bhakti-secure-admin-portal-84729/website")
def admin_website():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return redirect("/")

@app.route("/bhakti-secure-admin-portal-84729/election")
def admin_election():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return render_template("election.html")

@app.route("/bhakti-secure-admin-portal-84729/campaign")
def admin_campaign():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return render_template("campaign.html")

@app.route("/bhakti-secure-admin-portal-84729/loudspeaker")
def admin_loudspeaker():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return render_template("loudspeaker.html")

@app.route("/bhakti-secure-admin-portal-84729/production")
def admin_production():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return render_template("production.html")

@app.route("/bhakti-secure-admin-portal-84729/events")
def admin_events():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return render_template("events.html")

@app.route("/bhakti-secure-admin-portal-84729/social")
def admin_social():
    if "admin" not in session:
        return redirect("/bhakti-secure-admin-portal-84729/login")
    return render_template("socialMedia.html")


@app.route("/booking", methods=["GET", "POST"])
def booking():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        service = request.form.get("service", "").strip()
        booking_date = request.form.get("booking_date", "").strip()

        # Basic validation
        if not all([name, phone, service, booking_date]):
            flash("All fields are required.", "error")
            return redirect(url_for('booking'))

        # Phone validation
        if not re.match(r'^\d{10}$', phone):
            flash("Phone must be exactly 10 digits.", "error")
            return redirect(url_for('booking'))

        # Date validation
        try:
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            booking_date = booking_date_obj.date()
            
            if booking_date_obj.date() < datetime.now().date():
                flash("Booking date cannot be in the past.", "error")
                return redirect(url_for('booking'))
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for('booking'))

        conn = get_db_connection()
        if conn is not None:
            try:
                cursor = conn.cursor(buffered=True)
                placeholder = get_param_style(conn)
                query = f"INSERT INTO bookings (name, phone, service, booking_date) VALUES ({', '.join([placeholder] * 4)})"

                cursor.execute(
                    query,
                    (name, phone, service, booking_date)
                )

                conn.commit()
                conn.close()

                # ✅ SUCCESS REDIRECT
                return redirect(url_for('booking', success='true'))

            except Exception as e:
                print(f"Database error: {e}")
                flash("Error saving booking", "error")
                return redirect(url_for('booking'))

        else:
            flash("Database not available", "error")
            return redirect(url_for('booking'))

    return render_template("booking.html")


@app.route("/delete-booking/<int:id>", methods=["POST"])
def delete_booking(id):

    if "admin" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "Database not available"}), 500

    try:
        cursor = conn.cursor(buffered=True)
        placeholder = get_param_style(conn)

        cursor.execute(f"DELETE FROM bookings WHERE id = {placeholder}", (id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Booking deleted successfully"})

    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500



@app.route("/")
def client_dashboard():
    return render_template("welcome.html")

@app.route('/logo')
def logo_page():
    return render_template('wel2.html')

@app.route('/election')
def election_page():
    return render_template('election.html')


@app.route('/campaign')
def campaign_page():
    return render_template('campaign.html')


@app.route('/loudspeaker')
def loudspeaker_page():
    return render_template('loudspeaker.html')


@app.route('/pro')
def production_page():
    return render_template('production.html')



@app.route('/events')
def events_page():
    return render_template('events.html')



@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/dia')
def dialogue_page():
    return render_template('dialouge.html')

@app.route('/social')
def social_page():
    return render_template('socialMedia.html')


@app.route("/chat", methods=["POST"])
def chat():

    user_message = request.json["message"].lower()

    if len(user_message) > 500:
        return jsonify({"reply": "Message too long. Please keep it under 500 characters."})

    reply = ""
    
    location_words = ["location","address","map","कुठे","लोकेशन","पत्ता"]
    # PRICE
    price_words = ["price","charges","cost","किंमत","पैसे","rate"]

    # RICKSHAW
    rickshaw_words = ["rickshaw","announcement","रिक्शा","रिक्षा","speaker","प्रचार" , "demo","playlist","songs","गाणी","डेमो","music"]

   
    # ---------------- PRICE ----------------
    if any(word in user_message for word in price_words):

        reply = """
        💰 प्रचार गीत बनवण्याचे चार्जेस 🎵<br><br>

        🎧 मोठी निवडणूक प्रचारगीतं 👇<br>
        1 गाणं — ₹3,500<br>
        2 गाणी — ₹6000<br>
        3 गाणी — ₹9000<br><br>

        🎬 नाव & चिन्हासह रील प्रचारगीतं 👇<br>
        ₹2000 प्रति रील<br><br>

        🔥 स्मार्ट सॉंग <br> 
        ₹1500 प्रति गाणे<br>
    """

    # ---------------- RICKSHAW ----------------
    elif any(word in user_message for word in rickshaw_words):

        reply = """
        🚕 रिक्षा अनाउन्समेंट चार्जेस 👇<br> <br>

        🔶 ५ मिनिटांचा प्रीमियम प्रचार पॅकेज <br> 
        💰 ₹6000<br><br>

        🟧 2 - 2.30 मिनिटांचा प्रचार <br> 
        💰 ₹3500 <br><br>

        🟨 1.30 मिनिटांचा शॉर्ट प्रचार <br>  
        💰 ₹2500 <br><br>

        📞 बुकिंगसाठी कॉल करा  <br>
        👉 9146940518<br><br>
    """
    elif any(word in user_message for word in location_words):

       reply = """
    📍 आमचे स्टुडिओ लोकेशन 👇 <br><br>

    🎙 Bhakti Recording Studio  
    Junnar, Pune <br><br>

    <a href="https://www.google.com/maps?q=19.1138352,74.1761465" target="_blank" style="background: linear-gradient(45deg, #ff416c, #ff4b2b); color: white; padding: 10px 16px; border-radius: 25px; text-decoration: none; display: inline-block; font-weight: bold;">
    📍 View Location
    </a>
    """  

    else:

        reply = "कृपया आपला प्रश्न स्पष्ट लिहा. Example: price / demo / रिक्षा"

    # SAVE CHAT
    try:
        conn = get_db_connection()
        if conn is None:
            print("[ERROR] Database not available to save chat history")
        else:
            cursor = conn.cursor(buffered=True)
            placeholder = get_param_style(conn)

            cursor.execute(
                f"INSERT INTO chat_history (user_message, bot_reply) VALUES ({placeholder}, {placeholder})",
                (user_message, reply)
            )

            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[ERROR] Database error in chat saving: {e}")

    return jsonify({"reply": reply})

if __name__ == "__main__":
   app.run(
    host='0.0.0.0',
    port=int(os.getenv("PORT", 5000))
)