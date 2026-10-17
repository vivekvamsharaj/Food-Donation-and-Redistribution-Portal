from getpass import getpass
from werkzeug.security import generate_password_hash
import mysql.connector
import os

conn = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "food_donation_portal")
)
name = input("Admin name: ").strip()
email = input("Admin email: ").strip().lower()
password = getpass("Admin password (minimum 8 characters): ")
if not name or not email or len(password) < 8:
    raise SystemExit("Name/email required; password must be at least 8 characters.")
cur = conn.cursor()
cur.execute("INSERT INTO users(name,email,password_hash,role,verified) VALUES(%s,%s,%s,'Admin',1)",
            (name, email, generate_password_hash(password)))
conn.commit()
cur.close()
conn.close()
print("Admin account created. Log in through the website.")
