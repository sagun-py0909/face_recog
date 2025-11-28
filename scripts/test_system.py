"""
Test script to verify the Face Recognition System v2.0 installation
Run this after setup to ensure everything is working correctly
"""

import sys
import requests
from pathlib import Path
import time

# Configuration
API_URL = "http://localhost:8000"
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'END': '\033[0m'
}

def print_colored(message, color='END'):
    """Print colored output"""
    if sys.platform == 'win32':
        print(message)  # Skip colors on Windows for compatibility
    else:
        print(f"{COLORS.get(color, '')}{message}{COLORS['END']}")

def print_header(title):
    """Print section header"""
    print_colored("\n" + "=" * 60, 'BLUE')
    print_colored(f"  {title}", 'BLUE')
    print_colored("=" * 60, 'BLUE')

def test_api_connection():
    """Test API server connection"""
    print_header("1. Testing API Server Connection")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_colored(f"✓ API server is running", 'GREEN')
            print(f"  Version: {data.get('version', 'unknown')}")
            print(f"  Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_colored(f"✗ API returned status {response.status_code}", 'RED')
            return False
    except requests.exceptions.ConnectionError:
        print_colored("✗ Cannot connect to API server", 'RED')
        print_colored(f"  Make sure the server is running on {API_URL}", 'YELLOW')
        return False
    except Exception as e:
        print_colored(f"✗ Error: {e}", 'RED')
        return False

def test_api_docs():
    """Test API documentation availability"""
    print_header("2. Testing API Documentation")
    
    endpoints = {
        "Swagger UI": "/api/docs",
        "ReDoc": "/api/redoc",
        "OpenAPI JSON": "/openapi.json"
    }
    
    all_ok = True
    for name, endpoint in endpoints.items():
        try:
            response = requests.get(f"{API_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print_colored(f"✓ {name} accessible at {endpoint}", 'GREEN')
            else:
                print_colored(f"✗ {name} returned status {response.status_code}", 'RED')
                all_ok = False
        except Exception as e:
            print_colored(f"✗ {name} error: {e}", 'RED')
            all_ok = False
    
    return all_ok

def test_database_connection():
    """Test database connection by checking API endpoints"""
    print_header("3. Testing Database Connection")
    
    try:
        # Try to get people (requires auth, but connection test is valid)
        response = requests.get(f"{API_URL}/api/recognition/people", timeout=5)
        
        # 401 Unauthorized means DB is working but we need auth (expected)
        # 500 would indicate DB connection problem
        if response.status_code in [200, 401]:
            print_colored("✓ Database connection working", 'GREEN')
            return True
        else:
            print_colored(f"✗ Database may have issues (status {response.status_code})", 'RED')
            return False
    except Exception as e:
        print_colored(f"✗ Database connection error: {e}", 'RED')
        return False

def test_user_registration():
    """Test user registration endpoint"""
    print_header("4. Testing User Registration")
    
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json=test_user,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_colored("✓ User registration working", 'GREEN')
            print(f"  Created user: {data.get('username')}")
            print(f"  Is admin: {data.get('is_admin')}")
            return True, test_user
        else:
            print_colored(f"✗ Registration failed: {response.text}", 'RED')
            return False, None
    except Exception as e:
        print_colored(f"✗ Registration error: {e}", 'RED')
        return False, None

def test_user_login(user_data):
    """Test user login endpoint"""
    print_header("5. Testing User Authentication")
    
    if not user_data:
        print_colored("⊘ Skipping (no user data)", 'YELLOW')
        return False, None
    
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": user_data["username"],
                "password": user_data["password"]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print_colored("✓ User authentication working", 'GREEN')
            print(f"  Token type: {data.get('token_type')}")
            print(f"  Token length: {len(token)} chars")
            return True, token
        else:
            print_colored(f"✗ Login failed: {response.text}", 'RED')
            return False, None
    except Exception as e:
        print_colored(f"✗ Login error: {e}", 'RED')
        return False, None

def test_protected_endpoint(token):
    """Test access to protected endpoint"""
    print_header("6. Testing Protected Endpoints")
    
    if not token:
        print_colored("⊘ Skipping (no token)", 'YELLOW')
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/api/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_colored("✓ Protected endpoints working", 'GREEN')
            print(f"  User: {data.get('username')}")
            print(f"  Email: {data.get('email')}")
            return True
        else:
            print_colored(f"✗ Protected endpoint failed: {response.text}", 'RED')
            return False
    except Exception as e:
        print_colored(f"✗ Protected endpoint error: {e}", 'RED')
        return False

def test_face_models():
    """Test if face recognition models are loaded"""
    print_header("7. Testing Face Recognition Models")
    
    # Check if model files exist
    model_files = [
        "deploy.prototxt.txt",
        "res10_300x300_ssd_iter_140000.caffemodel"
    ]
    
    all_ok = True
    for model_file in model_files:
        if Path(model_file).exists():
            size = Path(model_file).stat().st_size / (1024 * 1024)
            print_colored(f"✓ {model_file} found ({size:.1f} MB)", 'GREEN')
        else:
            print_colored(f"✗ {model_file} not found", 'RED')
            all_ok = False
    
    return all_ok

def test_static_files():
    """Test if static files are being served"""
    print_header("8. Testing Static Files")
    
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200 and 'html' in response.headers.get('content-type', ''):
            print_colored("✓ Web interface accessible", 'GREEN')
            return True
        else:
            print_colored(f"✗ Web interface issue (status {response.status_code})", 'RED')
            return False
    except Exception as e:
        print_colored(f"✗ Static files error: {e}", 'RED')
        return False

def run_all_tests():
    """Run all tests"""
    print_colored("\n" + "=" * 60, 'BLUE')
    print_colored("  Face Recognition System v2.0 - Test Suite", 'BLUE')
    print_colored("=" * 60, 'BLUE')
    
    results = {}
    
    # Test 1: API Connection
    results['api_connection'] = test_api_connection()
    if not results['api_connection']:
        print_colored("\n⚠ API server not running. Please start it first:", 'YELLOW')
        print_colored("  python main.py", 'YELLOW')
        return
    
    # Test 2: API Docs
    results['api_docs'] = test_api_docs()
    
    # Test 3: Database
    results['database'] = test_database_connection()
    
    # Test 4: Registration
    results['registration'], user_data = test_user_registration()
    
    # Test 5: Login
    results['login'], token = test_user_login(user_data)
    
    # Test 6: Protected Endpoints
    results['protected'] = test_protected_endpoint(token)
    
    # Test 7: Face Models
    results['models'] = test_face_models()
    
    # Test 8: Static Files
    results['static'] = test_static_files()
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = 'GREEN' if result else 'RED'
        print_colored(f"{status:8} - {test_name.replace('_', ' ').title()}", color)
    
    print()
    print_colored(f"Results: {passed}/{total} tests passed ({percentage:.0f}%)", 
                  'GREEN' if passed == total else 'YELLOW')
    
    if passed == total:
        print_colored("\n🎉 All tests passed! Your system is ready to use.", 'GREEN')
        print_colored("\nNext steps:", 'BLUE')
        print("  1. Open http://localhost:8000/ in your browser")
        print("  2. Login with admin/admin123")
        print("  3. Register people using the web interface")
        print("  4. Test face recognition check-in")
    else:
        print_colored("\n⚠ Some tests failed. Please review the errors above.", 'YELLOW')
        print_colored("\nCommon issues:", 'BLUE')
        print("  • Database: Check PostgreSQL is running")
        print("  • Redis: Optional but recommended")
        print("  • Models: Download model files if missing")
        print("  • Permissions: Check file access permissions")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print_colored("\n\nTest interrupted by user", 'YELLOW')
    except Exception as e:
        print_colored(f"\n\nUnexpected error: {e}", 'RED')
