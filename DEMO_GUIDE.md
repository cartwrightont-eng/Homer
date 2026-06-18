# System Demo Guide

This guide walks you through demonstrating the accommodation management system to your friends.

## Prerequisites

1. **MySQL Server** running locally
2. **Python 3.7+** installed
3. **Dependencies installed**: `pip install -r requirements.txt`
4. **Environment variables configured** (see config.py)

## Setup (First Time Only)

### 1. Initialize Database and Seed Data

```bash
# Navigate to project directory
cd "c:\Users\ADMIN\OneDrive\Desktop\python projects"

# Initialize database schema
python init_db.py

# Seed demo data (creates sample users, accommodations, amenities, photos, videos)
python unisphere.py
```

**What this does:**
- Creates MySQL database and tables
- Creates 3 sample users: admin, landlord, regular user
- Creates 2 sample accommodations (one public, one student)
- Links sample amenities (mall, restaurant) with distances
- Adds sample photos and videos for virtual tours

### 2. Start the API Server

```bash
python app.py
```

The server runs on `http://localhost:5000`

## Demo Scenarios

### Scenario 1: User Registration & Email Verification

**Demonstrate:** New user signup process

```bash
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "role": "user"
  }'
```

**Response:**
```json
{
  "status": "user created",
  "email_verification_token": "...",
  "message": "Use the token with /verify-email to complete registration"
}
```

**Then verify email:**

```bash
curl -X POST http://localhost:5000/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN_HERE"}'
```

---

### Scenario 2: User Login

**Demonstrate:** Authentication and JWT token generation

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "landlord@example.com",
    "password": "Password123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 2,
    "name": "Landlord User",
    "email": "landlord@example.com",
    "role": "landlord",
    "is_landlord_verified": false
  }
}
```

Save this `access_token` for authenticated requests.

---

### Scenario 3: Landlord Creating a Listing

**Demonstrate:** Landlord posting an accommodation

```bash
curl -X POST http://localhost:5000/accommodations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Luxury Penthouse",
    "description": "5-star penthouse with city views",
    "price": 2500,
    "location": "789 Park Ave, Downtown",
    "latitude": 40.7614,
    "longitude": -73.9776,
    "availability_option": "rent",
    "vacancy_status": "vacant",
    "units_available": 1,
    "is_student_accommodation": false
  }'
```

**Response:**
```json
{
  "status": "accommodation created",
  "id": 3
}
```

---

### Scenario 4: Landlord Uploading Photos

**Demonstrate:** Adding property photos for virtual tour

```bash
curl -X POST http://localhost:5000/accommodations/3/photos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "photo_url": "https://example.com/penthouse-front.jpg",
    "description": "Front view of the penthouse"
  }'
```

Add another photo:

```bash
curl -X POST http://localhost:5000/accommodations/3/photos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "photo_url": "https://example.com/penthouse-interior.jpg",
    "description": "Modern interior with floor-to-ceiling windows"
  }'
```

---

### Scenario 5: Landlord Uploading Virtual Tour Video

**Demonstrate:** Adding video for virtual property tour

```bash
curl -X POST http://localhost:5000/accommodations/3/videos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "video_url": "https://example.com/penthouse-tour.mp4",
    "title": "360 Virtual Tour"
  }'
```

---

### Scenario 6: Landlord Adding Nearby Amenities

**Demonstrate:** Linking malls, restaurants, and facilities

```bash
curl -X POST http://localhost:5000/accommodations/3/amenities \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Downtown Shopping Center",
    "category": "mall",
    "distance_km": 0.3
  }'
```

Add a restaurant:

```bash
curl -X POST http://localhost:5000/accommodations/3/amenities \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Michelin Star Restaurant",
    "category": "restaurant",
    "distance_km": 0.1
  }'
```

---

### Scenario 7: Landlord Updating Vacancy Status

**Demonstrate:** Updating inventory/availability

```bash
curl -X PUT http://localhost:5000/accommodations/3 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "vacancy_status": "occupied",
    "units_available": 0,
    "price": 2750
  }'
```

---

### Scenario 8: Public User Browsing Accommodations

**Demonstrate:** Users searching for properties

Get all public (non-student) accommodations:

```bash
curl http://localhost:5000/accommodations
```

Filter by availability:

```bash
curl "http://localhost:5000/accommodations?availability=rent"
```

Filter by vacancy:

```bash
curl "http://localhost:5000/accommodations?vacancy=vacant"
```

Filter by student accommodations:

```bash
curl "http://localhost:5000/accommodations?student=true"
```

---

### Scenario 9: Viewing Full Accommodation Details

**Demonstrate:** Complete property view with all data

```bash
curl http://localhost:5000/accommodations/1
```

**Response includes:**
```json
{
  "id": 1,
  "name": "Modern Apartment Downtown",
  "description": "...",
  "price": 1500,
  "location": "...",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "owner_id": 2,
  "availability_option": "rent",
  "vacancy_status": "vacant",
  "units_available": 2,
  "is_student_accommodation": false,
  "created_at": "...",
  "amenities": [
    {
      "id": 1,
      "name": "Downtown Shopping Mall",
      "category": "mall",
      "distance_km": 0.5
    },
    {
      "id": 2,
      "name": "Italian Restaurant",
      "category": "restaurant",
      "distance_km": 0.2
    }
  ],
  "photos": [
    {
      "id": 1,
      "photo_url": "https://example.com/photo1.jpg",
      "description": "Front view of apartment",
      "uploaded_at": "..."
    }
  ],
  "videos": [
    {
      "id": 1,
      "video_url": "https://example.com/virtual-tour.mp4",
      "title": "Virtual tour of apartment",
      "uploaded_at": "..."
    }
  ]
}
```

---

### Scenario 10: Admin User Management

**First, get an admin token** (use admin@example.com / Password123!)

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Password123!"
  }'
```

**View all registered users:**

```bash
curl http://localhost:5000/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Search for users:**

```bash
curl "http://localhost:5000/users/search?q=landlord" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Verify a landlord:**

```bash
curl -X POST http://localhost:5000/users/2/verify-landlord \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Suspend a user account:**

```bash
curl -X POST http://localhost:5000/users/3/suspend \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

(Now that user cannot login)

**Reactivate a suspended user:**

```bash
curl -X POST http://localhost:5000/users/3/reactivate \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Delete a user:**

```bash
curl -X POST http://localhost:5000/users/3/delete \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Demo Tools

### Using Postman (Recommended)

1. **Download Postman:** https://www.postman.com/downloads/
2. **Import collection:** (See end of this file)
3. **Set base URL:** `localhost:5000`
4. **Set environment variable** for `access_token` from login response

### Using cURL (Command Line)

All examples above use cURL and can be run directly in PowerShell or Command Prompt.

### Using Insomnia

Similar to Postman - import collection and test endpoints.

---

## Demo Flow (10-15 minutes)

1. **Registration & Verification** (1 min)
   - Show user signup process
   - Explain email verification token

2. **Login** (1 min)
   - Show JWT token generation
   - Explain token usage for authenticated requests

3. **Landlord Features** (5 min)
   - Create new listing
   - Upload multiple photos
   - Upload virtual tour video
   - Add nearby amenities with distances
   - Update vacancy/price

4. **Public Browsing** (2 min)
   - View full accommodation with all details
   - Filter by type, availability, student status
   - Show complete response with nested amenities/photos/videos

5. **Admin Controls** (3 min)
   - Show all users
   - Search for users
   - Verify landlord (approve verification)
   - Suspend/reactivate account
   - Delete user
   - Explain landlord verification flow

---

## Explaining the Architecture

**Talk points:**

- **Role-based access:** Admin, Landlord, User - each with different permissions
- **Landlord verification:** Admins can approve landlords before they go live
- **Account suspension:** Maintain platform safety and quality
- **Media management:** Photos and videos for property showcase
- **Amenity discovery:** Help users find properties near malls, restaurants, etc.
- **Inventory management:** Landlords track available units and vacancy status
- **Dual availability:** Properties can be buy-only, rent-only, or both
- **Student accommodation flag:** Optional filtering for student housing

---

## Questions to Answer

- **Q: Where does the data persist?**
  - A: MySQL database (configured in `config.py`)

- **Q: How are passwords secured?**
  - A: Hashed with werkzeug.security using bcrypt algorithm

- **Q: Can two developers work on this?**
  - A: Yes! See DEBUGGING_GUIDE.md for setup

- **Q: What about real photos/videos?**
  - A: Currently URLs (S3, CDN, etc). Frontend would handle upload.

- **Q: How do we deploy?**
  - A: Ready for production deployment (see README.md)

