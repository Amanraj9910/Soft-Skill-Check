import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env.backend")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

try:
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'assessment_scores';")
    rows = cur.fetchall()
    print("Columns in assessment_scores:")
    for row in rows:
        print(f"- {row[0]} ({row[1]})")
    conn.close()
except Exception as e:
    print(e)
