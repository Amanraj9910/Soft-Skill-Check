import os
import sys
import psycopg2

# Add parent dir to path to find app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.config import settings

def fix_schema():
    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(settings.SUPABASE_DB_URL)
        cur = conn.cursor()
        
        print("🛠️ Checking columns...")
        # Check if raw_ai_response exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' AND column_name='raw_ai_response';")
        if cur.fetchone():
            print("Found raw_ai_response. Renaming to details...")
            cur.execute("ALTER TABLE public.assessment_scores RENAME COLUMN raw_ai_response TO details;")
        else:
            print("raw_ai_response not found.")
            
        # Check if details exists now
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' AND column_name='details';")
        if not cur.fetchone():
            print("details column missing. Adding it...")
            cur.execute("ALTER TABLE public.assessment_scores ADD COLUMN details JSONB;")
        else:
            print("details column exists.")

        # Check if grade exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' AND column_name='grade';")
        if not cur.fetchone():
            print("grade column missing. Adding it...")
            cur.execute("ALTER TABLE public.assessment_scores ADD COLUMN grade TEXT;")
        else:
            print("grade column exists.")
            
        conn.commit()

        print("🔄 Reloading PostgREST schema cache...")
        cur.execute("NOTIFY pgrst, 'reload schema';")
        conn.commit()
        
        print("✅ Schema fixed!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_schema()
