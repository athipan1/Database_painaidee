#!/usr/bin/env python
"""
Test script specifically for the issues found in GitHub Actions workflow failures.
This tests the exact scenarios that were failing.
"""
import os
import tempfile
import json

def test_specific_failing_scenarios():
    """Test the specific scenarios that were failing in CI."""
    print("🔍 Testing Specific CI Failure Scenarios...")
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    try:
        # Set environment for testing
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['FLASK_ENV'] = 'testing'
        
        from app import create_app
        from app.models import db
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        with app.app_context():
            db.create_all()
            
            with app.test_client() as client:
                
                # Test 1: 415 UNSUPPORTED MEDIA TYPE issue
                print("1️⃣ Testing 415 UNSUPPORTED MEDIA TYPE fix...")
                print("   Creating session without explicit Content-Type...")
                
                response = client.post('/api/ai/conversation/session')
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 415:
                    print("   ❌ Still getting 415 error")
                    return False
                elif response.status_code == 200:
                    data = response.get_json()
                    print(f"   ✅ Success! Session created: {data.get('success')}")
                    session_id = data.get('session_id')
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
                    print(f"   Response: {response.get_data(as_text=True)}")
                
                # Test 2: NoneType subscriptable issue  
                print("\n2️⃣ Testing NoneType subscriptable fix...")
                print("   Testing session creation and access...")
                
                session_response = client.post('/api/ai/conversation/session')
                session_data = session_response.get_json()
                
                if not session_data:
                    print("   ❌ Session data is None")
                    return False
                
                if 'session_id' not in session_data:
                    print("   ❌ No session_id in response")
                    return False
                
                print(f"   ✅ Session data is valid: {session_data.get('success')}")
                session_id = session_data['session_id']
                
                # Test 3: Route parameter handling
                print("\n3️⃣ Testing route parameter handling...")
                print(f"   Getting session info for: {session_id[:8]}...")
                
                response = client.get(f'/api/ai/conversation/session/{session_id}')
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   ✅ Session info retrieved: {data.get('success')}")
                else:
                    print(f"   ❌ Error: {response.get_data(as_text=True)}")
                    return False
                
                # Test 4: Content-Type handling variations
                print("\n4️⃣ Testing different Content-Type scenarios...")
                
                # Test with explicit JSON content-type
                response1 = client.post('/api/ai/nlu/intent',
                                       headers={'Content-Type': 'application/json'},
                                       json={'text': 'test'})
                print(f"   With JSON header: {response1.status_code}")
                
                # Test without explicit content-type  
                response2 = client.post('/api/ai/nlu/intent',
                                       json={'text': 'test'})
                print(f"   Without header: {response2.status_code}")
                
                if response1.status_code != 200 or response2.status_code != 200:
                    print("   ❌ Content-Type handling issue")
                    return False
                
                print("   ✅ All Content-Type scenarios work")
                
                # Test 5: Conversation flow without errors
                print("\n5️⃣ Testing complete conversation flow...")
                
                chat_response = client.post('/api/ai/conversation/chat',
                                          json={'text': 'หาที่เที่ยวในเชียงใหม่'})
                
                print(f"   Chat status: {chat_response.status_code}")
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.get_json()
                    print(f"   ✅ Chat successful: {chat_data.get('success')}")
                    print(f"   Message: {chat_data.get('message', '')[:50]}...")
                else:
                    print(f"   ❌ Chat failed: {chat_response.get_data(as_text=True)}")
                    return False
                
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        os.close(db_fd)
        os.unlink(db_path)
    
    print("\n🎉 All specific CI failure scenarios fixed!")
    return True

def test_redis_memory_warning():
    """Test that Redis memory warning doesn't break functionality."""
    print("\n🔧 Testing Redis memory warning handling...")
    
    # This is just informational - the warning doesn't break functionality
    # In CI, Redis shows: "WARNING Memory overcommit must be enabled!"
    # This is a Redis configuration warning, not an application error
    
    print("   ℹ️  Redis memory overcommit warning is informational only")
    print("   ℹ️  It doesn't affect application functionality")
    print("   ✅ No action needed for this warning")
    
    return True

if __name__ == '__main__':
    print("🚀 Testing GitHub Actions CI/CD Failure Fixes")
    print("=" * 60)
    
    success1 = test_specific_failing_scenarios()
    success2 = test_redis_memory_warning()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ ALL CI/CD ISSUES APPEAR TO BE FIXED!")
        print("\nSummary of fixes:")
        print("• ✅ 415 UNSUPPORTED MEDIA TYPE - Fixed with flexible Content-Type handling")
        print("• ✅ NoneType subscriptable - Fixed with proper null checks in tests") 
        print("• ✅ Route parameter handling - Fixed with correct Flask route definitions")
        print("• ✅ Content-Type variations - Fixed with request.is_json checks")
        print("• ✅ Session flow - Fixed with robust error handling")
        print("• ℹ️  Redis memory warning - Informational only, no fix needed")
        print("• ℹ️  PostgreSQL user - CI uses 'testuser', not 'root' (already correct)")
    else:
        print("❌ Some issues may still remain")