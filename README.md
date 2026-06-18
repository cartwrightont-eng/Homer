# University Accommodation Finder

A multi-role accommodation management system for university students, landlords, and schools.

## Features

- **Multi-role authentication**: Admin, school, landlord, user
- **Role-based access control**: Different endpoints for different user roles
- **Email verification**: Users must verify email before login
- **Password reset**: Secure password recovery flow
- **Accommodation management**: Link accommodations to universities by distance
- **Buy/rent options**: Support for both purchase and rental properties
- **MySQL backend**: Scalable persistence layer

## Tech Stack

- Flask (Python web framework)
- MySQL (relational database)
- JWT (authentication)
- Werkzeug (password hashing)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/university-accommodation.git
cd university-accommodation
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set MySQL environment variables (PowerShell)

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your-db-password"
$env:MYSQL_DATABASE="university_app"
$env:JWT_SECRET_KEY="your-jwt-secret"
```

### 5. Initialize the database

```bash
python init_db.py
```

### 6. Create an admin account

```bash
python create_admin.py
```

### 7. Start the API server

```bash
python app.py
```

The server will run on `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get JWT token
- `POST /verify-email` - Verify email with token
- `POST /request-password-reset` - Request password reset
- `POST /reset-password` - Reset password with token

### Admin
- `POST /register-admin` - Create admin user (admin only)
- `GET /users` - List all users (admin only)

### User Profile
- `GET /users/<id>` - Get user details
- `GET /profile` - Get current user profile

### Universities
- `GET /universities` - List all universities
- `POST /universities` - Create university (school/admin)

### Accommodations
- `GET /accommodations` - List all accommodations
- `GET /universities/<id>/accommodations` - List accommodations by university
- `POST /accommodations` - Create accommodation (landlord/admin)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | localhost | MySQL server host |
| `MYSQL_PORT` | 3306 | MySQL server port |
| `MYSQL_USER` | root | MySQL username |
| `MYSQL_PASSWORD` | (empty) | MySQL password |
| `MYSQL_DATABASE` | university_app | Database name |
| `JWT_SECRET_KEY` | change-this-secret | JWT signing secret |
| `JWT_EXPIRES_HOURS` | 24 | JWT token expiry in hours |
| `EMAIL_TOKEN_EXPIRES_HOURS` | 24 | Email verification token expiry |
| `PASSWORD_RESET_EXPIRES_HOURS` | 2 | Password reset token expiry |

## Project Structure

```
.
├── app.py                    # Flask API
├── models.py                 # Database models and business logic
├── database.py               # Database connection
├── config.py                 # Configuration
├── init_db.py                # Database initialization
├── create_admin.py           # Admin user creation utility
├── unisphere.py              # Test/seed script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Testing

Run the test script to seed sample data:

```bash
python unisphere.py
```

## Database Schema

### users
- id, name, email, password (hashed), role, email_verified

### universities
- id, name, description, location, created_by (user_id)

### accommodations
- id, name, description, price, location, university_id, owner_id, distance_km, is_university_owned, availability_option

### user_tokens
- id, user_id, token, token_type, expires_at, used

## User Roles

- **admin**: Full system access, can create users and manage all resources
- **school**: Can create universities and manage school-owned accommodations
- **landlord**: Can create and manage accommodations
- **user**: Standard user, can view accommodations and universities

## Next Steps

- Email sending integration
- Frontend UI (React/Vue)
- Payment processing for bookings
- Notifications system
- Analytics dashboard
# Homerr
