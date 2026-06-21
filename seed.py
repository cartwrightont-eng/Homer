import psycopg2

conn = psycopg2.connect('postgresql://neondb_owner:npg_bEtsKX72LkND@ep-tiny-cloud-ad5pn9li-pooler.c-2.us-east-1.aws.neon.tech/mydb?sslmode=require')
cur = conn.cursor()

cur.execute("""
    INSERT INTO users (name, email, password, role, email_verified, is_suspended, is_landlord_verified)
    VALUES ('John Kamau', 'john.kamau@email.com', 'hashedpassword123', 'landlord', true, false, true)
    ON CONFLICT DO NOTHING
    RETURNING id;
""")
landlord = cur.fetchone()
print('Landlord added, ID:', landlord)

cur.execute("""
    INSERT INTO users (name, email, password, role, email_verified, is_suspended, is_landlord_verified)
    VALUES ('Amina Odhiambo', 'amina.student@email.com', 'hashedpassword123', 'user', true, false, false)
    ON CONFLICT DO NOTHING
    RETURNING id;
""")
student = cur.fetchone()
print('Student added, ID:', student)

conn.commit()
cur.close()
conn.close()
print('Done!')