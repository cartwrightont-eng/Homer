import secrets
from datetime import datetime, timedelta

import psycopg2.extras
from werkzeug.security import check_password_hash, generate_password_hash

from config import EMAIL_TOKEN_EXPIRES_HOURS, PASSWORD_RESET_EXPIRES_HOURS
from database import get_connection


def _dict_rows(cursor, rows):
    return [dict(row) for row in rows]


def _now():
    return datetime.utcnow()


def _format_datetime(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def create_user(name, email, password, role='user'):
    hashed = generate_password_hash(password)
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "INSERT INTO users(name, email, password, role, email_verified) VALUES(%s, %s, %s, %s, %s) RETURNING id",
        (name, email, hashed, role, False),
    )
    user_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, name, email, password, role, email_verified FROM users WHERE email=%s",
        (email,),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, name, email, role, email_verified FROM users WHERE id=%s",
        (user_id,),
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_users():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, name, email, role, email_verified FROM users"
    )
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    if not user['email_verified']:
        return None
    if user.get('is_suspended'):
        return None
    if not check_password_hash(user['password'], password):
        return None
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
    }


def add_university(name, description, location, created_by=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO universities(name, description, location, created_by) VALUES(%s, %s, %s, %s)",
        (name, description, location, created_by),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_universities():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM universities")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def add_accommodation(
    name,
    description,
    price,
    location,
    university_id=None,
    owner_id=None,
    latitude=None,
    longitude=None,
    distance_km=None,
    vacancy_status='vacant',
    units_available=1,
    is_student_accommodation=False,
    is_university_owned=False,
    availability_option='rent',
):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        INSERT INTO accommodations(
            name,
            description,
            price,
            location,
            latitude,
            longitude,
            university_id,
            owner_id,
            distance_km,
            vacancy_status,
            units_available,
            is_student_accommodation,
            is_university_owned,
            availability_option
        ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """,
        (
            name,
            description,
            price,
            location,
            latitude,
            longitude,
            university_id,
            owner_id,
            distance_km,
            vacancy_status,
            units_available,
            is_student_accommodation,
            is_university_owned,
            availability_option,
        ),
    )
    accommodation_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return accommodation_id


def get_accommodations_by_university(university_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM accommodations WHERE university_id=%s",
        (university_id,),
    )
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def get_accommodations(university_id=None, availability_option=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = "SELECT * FROM accommodations"
    params = []
    conditions = []
    if university_id is not None:
        conditions.append("university_id=%s")
        params.append(university_id)
    if availability_option:
        conditions.append("availability_option=%s")
        params.append(availability_option)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def _generate_token():
    return secrets.token_urlsafe(32)


def _save_user_token(user_id, token, token_type, expires_at):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "INSERT INTO user_tokens(user_id, token, token_type, expires_at, used) VALUES(%s, %s, %s, %s, %s) RETURNING id",
        (user_id, token, token_type, expires_at, False),
    )
    token_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return token_id


def _get_user_token(token, token_type):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM user_tokens WHERE token=%s AND token_type=%s",
        (token, token_type),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def _mark_token_used(token_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_tokens SET used=TRUE WHERE id=%s", (token_id,))
    conn.commit()
    cursor.close()
    conn.close()


def create_verification_token(user_id):
    token = _generate_token()
    expires_at = _format_datetime(_now() + timedelta(hours=EMAIL_TOKEN_EXPIRES_HOURS))
    _save_user_token(user_id, token, 'verification', expires_at)
    return token


def verify_user_email(token):
    row = _get_user_token(token, 'verification')
    if not row or row['used']:
        return False
    # expires_at is already a datetime object from PostgreSQL
    expires_at = row['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
    if expires_at < _now():
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email_verified=TRUE WHERE id=%s", (row['user_id'],))
    conn.commit()
    cursor.close()
    conn.close()
    _mark_token_used(row['id'])
    return True


def create_password_reset_token(email):
    user = get_user_by_email(email)
    if not user:
        return None
    token = _generate_token()
    expires_at = _format_datetime(_now() + timedelta(hours=PASSWORD_RESET_EXPIRES_HOURS))
    _save_user_token(user['id'], token, 'reset', expires_at)
    return token


def reset_password(token, new_password):
    row = _get_user_token(token, 'reset')
    if not row or row['used']:
        return False
    # expires_at is already a datetime object from PostgreSQL
    expires_at = row['expires_at']
    if isinstance(expires_at, str):
        expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
    if expires_at < _now():
        return False
    hashed = generate_password_hash(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, row['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    _mark_token_used(row['id'])
    return True


def get_accommodation(accommodation_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM accommodations WHERE id=%s", (accommodation_id,))
    accommodation = cursor.fetchone()
    cursor.close()
    conn.close()
    return accommodation


def get_accommodation_amenities(accommodation_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        """
        SELECT aa.id, aa.accommodation_id, aa.amenity_id, aa.distance_km,
               a.name, a.category
        FROM accommodation_amenities aa
        JOIN amenities a ON aa.amenity_id = a.id
        WHERE aa.accommodation_id=%s
        """,
        (accommodation_id,),
    )
    amenities = cursor.fetchall()
    cursor.close()
    conn.close()
    return amenities


def get_accommodation_photos(accommodation_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, accommodation_id, photo_url, description, uploaded_at FROM photos WHERE accommodation_id=%s",
        (accommodation_id,),
    )
    photos = cursor.fetchall()
    cursor.close()
    conn.close()
    return photos


def get_accommodation_videos(accommodation_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, accommodation_id, video_url, title, uploaded_at FROM videos WHERE accommodation_id=%s",
        (accommodation_id,),
    )
    videos = cursor.fetchall()
    cursor.close()
    conn.close()
    return videos


def get_accommodations_by_landlord(landlord_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM accommodations WHERE owner_id=%s",
        (landlord_id,),
    )
    accommodations = cursor.fetchall()
    cursor.close()
    conn.close()
    return accommodations


def get_accommodations(university_id=None, availability_option=None, is_student_accommodation=None, vacancy_status=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = "SELECT * FROM accommodations"
    params = []
    conditions = []
    if university_id is not None:
        conditions.append("university_id=%s")
        params.append(university_id)
    if availability_option:
        conditions.append("availability_option=%s")
        params.append(availability_option)
    if vacancy_status:
        conditions.append("vacancy_status=%s")
        params.append(vacancy_status)
    if is_student_accommodation is not None:
        conditions.append("is_student_accommodation=%s")
        params.append(is_student_accommodation)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def _update_record(table, record_id, fields):
    if not fields:
        return False
    allowed_fields = {
        'name', 'description', 'price', 'location', 'latitude', 'longitude',
        'university_id', 'owner_id', 'distance_km', 'vacancy_status', 'units_available',
        'is_student_accommodation', 'is_university_owned', 'availability_option',
        'approval_status', 'rejection_reason', 'is_suspicious', 'suspicious_reason',
        'photo_url', 'title', 'is_active', 'content', 'announcement_type',
        'updated_by', 'section_name', 'updated_at', 'status', 'resolution_notes',
    }
    update_fields = {k: v for k, v in fields.items() if k in allowed_fields}
    if not update_fields:
        return False
    columns = ", ".join(f"{key}=%s" for key in update_fields)
    params = list(update_fields.values()) + [record_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table} SET {columns} WHERE id=%s", tuple(params))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def update_accommodation(accommodation_id, **data):
    return _update_record('accommodations', accommodation_id, data)


def edit_listing(listing_id, **data):
    return update_accommodation(listing_id, **data)


def get_all_listings(approval_status=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if approval_status:
        cursor.execute(
            "SELECT * FROM accommodations WHERE approval_status=%s",
            (approval_status,),
        )
    else:
        cursor.execute("SELECT * FROM accommodations")
    listings = cursor.fetchall()
    cursor.close()
    conn.close()
    return listings


def approve_listing(listing_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accommodations SET approval_status='approved', rejection_reason=NULL WHERE id=%s",
        (listing_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def reject_listing(listing_id, reason):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accommodations SET approval_status='rejected', rejection_reason=%s WHERE id=%s",
        (reason, listing_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def mark_listing_suspicious(listing_id, reason=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accommodations SET is_suspicious=TRUE, suspicious_reason=%s WHERE id=%s",
        (reason, listing_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def unmark_listing_suspicious(listing_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE accommodations SET is_suspicious=FALSE, suspicious_reason=NULL WHERE id=%s",
        (listing_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_or_create_amenity(name, category):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id FROM amenities WHERE name=%s AND category=%s",
        (name, category),
    )
    row = cursor.fetchone()
    if row:
        amenity_id = row['id']
        cursor.close()
        conn.close()
        return amenity_id
    cursor.execute(
        "INSERT INTO amenities(name, category) VALUES(%s, %s) RETURNING id",
        (name, category),
    )
    amenity_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return amenity_id


def add_accommodation_amenity(accommodation_id, amenity_id, distance_km=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO accommodation_amenities(accommodation_id, amenity_id, distance_km) VALUES(%s, %s, %s) RETURNING id",
        (accommodation_id, amenity_id, distance_km),
    )
    amenity_link_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return amenity_link_id


def add_accommodation_photo(accommodation_id, photo_url, description=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO photos(accommodation_id, photo_url, description) VALUES(%s, %s, %s) RETURNING id",
        (accommodation_id, photo_url, description),
    )
    photo_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return photo_id


def add_accommodation_video(accommodation_id, video_url, title=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO videos(accommodation_id, video_url, title) VALUES(%s, %s, %s) RETURNING id",
        (accommodation_id, video_url, title),
    )
    video_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return video_id


def create_announcement(title, content, announcement_type, created_by):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO announcements(title, content, announcement_type, created_by) VALUES(%s, %s, %s, %s) RETURNING id",
        (title, content, announcement_type, created_by),
    )
    announcement_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return announcement_id


def get_announcements(announcement_type=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if announcement_type:
        cursor.execute(
            "SELECT * FROM announcements WHERE announcement_type=%s AND is_active=TRUE",
            (announcement_type,),
        )
    else:
        cursor.execute("SELECT * FROM announcements WHERE is_active=TRUE")
    announcements = cursor.fetchall()
    cursor.close()
    conn.close()
    return announcements


def deactivate_announcement(announcement_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE announcements SET is_active=FALSE WHERE id=%s",
        (announcement_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_homepage_content(section_name=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if section_name:
        cursor.execute(
            "SELECT * FROM homepage_content WHERE section_name=%s",
            (section_name,),
        )
        content = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM homepage_content")
        content = cursor.fetchall()
    cursor.close()
    conn.close()
    return content


def update_homepage_content(section_name, content, updated_by):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO homepage_content(section_name, content, updated_by, updated_at) VALUES(%s, %s, %s, CURRENT_TIMESTAMP) "
        "ON CONFLICT(section_name) DO UPDATE SET content=EXCLUDED.content, updated_by=EXCLUDED.updated_by, updated_at=CURRENT_TIMESTAMP",
        (section_name, content, updated_by),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def create_report(report_type, reason, description, reporter_id, reported_user_id=None, reported_accommodation_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports(report_type, reported_user_id, reported_accommodation_id, reporter_id, reason, description) VALUES(%s, %s, %s, %s, %s, %s) RETURNING id",
        (report_type, reported_user_id, reported_accommodation_id, reporter_id, reason, description),
    )
    report_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return report_id


def get_reports(status=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if status:
        cursor.execute("SELECT * FROM reports WHERE status=%s", (status,))
    else:
        cursor.execute("SELECT * FROM reports")
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    return reports


def get_report(report_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM reports WHERE id=%s", (report_id,))
    report = cursor.fetchone()
    cursor.close()
    conn.close()
    return report


def resolve_report(report_id, resolution_notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reports SET status='resolved', resolution_notes=%s, resolved_at=%s WHERE id=%s",
        (resolution_notes, _format_datetime(_now()), report_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True


def search_users(query):
    like_query = f"%{query}%"
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, name, email, role, email_verified, is_suspended, is_landlord_verified FROM users WHERE name LIKE %s OR email LIKE %s",
        (like_query, like_query),
    )
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def suspend_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_suspended=TRUE WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def reactivate_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_suspended=FALSE WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_suspended=TRUE WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def verify_landlord(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_landlord_verified=TRUE WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def unverify_landlord(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_landlord_verified=FALSE WHERE id=%s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_analytics_dashboard():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    cursor.execute("SELECT COUNT(*) AS total_landlords FROM users WHERE role='landlord'")
    total_landlords = cursor.fetchone()['total_landlords']
    cursor.execute("SELECT COUNT(*) AS total_admins FROM users WHERE role='admin'")
    total_admins = cursor.fetchone()['total_admins']
    cursor.execute("SELECT COUNT(*) AS total_accommodations FROM accommodations")
    total_accommodations = cursor.fetchone()['total_accommodations']
    cursor.execute("SELECT COUNT(*) AS approved_listings FROM accommodations WHERE approval_status='approved'")
    approved_listings = cursor.fetchone()['approved_listings']
    cursor.execute("SELECT COUNT(*) AS pending_listings FROM accommodations WHERE approval_status='pending'")
    pending_listings = cursor.fetchone()['pending_listings']
    cursor.execute("SELECT COUNT(*) AS suspicious_listings FROM accommodations WHERE is_suspicious=TRUE")
    suspicious_listings = cursor.fetchone()['suspicious_listings']
    cursor.execute("SELECT COUNT(*) AS open_reports FROM reports WHERE status='open'")
    open_reports = cursor.fetchone()['open_reports']
    cursor.execute("SELECT COUNT(*) AS resolved_reports FROM reports WHERE status='resolved'")
    resolved_reports = cursor.fetchone()['resolved_reports']
    dashboard = {
        'total_users': total_users,
        'total_landlords': total_landlords,
        'total_admins': total_admins,
        'total_accommodations': total_accommodations,
        'approved_listings': approved_listings,
        'pending_listings': pending_listings,
        'suspicious_listings': suspicious_listings,
        'open_reports': open_reports,
        'resolved_reports': resolved_reports,
    }
    cursor.close()
    conn.close()
    return dashboard

