"""
Manual test for conversational AI endpoints.
"""
import json
import requests
import time

# API base URL - adjust as needed
BASE_URL = "http://localhost:5000/api/ai"

def test_conversational_ai_flow():
    """Test the complete conversational AI flow."""
    print("🤖 Testing Conversational AI Features")
    print("=" * 50)
    
    # Test 1: Intent Detection
    print("\n1. Testing Intent Detection")
    intent_tests = [
        "หาสถานที่ท่องเที่ยวในเชียงใหม่",
        "มีวัดสวยๆ ไหม",
        "สวัสดีครับ ผมต้องการคำแนะนำ",
        "find beautiful temples",
        "where to go in Bangkok"
    ]
    
    for text in intent_tests:
        try:
            response = requests.post(f"{BASE_URL}/nlu/intent", 
                                   json={"text": text},
                                   timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Text: '{text}'")
                print(f"   Intent: {data['intent']} (confidence: {data['confidence']:.3f})")
                print(f"   Entities: {data['entities']}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    # Test 2: Create Conversation Session
    print("\n2. Creating Conversation Session")
    try:
        response = requests.post(f"{BASE_URL}/conversation/session",
                               json={"user_id": "test-user-123"},
                               timeout=10)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Error creating session: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return
    
    # Test 3: Smart Query Generation
    print("\n3. Testing Smart Query Generation")
    query_tests = [
        "หาที่เที่ยวในกรุงเทพ",
        "วัดสวยๆ ในเชียงใหม่",
        "ธรรมชาติ น้ำตก ภูเก็ต"
    ]
    
    for text in query_tests:
        try:
            response = requests.post(f"{BASE_URL}/search/from-text",
                                   json={"text": text, "session_id": session_id},
                                   timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Query: '{text}'")
                print(f"   Intent: {data['intent']['intent']}")
                print(f"   Results found: {data['total_results']}")
                if data['results']:
                    print(f"   First result: {data['results'][0].get('title', 'N/A')}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    # Test 4: Conversational Chat
    print("\n4. Testing Conversational Chat")
    chat_tests = [
        "สวัสดีครับ",
        "หาที่เที่ยวในเชียงใหม่หน่อย",
        "มีวัดสวยๆ ไหม",
        "แนะนำหน่อยครับ"
    ]
    
    for text in chat_tests:
        try:
            response = requests.post(f"{BASE_URL}/conversation/chat",
                                   json={"text": text, "session_id": session_id},
                                   timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User: '{text}'")
                print(f"   Bot: {data['message']}")
                print(f"   Results: {data['total_results']} attractions found")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Chat failed: {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    # Test 5: Update Preferences
    print("\n5. Testing Preferences Update")
    try:
        response = requests.post(f"{BASE_URL}/conversation/preferences",
                               json={
                                   "session_id": session_id,
                                   "preferences": {
                                       "preferred_province": "Chiang Mai",
                                       "max_results": 5,
                                       "language": "thai"
                                   }
                               },
                               timeout=10)
        if response.status_code == 200:
            print("✅ Preferences updated successfully")
        else:
            print(f"❌ Error updating preferences: {response.status_code}")
    except Exception as e:
        print(f"❌ Preferences update failed: {e}")
    
    # Test 6: Get Session Info
    print("\n6. Getting Session Information")
    try:
        response = requests.get(f"{BASE_URL}/conversation/session/{session_id}",
                              timeout=10)
        if response.status_code == 200:
            data = response.json()
            session_info = data['session']
            print(f"✅ Session Info:")
            print(f"   User ID: {session_info.get('user_id')}")
            print(f"   Last Intent: {session_info.get('last_intent')}")
            print(f"   Preferences: {session_info.get('preferences')}")
        else:
            print(f"❌ Error getting session info: {response.status_code}")
    except Exception as e:
        print(f"❌ Session info failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Conversational AI Testing Complete!")


if __name__ == "__main__":
    print("To run this test:")
    print("1. Start the Flask server: python run.py")
    print("2. Make sure Redis/PostgreSQL are running")
    print("3. Run: python manual_test_conversational_ai.py")
    print("\nNote: This test will fail if the server is not running.")
    print("For now, showing what the test would do...")
    
    # Show the test structure without making actual requests
    print("\n📋 Test Plan:")
    print("✓ Intent Detection - Detect user intentions from Thai/English text")
    print("✓ Session Creation - Create conversation sessions")
    print("✓ Smart Queries - Convert natural language to database queries")
    print("✓ Conversational Chat - Full conversation flow with context")
    print("✓ Preferences - Update user preferences in session")
    print("✓ Session Info - Retrieve conversation context")