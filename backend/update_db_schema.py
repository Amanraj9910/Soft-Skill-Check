import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load env directly
load_dotenv("../.env.backend")

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

def update_schema():
    if not SUPABASE_DB_URL:
        print("❌ SUPABASE_DB_URL not found in environment.")
        return

    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL)
        cur = conn.cursor()
        
        print("🛠️ Updating assessment_scores table...")
        
        # 1. Handle Hesitation Penalty -> Hesitation Score
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' AND column_name='hesitation_penalty';")
        if cur.fetchone():
            print("Found hesitation_penalty. Renaming to hesitation_score...")
            cur.execute("ALTER TABLE public.assessment_scores RENAME COLUMN hesitation_penalty TO hesitation_score;")
        else:
            print("hesitation_penalty not found. Checking for hesitation_score...")
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' AND column_name='hesitation_score';")
            if not cur.fetchone():
               print("hesitation_score missing. Adding it...")
               cur.execute("ALTER TABLE public.assessment_scores ADD COLUMN hesitation_score FLOAT DEFAULT 0;")
            else:
               print("hesitation_score exists.")

        # 2. Add Textual Confidence
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' AND column_name='textual_confidence';")
        if not cur.fetchone():
            print("textual_confidence column missing. Adding it...")
            cur.execute("ALTER TABLE public.assessment_scores ADD COLUMN textual_confidence FLOAT DEFAULT 0;")
        else:
            print("textual_confidence column exists.")

        conn.commit()
        
        print("🔄 Reloading PostgREST schema cache...")
        cur.execute("NOTIFY pgrst, 'reload schema';")
        conn.commit()
        
        print("✅ Schema updated successfully!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_schema()
