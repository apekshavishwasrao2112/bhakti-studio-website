# Bhakti Studio – Music Studio Booking and Management System

Bhakti Studio is a Flask-based music studio website and management system. It combines service information, Marathi/Hindi/English booking, music demos, a customer chatbot, WhatsApp communication links, MySQL storage, and an authenticated admin dashboard.

## Project Overview

This project came from a real business need. My brother runs a music studio, and I noticed that customer requirements, service information, demo links, bookings, and follow-up communication were being handled separately. Bhakti Studio brings those activities into one web application.

Customers can explore studio services and demos, ask common questions, choose their preferred booking language, select a service/date/time, and submit a booking request. The studio administrator can sign in, view booking statistics and records, update booking status, contact customers through WhatsApp links, and manage database-backed demos through the admin assistant.

The application connects Jinja HTML templates and CSS/JavaScript in the browser to Flask routes and business logic. Flask validates requests and uses `mysql-connector-python` to read and write MySQL data. YouTube, WhatsApp, Google Maps, and the deployment platform are external services linked from the frontend or configuration.

## Problem Statement

The original studio workflow created several practical problems:

- Customers needed one place to understand the available studio services.
- Customers needed convenient access to music and demo videos.
- Booking requests needed consistent fields and an initial status.
- Customer questions and follow-up communication needed to be easier.
- Marathi, Hindi, and English customers needed a usable booking interface.
- The studio needed an admin view for booking decisions and content management.
- Managing these activities separately could lead to missed information or confusion.

Bhakti Studio addresses these needs with a public service/demo website, a validated booking endpoint, a rule-based customer chatbot, database-backed records, and protected administrator tools.

## Main Features

### Customer side

- Landing page at `/` with studio branding, a background video, and a link to the main studio page.
- Service and content pages for election songs, campaigns, loudspeaker announcements, production, events, dialogue, social media, and Hindi demos.
- YouTube demo cards with thumbnails. Clicking a card replaces its thumbnail with an autoplaying YouTube iframe.
- Booking at `/booking` for Song Recording, Video Reel, or Announcement.
- Booking language buttons for English (`en`), Marathi (`mr`), and Hindi (`hi`). The selected language updates the visible labels and is submitted with the form.
- Required booking date and time-slot selection.
- A success modal after a successful asynchronous booking request.
- A floating customer chatbot included by the public demo pages.
- Service-related links, a booking call-to-action, a Google Maps location link, and WhatsApp contact links.

### Booking system

The form in `templates/booking.html` collects:

| Field | Purpose |
| --- | --- |
| `name` | Customer name |
| `phone` | Ten-digit customer phone number |
| `service` | `song`, `reel`, or `announcement` |
| `booking_date` | Requested recording date |
| `booking_time` | Selected time slot, such as `09:00` or `14:00` |
| `language` | `en`, `mr`, or `hi` |
| `csrf_token` | Token included by the form, although the booking route itself is not CSRF-exempted in the current code |

The browser prevents the normal form navigation and sends a `FormData` request to `POST /booking`. The Flask `booking()` route strips values, checks required fields, accepts only `en`, `mr`, and `hi` (falling back to `en` for another value), and validates that the phone contains exactly ten digits. It parses the date as `%Y-%m-%d` and rejects dates before the current date. A successful insert writes the record to MySQL with status `Pending` and returns JSON. The browser reads that JSON and opens the success modal; errors are shown through an alert.

### Multilingual booking

The booking page contains translations in JavaScript for English, Marathi, and Hindi. `setLang()` changes the page labels, placeholders, service names, date/time labels, button text, and success text. It also writes the selected two-letter code to the hidden `language` field. Flask stores that code in the `bookings.language` column.

This is user-selected language, not automatic language detection. The backend does not use regular expressions to detect a booking language. A separate Devanagari regular expression appears in the admin dashboard's WhatsApp helpers to decide whether the customer's name contains Devanagari characters when choosing Marathi or English message text.

## Music Demo System

The public demo pages use two sources of content:

1. Some demo cards are hard-coded in templates with YouTube video IDs.
2. New demos are loaded from the MySQL `demos` table by `get_demos(language, category)`.

`get_demos()` selects the demo ID, title, URL, and `is_new` flag for a language and optional category. A regular expression extracts a video ID from either a `youtube.com/watch?v=...` or `youtu.be/...` URL. The templates then request thumbnails from `https://img.youtube.com/vi/<video-id>/hqdefault.jpg`. `playVideo()` replaces the thumbnail with `https://www.youtube.com/embed/<video-id>?autoplay=1&rel=0`; when another card is selected, the previous card is restored to its thumbnail.

Marathi categories are served by `/election`, `/campaign`, `/loudspeaker`, `/pro`, `/events`, `/dia`, and `/social`. Hindi demos are served by `/hindi-demos`. The category pages include `chatbot.html`; Hindi has its own page layout and a Hindi booking link. The admin assistant can add Marathi demos by category and Hindi demos under the `general` category. It clears old `is_new` flags for the language/category, inserts the new row, and marks the latest two rows as new. It can also find and delete a matching latest demo after confirmation.

The admin assistant displays a `See New Video` link after insertion. Marathi links return to the relevant category page, while Hindi links return to `/hindi-demos`.

## Customer Chatbot

The customer chatbot is the floating interface in `templates/chatbot.html`, included by `templates/election.html` and inherited by the Hindi demo page. It is a rule-based, keyword-matching chatbot, not an external AI model or generative API.

The supported response groups include:

- price, charges, cost, rate, and Marathi price terms
- rickshaw, announcement, speaker, demo, playlist, songs, and music terms
- location, address, map, and Marathi location terms
- booking, book, slot, and appointment terms

The browser chooses the initial welcome/typing language from the current URL: paths containing `hindi` use Hindi text; other paths use Marathi text. The selected `language` is also sent in the JSON request, but `chat()` currently chooses replies from keyword matches rather than using that field for response selection.

The request flow is:

1. The user enters a message or presses a quick-action button.
2. JavaScript adds the escaped user message to the chat window, shows a typing indicator, and sends `POST /chat` with `Content-Type: application/json` and a body containing `message` and `language`.
3. Flask reads the JSON body, lowercases and trims `message`, and checks the keyword groups.
4. The route builds an HTML reply containing prices, a booking link, a location link, a demo/announcement response, or a help message.
5. When MySQL is available, the original message and generated reply are inserted into `chat_history`.
6. Flask returns `jsonify({"reply": reply})`.
7. JavaScript reads the JSON, removes the typing indicator, and renders the returned HTML inside the chat message area.

The public chatbot route is CSRF-exempt and does not require authentication. If the database is unavailable, the response can still be returned, but the chat record is not saved.

## Admin Dashboard

The admin area is protected by the `admin_required` decorator in `auth.py`. An unauthenticated browser request is redirected to `/bhakti-secure-admin-portal-84729/login`; a request expecting JSON receives HTTP 401. A successful login clears the session and stores the username in `session["admin"]`.

The authenticated dashboard at `/bhakti-secure-admin-portal-84729/dashboard` displays total, pending, confirmed, and completed booking counts, database status, and booking ID, name, phone, service, date, language, time, status, and creation time.

The dashboard actions are:

- `Pending` bookings can be confirmed or rejected.
- `Confirmed` bookings can be marked completed.
- `Completed` and `Rejected` bookings can be deleted.
- Customer phone numbers are clickable WhatsApp actions.

Authenticated administrators can also open the website preview, category pages, and the admin assistant. The admin navigation includes election, campaign, loudspeaker, production, events, and social pages, plus `Back to Admin Dashboard` links where the templates provide them. Logout clears the Flask session.

### Admin assistant

The full-page assistant in `templates/admin_ai_assistant.html` is available at `/bhakti-secure-admin-portal-84729/ai-assistant`. It is a separate admin-only system from the public customer chatbot. Its backend is registered by `register_admin_chatbot()` in `admin_ai.py` at `POST /admin-ai-chat`.

It supports keyword/command processing for:

- listing all bookings or filtering by Pending, Confirmed, Completed, or Rejected
- counting bookings
- adding a Marathi demo with a selected category and YouTube URL
- adding a Hindi demo
- finding the latest matching demo for deletion
- confirming or cancelling a demo deletion

The quick-action forms send JSON directly for demo addition. Text commands are parsed with `detect_language()`, `detect_category()`, `is_booking_command()`, `detect_booking_status()`, and related helpers. Replies are JSON objects containing a `reply` value, which the admin JavaScript inserts into the assistant panel. The template includes a CSRF token header, while `register_admin_chatbot()` explicitly exempts this endpoint and `admin_required` manually protects authenticated mutating requests.

`templates/admin_chatbot.html` contains another floating admin-chat implementation, but it is not included or referenced by the current active templates. The active admin assistant is the full-page implementation described above.

## Admin Booking Logic

1. A customer submits a valid form to `POST /booking`.
2. Flask inserts the submitted values into `bookings` with status `Pending` and commits the transaction.
3. The dashboard counts records by status and displays them to the authenticated admin.
4. The admin dashboard sends `POST /update-status/<booking_id>/<status>` when an action is selected.
5. The route executes `UPDATE bookings SET status=%s WHERE id=%s` and returns JSON indicating success or failure.
6. The dashboard reloads after a successful update.
7. Confirm, reject, and delete actions can open WhatsApp or make the corresponding database change. The status endpoint does not currently whitelist the status path value, so direct callers can submit arbitrary status strings even though the visible UI presents the normal status transitions.

## WhatsApp Communication

The admin dashboard defines `openWhatsApp(phone, name)` and `openRejectWhatsApp(phone, name)`. These functions:

1. Remove non-numeric characters with `phone.replace(/\D/g, "")`.
2. Prefix `91` when the cleaned value has exactly ten digits.
3. Test the name with `/[\u0900-\u097F]/` to choose Marathi or English message text.
4. Build a confirmation or rejection message containing the customer's name, studio contact number, website, and, for confirmation, Google Maps coordinates.
5. Encode the message with `encodeURIComponent()`.
6. Open `https://wa.me/<cleaned-number>?text=<encoded-message>` in a new browser tab.

This opens a pre-filled WhatsApp URL in the browser. It is not server-side automatic WhatsApp delivery. The rejection action in the current dashboard calls `openRejectWhatsApp('', '')`, so its visible UI path can produce a WhatsApp URL without a recipient before updating the status. The social page also contains a fixed WhatsApp consultation link.

## Location Feature

The customer chatbot's location response and the admin confirmation message use the Google Maps URL:

`https://www.google.com/maps?q=19.1138352,74.1761465`

The chatbot renders it as a `View Location` link. Customers can open the studio location from the chat response, and administrators can include the same location in a confirmation message sent through WhatsApp.

## Technology Stack

| Technology | Role in this project |
| --- | --- |
| Python | Application language and backend logic |
| Flask 3.0.3 | Web framework, routes, templates, sessions, and JSON responses |
| Jinja templates | Server-rendered HTML in `templates/` |
| MySQL | Stores bookings, admins, chat history, and demos |
| `mysql-connector-python` 9.0.0 | Connects Flask to MySQL with parameterized SQL values |
| HTML and CSS | Customer and admin page structure and styling |
| JavaScript | Booking submission, language switching, chatbot UI, demo playback, dashboard actions, and WhatsApp links |
| Fetch API | Sends asynchronous booking, customer-chat, admin-chat, and dashboard requests |
| JSON | Request/response format for the API-style endpoints |
| Flask-WTF 1.2.1 | Flask CSRF extension and form token generation |
| Werkzeug 3.0.3 | Password hashing and password verification |
| `python-dotenv` 1.0.1 | Loads environment variables from local environment files |
| Regular expressions | YouTube ID extraction, ten-digit phone validation, and Devanagari-name detection |
| YouTube embeds | Thumbnails and iframe playback for demos |
| WhatsApp `wa.me` links | Browser-based customer communication |
| Google Maps link | Studio location access |
| Gunicorn 22.0.0 | Production WSGI server specified in `Procfile` |
| Railway | Mentioned by the existing README as the hosting platform; local source confirms deployment configuration but cannot verify live availability |

Bootstrap, Font Awesome, Google Fonts, AOS, and external image assets are also referenced by some templates through CDN URLs.

## System Architecture

```text
Customer browser
	-> Jinja HTML, CSS, and JavaScript
	-> Flask public routes and JSON endpoints
	-> validation and application logic
	-> MySQL tables

Administrator browser
	-> authenticated Flask session
	-> protected dashboard and admin assistant routes
	-> booking/demo queries and updates
	-> MySQL tables

External services
	-> YouTube thumbnails and embedded players
	-> WhatsApp pre-filled browser links
	-> Google Maps location link
	-> Railway/Gunicorn deployment configuration
```

The application does not contain a separate frontend framework or a separate REST service. Templates, inline JavaScript, Flask routes, and MySQL form one application.

## Important API and Route Flow

### Public routes

| Method | Route | Purpose | Access and response |
| --- | --- | --- | --- |
| `GET` | `/` | Render the public landing page | Public HTML from `welcome.html` |
| `GET` | `/logo` | Render the main studio page | Public HTML from `wel2.html` |
| `GET` | `/wel2` | Render the same studio page | Public HTML from `wel2.html` |
| `GET` | `/booking` | Show booking form | Public HTML |
| `POST` | `/booking` | Validate and insert a booking | Public JSON success/error response |
| `GET` | `/election` | Show Marathi election demos | Public HTML plus database demos |
| `GET` | `/campaign` | Show Marathi campaign demos | Public HTML plus database demos |
| `GET` | `/loudspeaker` | Show Marathi loudspeaker demos | Public HTML plus database demos |
| `GET` | `/pro` | Show Marathi production demos | Public HTML plus database demos |
| `GET` | `/events` | Show Marathi event demos | Public HTML plus database demos |
| `GET` | `/dia` | Show Marathi dialogue demos | Public HTML plus database demos |
| `GET` | `/social` | Show social/media content | Public HTML plus database demos |
| `GET` | `/hindi-demos` | Show Hindi demos | Public HTML plus database demos |
| `POST` | `/chat` | Process a customer chatbot message | Public JSON containing `reply` |
| `GET` | `/db-test` | Check whether a database connection can be opened | Public text response |
| `GET` | `/health/db` | Return database health information | Public JSON, HTTP 200 or 503 |
| `GET` | `/about` | Attempt to render `about.html` | Route exists, but `about.html` is not present in this repository |

### Protected admin routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET`, `POST` | `/bhakti-secure-admin-portal-84729/login` | Validate admin credentials and create a session |
| `GET` | `/bhakti-secure-admin-portal-84729/dashboard` | Show booking statistics and booking records |
| `GET` | `/bhakti-secure-admin-portal-84729/ai-assistant` | Show the authenticated admin assistant |
| `POST` | `/admin-ai-chat` | Add/delete demos or query bookings through the admin assistant |
| `POST` | `/update-status/<int:booking_id>/<status>` | Update a booking status |
| `POST` | `/delete-booking/<int:id>` | Delete a booking |
| `GET` | `/bhakti-secure-admin-portal-84729/website` | Redirect the admin to `/` |
| `GET` | `/bhakti-secure-admin-portal-84729/election` | Open protected election preview |
| `GET` | `/bhakti-secure-admin-portal-84729/campaign` | Open protected campaign preview |
| `GET` | `/bhakti-secure-admin-portal-84729/loudspeaker` | Open protected loudspeaker preview |
| `GET` | `/bhakti-secure-admin-portal-84729/production` | Open protected production preview |
| `GET` | `/bhakti-secure-admin-portal-84729/events` | Open protected events preview |
| `GET` | `/bhakti-secure-admin-portal-84729/social` | Open protected social preview |
| `GET` | `/bhakti-secure-admin-portal-84729/logout` | Clear the admin session |

## Frontend to Backend to Database Flow

### Booking

1. The customer selects a language and fills in name, phone, service, date, and time.
2. The booking page JavaScript creates `new FormData(this)` and sends it to `/booking` with `fetch()`.
3. Flask's `booking()` function reads the form fields and performs required-field, phone, language, and date validation.
4. Flask opens a MySQL connection through `get_db_connection()`.
5. A parameterized SQL `INSERT` writes the fields and the literal initial status `Pending` to `bookings`.
6. Flask commits the transaction and returns a JSON success message.
7. JavaScript calls `showSuccessModal()`; an error response re-enables the button and displays the error.
8. The admin dashboard later reads the row, changes its status, or deletes it.

### Customer chatbot

The public chatbot sends JSON to `/chat`, where Python performs keyword matching, creates the reply, optionally inserts the conversation into `chat_history`, and returns JSON. JavaScript reads `response.json()` and inserts the reply into the chat UI. This is an asynchronous browser-to-Flask flow and does not call an AI provider.

## Database

`database.init()` creates the following tables when the configured MySQL connection is available.

### `bookings`

| Column | Meaning |
| --- | --- |
| `id` | Auto-incrementing primary key |
| `name` | Customer name |
| `phone` | Customer phone number |
| `service` | Requested studio service |
| `booking_date` | Requested date |
| `language` | Booking language code, default `en` |
| `booking_time` | Requested time slot |
| `status` | Workflow status, default `Pending` |
| `created_at` | Database-created timestamp |

### `admin`

Contains an auto-incrementing `id`, `username`, and a hashed `password`. If `ADMIN_USERNAME` and `ADMIN_PASSWORD` are present and the username does not already exist, `init()` hashes the configured password and creates the account.

### `chat_history`

Contains `id`, `user_message`, and `bot_reply`. The public `/chat` route saves the matched customer message and response when the database is available.

### `demos`

Contains `id`, `title`, `language`, `category`, `video_url`, `is_new`, and `created_at`. `init()` also adds the `category` column to an older `demos` table when necessary.

## Security

Implemented security-related behavior includes:

- `SECRET_KEY` is loaded from the environment and used by Flask sessions.
- Admin passwords are stored with Werkzeug `generate_password_hash()` and checked with `check_password_hash()`.
- `admin_required` protects the dashboard, admin previews, status changes, booking deletion, and admin assistant.
- The admin session stores only the authenticated username under `session["admin"]`.
- Session cookies are configured as `HttpOnly` and `SameSite=Lax`; `Secure` is enabled when `FLASK_ENV` is `production`.
- Failed login attempts are tracked per client address, with a five-attempt lockout window of five minutes in the current process.
- Flask-WTF `CSRFProtect` is initialized, and login, booking, and admin pages include CSRF tokens. Dashboard JavaScript sends `X-CSRFToken` headers.
- SQL values are passed as parameters in the main booking, admin, status, deletion, and demo queries.
- Chatbot HTML replies escape database-derived demo titles and booking values in the admin assistant.

Important current limitations are also worth understanding: `/chat`, `/admin-ai-chat`, `/update-status`, and `/delete-booking` are explicitly route-level CSRF exemptions, although authenticated mutating admin requests call CSRF protection through `admin_required`. The public booking/chat endpoints have no login requirement or rate limiting. The login-attempt dictionary is process-local, and `SECRET_KEY` is required at import time. These are implementation observations, not claims of complete production security.

## Deployment

The repository contains deployment configuration for a Flask WSGI application:

```text
web: gunicorn app:app
```

The existing project README states that the application was deployed on Railway and lists a public Railway URL. The local source confirms the Gunicorn `Procfile`, environment-based configuration, and the application port fallback, but it cannot independently verify that the current Railway deployment is online or that its production MySQL connection is working.

Expected environment variable names are:

```env
SECRET_KEY=<private application secret>
DB_HOST=<mysql host>
DB_USER=<mysql user>
DB_PASSWORD=<private database password>
DB_NAME=<database name>
DB_PORT=3306
ADMIN_USERNAME=<private admin username>
ADMIN_PASSWORD=<private admin password>
```

Do not commit real values. `database.py` uses these variables for MySQL and optional initial admin creation. `app.py` uses the `PORT` environment variable when run directly and defaults to `8080`.

## Project Workflow

### Customer workflow

The customer opens the landing page, follows the studio/home link, reviews services and demos, and opens the booking page. On the booking page, the customer selects English, Marathi, or Hindi, enters contact and service information, chooses a future date and available time slot, and submits the form. Flask validates the request and stores it as `Pending` in MySQL. The browser displays a success modal, and the studio can later contact the customer through the admin dashboard.

### Admin workflow

The administrator opens the secure login route and submits credentials. After authentication, the session permits access to the dashboard and protected preview/assistant routes. The dashboard loads booking counts and records, and the administrator can confirm, reject, complete, or delete records. Confirmation/rejection actions prepare WhatsApp messages in the browser where the current button flow supplies a recipient. The administrator can then use the assistant to add Marathi/Hindi demos, list or count bookings, delete a selected latest demo, preview public pages, return to the dashboard, and log out.

## Project Folder Structure

```text
Bhakti Studio/
├── app.py                  # Flask app, routes, booking and customer chatbot logic
├── admin_ai.py             # Authenticated admin assistant and demo/booking commands
├── auth.py                 # admin_required decorator
├── database.py             # MySQL connection and table initialization
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn process command
├── .gitignore              # Environment, cache, and local database exclusions
├── README.md               # Project documentation
├── templates/
│   ├── welcome.html        # Public landing page
│   ├── wel2.html           # Main studio/home page
│   ├── booking.html        # Multilingual booking form and submission JavaScript
│   ├── chatbot.html        # Public customer chatbot partial
│   ├── election.html       # Marathi election demo base page
│   ├── campaign.html       # Campaign demo page
│   ├── loudspeaker.html    # Loudspeaker demo page
│   ├── production.html     # Production demo page
│   ├── events.html         # Events demo page
│   ├── dialouge.html       # Dialogue demo page
│   ├── socialMedia.html    # Social, media, and contact page
│   ├── hindi_demos.html    # Hindi demo page
│   ├── admin_login.html    # Admin login UI
│   ├── admin_dashboard.html# Protected booking dashboard
│   ├── admin_ai_assistant.html # Protected admin assistant UI
│   ├── admin_chatbot.html  # Additional admin chatbot template not currently included
│   └── dashboard.html      # Older static dashboard mockup, not the live dashboard route
└── static/
		├── css/                # Page, booking, login, dashboard, and control styles
		├── js/script.js        # Welcome audio and logo animation behavior
		├── images/             # Logos, backgrounds, and studio images
		├── audio/welcome.wav   # Welcome-page audio
		└── videos/             # Background and social/demo video assets
```

The repository does not contain a separate test directory or frontend build system.

## How the Chatbot Works

The customer UI is a floating button and chat panel in `chatbot.html`. `sendMessage()` escapes the displayed user text, appends it to the panel, and uses `fetch("/chat", { method: "POST" })` with `JSON.stringify({ message, language })`. The Flask `chat()` function validates that a message exists, lowercases it, checks fixed keyword arrays, creates an HTML response, and attempts to insert the interaction into `chat_history`. It returns `jsonify({"reply": reply})`. The browser parses the JSON, removes the typing state, and renders the reply.

The admin assistant uses the same browser/fetch/JSON pattern but targets `/admin-ai-chat` and requires the admin session. It supports structured JSON for direct demo addition and command text for booking queries and deletion. It is called “AI Assistant” in the UI, but the inspected implementation is deterministic command and keyword logic rather than an AI API integration.

## How Booking Works

`booking.html` renders the form and language translations. The selected language is kept in a hidden field. Browser-side constraints mark fields as required, limit the phone input to ten digits, and set the minimum date to today. On submission, JavaScript sends `FormData` asynchronously to `/booking`.

The Flask `booking()` function performs the authoritative checks, parses the date, obtains a MySQL connection, and executes a parameterized `INSERT INTO bookings` containing name, phone, service, date, language, time, and `Pending`. It commits the transaction and returns JSON. The frontend opens the success modal only when the response is successful. The dashboard later selects all rows and status counts, and its JavaScript calls the status/deletion endpoints for admin actions.

## Challenges Reflected by the Code

The current implementation reflects several practical integration areas:

- connecting a Flask application to MySQL through environment-specific settings
- creating tables and an initial admin account during application initialization
- moving from normal form navigation to asynchronous JSON/FormData responses
- keeping booking labels and result messages usable in three languages
- extracting YouTube IDs and displaying both fixed and database-managed demos
- combining public keyword chatbot behavior with a separate protected admin assistant
- coordinating status changes, database records, WhatsApp links, and location links
- preparing a Gunicorn process for a hosting platform such as Railway
- handling database failures with JSON errors and dashboard database status indicators

These are implementation areas visible in the repository; no separate project history file is present to verify additional challenges.

## Testing

No automated test files, pytest/unittest configuration, coverage configuration, or CI workflow were found in the repository. Testing that can be performed from the current implementation is therefore primarily manual:

- open the public pages and verify templates, assets, demo cards, and navigation
- submit valid and invalid booking forms and inspect JSON responses and the success modal
- verify that the inserted booking appears in MySQL and the admin dashboard
- test admin login, logout, protected-route redirects, and failed-login behavior
- test each booking status action and deletion from the dashboard
- send supported and unsupported customer-chat messages and verify the returned reply
- test admin assistant booking queries, demo addition, deletion confirmation, and preview links
- test YouTube thumbnail-to-iframe behavior, Maps links, and WhatsApp URL generation
- verify environment variables, MySQL connectivity, Gunicorn startup, and the deployed URL separately

The source inspection alone does not prove that these runtime or deployment checks have been executed successfully.

## Learning Outcomes

Building this project demonstrates practical experience with Flask routing, Jinja templates, HTML/CSS/JavaScript integration, form handling, date and phone validation, MySQL connection and SQL operations, Fetch API, JSON request/response handling, sessions, password hashing, CSRF configuration, multilingual UI logic, regular expressions, YouTube embeds, WhatsApp and Maps links, admin dashboards, database-backed content management, deployment configuration, and debugging communication between browser and backend.

## Interview-Relevant Technical Concepts

- HTTP `GET` and `POST` requests
- Flask routes and protected routes
- JSON APIs and REST-style request patterns where applicable
- `fetch()`, `FormData`, `JSON.stringify()`, and `response.json()`
- MySQL `INSERT`, `SELECT`, `UPDATE`, `DELETE`, and parameterized values
- Flask sessions and admin authentication
- Werkzeug password hashing
- Flask-WTF CSRF tokens and CSRF protection configuration
- environment variables and `.env` loading
- JavaScript DOM events and dynamic HTML rendering
- regular expressions for phone, YouTube URL, and Devanagari checks
- YouTube thumbnail and iframe embedding
- WhatsApp URL and `encodeURIComponent()` generation
- Gunicorn WSGI serving and Railway-oriented configuration

## Future Improvements

The following are future work, not current features:

- add automated unit, integration, and browser tests
- validate and whitelist status transitions on the backend
- improve CSRF and rate-limiting strategy for public and API endpoints
- add a real booking calendar with conflict detection
- add email or server-side notification workflows
- add payment support and booking reminders
- add analytics and more detailed reports
- add role-based administrator accounts
- improve chatbot intent handling and multilingual response selection

## Author / Developer

**Apeksha Vishwasrao**

No GitHub or LinkedIn URL is included because no such link could be verified in the current project files or README context.

## Verification Notes

This README was written from the current source tree, including Python modules, all listed templates, static assets, database initialization, deployment files, and JavaScript behavior. The following could not be verified from local source alone:

- whether the previously documented Railway URL is currently online
- whether the production Railway MySQL database is connected
- whether external YouTube, WhatsApp, Google Maps, CDN, and browser interactions work in production
- whether manual tests have already been executed

The repository also contains two current inconsistencies worth knowing about: `/about` points to a missing `about.html`, and `election.html` references a missing `static/css/election.css`. These are documented observations only; application code was not changed.
