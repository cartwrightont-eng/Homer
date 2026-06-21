import psycopg2

conn = psycopg2.connect('postgresql://neondb_owner:npg_bEtsKX72LkND@ep-tiny-cloud-ad5pn9li-pooler.c-2.us-east-1.aws.neon.tech/mydb?sslmode=require')
cur = conn.cursor()

accommodations = [
    ('Madaraka Student Hostel', 'Modern hostel 5 minutes from Strathmore', 8000, 'Madaraka Estate, Nairobi', -1.3096, 36.8219, 1, 2, 0.5, 'rent', 'available', 10, True, False, 'approved'),
    ('Ole Sangale Bedsitter', 'Self contained bedsitter near Strathmore gate', 12000, 'Ole Sangale Road, Nairobi', -1.3112, 36.8134, 1, 2, 0.8, 'rent', 'available', 5, True, False, 'approved'),
    ('South C Studio Apartment', 'Quiet studio with WiFi included', 15000, 'South C, Nairobi', -1.3201, 36.8310, 1, 2, 2.1, 'rent', 'available', 3, True, False, 'approved'),
]

for acc in accommodations:
    cur.execute("""
        INSERT INTO accommodations (name, description, price, location, latitude, longitude, university_id, owner_id, distance_km, availability_option, vacancy_status, units_available, is_student_accommodation, is_university_owned, approval_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, acc)
    result = cur.fetchone()
    print('Accommodation added, ID:', result)

conn.commit()
cur.close()
conn.close()
print('Done!')
