import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.config import settings
    print("✅ Settings loaded!")
    print(settings.model_dump())
except Exception as e:
    print(f"❌ Error loading settings: {e}")
