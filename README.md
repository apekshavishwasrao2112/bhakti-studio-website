# Bhakti Studio App

## Developed By

Developed by Apeksha Ramesh Vishwasrao

## Project Status

This project has been successfully deployed on Railway and is ready for live use in a production environment.

Live Demo: https://bhakti-studio-website-production.up.railway.app/

## Professional Project Overview

Bhakti Studio App is a modern Flask-based web application designed to streamline studio booking, customer inquiry handling, and administrative management for a creative studio environment. The system combines a user-friendly frontend, secure admin access, and database-backed booking management to provide a reliable and professional solution for service-based business operations.

This project is built to support the core business flow of a studio that offers music, production, announcements, and related creative services. It allows clients to submit booking requests quickly, while administrators can review, confirm, reject, and complete those requests through an efficient dashboard.

---

## Project Objective

The main objective of this application is to:

- simplify the booking and service request process for clients
- provide an organized digital workspace for studio administrators
- improve response time and communication efficiency
- reduce manual work through an automated booking management system
- create a scalable platform that can be further enhanced with payment, analytics, and CRM features

---

## Key Features

### 1. Client Booking System
The application provides a dedicated booking form where clients can enter:

- full name
- mobile number
- selected service
- preferred booking date

The system performs validation to ensure the submitted details are complete and correctly formatted before storing the booking request.

### 2. Admin Dashboard
A secure admin portal enables authorized users to:

- view all booking records
- monitor booking status
- confirm or reject requests
- mark requests as completed
- remove outdated or unnecessary bookings

### 3. Secure Authentication
The admin login process includes:

- password hashing
- session-based authentication
- brute-force protection
- protected routes for admin-only pages

### 4. Database Integration
The application uses MySQL to store essential data such as:

- booking records
- admin credentials
- chat history support

This creates a stable backend for managing business operations.

### 5. Responsive Web Interface
The frontend consists of multiple HTML templates and CSS/JavaScript assets for a visually appealing experience. The interface is designed to support service presentation, booking actions, and admin management workflows.

---

## Technology Stack

The project is developed using the following technologies:

- Python 3
- Flask Framework
- MySQL Database
- Flask-WTF for form security
- Werkzeug for password hashing and security utilities
- Python-dotenv for environment configuration
- HTML, CSS, and JavaScript for frontend templates
- Gunicorn for production deployment readiness

---

## Project Structure

The main project files and folders are organized as follows:

- app.py - Core Flask application with routes, booking logic, and admin controls
- database.py - Database connection, table creation, and admin setup
- requirements.txt - Python dependencies for the project
- Procfile - Deployment configuration for hosting platforms
- templates/ - HTML files for the user interface and admin dashboard
- static/ - CSS, JavaScript, images, and media assets
- .env - Local environment variables for configuration

---

## Application Workflow

### Client Side
1. A visitor opens the platform.
2. The user accesses the booking section.
3. The booking form is filled with personal and service details.
4. The request is submitted and stored in the database.
5. The admin reviews the request and updates its status.

### Admin Side
1. The administrator logs into the secure admin portal.
2. The dashboard displays current booking statistics.
3. Admin can confirm, reject, or complete a booking.
4. The booking status is updated in real time through the backend.
5. Relevant actions are managed efficiently through the admin interface.

---

## Database Design

The application uses the following core database entities:

- bookings: stores client booking information and current status
- admin: stores secure login credentials for the admin panel
- chat_history: supports chatbot-related records and interaction logging

This structure allows the project to grow into a more advanced studio management system in the future.

---

## Security and Reliability

The current version includes important security practices such as:

- secure session handling
- hashed passwords for admin users
- protection against repeated failed login attempts
- form validation for user input
- restricted admin access for sensitive pages

These features improve the reliability of the system and make the application more suitable for real-world use.

---

## Installation and Setup

### Prerequisites
Make sure the following are installed on your system:

- Python 3.10 or higher
- pip
- MySQL Server
- Virtual environment (recommended)

### Setup Instructions

1. Clone or download the project to your local machine.
2. Navigate to the project folder.
3. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Configure your environment variables in a .env file:

```env
SECRET_KEY=your_secret_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=bhakti_studio
DB_PORT=3306
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
```

6. Initialize the database:

```bash
python app.py
```

On startup, the application will create the required database tables automatically.

---

## Running the Application

Start the Flask application using:

```bash
python app.py
```

Then open the local server in your browser. The main booking and studio interface will be available through the application routes.

---

## Deployment Guidance

This application is currently deployed on Railway.

### Railway Deployment Notes

The project is configured to run as a Python Flask application on Railway with the following deployment considerations:

1. Set all required environment variables in the Railway dashboard.
2. Use the MySQL database connection details provided by the hosting environment.
3. Ensure the application starts through the Procfile using Gunicorn.
4. Keep the SECRET_KEY, DB credentials, and admin login credentials secure in Railway environment settings.

### Recommended Railway Environment Variables

- SECRET_KEY
- DB_HOST
- DB_USER
- DB_PASSWORD
- DB_NAME
- DB_PORT
- ADMIN_USERNAME
- ADMIN_PASSWORD

This setup allows the application to run smoothly in the live Railway environment.

---

## Future Enhancement Opportunities

This project has excellent potential for future growth. Suggested improvements include:

- online payment integration
- automated WhatsApp/SMS notifications
- appointment reminders
- client history and reporting
- analytics dashboard for bookings and usage trends
- multi-user role management for staff and managers
- mobile-first optimization and improved UI/UX

---

## Conclusion

Bhakti Studio App is a professional and practical web solution for managing studio bookings and administrative tasks in an organized and efficient manner. It combines secure backend logic, a smooth user experience, and a scalable architecture that can be expanded as the studio grows.

This project demonstrates a strong foundation in Python Flask development, database integration, secure authentication, and web-based business workflow management.

---

Developed by Apeksha Ramesh Vishwasrao
