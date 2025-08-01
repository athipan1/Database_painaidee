#!/usr/bin/env python3
"""
Test script for User Behavior Intelligence System
พัฒนาระบบเรียนรู้พฤติกรรมผู้ใช้ (User Behavior Intelligence)
"""
import json
import time
import uuid
from datetime import datetime, timedelta
import requests
from typing import Dict, List

class BehaviorIntelligenceTest:
    """Test class for behavior intelligence features."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.test_session_id = str(uuid.uuid4())
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Dict = None):
        """Log test result."""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    def test_api_health(self):
        """Test API health check."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200
            
            self.log_test(
                "API Health Check",
                success,
                f"Status: {response.status_code}",
                response.json() if success else None
            )
            return success
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_behavior_tracking(self):
        """
        Test behavior tracking functionality.
        ติดตามพฤติกรรมผู้ใช้: การคลิก, การค้นหา, การกด Favorite, เวลาเข้าเยี่ยมชม
        """
        test_cases = [
            {
                'name': 'Page View Tracking',
                'data': {
                    'user_id': self.test_user_id,
                    'interaction_type': 'view',
                    'duration_seconds': 45,
                    'page_url': '/attractions/1',
                    'session_id': self.test_session_id
                }
            },
            {
                'name': 'Click Tracking',
                'data': {
                    'user_id': self.test_user_id,
                    'attraction_id': 1,
                    'interaction_type': 'click',
                    'duration_seconds': 120,
                    'session_id': self.test_session_id
                }
            },
            {
                'name': 'Search Tracking',
                'data': {
                    'user_id': self.test_user_id,
                    'interaction_type': 'search',
                    'search_query': 'temple bangkok',
                    'duration_seconds': 30,
                    'session_id': self.test_session_id
                }
            },
            {
                'name': 'Favorite Tracking',
                'data': {
                    'user_id': self.test_user_id,
                    'attraction_id': 1,
                    'interaction_type': 'favorite',
                    'session_id': self.test_session_id
                }
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/api/behavior/track",
                    json=test_case['data'],
                    timeout=10
                )
                
                success = response.status_code == 200
                if success:
                    result = response.json()
                    success = result.get('success', False)
                
                self.log_test(
                    f"Behavior Tracking - {test_case['name']}",
                    success,
                    f"Status: {response.status_code}",
                    response.json() if response.status_code == 200 else None
                )
                
                if not success:
                    all_passed = False
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                self.log_test(
                    f"Behavior Tracking - {test_case['name']}",
                    False,
                    f"Error: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_behavior_analysis(self):
        """
        Test behavior analysis functionality.
        การวิเคราะห์แนวโน้มพฤติกรรมของผู้ใช้อย่าง dynamic
        """
        try:
            # Wait a moment for data to be processed
            time.sleep(1)
            
            response = requests.get(
                f"{self.base_url}/api/behavior/analyze/{self.test_user_id}",
                params={'days': 30},
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data')
                
                # Validate analysis structure
                if success and data:
                    required_keys = [
                        'user_id', 'analysis_period', 'interaction_summary',
                        'session_summary', 'search_summary', 'behavior_patterns'
                    ]
                    success = all(key in data for key in required_keys)
            
            self.log_test(
                "Behavior Analysis",
                success,
                f"Status: {response.status_code}",
                data
            )
            return success
            
        except Exception as e:
            self.log_test("Behavior Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_real_time_recommendations(self):
        """
        Test real-time recommendation system.
        ระบบแนะนำแบบ Real-time: ใช้ข้อมูลที่วิเคราะห์เพื่อสร้างคำแนะนำแบบเรียลไทม์
        """
        try:
            # Test basic recommendations
            response = requests.get(
                f"{self.base_url}/api/behavior/recommendations/{self.test_user_id}",
                params={'limit': 5},
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data', [])
                
                # Validate recommendation structure
                if success and data:
                    for rec in data[:3]:  # Check first 3 recommendations
                        required_keys = ['attraction', 'score', 'reasons']
                        if not all(key in rec for key in required_keys):
                            success = False
                            break
            
            self.log_test(
                "Real-time Recommendations - Basic",
                success,
                f"Status: {response.status_code}, Count: {len(data) if data else 0}",
                data[:2] if data else None  # Show first 2 recommendations
            )
            
            # Test context-aware recommendations
            response_context = requests.get(
                f"{self.base_url}/api/behavior/recommendations/{self.test_user_id}",
                params={
                    'limit': 5,
                    'search_query': 'temple',
                    'province': 'Bangkok'
                },
                timeout=10
            )
            
            context_success = response_context.status_code == 200
            if context_success:
                result = response_context.json()
                context_success = result.get('success', False)
            
            self.log_test(
                "Real-time Recommendations - Context-Aware",
                context_success,
                f"Status: {response_context.status_code}",
                result.get('data', [])[:1] if context_success else None
            )
            
            return success and context_success
            
        except Exception as e:
            self.log_test("Real-time Recommendations", False, f"Error: {str(e)}")
            return False
    
    def test_behavior_trends(self):
        """Test behavior trends analysis."""
        try:
            response = requests.get(
                f"{self.base_url}/api/behavior/trends",
                params={'days': 30},
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data')
                
                # Validate trend structure
                if success and data:
                    required_keys = [
                        'period', 'daily_trends', 'keyword_trends',
                        'province_trends', 'seasonal_patterns'
                    ]
                    success = all(key in data for key in required_keys)
            
            self.log_test(
                "Behavior Trends",
                success,
                f"Status: {response.status_code}",
                data
            )
            return success
            
        except Exception as e:
            self.log_test("Behavior Trends", False, f"Error: {str(e)}")
            return False
    
    def test_user_preferences(self):
        """Test user preference learning."""
        try:
            # Wait for preferences to be learned
            time.sleep(1)
            
            response = requests.get(
                f"{self.base_url}/api/behavior/preferences/{self.test_user_id}",
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data', {})
            
            self.log_test(
                "User Preferences",
                success,
                f"Status: {response.status_code}, Types: {list(data.keys()) if data else []}",
                data
            )
            return success
            
        except Exception as e:
            self.log_test("User Preferences", False, f"Error: {str(e)}")
            return False
    
    def test_user_sessions(self):
        """Test user session tracking."""
        try:
            response = requests.get(
                f"{self.base_url}/api/behavior/sessions/{self.test_user_id}",
                params={'days': 30},
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data', [])
            
            self.log_test(
                "User Sessions",
                success,
                f"Status: {response.status_code}, Sessions: {len(data) if data else 0}",
                data[:1] if data else None  # Show first session
            )
            return success
            
        except Exception as e:
            self.log_test("User Sessions", False, f"Error: {str(e)}")
            return False
    
    def test_search_queries(self):
        """Test search query tracking."""
        try:
            response = requests.get(
                f"{self.base_url}/api/behavior/search-queries/{self.test_user_id}",
                params={'days': 30},
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data', [])
            
            self.log_test(
                "Search Queries",
                success,
                f"Status: {response.status_code}, Queries: {len(data) if data else 0}",
                data[:2] if data else None  # Show first 2 queries
            )
            return success
            
        except Exception as e:
            self.log_test("Search Queries", False, f"Error: {str(e)}")
            return False
    
    def test_behavior_stats(self):
        """Test behavior statistics."""
        try:
            response = requests.get(
                f"{self.base_url}/api/behavior/stats",
                params={'days': 30},
                timeout=10
            )
            
            success = response.status_code == 200
            data = None
            
            if success:
                result = response.json()
                success = result.get('success', False)
                data = result.get('data')
                
                # Validate stats structure
                if success and data:
                    required_keys = ['period', 'totals', 'interaction_types']
                    success = all(key in data for key in required_keys)
            
            self.log_test(
                "Behavior Statistics",
                success,
                f"Status: {response.status_code}",
                data
            )
            return success
            
        except Exception as e:
            self.log_test("Behavior Statistics", False, f"Error: {str(e)}")
            return False
    
    def test_session_end(self):
        """Test session ending."""
        try:
            response = requests.post(
                f"{self.base_url}/api/behavior/session/{self.test_session_id}/end",
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                result = response.json()
                success = result.get('success', False)
            
            self.log_test(
                "Session End",
                success,
                f"Status: {response.status_code}",
                response.json() if response.status_code == 200 else None
            )
            return success
            
        except Exception as e:
            self.log_test("Session End", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all behavior intelligence tests."""
        print("\n🧠 Testing User Behavior Intelligence System")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("API Health", self.test_api_health),
            ("Behavior Tracking", self.test_behavior_tracking),
            ("Behavior Analysis", self.test_behavior_analysis),
            ("Real-time Recommendations", self.test_real_time_recommendations),
            ("Behavior Trends", self.test_behavior_trends),
            ("User Preferences", self.test_user_preferences),
            ("User Sessions", self.test_user_sessions),
            ("Search Queries", self.test_search_queries),
            ("Behavior Statistics", self.test_behavior_stats),
            ("Session End", self.test_session_end)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name}...")
            if test_func():
                passed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! User Behavior Intelligence system is working correctly.")
        else:
            print(f"⚠️  {total-passed} test(s) failed. Please check the implementation.")
        
        return passed == total
    
    def generate_report(self, filename: str = "behavior_intelligence_test_report.json"):
        """Generate detailed test report."""
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['success']),
                'failed': sum(1 for r in self.test_results if not r['success']),
                'success_rate': (sum(1 for r in self.test_results if r['success']) / len(self.test_results)) * 100 if self.test_results else 0
            },
            'test_results': self.test_results,
            'test_user_id': self.test_user_id,
            'test_session_id': self.test_session_id,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed test report saved to: {filename}")
        return report


def main():
    """Main test function."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Test User Behavior Intelligence System')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL for API')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    
    args = parser.parse_args()
    
    # Create test instance
    tester = BehaviorIntelligenceTest(args.url)
    
    # Run tests
    success = tester.run_all_tests()
    
    # Generate report if requested
    if args.report:
        tester.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()