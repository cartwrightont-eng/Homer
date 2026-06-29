
import bcrypt
from database import db_cursor

# ─────────────────────────────────────────────
#  EXISTING HELPERS (unchanged)
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ─────────────────────────────────────────────
#  USERS
# ─────────────────────────────────────────────

def create_user(name, email, password, role="user"):
    """role: user | landlord | service_provider | admin"""
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO users (name, email, password, role, email_verified)
            VALUES (%s, %s, %s, %s, FALSE)
            RETURNING id, name, email, role
        """, (name, email, hash_password(password), role))
        return cur.fetchone()

def authenticate_user(email, password):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT id, name, email, role, password, email_verified
            FROM users WHERE email = %s
        """, (email,))
        user = cur.fetchone()
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    # if not user["email_verified"]:  # re-enable post-launch
    return user

def get_user_by_id(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT id, name, email, role, email_verified, phone,
                   profile_photo_url, bio, review_score, created_at
            FROM users WHERE id = %s
        """, (user_id,))
        return cur.fetchone()

def update_user_profile(user_id, data: dict):
    allowed = {"name", "phone", "bio", "profile_photo_url"}
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        return None
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    with db_cursor(commit=True) as (conn, cur):
        cur.execute(
            f"UPDATE users SET {set_clause} WHERE id = %s RETURNING id",
            list(fields.values()) + [user_id]
        )
        return cur.fetchone()


# ─────────────────────────────────────────────
#  ACCOMMODATIONS  (existing, lightly extended)
# ─────────────────────────────────────────────

def get_all_accommodations(filters=None):
    filters = filters or {}
    query = """
        SELECT a.*, u.name AS landlord_name, NULL AS landlord_phone,
               NULL AS landlord_photo,
               NULL AS landlord_review_score,
               COALESCE(
                   (SELECT AVG(r.rating) FROM reviews r
                    WHERE r.target_id = a.id AND r.target_type = 'accommodation'),
                   0
               ) AS avg_rating,
               COALESCE(
                   (SELECT COUNT(*) FROM reviews r
                    WHERE r.target_id = a.id AND r.target_type = 'accommodation'),
                   0
               ) AS review_count
        FROM accommodations a
        JOIN users u ON a.owner_id = u.id
        WHERE a.approval_status = 'approved'
    """
    params = []
    # listing_type column not in DB yet
    # if filters.get("listing_type"):
    #     query += " AND a.listing_type = %s"
    #     params.append(filters["listing_type"])
    if filters.get("min_price"):
        query += " AND a.price >= %s"
        params.append(filters["min_price"])
    if filters.get("max_price"):
        query += " AND a.price <= %s"
        params.append(filters["max_price"])
    if filters.get("location"):
        query += " AND a.location ILIKE %s"
        params.append(f"%{filters['location']}%")
    query += " ORDER BY u.review_score DESC NULLS LAST, a.created_at DESC"
    with db_cursor() as (conn, cur):
        cur.execute(query, params)
        return cur.fetchall()

def get_accommodation_by_id(acc_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT a.*, u.name AS landlord_name, NULL AS landlord_phone,
                   NULL AS landlord_photo,
                   NULL AS landlord_review_score,
                   u.email AS landlord_email,
                   COALESCE(
                       (SELECT AVG(r.rating) FROM reviews r
                        WHERE r.target_id = a.id AND r.target_type = 'accommodation'),
                       0
                   ) AS avg_rating
            FROM accommodations a
            JOIN users u ON a.owner_id = u.id
            WHERE a.id = %s
        """, (acc_id,))
        acc = cur.fetchone()
        if acc:
            cur.execute("SELECT * FROM accommodation_photos WHERE accommodation_id = %s ORDER BY sort_order", (acc_id,))
            acc["photos"] = cur.fetchall()
            cur.execute("SELECT * FROM accommodation_amenities WHERE accommodation_id = %s", (acc_id,))
            acc["amenities"] = cur.fetchall()
        return acc

def get_landlord_accommodations(landlord_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT a.*,
                   COALESCE(
                       (SELECT AVG(r.rating) FROM reviews r
                        WHERE r.target_id = a.id AND r.target_type = 'accommodation'),
                       0
                   ) AS avg_rating,
                   (SELECT COUNT(*) FROM tenant_applications ta
                    WHERE ta.accommodation_id = a.id AND ta.status = 'pending') AS pending_applications
            FROM accommodations a
            WHERE a.owner_id = %s
            ORDER BY a.created_at DESC
        """, (landlord_id,))
        return cur.fetchall()

def create_accommodation(landlord_id, data: dict):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO accommodations (
                owner_id, name, description, price, location,
                latitude, longitude, vacancy_status, approval_status
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,'available','pending')
            RETURNING id, name, description, price, location, latitude, longitude, vacancy_status, approval_status, created_at
        """, (
            landlord_id,
            data.get("name") or data.get("title"),
            data.get("description"),
            data.get("price"),
            data.get("location"),
            data.get("latitude"),
            data.get("longitude"),
        ))
        row = cur.fetchone()
        if row is None:
            return None
        keys = ["id","name","description","price","location","latitude","longitude","vacancy_status","approval_status","created_at"]
        return dict(zip(keys, row))

def update_accommodation_status(acc_id, status):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute(
            "UPDATE accommodations SET status=%s WHERE id=%s RETURNING id",
            (status, acc_id)
        )
        return cur.fetchone()


# ─────────────────────────────────────────────
#  FAVOURITES
# ─────────────────────────────────────────────

def add_favourite(user_id, accommodation_id):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO favourites (user_id, accommodation_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
            RETURNING id
        """, (user_id, accommodation_id))
        return cur.fetchone()

def remove_favourite(user_id, accommodation_id):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            DELETE FROM favourites
            WHERE user_id=%s AND accommodation_id=%s
            RETURNING id
        """, (user_id, accommodation_id))
        return cur.fetchone()

def get_user_favourites(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT a.*, u.name AS landlord_name, NULL AS landlord_review_score
            FROM favourites f
            JOIN accommodations a ON f.accommodation_id = a.id
            JOIN users u ON a.owner_id = u.id
            WHERE f.user_id = %s
            ORDER BY f.created_at DESC
        """, (user_id,))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  TENANT APPLICATIONS / PIPELINE
# ─────────────────────────────────────────────

def create_application(user_id, accommodation_id, message=""):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO tenant_applications (user_id, accommodation_id, message, status)
            VALUES (%s, %s, %s, 'pending')
            ON CONFLICT (user_id, accommodation_id) DO NOTHING
            RETURNING *
        """, (user_id, accommodation_id, message))
        return cur.fetchone()

def get_user_applications(user_id):
    """Tenant pipeline: pending contacts + active tenancy."""
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT ta.*, a.name, a.price, a.location,
                   -- a.listing_type, -- a.property_type,
                   u.name AS landlord_name, NULL AS landlord_phone
            FROM tenant_applications ta
            JOIN accommodations a ON ta.accommodation_id = a.id
            JOIN users u ON a.owner_id = u.id
            WHERE ta.user_id = %s
            ORDER BY ta.created_at DESC
        """, (user_id,))
        return cur.fetchall()

def update_application_status(app_id, status, landlord_id):
    """Landlord accepts or rejects. status: pending|approved|rejected|active"""
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            UPDATE tenant_applications ta
            SET status = %s, updated_at = NOW()
            FROM accommodations a
            WHERE ta.id = %s AND ta.accommodation_id = a.id
              AND a.owner_id = %s
            RETURNING ta.*
        """, (status, app_id, landlord_id))
        row = cur.fetchone()
        # If approved → mark property as occupied
        if row and status == "active":
            cur.execute("""
                UPDATE accommodations SET vacancy_status = 'occupied'
                WHERE id = %s
            """, (row["accommodation_id"],))
        return row

def get_active_tenancy(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT ta.*, a.name, a.location, a.price, a.owner_id,
                   u.name AS landlord_name, NULL AS landlord_phone, u.email AS landlord_email
            FROM tenant_applications ta
            JOIN accommodations a ON ta.accommodation_id = a.id
            JOIN users u ON a.owner_id = u.id
            WHERE ta.user_id = %s AND ta.status = 'active'
            LIMIT 1
        """, (user_id,))
        return cur.fetchone()


# ─────────────────────────────────────────────
#  PAYMENTS & RENT
# ─────────────────────────────────────────────

def create_payment(payer_id, accommodation_id, amount, payment_type, surcharge=0.0):
    """payment_type: rent | deposit | service"""
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO payments (
                payer_id, accommodation_id, amount, surcharge,
                total_amount, payment_type, status
            ) VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            RETURNING *
        """, (payer_id, accommodation_id, amount, surcharge,
              amount + surcharge, payment_type))
        row = cur.fetchone()
        # Credit landlord wallet
        cur.execute("""
            SELECT landlord_id FROM accommodations WHERE id = %s
        """, (accommodation_id,))
        acc = cur.fetchone()
        if acc:
            credit_wallet(acc["landlord_id"], amount, f"Rent payment for accommodation {accommodation_id}", cur)
        return row

def credit_wallet(user_id, amount, description, cur=None):
    def _do(cur):
        cur.execute("""
            INSERT INTO wallet_transactions (user_id, amount, transaction_type, description)
            VALUES (%s, %s, 'credit', %s)
        """, (user_id, amount, description))
        cur.execute("""
            UPDATE users SET wallet_balance = COALESCE(wallet_balance, 0) + %s
            WHERE id = %s
        """, (amount, user_id))
    if cur:
        _do(cur)
    else:
        with db_cursor(commit=True) as (conn, cur2):
            _do(cur2)

def get_wallet(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT
                COALESCE(SUM(amount),0) AS total,
                COALESCE(SUM(CASE WHEN created_at >= date_trunc('month', NOW()) THEN amount ELSE 0 END),0) AS this_month,
                COALESCE(SUM(CASE WHEN created_at >= date_trunc('year', NOW()) THEN amount ELSE 0 END),0) AS this_year
            FROM wallet_transactions WHERE user_id=%s
        """, (user_id,))
        totals = cur.fetchone()
        cur.execute("""
            SELECT * FROM wallet_transactions WHERE user_id=%s
            ORDER BY created_at DESC LIMIT 50
        """, (user_id,))
        transactions = cur.fetchall()
        return {
            "total": float(totals["total"]),
            "this_month": float(totals["this_month"]),
            "this_year": float(totals["this_year"]),
            "transactions": transactions
        }

def get_payments_for_accommodation(accommodation_id, landlord_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT p.*, u.name AS payer_name, u.email AS payer_email
            FROM payments p
            JOIN accommodations a ON p.accommodation_id = a.id
            JOIN users u ON p.payer_id = u.id
            WHERE p.accommodation_id = %s AND a.owner_id = %s
            ORDER BY p.created_at DESC
        """, (accommodation_id, landlord_id))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  REVIEWS
# ─────────────────────────────────────────────

def create_review(reviewer_id, target_id, target_type, rating, comment):
    """target_type: user | accommodation | service_provider"""
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO reviews (reviewer_id, target_id, target_type, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (reviewer_id, target_id, target_type) DO UPDATE
              SET rating = EXCLUDED.rating, comment = EXCLUDED.comment, updated_at = NOW()
            RETURNING *
        """, (reviewer_id, target_id, target_type, rating, comment))
        row = cur.fetchone()
        # Refresh aggregate score on users table
        if target_type == "user":
            cur.execute("""
                UPDATE users SET review_score = (
                    SELECT AVG(rating) FROM reviews
                    WHERE target_id = %s AND target_type = 'user'
                ) WHERE id = %s
            """, (target_id, target_id))
        elif target_type == "service_provider":
            cur.execute("""
                UPDATE service_providers SET avg_rating = (
                    SELECT AVG(rating) FROM reviews
                    WHERE target_id = %s AND target_type = 'service_provider'
                ) WHERE id = %s
            """, (target_id, target_id))
        return row

def get_reviews(target_id, target_type):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT r.*, u.name AS reviewer_name, u.profile_photo_url AS reviewer_photo
            FROM reviews r
            JOIN users u ON r.reviewer_id = u.id
            WHERE r.target_id = %s AND r.target_type = %s
            ORDER BY r.created_at DESC
        """, (target_id, target_type))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  CHAT
# ─────────────────────────────────────────────

def get_or_create_conversation(tenant_id, landlord_id, accommodation_id):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            SELECT id FROM conversations
            WHERE tenant_id=%s AND landlord_id=%s AND accommodation_id=%s
        """, (tenant_id, landlord_id, accommodation_id))
        row = cur.fetchone()
        if row:
            return row
        cur.execute("""
            INSERT INTO conversations (tenant_id, landlord_id, accommodation_id)
            VALUES (%s, %s, %s) RETURNING id
        """, (tenant_id, landlord_id, accommodation_id))
        return cur.fetchone()

def send_message(conversation_id, sender_id, content):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO messages (conversation_id, sender_id, content)
            VALUES (%s, %s, %s) RETURNING *
        """, (conversation_id, sender_id, content))
        cur.execute("""
            UPDATE conversations SET updated_at=NOW(), last_message=%s
            WHERE id=%s
        """, (content[:100], conversation_id))
        return cur.fetchone()

def get_conversation_messages(conversation_id, user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT c.id, c.tenant_id, c.landlord_id, c.accommodation_id,
                   a.name AS accommodation_title
            FROM conversations c
            JOIN accommodations a ON c.accommodation_id = a.id
            WHERE c.id = %s AND (c.tenant_id=%s OR c.landlord_id=%s)
        """, (conversation_id, user_id, user_id))
        convo = cur.fetchone()
        if not convo:
            return None
        cur.execute("""
            SELECT m.*, u.name AS sender_name, u.profile_photo_url AS sender_photo
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = %s
            ORDER BY m.created_at ASC
        """, (conversation_id,))
        convo["messages"] = cur.fetchall()
        return convo

def get_user_conversations(user_id, role):
    with db_cursor() as (conn, cur):
        if role == "landlord":
            cur.execute("""
                SELECT c.*, a.name AS accommodation_title,
                       u.name AS other_name, u.profile_photo_url AS other_photo
                FROM conversations c
                JOIN accommodations a ON c.accommodation_id = a.id
                JOIN users u ON c.tenant_id = u.id
                WHERE c.landlord_id = %s
                ORDER BY c.created_at DESC
            """, (user_id,))
        else:
            cur.execute("""
                SELECT c.*, a.name AS accommodation_title,
                       u.name AS other_name, u.profile_photo_url AS other_photo,
                       u.phone AS other_phone
                FROM conversations c
                JOIN accommodations a ON c.accommodation_id = a.id
                JOIN users u ON c.landlord_id = u.id
                WHERE c.tenant_id = %s
                ORDER BY c.created_at DESC
            """, (user_id,))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  TOUR BOOKINGS
# ─────────────────────────────────────────────

def book_tour(user_id, accommodation_id, tour_type, scheduled_at):
    """tour_type: physical | virtual"""
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO tour_bookings (user_id, accommodation_id, tour_type, scheduled_at, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING *
        """, (user_id, accommodation_id, tour_type, scheduled_at))
        return cur.fetchone()

def get_user_tours(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT tb.*, a.name, a.location, u.name AS landlord_name
            FROM tour_bookings tb
            JOIN accommodations a ON tb.accommodation_id = a.id
            JOIN users u ON a.owner_id = u.id
            WHERE tb.user_id = %s
            ORDER BY tb.scheduled_at DESC
        """, (user_id,))
        return cur.fetchall()

def get_landlord_tours(landlord_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT tb.*, a.name, u.name AS tenant_name, u.phone AS tenant_phone
            FROM tour_bookings tb
            JOIN accommodations a ON tb.accommodation_id = a.id
            JOIN users u ON tb.user_id = u.id
            WHERE a.owner_id = %s
            ORDER BY tb.scheduled_at ASC
        """, (landlord_id,))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  VERIFICATION DOCUMENTS
# ─────────────────────────────────────────────

def submit_verification_document(user_id, doc_type, file_url, accommodation_id=None):
    """
    doc_type: national_id | business_permit | title_deed | kra_pin | other
    accommodation_id: only for title deed tied to a specific property
    """
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO verification_documents
                (user_id, doc_type, file_url, accommodation_id, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING *
        """, (user_id, doc_type, file_url, accommodation_id))
        return cur.fetchone()

def get_user_verification_status(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT doc_type, status, created_at, reviewed_at, rejection_reason
            FROM verification_documents
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        docs = cur.fetchall()
        required_landlord = {"national_id", "business_permit", "title_deed"}
        submitted = {d["doc_type"] for d in docs if d["status"] in ("approved", "pending")}
        approved = {d["doc_type"] for d in docs if d["status"] == "approved"}
        return {
            "documents": docs,
            "submitted_types": list(submitted),
            "approved_types": list(approved),
            "fully_verified": required_landlord.issubset(approved),
        }

def admin_review_document(doc_id, status, rejection_reason=None):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            UPDATE verification_documents
            SET status=%s, reviewed_at=NOW(), rejection_reason=%s
            WHERE id=%s RETURNING *
        """, (status, rejection_reason, doc_id))
        return cur.fetchone()


# ─────────────────────────────────────────────
#  SERVICE PROVIDERS
# ─────────────────────────────────────────────

def create_service_provider_profile(user_id, data: dict):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO service_providers
                (user_id, business_name, category, description,
                 base_price, price_unit, coverage_area)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                business_name=EXCLUDED.business_name,
                category=EXCLUDED.category,
                description=EXCLUDED.description,
                base_price=EXCLUDED.base_price,
                price_unit=EXCLUDED.price_unit,
                coverage_area=EXCLUDED.coverage_area
            RETURNING *
        """, (
            user_id,
            data.get("business_name"), data.get("category"),
            data.get("description"), data.get("base_price"),
            data.get("price_unit", "per_job"), data.get("coverage_area"),
        ))
        return cur.fetchone()

def get_service_providers(category=None, verified_only=True):
    with db_cursor() as (conn, cur):
        query = """
            SELECT sp.*, u.name, u.phone, u.profile_photo_url,
                   u.review_score AS user_review_score
            FROM service_providers sp
            JOIN users u ON sp.user_id = u.id
            WHERE u.role = 'service_provider'
        """
        params = []
        if verified_only:
            query += " AND sp.is_verified = TRUE"
        if category:
            query += " AND sp.category = %s"
            params.append(category)
        query += " ORDER BY sp.avg_rating DESC NULLS LAST"
        cur.execute(query, params)
        return cur.fetchall()

def get_provider_by_user_id(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT sp.*, u.name, u.email, u.phone, u.profile_photo_url
            FROM service_providers sp
            JOIN users u ON sp.user_id = u.id
            WHERE sp.user_id = %s
        """, (user_id,))
        return cur.fetchone()

def update_provider_location(user_id, lat, lng):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            UPDATE service_providers
            SET current_lat=%s, current_lng=%s,
                location_updated_at=NOW(), is_online=TRUE
            WHERE user_id=%s
        """, (lat, lng, user_id))


# ─────────────────────────────────────────────
#  HOMERRFIX JOBS
# ─────────────────────────────────────────────

def create_job(tenant_id, category, description,
               address=None, urgency='normal', accommodation_id=None):
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO fix_jobs (
                tenant_id, category, description,
                address, urgency, accommodation_id, status
            ) VALUES (%s,%s,%s,%s,%s,%s,'open')
            RETURNING *
        """, (tenant_id, category, description,
              address, urgency, accommodation_id))
        return cur.fetchone()


def accept_job(job_id, provider_user_id):
    with db_cursor(commit=True) as (conn, cur):
        # Get provider record
        cur.execute("SELECT id FROM service_providers WHERE user_id=%s", (provider_user_id,))
        sp = cur.fetchone()
        if not sp:
            return None
        cur.execute("""
            UPDATE fix_jobs SET provider_id=%s, status='accepted', updated_at=NOW()
            WHERE id=%s AND status='open'
            RETURNING *
        """, (provider_user_id, job_id))
        return cur.fetchone()


def get_open_jobs(category=None):
    with db_cursor() as (conn, cur):
        q = """
            SELECT j.*, u.name AS tenant_name, a.name AS property_name,
                   a.location AS property_location
            FROM fix_jobs j
            JOIN users u ON j.tenant_id = u.id
            LEFT JOIN accommodations a ON j.accommodation_id = a.id
            WHERE j.status = 'open'
        """
        params = []
        if category:
            q += " AND j.category = %s"
            params.append(category)
        q += " ORDER BY CASE j.urgency WHEN 'emergency' THEN 1 WHEN 'urgent' THEN 2 ELSE 3 END, j.created_at DESC"
        cur.execute(q, params)
        return cur.fetchall()

def update_job_status(job_id, status, provider_id):
    """status: pending|accepted|en_route|arrived|in_progress|completed|cancelled"""
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            UPDATE fix_jobs SET status=%s, updated_at=NOW()
            WHERE id=%s AND provider_id=%s
            RETURNING *
        """, (status, job_id, provider_id))
        return cur.fetchone()

def get_tenant_jobs(tenant_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT j.*,
                   u.name AS provider_name,
                   sp.business_name, sp.avg_rating AS provider_rating,
                   sp.phone AS provider_phone
            FROM fix_jobs j
            LEFT JOIN users u ON j.provider_id = u.id
            LEFT JOIN service_providers sp ON sp.user_id = j.provider_id
            WHERE j.tenant_id = %s
            ORDER BY j.created_at DESC
        """, (tenant_id,))
        return cur.fetchall()

def get_provider_jobs(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT j.*, u.name AS tenant_name, u.email AS tenant_email
            FROM fix_jobs j
            JOIN users u ON j.tenant_id = u.id
            WHERE j.provider_id = %s
            ORDER BY j.created_at DESC
        """, (user_id,))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  HOMERRINSURANCE
# ─────────────────────────────────────────────

INSURANCE_TIERS = {
    "basic":    {"monthly_fee": 500,  "coverage_type": "fixed",      "coverage_value": 5000},
    "premium":  {"monthly_fee": 1200, "coverage_type": "percentage", "coverage_value": 60},
    "platinum": {"monthly_fee": 2500, "coverage_type": "full",       "coverage_value": 100},
}

def subscribe_insurance(user_id, tier):
    if tier not in INSURANCE_TIERS:
        raise ValueError(f"Unknown tier: {tier}")
    t = INSURANCE_TIERS[tier]
    with db_cursor(commit=True) as (conn, cur):
        cur.execute("""
            INSERT INTO insurance_policies (user_id, tier, monthly_fee,
                        coverage_type, coverage_value, status)
            VALUES (%s, %s, %s, %s, %s, 'active')
            ON CONFLICT (user_id) DO UPDATE SET
                tier=EXCLUDED.tier, monthly_fee=EXCLUDED.monthly_fee,
                coverage_type=EXCLUDED.coverage_type,
                coverage_value=EXCLUDED.coverage_value,
                status='active', updated_at=NOW()
            RETURNING *
        """, (user_id, tier, t["monthly_fee"], t["coverage_type"], t["coverage_value"]))
        return cur.fetchone()

def get_insurance_policy(user_id):
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT * FROM insurance_policies WHERE user_id=%s AND status='active'
        """, (user_id,))
        return cur.fetchone()

def calculate_coverage(user_id, bill_amount):
    """Returns how much insurance covers for a given bill."""
    policy = get_insurance_policy(user_id)
    if not policy:
        return {"covered": 0, "tenant_pays": bill_amount, "policy": None}
    t = policy["coverage_type"]
    v = policy["coverage_value"]
    if t == "fixed":
        covered = min(v, bill_amount)
    elif t == "percentage":
        covered = round(bill_amount * v / 100, 2)
    else:  # full
        covered = bill_amount
    return {
        "covered": covered,
        "tenant_pays": round(bill_amount - covered, 2),
        "policy": dict(policy),
    }


# ─────────────────────────────────────────────
#  SMART MATCHING  (review-score based ranking)
# ─────────────────────────────────────────────

def get_matched_accommodations(user_id):
    """
    Returns listings sorted by how well they match the tenant's review score.
    High-score tenant → high-score landlord listings first.
    Low-score tenant → lower-score listings first (still shown, just ranked).
    """
    with db_cursor() as (conn, cur):
        cur.execute("SELECT COALESCE(review_score, 3) FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        tenant_score = row[0] if row else 3.0

        cur.execute("""
            SELECT a.*, u.name AS landlord_name, NULL AS landlord_phone,
                   COALESCE(u.review_score, 3) AS landlord_score,
                   ABS(COALESCE(u.review_score, 3) - %s) AS score_diff,
                   COALESCE(
                       (SELECT AVG(r.rating) FROM reviews r
                        WHERE r.target_id = a.id AND r.target_type = 'accommodation'),
                       0
                   ) AS avg_rating
            FROM accommodations a
            JOIN users u ON a.owner_id = u.id
            WHERE a.approval_status='approved' AND a.vacancy_status='available'
            ORDER BY score_diff ASC, avg_rating DESC
        """, (tenant_score,))
        return cur.fetchall()


# ─────────────────────────────────────────────
#  ADMIN HELPERS
# ─────────────────────────────────────────────

def get_platform_stats():
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT
              (SELECT COUNT(*) FROM users WHERE role='user') AS total_tenants,
              (SELECT COUNT(*) FROM users WHERE role='landlord') AS total_landlords,
              (SELECT COUNT(*) FROM users WHERE role='service_provider') AS total_providers,
              (SELECT COUNT(*) FROM accommodations) AS total_listings,
              (SELECT COUNT(*) FROM accommodations WHERE status='approved') AS approved_listings,
              (SELECT COUNT(*) FROM accommodations WHERE status='pending') AS pending_listings,
              (SELECT COUNT(*) FROM fix_jobs) AS total_jobs,
              (SELECT COUNT(*) FROM insurance_policies WHERE status='active') AS active_policies,
              (SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='completed') AS total_revenue
        """)
        return cur.fetchone()

def get_pending_verifications():
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT vd.*, u.name, u.email, u.role
            FROM verification_documents vd
            JOIN users u ON vd.user_id = u.id
            WHERE vd.status = 'pending'
            ORDER BY vd.created_at ASC
        """)
        return cur.fetchall()


def get_landlord_analytics(landlord_id):
    from database import db_cursor
    with db_cursor() as (conn, cur):
        cur.execute("""
            SELECT
                COUNT(*) AS total_listings,
                COUNT(*) FILTER (WHERE approval_status='approved') AS approved,
                COUNT(*) FILTER (WHERE approval_status='pending')  AS pending,
                COUNT(*) FILTER (WHERE vacancy_status='available') AS vacant,
                COUNT(*) FILTER (WHERE vacancy_status='occupied')  AS occupied
            FROM accommodations WHERE owner_id = %s
        """, (landlord_id,))
        listing_stats = dict(cur.fetchone())
        cur.execute("""
            SELECT
                COALESCE(SUM(amount) FILTER (WHERE created_at >= DATE_TRUNC('month', NOW())), 0) AS this_month,
                COALESCE(SUM(amount) FILTER (WHERE created_at >= DATE_TRUNC('year', NOW())), 0) AS this_year,
                COALESCE(SUM(amount), 0) AS total
            FROM wallet_transactions WHERE user_id = %s AND transaction_type = 'credit'
        """, (landlord_id,))
        income_totals = dict(cur.fetchone())
        cur.execute("""
            SELECT TO_CHAR(DATE_TRUNC('month', created_at), 'Mon') AS month,
                   DATE_TRUNC('month', created_at) AS month_dt,
                   COALESCE(SUM(amount), 0) AS income
            FROM wallet_transactions
            WHERE user_id = %s AND transaction_type = 'credit'
              AND created_at >= NOW() - INTERVAL '6 months'
            GROUP BY month_dt, month ORDER BY month_dt
        """, (landlord_id,))
        monthly_income = [{"month": r["month"], "income": float(r["income"])} for r in cur.fetchall()]
        cur.execute("""
            SELECT a.name AS listing_name, COUNT(ta.id) AS applications
            FROM accommodations a
            LEFT JOIN tenant_applications ta ON ta.accommodation_id = a.id
              AND ta.created_at >= NOW() - INTERVAL '30 days'
            WHERE a.owner_id = %s GROUP BY a.id, a.name ORDER BY applications DESC
        """, (landlord_id,))
        listing_inquiries = [dict(r) for r in cur.fetchall()]
        cur.execute("""
            SELECT ta.id, ta.status, ta.message, ta.created_at,
                   u.name AS tenant_name, u.email AS tenant_email,
                   a.name AS listing_name, a.id AS listing_id
            FROM tenant_applications ta
            JOIN users u ON u.id = ta.user_id
            JOIN accommodations a ON a.id = ta.accommodation_id
            WHERE a.owner_id = %s ORDER BY ta.created_at DESC LIMIT 10
        """, (landlord_id,))
        recent_applications = [dict(r) for r in cur.fetchall()]
        approved = listing_stats.get("approved", 0)
        occupied = listing_stats.get("occupied", 0)
        occupancy_rate = round((occupied / approved * 100) if approved > 0 else 0, 1)
        return {
            "listing_stats": listing_stats,
            "monthly_income": monthly_income,
            "income_totals": {k: float(v) for k, v in income_totals.items()},
            "listing_inquiries": listing_inquiries,
            "recent_applications": recent_applications,
            "occupancy_rate": occupancy_rate,
        }


def add_accommodation_photo(accommodation_id, photo_url, sort_order=0):
    from database import db_cursor
    with db_cursor(commit=True) as (conn, cur):
        cur.execute(
            "INSERT INTO accommodation_photos (accommodation_id, photo_url, sort_order) VALUES (%s,%s,%s) RETURNING id",
            (accommodation_id, photo_url, sort_order)
        )
        return cur.fetchone()["id"]

def get_accommodation_photos(accommodation_id):
    from database import db_cursor
    with db_cursor() as (conn, cur):
        cur.execute(
            "SELECT * FROM accommodation_photos WHERE accommodation_id=%s ORDER BY sort_order",
            (accommodation_id,)
        )
        return cur.fetchall()

def delete_accommodation_photo(photo_id, owner_id):
    from database import db_cursor
    with db_cursor(commit=True) as (conn, cur):
        cur.execute(
            "DELETE FROM accommodation_photos WHERE id=%s AND accommodation_id IN (SELECT id FROM accommodations WHERE owner_id=%s) RETURNING id",
            (photo_id, owner_id)
        )
        return cur.fetchone()
