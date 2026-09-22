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
from admin_ai import register_admin_chatbot
from auth import admin_required



load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

app.config['PREFERRED_URL_SCHEME'] = 'https'

csrf = CSRFProtect(app)
register_admin_chatbot(app, csrf)
init()


def get_demos(language, category=None):
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    try:
        query = """
            SELECT id, title, video_url, is_new
            FROM demos
            WHERE language = %s
        """
        params = [language]
        if category is not None:
            query += " AND category = %s"
            params.append(category)
        query += " ORDER BY created_at DESC, id DESC"

        cursor.execute(query, tuple(params))
        demos = []
        for demo_id, title, video_url, is_new in cursor.fetchall():
            video_id = re.search(r"(?:v=|youtu\.be/)([^&?\s]+)", video_url)
            if video_id:
                demos.append({
                    "id": demo_id,
                    "title": title,
                    "video_id": video_id.group(1),
                    "is_new": bool(is_new)
                })
        return demos
    except Exception as e:
        print(f"Demo loading error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

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



@app.route("/db-test")
def db_test():
    conn = get_db_connection()

    if conn:
        conn.close()
        return "DB CONNECTED"

    return "DB FAILED"

@app.route("/health/db")
def db_health():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "unavailable", "database": "unavailable"}), 503

    conn.close()
    return jsonify({"status": "ok", "database": "connected"}), 200



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
            cursor.close()
            conn.close()

            if result and check_password_hash(result[0], password):
                session.clear()
                session["admin"] = username
                if client_ip in login_attempts:
                    del login_attempts[client_ip]
                return redirect("/bhakti-secure-admin-portal-84729/dashboard")
            else:
                if client_ip not in login_attempts:
                    login_attempts[client_ip] = [0, current_time]
                login_attempts[client_ip][0] += 1
                login_attempts[client_ip][1] = current_time
                flash("Invalid username or password", "error")

        except Exception:
            app.logger.exception("Admin login database query failed.")
            flash("An error occurred. Please try again.", "error")

    return render_template("admin_login.html")

@app.route("/bhakti-secure-admin-portal-84729/ai-assistant")
@admin_required
def admin_ai_assistant():
    return render_template("admin_ai_assistant.html")

@app.route("/bhakti-secure-admin-portal-84729/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    if conn is None:
        return render_template(
            "admin_dashboard.html",
            bookings=[],
            total_bookings=0,
            pending_bookings=0,
            confirmed_bookings=0,
            completed_bookings=0,
            db_status="Database not connected",
        )

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
        bookings = []
        for booking_row in cursor.fetchall():
            booking_row = list(booking_row)

            # booking_date
            if booking_row[4]:
                booking_row[4] = (
                    booking_row[4].strftime("%Y-%m-%d")
                    if hasattr(booking_row[4], "strftime")
                    else str(booking_row[4])
                )

            # booking_time
            if booking_row[6]:
                booking_row[6] = str(booking_row[6])

            # created_at
            if booking_row[8]:
                booking_row[8] = (
                    booking_row[8].strftime("%Y-%m-%d %H:%M")
                    if hasattr(booking_row[8], "strftime")
                    else str(booking_row[8])
                )

            bookings.append(booking_row)
        cursor.close()
        conn.close()
        return render_template(
            "admin_dashboard.html",
            bookings=bookings,
            total_bookings=total_bookings,
            pending_bookings=pending_bookings,
            confirmed_bookings=confirmed_bookings,
            completed_bookings=completed_bookings,
            db_status="Connected",
        )
    except Exception:
        app.logger.exception("Admin dashboard database query failed.")
        return render_template(
            "admin_dashboard.html",
            bookings=[],
            total_bookings=0,
            pending_bookings=0,
            confirmed_bookings=0,
            completed_bookings=0,
            db_status="Database error",
        )

@app.route("/bhakti-secure-admin-portal-84729/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/update-status/<int:booking_id>/<status>", methods=["POST"])
@csrf.exempt
@admin_required
def update_status(booking_id, status):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "Database not connected"}), 503
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status=%s WHERE id=%s", (status, booking_id))
        conn.commit()
        return jsonify({"success": True})
    except Exception:
        app.logger.exception("Booking status update failed.")
        return jsonify({"success": False, "message": "Database error"}), 503
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

@app.route("/bhakti-secure-admin-portal-84729/website")
@admin_required
def admin_website():
    return redirect("/")

@app.route("/bhakti-secure-admin-portal-84729/election")
@admin_required
def admin_election():
    return render_template("election.html")

@app.route("/bhakti-secure-admin-portal-84729/campaign")
@admin_required
def admin_campaign():
    return render_template("campaign.html")

@app.route("/bhakti-secure-admin-portal-84729/loudspeaker")
@admin_required
def admin_loudspeaker():
    return render_template("loudspeaker.html")

@app.route("/bhakti-secure-admin-portal-84729/production")
@admin_required
def admin_production():
    return render_template("production.html")

@app.route("/bhakti-secure-admin-portal-84729/events")
@admin_required
def admin_events():
    return render_template("events.html")

@app.route("/bhakti-secure-admin-portal-84729/social")
@admin_required
def admin_social():
    return render_template("socialMedia.html")
@app.route("/hindi-demos")
def hindi_demos():
    return render_template("hindi_demos.html", database_demos=get_demos("hindi"))

@app.route("/wel2")
def wel2():
    return render_template("wel2.html")


@app.route("/booking", methods=["GET", "POST"])
def booking():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        service = request.form.get("service", "").strip()
        booking_date = request.form.get("booking_date", "").strip()
        language = request.form.get("language", "en").strip()
        booking_time = request.form.get("booking_time", "").strip()

        # -----------------------------
        # BASIC VALIDATION
        # -----------------------------
        if not name:
            return jsonify({
                "success": False,
                "message": "Name is required."
            }), 400

        if not phone:
            return jsonify({
                "success": False,
                "message": "Phone number is required."
            }), 400

        if not service:
            return jsonify({
                "success": False,
                "message": "Service is required."
            }), 400

        if not booking_date:
            return jsonify({
                "success": False,
                "message": "Booking date is required."
            }), 400

        if not booking_time:
            return jsonify({
                "success": False,
                "message": "Booking time is required."
            }), 400

        # -----------------------------
        # LANGUAGE
        # -----------------------------
        allowed_languages = ["en", "mr", "hi"]

        if language not in allowed_languages:
            language = "en"

        # -----------------------------
        # PHONE
        # -----------------------------
        if not re.fullmatch(r"\d{10}", phone):
            return jsonify({
                "success": False,
                "message": "Phone must be exactly 10 digits."
            }), 400

        # -----------------------------
        # DATE
        # -----------------------------
        try:
            booking_date_obj = datetime.strptime(
                booking_date,
                "%Y-%m-%d"
            ).date()

            if booking_date_obj < datetime.now().date():
                return jsonify({
                    "success": False,
                    "message": "Booking date cannot be in the past."
                }), 400

        except ValueError:
            return jsonify({
                "success": False,
                "message": "Invalid booking date."
            }), 400

        # -----------------------------
        # DATABASE
        # -----------------------------
        conn = get_db_connection()

        if conn is None:
            app.logger.error("Booking failed: database connection unavailable.")

            return jsonify({
                "success": False,
                "message": "Database connection failed."
            }), 503

        cursor = None

        try:

            cursor = conn.cursor()

            # IMPORTANT:
            # booking_time is now included in the INSERT.
            cursor.execute(
                """
                INSERT INTO bookings
                (
                    name,
                    phone,
                    service,
                    booking_date,
                    language,
                    booking_time,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    phone,
                    service,
                    booking_date_obj,
                    language,
                    booking_time,
                    "Pending"
                )
            )

            conn.commit()

            app.logger.info(
                "Booking saved successfully for %s on %s at %s",
                name,
                booking_date,
                booking_time
            )

            return jsonify({
                "success": True,
                "message": "Booking submitted successfully."
            }), 200

        except Exception as e:

            try:
                conn.rollback()
            except Exception:
                pass

            app.logger.exception(
                "BOOKING INSERT ERROR: %s",
                e
            )

            return jsonify({
                "success": False,
                "message": "Booking could not be saved. Please try again."
            }), 503

        finally:

            if cursor is not None:
                cursor.close()

            conn.close()

    # -----------------------------
    # GET REQUEST
    # -----------------------------
    return render_template(
        "booking.html",
        success=request.args.get("success")
    )


@app.route("/delete-booking/<int:id>", methods=["POST"])
@csrf.exempt
@admin_required
def delete_booking(id):
    conn = get_db_connection()

    if conn is None:
        return jsonify({
            "success": False,
            "message": "Database not connected"
        })

    try:

        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM bookings WHERE id=%s",
            (id,)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:

        print("DELETE ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Database error"
        })


@app.route("/")
def client_dashboard():
    return render_template("welcome.html")

@app.route('/logo')
def logo_page():
    return render_template('wel2.html')

@app.route('/election')
def election_page():
    return render_template(
        'election.html',
        database_demos=get_demos("marathi", "election") + get_demos("marathi", "general")
    )


@app.route('/campaign')
def campaign_page():
    return render_template('campaign.html', database_demos=get_demos("marathi", "campaign"))


@app.route('/loudspeaker')
def loudspeaker_page():
    return render_template('loudspeaker.html', database_demos=get_demos("marathi", "loudspeaker"))


@app.route('/pro')
def production_page():
    return render_template('production.html', database_demos=get_demos("marathi", "production"))



@app.route('/events')
def events_page():
    return render_template('events.html', database_demos=get_demos("marathi", "events"))



@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/dia')
def dialogue_page():
    return render_template('dialouge.html', database_demos=get_demos("marathi", "dialogue"))

@app.route('/social')
def social_page():
    return render_template('socialMedia.html', database_demos=get_demos("marathi", "social"))


@csrf.exempt
@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"reply": "Invalid request"})

        user_message = data["message"].lower().strip()

        reply = ""

        location_words = ["location","address","map","कुठे","लोकेशन","पत्ता"]

        price_words = ["price","charges","cost","किंमत","पैसे","rate"]

        rickshaw_words = [
            "rickshaw","announcement","रिक्शा","रिक्षा",
            "speaker","प्रचार","demo","playlist",
            "songs","गाणी","डेमो","music"
        ]

        booking_words = [
        "booking",
        "book",
        "बुकिंग",
        "बुक",
        "slot",
        "appointment"
    ]

        # PRICE
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

        elif any(word in user_message for word in rickshaw_words):

            reply = """
            🚕 रिक्षा अनाउन्समेंट चार्जेस 👇<br><br>

            🔶 ५ मिनिटांचा प्रीमियम प्रचार पॅकेज <br> 
            💰 ₹6000<br><br>

            🟧 2 - 2.30 मिनिटांचा प्रचार <br> 
            💰 ₹3500 <br><br>

            🟨 1.30 मिनिटांचा शॉर्ट प्रचार <br>  
            💰 ₹2500 <br><br>

            📞 बुकिंगसाठी कॉल करा <br>
            👉 9146940518<br><br>
            """

        elif any(word in user_message for word in location_words):

            reply = """
            📍 आमचे स्टुडिओ लोकेशन 👇<br><br>

            🎙 Bhakti Recording Studio<br>
            Junnar, Pune<br><br>

            <a href="https://www.google.com/maps?q=19.1138352,74.1761465"
            target="_blank"
            rel="noopener noreferrer">
            📍 View Location
            </a>
            """

        elif any(word in user_message for word in booking_words):

            reply = """
            📅 बुकिंगसाठी खालील बटनावर क्लिक करा 👇<br><br>

            🎙️ Bhakti Studio मध्ये तुमचा स्लॉट बुक करा.<br><br>

            📞 थेट बुकिंगसाठी कॉल करा:<br>
            👉 9146940518<br><br>

            <a href="/booking"
            style="
            display:inline-block;
            background:#c72c17;
            color:white;
            padding:10px 18px;
            border-radius:8px;
            text-decoration:none;
            font-weight:600;">
            📅 Book Your Slot
            </a>
            """

        else:

            reply = """
            कृपया प्रश्न स्पष्ट लिहा 🙏<br><br>

            Example:<br>
            • price<br>
            • location<br>
            • demo<br>
            • रिक्षा
            """

        # DATABASE SAVE
        try:

            conn = get_db_connection()

            if conn is not None:

                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO chat_history
                    (user_message, bot_reply)
                    VALUES (%s, %s)
                    """,
                    (user_message, reply)
                )

                conn.commit()

                cursor.close()
                conn.close()

            else:
                print("Database not connected")

        except Exception as db_error:
            print("Chat DB Error:", db_error)

        return jsonify({"reply": reply})

    except Exception as e:

        print("CHATBOT ERROR:", e)

        return jsonify({
            "reply": "⚠ Server error. Please try again."
        })



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)