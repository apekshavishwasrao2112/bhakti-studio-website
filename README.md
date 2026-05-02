# Bhakti Studio App

A secure, production-ready Flask web application for studio booking and management with PostgreSQL backend.

## Security Features

- Secure admin authentication with hashed passwords
- Brute-force protection (5 attempts lockout)
- CSRF protection on forms
- Secure session management
- Input validation and sanitization
- PostgreSQL database with proper migrations

## Local Development

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (SQLite for development)
python -c "from database import init; init()"

# Run the application
python app.py
```

### Testing
```bash
# Test admin login
curl -X POST http://localhost:5000/bhakti-secure-admin-portal-84729/login \
  -d "username=admin&password=admin123"

# Test booking
curl -X POST http://localhost:5000/booking \
  -d "name=Test&phone=123&service=Test&booking_date=2026-01-01"
```

## Production Deployment (Railway)

### Prerequisites
```bash
npm install -g @railway/cli
railway login
```

### Deploy
```bash
# Use production requirements
cp requirements-production.txt requirements.txt

# Deploy to Railway
railway init
railway variables set SECRET_KEY=your-super-secure-secret-key-here
railway variables set DATABASE_URL=postgresql://user:pass@host:port/db
railway up
```

### Environment Variables
- `SECRET_KEY`: Random secure key (generate with `openssl rand -hex 32`)
- `DATABASE_URL`: Railway PostgreSQL connection string
- `PORT`: Automatically set by Railway

## Database

- **Development:** SQLite (bhakti_studio.db)
- **Production:** PostgreSQL (Railway)

Tables:
- `admin`: User authentication
- `bookings`: Client bookings
- `chat_history`: Chatbot interactions

## Project Structure

- `app.py` — Main Flask application
- `database.py` — Database connection and initialization
- `wsgi.py` — Gunicorn entry point
- `requirements.txt` — Python dependencies
- `Procfile` — Railway deployment configuration
- `templates/` — Jinja2 templates
- `static/` — CSS, JS, images
- `.env` — Environment variables (local)
- Book slot without login
- Enter name, mobile, slot, date, service
- Submit as pending
- Admin accepts/rejects
- Client notified

### Payment Status
- Phase 1: offline payment (cash/UPI), admin updates status
- Phase 2: integrate partial online payment (future)

## Running the Project

### Frontend
Open `index.html` directly in browser, or use VS Code Live Server.

### Backend (DB initialization)
1. Install MySQL and create database `bhakti_studio`.
2. Install Python package:
   - `pip install mysql-connector-python`
3. Run:
   - `python -c "import database; database.init()"`

This creates `chat_history` table used by backend conversation logging.

## Next Steps (Recommended)
1. Add backend server (Flask/FastAPI) to serve booking APIs.
2. Add admin login + authentication.
3. Build booking form and database tables (`bookings`, `clients`, `payments`).
4. Wire frontend to backend endpoints.

---

This README replaces the previous layout notes and describes the current working code and system design.