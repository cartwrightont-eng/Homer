import psycopg2
from config import DATABASE_URL


def init_db():
    conn = psycopg2.connect(dsn=DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('''
CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_suspended BOOLEAN NOT NULL DEFAULT FALSE,
    is_landlord_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS universities(
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    location TEXT,
    created_by INTEGER,
    FOREIGN KEY(created_by) REFERENCES users(id)
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS accommodations(
    id SERIAL PRIMARY KEY,
    name TEXT,
    description TEXT,
    price REAL,
    location TEXT,
    latitude REAL DEFAULT NULL,
    longitude REAL DEFAULT NULL,
    university_id INTEGER,
    owner_id INTEGER NOT NULL,
    distance_km REAL DEFAULT NULL,
    availability_option TEXT NOT NULL DEFAULT 'rent',
    vacancy_status TEXT NOT NULL DEFAULT 'vacant',
    units_available INTEGER DEFAULT 1,
    is_student_accommodation BOOLEAN NOT NULL DEFAULT FALSE,
    is_university_owned BOOLEAN NOT NULL DEFAULT FALSE,
    approval_status TEXT NOT NULL DEFAULT 'pending',
    rejection_reason TEXT,
    is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    suspicious_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(university_id) REFERENCES universities(id),
    FOREIGN KEY(owner_id) REFERENCES users(id)
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS amenities(
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS accommodation_amenities(
    id SERIAL PRIMARY KEY,
    accommodation_id INTEGER NOT NULL,
    amenity_id INTEGER NOT NULL,
    distance_km REAL DEFAULT NULL,
    FOREIGN KEY(accommodation_id) REFERENCES accommodations(id) ON DELETE CASCADE,
    FOREIGN KEY(amenity_id) REFERENCES amenities(id),
    UNIQUE(accommodation_id, amenity_id)
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS photos(
    id SERIAL PRIMARY KEY,
    accommodation_id INTEGER NOT NULL,
    photo_url TEXT NOT NULL,
    description TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(accommodation_id) REFERENCES accommodations(id) ON DELETE CASCADE
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS videos(
    id SERIAL PRIMARY KEY,
    accommodation_id INTEGER NOT NULL,
    video_url TEXT NOT NULL,
    title TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(accommodation_id) REFERENCES accommodations(id) ON DELETE CASCADE
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS user_tokens(
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    token_type TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS reports(
    id SERIAL PRIMARY KEY,
    report_type TEXT NOT NULL,
    reported_user_id INTEGER,
    reported_accommodation_id INTEGER,
    reporter_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY(reported_user_id) REFERENCES users(id),
    FOREIGN KEY(reported_accommodation_id) REFERENCES accommodations(id),
    FOREIGN KEY(reporter_id) REFERENCES users(id)
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS announcements(
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    announcement_type TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(created_by) REFERENCES users(id)
)
''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS homepage_content(
    id SERIAL PRIMARY KEY,
    section_name TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    updated_by INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(updated_by) REFERENCES users(id)
)
''')

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    init_db()
