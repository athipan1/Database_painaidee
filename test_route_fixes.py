#!/usr/bin/env python
"""
Minimal test to verify conversational AI fixes work.
"""
import os
import tempfile
import json

def test_route_fixes():
    """Test the route fixes work with proper Content-Type handling."""
    print("🧪 Testing Route Fixes...")
    
    # Create temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    
    try:
        # Set environment variables for testing
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        os.environ['FLASK_ENV'] = 'testing'
        
        # Import after setting environment
        from app import create_app
        from app.models import db
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        with app.app_context():
            db.create_all()
            
            with app.test_client() as client:
                print("1️⃣ Testing intent detection endpoint...")
                
                # Test 1: Intent detection with JSON
                response = client.post('/api/ai/nlu/intent', 
                                     json={'text': 'หาที่เที่ยวในเชียงใหม่'})
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"   ✅ Intent: {data.get('intent')}")
                    print(f"   ✅ Success: {data.get('success')}")
                else:
                    print(f"   ❌ Error: {response.get_data(as_text=True)}")
                
                print("\n2️⃣ Testing session creation endpoint...")
                
                # Test 2: Session creation with proper headers
                response = client.post('/api/ai/conversation/session',
                                     headers={'Content-Type': 'application/json'},
                                     json={})
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    session_id = data.get('session_id')
                    print(f"   ✅ Session created: {session_id[:10]}..." if session_id else "No ID")
                    print(f"   ✅ Success: {data.get('success')}")
                    
                    if session_id:
                        print("\n3️⃣ Testing session info endpoint...")
                        
                        # Test 3: Session info retrieval 
                        response = client.get(f'/api/ai/conversation/session/{session_id}')
                        print(f"   Status: {response.status_code}")
                        if response.status_code == 200:
                            data = response.get_json()
                            print(f"   ✅ Session info retrieved: {data.get('success')}")
                        else:
                            print(f"   ❌ Error: {response.get_data(as_text=True)}")
                            
                        print("\n4️⃣ Testing conversational chat endpoint...")
                        
                        # Test 4: Chat endpoint
                        response = client.post('/api/ai/conversation/chat',
                                             json={'text': 'สวัสดี', 'session_id': session_id})
                        print(f"   Status: {response.status_code}")
                        if response.status_code == 200:
                            data = response.get_json()
                            print(f"   ✅ Chat response: {data.get('message', '')[:50]}...")
                            print(f"   ✅ Success: {data.get('success')}")
                        else:
                            print(f"   ❌ Error: {response.get_data(as_text=True)}")
                            
                else:
                    print(f"   ❌ Session creation failed: {response.get_data(as_text=True)}")
                
                print("\n5️⃣ Testing AI stats endpoint...")
                
                # Test 5: AI stats with conversation metrics
                response = client.get('/api/ai/stats')
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if 'conversations' in data:
                        print(f"   ✅ Conversation stats included: {data['conversations']}")
                    else:
                        print("   ❌ No conversation stats found")
                else:
                    print(f"   ❌ Error: {response.get_data(as_text=True)}")
                    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        os.close(db_fd)
        os.unlink(db_path)
    
    print("\n🎉 Route testing completed!")
    return True

if __name__ == '__main__':
    success = test_route_fixes()
    if success:
        print("✅ All route fixes appear to be working!")
    else:
        print("❌ Some issues remain")