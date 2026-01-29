import google.generativeai as genai
import os
import sys

# Add parent path to find config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.config import settings

def list_models():
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    print(f"🔑 Checking models for key: {settings.GOOGLE_API_KEY[:5]}...")
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_models()
