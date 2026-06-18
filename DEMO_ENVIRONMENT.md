# Where to Perform the Demo - Demo Environment Guide

This guide explains where on your device you can demonstrate the system and what tools are available.

## Table of Contents
1. [Demo Locations & Tools](#demo-locations--tools)
2. [Setting Up Each Environment](#setting-up-each-environment)
3. [Step-by-Step Demo Process](#step-by-step-demo-process)
4. [Live Demo Checklist](#live-demo-checklist)

---

## Demo Locations & Tools

You have **3 main options** for where to demonstrate the system. Choose based on your audience and comfort level:

### Option 1: PowerShell/Terminal (Command Line)
**Where:** Windows PowerShell or Command Prompt  
**Best for:** Technical audience, pure functionality demo  
**Tool:** cURL (command-line HTTP client)  

**Pros:**
- Simple, no extra software needed
- Pure API demonstration
- Shows backend power
- Easy to reproduce

**Cons:**
- Not visually polished
- Requires typing commands
- Less impressive for non-technical audience

### Option 2: Postman (Recommended for Most Demos)
**Where:** Postman application on your computer  
**Best for:** Professional demos, non-technical audience, saved workflows  
**Tool:** Postman desktop app (free)  

**Pros:**
- Clean, organized interface
- Save and reuse requests
- Pre-set headers and auth tokens
- Good visualization
- Easy to show request/response
- Can save entire collection

**Cons:**
- Requires installing Postman
- Slightly more setup time

### Option 3: VS Code REST Client Extension
**Where:** VS Code editor (right-click on file)  
**Best for:** Developer demo, code-alongside-demo  
**Tool:** REST Client extension for VS Code  

**Pros:**
- Integrated with code editor
- See API code while testing
- Can show code changes in real-time
- Developer-friendly
- Lightweight

**Cons:**
- Only useful if you're showing code
- Not as polished as Postman

### Option 4: Browser (Web Interface - Future)
**Where:** http://localhost:3000 (when frontend is built)  
**Best for:** End-user demo, most polished  
**Tool:** React/Vue frontend application  

**Status:** ⏳ Not yet built - coming when frontend developer joins

---

## Setting Up Each Environment

### Environment 1: PowerShell Terminal

**Location on your device:**
```
Windows Start Menu → PowerShell (or Command Prompt)
```

**Setup:**
```powershell
# Navigate to project
cd "c:\Users\ADMIN\OneDrive\Desktop\python projects"

# Start the API
python app.py

# Keep terminal open - API runs here
# Use another terminal window for cURL commands
```

**Making requests:**
```powershell
# In a SECOND terminal window:

# Login to get token
curl -X POST http://localhost:5000/login `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"admin@example.com\",\"password\":\"Password123!\"}'
```

**Pros:** Lightweight, no extra software  
**Cons:** Less visually appealing

---

### Environment 2: Postman (Best Option)

**Installation:**
1. Go to https://www.postman.com/downloads/
2. Download Postman for Windows
3. Install and launch

**Location on your device:**
```
Windows Start Menu → Postman
```

**Setup (First Time):**

1. **Create a new collection:**
   - Click "New" → "Collection"
   - Name it "Housing Demo"

2. **Set up environment variables:**
   - Click "Environments" (gear icon)
   - Create "Local Development"
   - Add variables:
     ```
     base_url = http://localhost:5000
     admin_token = (leave blank - fill after login)
     landlord_token = (leave blank)
     user_token = (leave blank)
     ```

3. **Create requests folder:**
   - Right-click collection → "Add Folder"
   - Name: "Authentication"
   - Create these requests:

**Request 1: Admin Login**
```
Method: POST
URL: {{base_url}}/login
Headers: 
  Content-Type: application/json
Body (raw JSON):
{
  "email": "admin@example.com",
  "password": "Password123!"
}

POST-request script (auto-save token):
var jsonData = pm.response.json();
pm.environment.set("admin_token", jsonData.access_token);
```

**Request 2: View All Users**
```
Method: GET
URL: {{base_url}}/users
Headers:
  Authorization: Bearer {{admin_token}}
  Content-Type: application/json
```

**Request 3: View Analytics Dashboard**
```
Method: GET
URL: {{base_url}}/admin/analytics
Headers:
  Authorization: Bearer {{admin_token}}
```

**Request 4: View All Listings**
```
Method: GET
URL: {{base_url}}/admin/listings
Headers:
  Authorization: Bearer {{admin_token}}
```

4. **Save collection:**
   - Click "Save" button
   - Export as JSON for sharing with co-developer

**Pros:**  
- Professional appearance
- Organized and reusable
- Easy to switch between requests
- Automatic token management

---

### Environment 3: VS Code REST Client

**Installation:**
1. Open VS Code
2. Extensions (Ctrl+Shift+X)
3. Search "REST Client"
4. Install by Huachao Guo (4M+ downloads)

**Create demo file:**

File: `demo-requests.http`

```http
### Variables
@baseUrl = http://localhost:5000
@admin_token = 
@landlord_token = 

### 1. Admin Login
POST {{baseUrl}}/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "Password123!"
}

### 2. View All Users
GET {{baseUrl}}/users
Authorization: Bearer {{admin_token}}

### 3. View Analytics
GET {{baseUrl}}/admin/analytics
Authorization: Bearer {{admin_token}}

### 4. View All Listings
GET {{baseUrl}}/admin/listings
Authorization: Bearer {{admin_token}}

### 5. View Pending Approvals
GET {{baseUrl}}/admin/listings?status=pending
Authorization: Bearer {{admin_token}}

### 6. Approve a Listing
POST {{baseUrl}}/admin/listings/1/approve
Authorization: Bearer {{admin_token}}
Content-Type: application/json

### 7. Reject a Listing
POST {{baseUrl}}/admin/listings/2/reject
Authorization: Bearer {{admin_token}}
Content-Type: application/json

{
  "reason": "Photos violate our guidelines"
}

### 8. Mark Listing as Suspicious
POST {{baseUrl}}/admin/listings/3/mark-suspicious
Authorization: Bearer {{admin_token}}
Content-Type: application/json

{
  "reason": "Unusual pricing pattern detected"
}

### 9. View Reports
GET {{baseUrl}}/admin/reports
Authorization: Bearer {{admin_token}}

### 10. View Home Page Content
GET {{baseUrl}}/homepage/content
```

**Usage:**
- Click "Send Request" above each request
- Response appears in right panel
- Copy token from login response into `@admin_token` variable

---

## Step-by-Step Demo Process

### Before the Demo

**Preparation (10 minutes before):**

```bash
# Terminal 1: Start API server
cd "c:\Users\ADMIN\OneDrive\Desktop\python projects"
python init_db.py
python unisphere.py
python app.py

# Keep running - shows "Running on http://127.0.0.1:5000"

# Terminal 2: Optionally open MySQL Workbench to show database
# To show database structure if asked
```

**Check before starting:**
- [ ] API is running on http://localhost:5000
- [ ] MySQL database is up
- [ ] Postman (or cURL) is ready
- [ ] Sample data is loaded (from unisphere.py)
- [ ] You have admin credentials (admin@example.com / Password123!)

### Demo Flow (15-20 minutes)

**Part 1: Authentication (2 min)**

"Let me show you how the system authenticates users."

1. Show login endpoint in Postman
2. Login with admin credentials
3. Show JWT token in response
4. Explain token is sent in Authorization header for subsequent requests

**Part 2: User Management (3 min)**

"Admins can view and manage all users on the platform."

1. Show `/users` endpoint - view all registered users
2. Show `/users/search?q=landlord` - search users
3. Explain verification, suspension, deletion

**Part 3: Analytics Dashboard (2 min)**

"Here's a complete overview of the platform at a glance."

1. Show `/admin/analytics` endpoint
2. Point out:
   - Total users
   - Total landlords
   - Total listings
   - Available vs occupied properties
   - Student vs public listings
   - Pending approvals count
   - Suspicious listings

**Part 4: Listing Management (3 min)**

"Admins can approve, review, and manage all property listings."

1. Show `/admin/listings` - all listings with status
2. Explain approval workflow: pending → approved/rejected
3. Show how to mark listings as suspicious
4. Show rejection with reason

**Part 5: Reports & Moderation (2 min)**

"Users can report problematic listings or users."

1. Show `/admin/reports` - all reports
2. Show report details (who reported, why, etc.)
3. Show resolution process

**Part 6: Content Management (2 min)**

"Admins can manage platform-wide announcements and content."

1. Show announcements (alerts, maintenance notices)
2. Show homepage content management
3. Explain how this appears to users

**Part 7: Q&A (3 min)**

Answer questions about:
- Security (passwords hashed, tokens signed)
- Scalability (MySQL, SQL injection safe)
- Deployment (ready for production)
- Next steps (frontend, payment, etc.)

---

## Live Demo Checklist

Before showing friends, verify:

### System Running
- [ ] MySQL running (Services on Windows)
- [ ] `python app.py` showing "Running on http://127.0.0.1:5000"
- [ ] No error messages in terminal

### Credentials Ready
- [ ] Admin credentials: admin@example.com / Password123!
- [ ] Landlord credentials: landlord@example.com / Password123!
- [ ] Test user: user@example.com / Password123!

### Demo Tool Ready
- [ ] Postman open with collection loaded
- [ ] OR VS Code with REST Client file ready
- [ ] OR PowerShell with cURL commands prepared

### Data Loaded
- [ ] Ran `python unisphere.py` to seed test data
- [ ] Can show:
  - At least 1 admin, 1 landlord, 1 user
  - At least 2 listings (1 public, 1 student)
  - Amenities linked to listings
  - Photos and videos

### Browser Ready (Optional)
- [ ] MySQL Workbench open (to show database if asked)
- [ ] VS Code open showing models.py (to explain code if asked)

### Timing
- [ ] Have 15-20 minute slot prepared
- [ ] Practice demo once beforehand
- [ ] Know your transitions between parts

---

## If Something Goes Wrong

### "Connection refused" error

**Fix:**
```bash
# Make sure API is running
python app.py

# If port 5000 is in use:
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process -Force
# Then restart app
```

### "Database connection error"

**Fix:**
```bash
# Verify MySQL is running
# Windows Services → look for MySQL service
# Or check if mysqld process is running

# Check config.py has correct credentials
cat config.py
```

### "Invalid token" in response

**Fix:**
```
This means you're using an old token. Just:
1. Run login request again
2. Copy new token from response
3. Paste into Authorization header
```

### Demo is slow

**Fix:**
```
This is likely MySQL query time. Show your friends:
- "Real-world systems query millions of records"
- "Our queries are optimized with SQL indexes"
- "In production, we'd use caching layer"
```

---

## Recommended Demo Setup

**For clearest demo to non-technical friends:**

1. **Use Postman** - most professional appearance
2. **Have browser open** to https://DEMO_GUIDE.md (your documentation)
3. **Have VS Code open** showing database structure if asked
4. **Use 2 monitors/screens** if possible:
   - Screen 1: Postman (where requests happen)
   - Screen 2: Browser (documentation) + VS Code (code)
5. **Pre-load requests** in Postman collection (don't type them live)
6. **Save tokens** in environment variables (auto-filling)

**For technical co-developer demo:**

1. **Use VS Code REST Client** - shows code + API testing together
2. **Have terminal open** showing API logs
3. **Have MySQL Workbench open** to show database structure
4. **Walk through code** in models.py and app.py
5. **Explain architecture** - separation of layers

---

## Folder Structure on Your Device

Your project is located at:
```
c:\Users\ADMIN\OneDrive\Desktop\python projects\

Key files:
├── app.py                    ← API endpoints (what Postman calls)
├── models.py                 ← Business logic
├── init_db.py               ← Database setup
├── unisphere.py             ← Seed data
├── DEMO_GUIDE.md            ← Detailed scenarios
├── DEBUGGING_GUIDE.md       ← Developer setup
├── DEMO_ENVIRONMENT.md      ← This file!
└── create_admin_account.py  ← Create admin account
```

---

## Summary: Where to Demo From

| Tool | Best For | Location | Setup Time |
|------|----------|----------|-----------|
| **Postman** | General demos | Install from postman.com | 10 min |
| **PowerShell + cURL** | Technical audience | Windows Start → PowerShell | 2 min |
| **VS Code REST** | Developer audience | VS Code Extension | 5 min |
| **Web UI** | End users | Coming soon! | N/A |

**Recommendation:** Start with **Postman** for your friends' demo - it's professional, organized, and requires minimal setup.

---

## Next Steps After Demo

1. **Save Postman collection** (File → Export) for sharing
2. **Share credentials** with co-developer securely
3. **Discuss next features** based on feedback
4. **Plan deployment** (AWS/Heroku)
5. **Build frontend** (React/Vue - separate project)

Good luck with your demo! 🚀

