import os
import sys
import psycopg2
from app.config import settings

def apply_migration():
    migration_file = "D:\\AI Projects\\Soft Skill Check\\database\\migrations\\009_add_ai_classification.sql"
    
    print(f"🔌 Connecting to database: {settings.SUPABASE_DB_URL}")
    try:
        conn = psycopg2.connect(settings.SUPABASE_DB_URL)
        cur = conn.cursor()
        
        print(f"📖 Reading migration file: {migration_file}")
        with open(migration_file, "r") as f:
            sql = f.read()
            
        print("🚀 Executing SQL...")
        cur.execute(sql)
        conn.commit()
        
        print("✅ Migration applied successfully!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
