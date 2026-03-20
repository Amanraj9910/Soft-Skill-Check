"""Debug JWT token to see what algorithm it actually uses"""
from jose import jwt

# Sample token from browser console - replace this with actual token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInN1YiI6Im1teXFqeGxyIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImV4cCI6MTcxMDkyMzAyMCwiaWF0IjoxNzEwOTE5NDIwfQ.test"

try:
    # Decode without verification to see header
    unverified_header = jwt.get_unverified_claims(token)
    print("Token header:", unverified_header)
except Exception as e:
    print(f"Error decoding: {e}")
