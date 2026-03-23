import asyncio
import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL", "error")
key = os.environ.get("SUPABASE_KEY", "error")

if url == "error" or key == "error":
    from app.core.config import settings
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY

supabase = create_client(url, key)

response = supabase.table("assessment_scores").select("*").order("created_at", desc=True).limit(1).execute()
if response.data:
    row = response.data[0]
    print(f"Total Score: {row['total_score']}")
    print(f"Fluency: {row['fluency_score']}")
    print(f"Pronunciation: {row['pronunciation_score']}")
    print(f"Grammar: {row['grammar_score']}")
    print(f"Vocal Confidence: {row['vocal_confidence_score']}")
    print(f"Textual Confidence: {row.get('textual_confidence')}")
    print(f"Hesitation: {row['hesitation_score']}")
    print(f"Storytelling: {row['storytelling_score']}")
    print(f"Vision: {row['vision_clarity_score']}")
    print(f"Aim: {row.get('aim_clarity_score')}")
    print("CALCULATED SUM OF PARTS:")
    # Calculate sum
    parts = [
        row['fluency_score'],
        row['pronunciation_score'],
        row['grammar_score'],
        row['vocal_confidence_score'],
        row.get('textual_confidence') or 0,
        row['hesitation_score'],
        row['storytelling_score'],
        row['vision_clarity_score'],
        row.get('aim_clarity_score') or 0
    ]
    parts = [p if p is not None else 0 for p in parts]
    print(sum(parts))
else:
    print("No data")
