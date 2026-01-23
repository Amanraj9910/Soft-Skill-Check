"""
Quick API test script to verify backend is working.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from app.config import settings
        print(f"  ✅ Config loaded: {settings.APP_NAME}")
        
        from app.models.schemas import AssessmentCreate
        print("  ✅ Models imported successfully")
        
        from app.services.supabase_client import supabase_service
        print("  ✅ Supabase service imported")
        
        from app.routers import assessments, conversation, scoring, responses, users
        print("  ✅ All routers imported")
        
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_config():
    """Test configuration values."""
    print("\n🧪 Testing configuration...")
    
    try:
        from app.config import settings
        
        checks = {
            "Supabase URL": bool(settings.SUPABASE_URL),
            "Azure OpenAI Endpoint": bool(settings.AZURE_OPENAI_ENDPOINT),
            "Azure Speech Key": bool(settings.AZURE_SPEECH_KEY),
            "Azure Storage": bool(settings.AZURE_STORAGE_CONNECTION_STRING),
            "Secret Key": bool(settings.SECRET_KEY)
        }
        
        all_good = True
        for name, result in checks.items():
            if result:
                print(f"  ✅ {name} configured")
            else:
                print(f"  ❌ {name} missing")
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False


def test_app_creation():
    """Test FastAPI app creation."""
    print("\n🧪 Testing FastAPI app...")
    
    try:
        from app.main import app
        print(f"  ✅ FastAPI app created: {app.title}")
        
        # Count routes
        routes = [route for route in app.routes if hasattr(route, 'methods')]
        print(f"  ✅ API routes registered: {len(routes)}")
        
        # List some routes
        print("\n  📋 Available endpoints:")
        for route in routes[:10]:  # Show first 10
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"    - {methods:10} {route.path}")
        
        if len(routes) > 10:
            print(f"    ... and {len(routes) - 10} more")
        
        return True
    except Exception as e:
        print(f"  ❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Backend Quick Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("App Creation", test_app_creation()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:20} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Backend is ready!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("  1. Run database migrations in Supabase")
        print("  2. Start server: python run.py")
        print("  3. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("=" * 60)
        print("\n📝 Troubleshooting:")
        print("  1. Check .env.backend file exists")
        print("  2. Verify all credentials are filled in")
        print("  3. Install dependencies: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
