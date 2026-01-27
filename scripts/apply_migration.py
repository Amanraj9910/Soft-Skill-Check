import os
import psycopg2
import glob
from urllib.parse import urlparse

def load_env_file(filepath):
    """Simple env file loader to avoid python-dotenv dependency if not present."""
    if not os.path.exists(filepath):
        return {}
    env_vars = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def apply_migrations():
    print("🚀 Starting database migration...")
    
    # Load environment variables
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, '.env.backend')
    env_vars = load_env_file(env_path)
    
    db_url = env_vars.get('SUPABASE_DB_URL')
    if not db_url:
        print("❌ Error: SUPABASE_DB_URL not found in .env.backend")
        return

    print(f"🔌 Connecting to database...")
    
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected.")

        # Get all migration files
        migrations_dir = os.path.join(base_dir, 'database', 'migrations')
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, '*.sql')))
        
        if not migration_files:
            print("⚠️ No migration files found.")
            return

        print(f"found {len(migration_files)} migration files.")

        for file_path in migration_files:
            filename = os.path.basename(file_path)
            print(f"📄 Applying {filename}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            try:
                cursor.execute(sql_content)
                print(f"   ✅ Success.")
            except Exception as e:
                print(f"   ⚠️ Error applying {filename}: {e}")
                print("   (Continuing as some statements might be 'already exists' errors)")

        print("✨ Migration process complete.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Connection closed.")

if __name__ == "__main__":
    apply_migrations()
