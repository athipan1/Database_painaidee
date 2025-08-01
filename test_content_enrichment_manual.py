#!/usr/bin/env python3
"""
Manual test script for AI Content Enrichment features.
Run this to validate that all new endpoints are working correctly.
"""

import requests
import json
import time
from datetime import datetime


class ContentEnrichmentTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/ai/enrich"
        
    def test_description_generation(self):
        """Test description generation with sample data."""
        print("\n=== Testing Description Generation ===")
        
        # Test with custom data
        test_data = {
            "title": "Wat Phra Kaew (Temple of the Emerald Buddha)",
            "body": "Sacred temple in Bangkok's Grand Palace complex",
            "province": "Bangkok"
        }
        
        try:
            response = requests.post(f"{self.api_base}/description", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Description generated successfully")
                print(f"  Method: {result.get('method', 'unknown')}")
                print(f"  Preview: {result.get('description', '')[:100]}...")
                return result
            else:
                print(f"✗ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_multilingual_translation(self):
        """Test multilingual content generation."""
        print("\n=== Testing Multilingual Translation ===")
        
        test_data = {
            "text": "Beautiful ancient temple with traditional Thai architecture",
            "languages": ["en", "th", "zh"]
        }
        
        try:
            response = requests.post(f"{self.api_base}/multilingual", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Translation completed successfully")
                print(f"  Method: {result.get('method', 'unknown')}")
                translations = result.get('translations', {})
                for lang, text in translations.items():
                    print(f"  {lang}: {text}")
                return result
            else:
                print(f"✗ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_key_features_extraction(self):
        """Test key features extraction."""
        print("\n=== Testing Key Features Extraction ===")
        
        test_data = {
            "text": "Family-friendly beachfront resort with great view, traditional architecture, and peaceful atmosphere perfect for romantic getaways"
        }
        
        try:
            response = requests.post(f"{self.api_base}/features", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Features extracted successfully")
                features = result.get('features', [])
                categories = result.get('categories', {})
                print(f"  Found {len(features)} features: {', '.join(features)}")
                print(f"  Categories: {list(categories.keys())}")
                return result
            else:
                print(f"✗ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_image_generation(self):
        """Test image generation."""
        print("\n=== Testing Image Generation ===")
        
        test_data = {
            "title": "Wat Phra Kaew",
            "body": "Sacred temple in Bangkok",
            "province": "Bangkok",
            "num_images": 2
        }
        
        try:
            response = requests.post(f"{self.api_base}/images", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Images generated successfully")
                print(f"  Method: {result.get('method', 'unknown')}")
                image_urls = result.get('image_urls', [])
                print(f"  Generated {len(image_urls)} images:")
                for i, url in enumerate(image_urls, 1):
                    print(f"    {i}. {url}")
                return result
            else:
                print(f"✗ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_enrichment_stats(self):
        """Test enrichment statistics."""
        print("\n=== Testing Enrichment Statistics ===")
        
        try:
            response = requests.get(f"{self.api_base}/stats")
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Statistics retrieved successfully")
                print(f"  Total attractions: {result.get('total_attractions', 0)}")
                print(f"  Enriched attractions: {result.get('enriched_attractions', 0)}")
                print(f"  Coverage: {result.get('enrichment_coverage', 0)}%")
                
                features = result.get('features', {})
                for feature_name, feature_data in features.items():
                    count = feature_data.get('count', 0)
                    coverage = feature_data.get('coverage', 0)
                    print(f"  {feature_name}: {count} ({coverage}%)")
                
                return result
            else:
                print(f"✗ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def test_service_functionality(self):
        """Test the service directly without API calls."""
        print("\n=== Testing Service Functionality ===")
        
        try:
            from app.services.content_enrichment import ContentEnrichmentService
            
            service = ContentEnrichmentService()
            print(f"✓ Service initialized successfully")
            print(f"  OpenAI available: {service.openai_available}")
            print(f"  OpenAI enabled: {service.openai_enabled}")
            print(f"  Translator available: {service.translator_available}")
            print(f"  Language detection available: {service.langdetect_available}")
            
            # Test key features extraction
            features_result = service.extract_key_features("family-friendly beachfront resort")
            print(f"  ✓ Key features test: {features_result['features']}")
            
            # Test description generation
            desc_result = service.generate_place_description({
                'title': 'Test Temple',
                'body': 'Beautiful temple',
                'province': 'Bangkok'
            })
            print(f"  ✓ Description generation: {desc_result['success']}")
            
            # Test multilingual
            multi_result = service.generate_multilingual_content("Hello world", ['en', 'th'])
            print(f"  ✓ Multilingual test: {multi_result['success']}")
            
            # Test image generation
            img_result = service.generate_images({
                'title': 'Test Location',
                'body': 'Test description',
                'province': 'Bangkok'
            }, 1)
            print(f"  ✓ Image generation: {img_result['success']}")
            
            return True
            
        except Exception as e:
            print(f"✗ Service test error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("AI Content Enrichment Features Test Suite")
        print("=" * 50)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now()}")
        
        # Test service functionality first (doesn't require server)
        service_test = self.test_service_functionality()
        
        # Test API endpoints (requires server to be running)
        print("\nAPI Endpoint Tests (requires server running):")
        
        tests = [
            ("Description Generation", self.test_description_generation),
            ("Multilingual Translation", self.test_multilingual_translation),
            ("Key Features Extraction", self.test_key_features_extraction),
            ("Image Generation", self.test_image_generation),
            ("Enrichment Statistics", self.test_enrichment_stats),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result is not None
            except Exception as e:
                print(f"✗ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print(f"Service Functionality: {'✓ PASS' if service_test else '✗ FAIL'}")
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{test_name}: {status}")
        
        total_tests = len(results) + 1  # +1 for service test
        passed_tests = sum(results.values()) + (1 if service_test else 0)
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! AI Content Enrichment is working correctly.")
        elif passed_tests >= len(results):  # All API tests failed but service works
            print("⚠️  Service works but API tests failed. Make sure Flask server is running:")
            print("   python run.py")
        else:
            print("❌ Some tests failed. Check the error messages above.")
        
        return passed_tests == total_tests


def main():
    """Main test function."""
    tester = ContentEnrichmentTester()
    
    # Check if we should use a different base URL
    import sys
    if len(sys.argv) > 1:
        tester.base_url = sys.argv[1]
        tester.api_base = f"{tester.base_url}/api/ai/enrich"
        print(f"Using custom base URL: {tester.base_url}")
    
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()