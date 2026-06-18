# Debugging & Development Guide

This guide explains how to set up the project for development and debugging with two (or more) developers.

## 1. Local Development Setup

Each developer should follow these steps once:

### Step 1: Clone/Download Repository

```bash
# Clone from Git
git clone <repository-url>
cd python projects

# OR if not using Git yet, just open the folder
```

### Step 2: Create Python Virtual Environment

**Windows PowerShell:**

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get "cannot be loaded" error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try activating again
```

**Windows Command Prompt:**

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Current dependencies:**
- flask
- flask-jwt-extended
- mysql-connector-python
- werkzeug (included with Flask)

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=university_app

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRES=1440

# Token Expiry (hours)
EMAIL_TOKEN_EXPIRES_HOURS=24
PASSWORD_RESET_EXPIRES_HOURS=2

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
```

Or set these manually:

```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DATABASE="university_app"
$env:JWT_SECRET_KEY="your-super-secret-key"
$env:FLASK_ENV="development"
$env:FLASK_DEBUG="1"
```

### Step 5: Initialize Database

```bash
python init_db.py
```

This creates the MySQL database and schema.

### Step 6: Seed Demo Data

```bash
python unisphere.py
```

This populates the database with test data for development.

---

## 2. Running & Debugging

### Start the Server

```bash
python app.py
```

Output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Note:** Flask debug mode is enabled (`FLASK_DEBUG=1`), so:
- The server auto-restarts when you save code changes
- Full error traceback shown in terminal and browser

### Testing Endpoints

**Option A: Use cURL (Command Line)**

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Password123!"}'
```

**Option B: Use Postman**

1. Download: https://www.postman.com/downloads/
2. Create new request
3. Set method to POST
4. Set URL to `http://localhost:5000/login`
5. Body → raw → JSON:
```json
{
  "email": "admin@example.com",
  "password": "Password123!"
}
```

**Option C: Use VS Code REST Client Extension**

1. Install: "REST Client" by Huachao Guo
2. Create file `requests.http`:

```http
### Login
POST http://localhost:5000/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "Password123!"
}

### Get all users
GET http://localhost:5000/users
Authorization: Bearer YOUR_TOKEN_HERE
```

3. Click "Send Request" above each request

---

## 3. Code-Level Debugging

### Enable Breakpoints (VS Code)

1. **Install Python extension** (if not already)
   - Ctrl+Shift+X → search "Python" → install Microsoft's Python extension

2. **Create `.vscode/launch.json`:**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "app.py",
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1"
      },
      "args": ["run", "--no-debugger"],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

3. **Set breakpoints:**
   - Click left of line number to add breakpoint (red dot)
   - Press F5 to start debugging
   - Make a request to hit the breakpoint
   - Use Debug console to inspect variables

4. **Debug commands:**
   - F10: Step over
   - F11: Step into
   - Shift+F11: Step out
   - F5: Continue

### Example: Debug a Login Request

**In models.py, add breakpoint on line ~70 (authenticate_user):**

```python
def authenticate_user(email, password):
    user = get_user_by_email(email)  # <- Add breakpoint here
    if not user:
        return None
    ...
```

**Then:**

```powershell
# Terminal 1: Start debugger
F5

# Terminal 2: Make login request
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Password123!"}'
```

**The debugger stops at the breakpoint!** Inspect variables in the panel.

---

## 4. Collaboration Workflow

### Setup Git (Recommended)

1. **Initialize repository:**

```bash
git init
git add .
git commit -m "Initial commit"
git branch develop
```

2. **Create feature branches:**

Developer 1:
```bash
git checkout -b feature/admin-dashboard
# ... make changes ...
git commit -m "Add admin dashboard endpoint"
git push origin feature/admin-dashboard
```

Developer 2:
```bash
git checkout -b feature/payment-integration
# ... make changes ...
git commit -m "Add Stripe integration"
git push origin feature/payment-integration
```

3. **Merge to main:**

```bash
git checkout main
git merge feature/admin-dashboard
git merge feature/payment-integration
```

### Without Git

**Option 1: Share via OneDrive (already set up)**
- Keep project in `c:\Users\ADMIN\OneDrive\Desktop\python projects`
- Changes auto-sync between developers

**Option 2: Use VS Code Live Share**
1. Install Live Share extension
2. Press Ctrl+Shift+X → search "Live Share"
3. Click "Share" button (bottom-right)
4. Send link to collaborator
5. Real-time collaborative coding!

---

## 5. Database Debugging

### View Database in MySQL Workbench

1. **Download MySQL Workbench:** https://dev.mysql.com/downloads/workbench/
2. **Connect:**
   - Hostname: 127.0.0.1
   - Username: root
   - Password: your_password
   - Database: university_app
3. **View tables:**
   - Double-click "university_app"
   - See all tables: users, accommodations, amenities, etc.
4. **Run queries:**

```sql
-- View all users
SELECT * FROM users;

-- View accommodations with owner details
SELECT a.id, a.name, a.price, u.name as landlord_name 
FROM accommodations a 
JOIN users u ON a.owner_id = u.id;

-- View amenities for specific accommodation
SELECT am.name, am.category, acam.distance_km
FROM amenities am
JOIN accommodation_amenities acam ON am.id = acam.amenity_id
WHERE acam.accommodation_id = 1;

-- Count photos and videos
SELECT 
  accommodation_id,
  COUNT(CASE WHEN id IS NOT NULL THEN 1 END) as photo_count
FROM photos
GROUP BY accommodation_id;
```

### View Logs

**Flask logs show all requests:**

```
127.0.0.1 - - [13/Jun/2026 14:30:45] "POST /login HTTP/1.1" 200 -
127.0.0.1 - - [13/Jun/2026 14:30:50] "GET /users HTTP/1.1" 403 -
```

**Errors show full traceback:**

```
Traceback (most recent call last):
  File "app.py", line 150, in login
    user = authenticate_user(...)
  File "models.py", line 70, in authenticate_user
    ...
```

---

## 6. Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Fix:**
```bash
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Can't connect to MySQL server"

**Fix:**
```bash
# Check MySQL is running
# Windows: Services → Look for MySQL service

# Check credentials
echo $env:MYSQL_USER
echo $env:MYSQL_PASSWORD

# Test connection
mysql -h localhost -u root -p
```

### Issue: "Address already in use (port 5000)"

**Fix:**
```bash
# Kill process on port 5000
# PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process -Force

# Or just change port in app.py:
# app.run(debug=True, port=5001)
```

### Issue: "Permission denied on .venv/Scripts/Activate.ps1"

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

---

## 7. Making Code Changes

### File Structure for Reference

```
python projects/
├── app.py              # Flask API routes (main file)
├── models.py           # Database functions & business logic
├── database.py         # Connection factory
├── init_db.py          # Schema initialization
├── config.py           # Configuration & environment variables
├── unisphere.py        # Test/seed data script
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (create this)
├── .gitignore          # Git ignore rules
├── DEMO_GUIDE.md       # This file!
└── DEBUGGING_GUIDE.md  # Debugging guide
```

### Adding a New Endpoint

**Step 1: Add database function in models.py**

```python
def get_user_stats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN role='user' THEN 1 END) as total_users,
            COUNT(CASE WHEN role='landlord' THEN 1 END) as total_landlords,
            COUNT(CASE WHEN is_suspended=TRUE THEN 1 END) as suspended_users
        FROM users
    """)
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    return stats
```

**Step 2: Import in app.py**

```python
from models import (
    # ... existing imports ...
    get_user_stats,
)
```

**Step 3: Add route in app.py**

```python
@app.route('/stats', methods=['GET'])
@role_required('admin')
def get_stats():
    stats = get_user_stats()
    return jsonify(stats)
```

**Step 4: Test**

```bash
curl http://localhost:5000/stats \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 8. Running Tests

### Create Test File (test_app.py)

```python
import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_login_success(self):
        response = self.client.post('/login', json={
            'email': 'admin@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.get_json())
    
    def test_login_failure(self):
        response = self.client.post('/login', json={
            'email': 'wrong@email.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
```

**Run tests:**

```bash
python -m unittest test_app.py
```

---

## 9. Summary: Full Development Workflow

```bash
# 1. Get setup (first time)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python init_db.py
python unisphere.py

# 2. Start development
python app.py
# Server running on http://localhost:5000

# 3. Make code changes
# Edit app.py, models.py, etc.
# Server auto-restarts on save

# 4. Test with cURL/Postman
curl http://localhost:5000/accommodations

# 5. Debug with breakpoints
# F5 to start debugger, click line numbers to add breakpoints

# 6. Commit changes (if using Git)
git add .
git commit -m "Added feature X"
git push
```

---

## 10. Getting Help

**Documentation files in project:**
- `README.md` - Project overview
- `DEMO_GUIDE.md` - How to demo the system
- `DEBUGGING_GUIDE.md` - This file!

**Flask documentation:** https://flask.palletsprojects.com/

**JWT tokens:** https://flask-jwt-extended.readthedocs.io/

**MySQL:** https://dev.mysql.com/doc/

