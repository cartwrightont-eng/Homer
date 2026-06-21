import psycopg2

conn = psycopg2.connect('postgresql://neondb_owner:npg_bEtsKX72LkND@ep-tiny-cloud-ad5pn9li-pooler.c-2.us-east-1.aws.neon.tech/mydb?sslmode=require')
cur = conn.cursor()

accommodations = [
    ('Madaraka Student Hostel', 'Modern hostel 5 minutes from Strathmore', 'Madaraka Estate', 8000, 'rent', 1, 2),
    ('Daystar Bedsitter', 'Self contained bedsitter near Strathmore gate', 'Ole Sangale Road', 12000, 'rent', 1, 2),
    ('South C Studio', 'Quiet studio apartment with WiFi included', 'South C', 15000, 'rent', 1, 2),
]

for acc in accommodations:
    cur.execute("""
        INSERT INTO accommodations (name, description, location, price, listing_type, university_id, owner_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id;
    """, acc)
    result = cur.fetchone()
    print('Accommodation added, ID:', result)

conn.commit()
cur.close()
conn.close()
print('Done!')
