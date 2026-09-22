import re
from html import escape
from flask import request, jsonify
from database import get_db_connection
from auth import admin_required


def register_admin_chatbot(app, csrf_protect=None):

    @app.route("/admin-ai-chat", methods=["POST"])
    @admin_required
    def admin_ai_chat():
        try:

            data = request.get_json(silent=True)

            if not data:
                return jsonify({
                    "reply": "⚠️ No data received."
                }), 400

            if data.get("action") == "cancel-delete":
                return jsonify({"reply": "Delete cancelled."})

            if data.get("action") == "confirm-delete":
                try:
                    demo_id = int(data.get("id"))
                except (TypeError, ValueError):
                    return jsonify({"reply": "⚠️ Invalid demo selection."}), 400
                return delete_demo(demo_id)

            # ==========================================
            # DIRECT ADD DEMO
            # ==========================================

            language = data.get("language")
            category = data.get("category")
            video_url = data.get("video_url")

            if language and category and video_url:

                return add_demo(
                    language=language,
                    category=category,
                    video_url=video_url
                )

            # ==========================================
            # OLD COMMAND MODE
            # ==========================================

            message = str(data.get("message", "")).strip()

            if not message:
                return jsonify({
                    "reply": "कृपया command लिहा."
                }), 400

            message_lower = message.lower()

            if is_delete_command(message_lower):
                language = detect_language(message)
                category = detect_category(message)

                if not language:
                    return jsonify({
                        "reply": "Please specify Marathi or Hindi before deleting a demo."
                    })

                demo = find_latest_demo(language, category)
                if demo is None:
                    return jsonify({
                        "reply": "No matching demo was found."
                    })

                demo_id, title, demo_language, demo_category = demo
                return jsonify({
                    "reply": f"""
                    <div class="delete-confirmation">
                        <strong>Delete this demo?</strong>
                        <p>{escape(title)}</p>
                        <button class="delete-demo-btn" data-action="confirm-delete" data-id="{demo_id}">Delete Demo</button>
                        <button class="cancel-delete-btn" data-action="cancel-delete">Cancel</button>
                    </div>
                    """
                })

            # ==========================================
            # YOUTUBE LINK
            # ==========================================

            youtube_match = re.search(
                r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[^\s\]\)]+|youtu\.be/[^\s\]\)]+)',
                message
            )

            video_url = (
                youtube_match.group(0)
                if youtube_match
                else None
            )

            # ==========================================
            # LANGUAGE
            # ==========================================

            language = detect_language(message)

            # ==========================================
            # CATEGORY
            # ==========================================

            category = detect_category(message) or "general"

            # ==========================================
            # ADD DEMO
            # ==========================================

            is_add_command = (
                "add" in message_lower
                or "new" in message_lower
                or "नवीन" in message
                or "नई" in message
                or "नया" in message
            )

            if language and video_url and is_add_command:

                return add_demo(
                    language=language,
                    category=category,
                    video_url=video_url
                )

            # ==========================================
            # BOOKINGS
            # ==========================================

            if is_booking_command(message):
                status = detect_booking_status(message)
                wants_count = is_booking_count_request(message)

                conn = get_db_connection()

                if conn is None:
                    return jsonify({
                        "reply": "⚠️ Database connection failed."
                    })

                cursor = conn.cursor()

                try:
                    if wants_count:
                        if status:
                            cursor.execute(
                                "SELECT COUNT(*) FROM bookings WHERE status = %s",
                                (status,)
                            )
                            count = cursor.fetchone()[0]
                            label = f"{status} Bookings"
                            reply = f"📋 {label}<br><br><strong>{count}</strong> {status.lower()} bookings आहेत."
                        else:
                            cursor.execute("SELECT COUNT(*) FROM bookings")
                            count = cursor.fetchone()[0]
                            reply = f"📋 Total Bookings<br><br><strong>{count}</strong> bookings आहेत."
                    else:
                        columns = "id, name, phone, service, booking_date, language, status"
                        query = f"SELECT {columns} FROM bookings"
                        params = ()

                        if status:
                            query += " WHERE status = %s"
                            params = (status,)

                        query += " ORDER BY created_at ASC"
                        cursor.execute(query, params)
                        bookings = cursor.fetchall()
                        reply = format_booking_list(bookings, status)
                finally:
                    cursor.close()
                    conn.close()

                return jsonify({"reply": reply})

            # ==========================================
            # HELP
            # ==========================================

            return jsonify({
                "reply": """
                कृपया योग्य command वापरा 🙏<br><br>

                उदाहरण:<br><br>

                • नवीन मराठी Election demo add कर<br>
                • नवीन हिंदी Campaign demo add कर<br>
                • bookings दाखव<br>
                • pending bookings दाखव
                """
            })

        except Exception as e:

            print("ADMIN CHATBOT ERROR:", repr(e))

            return jsonify({
                "reply": "⚠️ Server error. Please try again."
            }), 500

    if csrf_protect is not None:
        csrf_protect.exempt(admin_ai_chat)


# ==================================================
# CATEGORY DETECTION
# ==================================================

def detect_category(message):

    message_lower = message.lower()

    if (
        "election" in message_lower
        or "elections" in message_lower
        or "इलेक्शन" in message
    ):
        return "election"

    if (
        "campaign" in message_lower
        or "कॅम्पेन" in message
        or "कॅम्पेन" in message
    ):
        return "campaign"

    if (
        "loudspeaker" in message_lower
        or "loud speaker" in message_lower
        or "लाऊडस्पीकर" in message
    ):
        return "loudspeaker"

    if (
        "production" in message_lower
        or "प्रोडक्शन" in message
    ):
        return "production"

    if (
        "event" in message_lower
        or "events" in message_lower
        or "इव्हेंट" in message
    ):
        return "events"

    if (
        "dialogue" in message_lower
        or "डायलॉग" in message
        or "संवाद" in message
    ):
        return "dialogue"

    if (
        "social" in message_lower
        or "social media" in message_lower
        or "सोशल" in message
    ):
        return "social"

    return None


def is_booking_command(message):
    message_lower = message.lower()
    return (
        "booking" in message_lower
        or "bookings" in message_lower
        or "बुकिंग" in message
    )


def detect_booking_status(message):
    message_lower = message.lower()
    status_terms = (
        ("Pending", ("pending", "पेंडिंग")),
        ("Confirmed", ("confirmed", "कन्फर्म", "कन्फर्म्ड")),
        ("Completed", ("completed", "कम्प्लीट", "पूर्ण")),
        ("Rejected", ("rejected", "रिजेक्ट", "नाकारलेले")),
    )

    for status, terms in status_terms:
        if any(term in message_lower or term in message for term in terms):
            return status

    return None


def is_booking_count_request(message):
    message_lower = message.lower()
    return any(term in message_lower or term in message for term in (
        "how many",
        "count",
        "number",
        "किती",
        "किती आहेत",
        "किती आहे",
    ))


def format_booking_list(bookings, status=None):
    label = f"{status} Bookings" if status else "All Bookings"

    if not bookings:
        empty_text = (
            f"There are currently no {status.lower()} bookings."
            if status
            else "There are currently no bookings."
        )
        return f"📋 {label}<br><br>{empty_text}"

    lines = [f"📋 {label}<br><br>"]
    for index, booking in enumerate(bookings, start=1):
        booking_id, name, phone, service, booking_date, language, booking_status = booking
        date_text = booking_date.strftime("%Y-%m-%d") if hasattr(booking_date, "strftime") else str(booking_date or "N/A")
        lines.append(
            f"{index}. {escape(str(name or 'N/A'))}<br>"
            f"📞 {escape(str(phone or 'N/A'))}<br>"
            f"🎵 Service: {escape(str(service or 'N/A'))}<br>"
            f"📅 Booking Date: {escape(date_text)}<br>"
            f"🌐 Language: {escape(str(language or 'N/A'))}<br>"
            f"Status: {escape(str(booking_status or 'N/A'))}<br><br>"
        )

    return "".join(lines)


def detect_language(message):
    message_lower = message.lower()
    if "मराठी" in message or "marathi" in message_lower:
        return "marathi"
    if "हिंदी" in message or "hindi" in message_lower:
        return "hindi"
    return None


def is_delete_command(message_lower):
    return (
        "delete" in message_lower
        or "remove" in message_lower
        or "डिलीट" in message_lower
        or "हटव" in message_lower
    )


def find_latest_demo(language, category=None):
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    try:
        query = """
            SELECT id, title, language, category
            FROM demos
            WHERE language = %s
        """
        params = [language]
        if category:
            query += " AND category = %s"
            params.append(category)
        query += " ORDER BY created_at DESC, id DESC LIMIT 1"
        cursor.execute(query, tuple(params))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ==================================================
# ADD DEMO TO MYSQL
# ==================================================

def add_demo(language, category, video_url):

    conn = get_db_connection()

    if conn is None:
        return jsonify({
            "reply": "⚠️ Database connection failed."
        }), 500

    cursor = None

    try:

        cursor = conn.cursor()

        # ==========================================
        # REMOVE OLD NEW TAGS
        # ==========================================

        cursor.execute("""
            UPDATE demos
            SET is_new = FALSE
            WHERE language = %s
            AND category = %s
        """, (language, category))

        # ==========================================
        # TITLE
        # ==========================================

        language_name = (
            "Marathi"
            if language == "marathi"
            else "Hindi"
        )

        category_label = "" if category == "general" else f" {category}"
        title = f"New {language_name} Demo"

        # ==========================================
        # INSERT NEW VIDEO
        # ==========================================

        cursor.execute("""
            INSERT INTO demos
            (
                title,
                language,
                category,
                video_url,
                is_new
            )
            VALUES (%s, %s, %s, %s, TRUE)
        """, (
            title,
            language,
            category,
            video_url
        ))

        cursor.execute("""
            UPDATE demos
            SET is_new = TRUE
            WHERE id IN (
                SELECT id FROM (
                    SELECT id
                    FROM demos
                    WHERE language = %s
                    AND category = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT 2
                ) AS latest_demos
            )
        """, (language, category))

        conn.commit()

        # ==========================================
        # CLOSE DATABASE
        # ==========================================

        cursor.close()
        conn.close()

        # ==========================================
        # SUCCESS MESSAGE
        # ==========================================

        if language == "marathi":
            page = {
                "general": "/election",
                "election": "/election",
                "campaign": "/campaign",
                "loudspeaker": "/loudspeaker",
                "production": "/pro",
                "events": "/events",
                "dialogue": "/dia",
                "social": "/social"
            }.get(category, "/election")

        else:

            page = "/hindi-demos"

        reply = f"""
        <div class="success-message">

            <div class="success-icon">
                ✓
            </div>

            <div class="success-text">

                <strong>
                    Video added successfully!
                </strong>

                <span>
                    Your new {language_name}{category_label} demo has been added to the website.
                </span>

            </div>

        </div>

        <a href="{page}" class="view-demo-btn">
            🎧 See New Video →
        </a>
        """

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print("ADD DEMO ERROR:", repr(e))

        if conn:
            conn.rollback()

        if cursor:
            cursor.close()

        if conn:
            conn.close()

        return jsonify({
            "reply": f"⚠️ Video could not be added: {e}"
        }), 500


def delete_demo(demo_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"reply": "⚠️ Database connection failed."}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM demos WHERE id = %s", (demo_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"reply": "No matching demo was found."})

        conn.commit()
        return jsonify({
            "reply": """
            <div class="success-message">
                <div class="success-icon">✓</div>
                <div class="success-text">
                    <strong>Demo deleted successfully!</strong>
                    <span>The demo has been removed from the website.</span>
                </div>
            </div>
            """
        })
    except Exception as e:
        print("DELETE DEMO ERROR:", repr(e))
        conn.rollback()
        return jsonify({"reply": "⚠️ Demo could not be deleted."}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()