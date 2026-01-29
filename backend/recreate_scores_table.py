"""
Script to drop and recreate assessment_scores table.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.backend')
SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL')

def recreate_table():
    conn = psycopg2.connect(SUPABASE_DB_URL)
    cur = conn.cursor()

    print('🗑️ Dropping assessment_scores table...')
    cur.execute('DROP TABLE IF EXISTS public.assessment_scores CASCADE;')
    conn.commit()

    print('🏗️ Creating new assessment_scores table...')
    cur.execute('''
    CREATE TABLE public.assessment_scores (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        assessment_id UUID NOT NULL UNIQUE REFERENCES public.assessments(id) ON DELETE CASCADE,
        fluency_score DECIMAL(5,2),
        pronunciation_score DECIMAL(5,2),
        grammar_score DECIMAL(5,2),
        confidence_score DECIMAL(5,2),
        hesitation_score DECIMAL(5,2),
        storytelling_score DECIMAL(5,2),
        vision_clarity_score DECIMAL(5,2),
        total_score DECIMAL(5,2),
        grade TEXT,
        strengths TEXT[],
        weaknesses TEXT[],
        recommendations TEXT[],
        overall_feedback TEXT,
        details JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
    );
    ''')
    conn.commit()

    print('📇 Creating indexes...')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_scores_assessment_id ON public.assessment_scores(assessment_id);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_scores_total_score ON public.assessment_scores(total_score DESC);')
    conn.commit()

    print('🔄 Notifying PostgREST to reload schema...')
    cur.execute("NOTIFY pgrst, 'reload schema'")
    conn.commit()

    print('✅ Done! Listing columns:')
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assessment_scores' ORDER BY ordinal_position;")
    for r in cur.fetchall():
        print(f'  - {r[0]}')

    cur.close()
    conn.close()

if __name__ == "__main__":
    recreate_table()
