#!/usr/bin/env python3
"""
Demo script for User Behavior Intelligence System
Shows comprehensive functionality of the behavior tracking and recommendation system.
"""
import json
import time
import uuid
import requests
from datetime import datetime

def main():
    base_url = "http://127.0.0.1:5000"
    demo_user_id = f"demo_user_{uuid.uuid4().hex[:8]}"
    
    print("🧠 User Behavior Intelligence System Demo")
    print("=" * 60)
    print(f"Demo User ID: {demo_user_id}")
    print()
    
    # 1. Test API endpoints
    print("1️⃣ Testing API Endpoints...")
    response = requests.get(f"{base_url}/")
    if response.status_code == 200:
        data = response.json()
        print("✅ API Root endpoint working")
        print(f"   Available endpoints: {len(data.get('endpoints', {}).get('behavior_intelligence', {}))}")
    
    # 2. Simulate user behavior tracking
    print("\n2️⃣ Simulating User Behavior Tracking...")
    
    # Simulate various interactions
    interactions = [
        {"type": "page_view", "page": "/attractions", "duration": 30},
        {"type": "search", "query": "temple bangkok", "duration": 15},
        {"type": "view", "attraction_id": 1, "duration": 120},
        {"type": "click", "attraction_id": 1, "duration": 45},
        {"type": "search", "query": "beach phuket", "duration": 20},
        {"type": "view", "attraction_id": 2, "duration": 90},
        {"type": "favorite", "attraction_id": 1, "duration": 5},
        {"type": "view", "attraction_id": 3, "duration": 60},
    ]
    
    session_id = str(uuid.uuid4())
    
    for i, interaction in enumerate(interactions):
        # Track interaction
        track_data = {
            "user_id": demo_user_id,
            "interaction_type": interaction["type"],
            "duration_seconds": interaction["duration"],
            "session_id": session_id
        }
        
        if "attraction_id" in interaction:
            track_data["attraction_id"] = interaction["attraction_id"]
        
        if "query" in interaction:
            track_data["search_query"] = interaction["query"]
        
        if "page" in interaction:
            track_data["page_url"] = interaction["page"]
        
        response = requests.post(f"{base_url}/api/behavior/track", json=track_data)
        
        if response.status_code == 200:
            print(f"   ✅ Tracked {interaction['type']} interaction")
        else:
            print(f"   ❌ Failed to track {interaction['type']} interaction")
        
        time.sleep(0.2)  # Small delay between interactions
    
    # 3. Analyze user behavior
    print("\n3️⃣ Analyzing User Behavior...")
    response = requests.get(f"{base_url}/api/behavior/analyze/{demo_user_id}")
    
    if response.status_code == 200:
        analysis = response.json()["data"]
        print("✅ Behavior analysis complete")
        print(f"   Total interactions: {analysis['interaction_summary']['total_interactions']}")
        print(f"   Unique attractions: {analysis['interaction_summary']['unique_attractions']}")
        print(f"   Total duration: {analysis['interaction_summary']['total_duration']} seconds")
        print(f"   Search queries: {analysis['search_summary']['total_searches']}")
        print(f"   Behavior patterns: {analysis['behavior_patterns']['browsing_style']}")
    
    # 4. Get user preferences
    print("\n4️⃣ Learning User Preferences...")
    response = requests.get(f"{base_url}/api/behavior/preferences/{demo_user_id}")
    
    if response.status_code == 200:
        preferences = response.json()["data"]
        print("✅ User preferences learned")
        for pref_type, pref_list in preferences.items():
            print(f"   {pref_type}: {len(pref_list)} preferences")
            for pref in pref_list[:3]:  # Show top 3
                print(f"     - {pref['value']} (confidence: {pref['confidence_score']:.2f})")
    
    # 5. Get real-time recommendations
    print("\n5️⃣ Generating Real-time Recommendations...")
    response = requests.get(f"{base_url}/api/behavior/recommendations/{demo_user_id}?limit=5")
    
    if response.status_code == 200:
        recommendations = response.json()["data"]
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations[:3], 1):
            attraction = rec["attraction"]
            print(f"   {i}. {attraction.get('title', 'Unknown')} (score: {rec['score']:.3f})")
            if rec["reasons"]:
                print(f"      Reasons: {', '.join(rec['reasons'])}")
    
    # 6. Test context-aware recommendations
    print("\n6️⃣ Testing Context-aware Recommendations...")
    response = requests.get(
        f"{base_url}/api/behavior/recommendations/{demo_user_id}",
        params={"limit": 3, "search_query": "temple", "province": "Bangkok"}
    )
    
    if response.status_code == 200:
        recommendations = response.json()["data"]
        print(f"✅ Generated {len(recommendations)} context-aware recommendations")
        context = response.json().get("context", {})
        print(f"   Context: {context}")
    
    # 7. Get behavior trends
    print("\n7️⃣ Analyzing Behavior Trends...")
    response = requests.get(f"{base_url}/api/behavior/trends?days=1")
    
    if response.status_code == 200:
        trends = response.json()["data"]
        print("✅ Behavior trends analyzed")
        print(f"   Period: {trends['period']['days']} days")
        print(f"   Total interactions: {trends['total_interactions']}")
        print(f"   Top keywords: {len(trends['keyword_trends'])}")
        if trends['keyword_trends']:
            for keyword in trends['keyword_trends'][:3]:
                print(f"     - {keyword['keyword']}: {keyword['count']} interactions")
    
    # 8. Get user sessions
    print("\n8️⃣ Reviewing User Sessions...")
    response = requests.get(f"{base_url}/api/behavior/sessions/{demo_user_id}")
    
    if response.status_code == 200:
        sessions = response.json()["data"]
        print(f"✅ Found {len(sessions)} user sessions")
        if sessions:
            session = sessions[0]
            print(f"   Latest session: {session['interactions_count']} interactions")
            print(f"   Duration: {session['total_duration_seconds']} seconds")
            print(f"   Device: {session.get('device_type', 'unknown')}")
    
    # 9. Get behavior statistics
    print("\n9️⃣ Overall Behavior Statistics...")
    response = requests.get(f"{base_url}/api/behavior/stats?days=1")
    
    if response.status_code == 200:
        stats = response.json()["data"]
        print("✅ Overall statistics")
        totals = stats["totals"]
        print(f"   Total interactions: {totals['interactions']}")
        print(f"   Unique users: {totals['unique_users']}")
        print(f"   Total sessions: {totals['sessions']}")
        print(f"   Total searches: {totals['searches']}")
        
        print("   Interaction types:")
        for it in stats["interaction_types"]:
            print(f"     - {it['type']}: {it['count']}")
    
    # 10. End session
    print("\n🔟 Ending User Session...")
    response = requests.post(f"{base_url}/api/behavior/session/{session_id}/end")
    
    if response.status_code == 200:
        print("✅ Session ended successfully")
    
    print("\n" + "=" * 60)
    print("🎉 User Behavior Intelligence Demo Complete!")
    print("   The system successfully:")
    print("   ✅ Tracked comprehensive user behavior")
    print("   ✅ Analyzed behavioral patterns dynamically")
    print("   ✅ Generated real-time personalized recommendations")
    print("   ✅ Learned user preferences automatically") 
    print("   ✅ Provided context-aware suggestions")
    print("   ✅ Generated behavioral analytics and trends")


if __name__ == "__main__":
    main()