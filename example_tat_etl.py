#!/usr/bin/env python3
"""
Example script demonstrating TAT Open Data ETL functionality.
This script shows how to use the new TAT CSV ETL pipeline.
"""

import logging
import sys
from etl_orchestrator import ETLOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Example of running TAT CSV ETL pipeline."""
    print("🚀 TAT Open Data ETL Example")
    print("=" * 50)
    
    # TAT Open Data CSV URL from the problem statement
    csv_url = "https://opendata.tourismthailand.org/data/attractions.csv"
    
    print(f"📊 CSV URL: {csv_url}")
    print(f"🔧 Geocoding: Disabled (for demo)")
    print()
    
    try:
        print("🔄 Running TAT CSV ETL process...")
        
        # Run the ETL process
        result = ETLOrchestrator.run_tat_csv_etl(
            csv_url=csv_url,
            timeout=60,  # Longer timeout for real CSV download
            enable_geocoding=False,  # Disable to avoid API requirements
            google_api_key=None
        )
        
        print("✅ ETL Process completed successfully!")
        print()
        print("📈 Results:")
        print(f"   • Total processed: {result.get('total_processed', 0)}")
        print(f"   • Successfully saved: {result.get('saved', 0)}")
        print(f"   • Updated: {result.get('updated', 0)}")
        print(f"   • Skipped (duplicates): {result.get('skipped', 0)}")
        print(f"   • Errors: {result.get('errors', 0)}")
        
        if result.get('errors', 0) > 0:
            print(f"⚠️  Some items had errors during processing")
        
        return 0
        
    except Exception as e:
        print(f"❌ ETL process failed: {e}")
        logger.exception("Detailed error information:")
        return 1


def demo_with_sample_data():
    """Demo with sample data (no network required)."""
    print("🧪 Demo with Sample Data (No Network Required)")
    print("=" * 50)
    
    try:
        from extractors.tat_csv import TATCSVExtractor
        from transformers.attraction_transformer import AttractionTransformer
        import tempfile
        import unittest.mock
        
        # Sample TAT CSV data
        sample_csv = """ชื่อสถานที่,รายละเอียด,จังหวัด,อำเภอ,ละติจูด,ลองจิจูด,ประเภท,เวลาเปิด,ค่าเข้าชม,โทรศัพท์
วัดพระแก้ว,วัดพระแก้วเป็นวัดที่สำคัญในประเทศไทย,กรุงเทพมหานคร,พระนคร,13.7515,100.4924,วัด,08:30-15:30,500 บาท,02-123-4567
อุทยานประวัติศาสตร์สุโขทัย,อุทยานประวัติศาสตร์ที่มีความสำคัญทางประวัติศาสตร์,สุโขทัย,เมืองสุโขทัย,17.0238,99.7033,อุทยาน,06:00-18:00,100 บาท,055-123-456
ตลาดน้ำดำเนินสะดวก,ตลาดน้ำที่มีชื่อเสียง,ราชบุรี,ดำเนินสะดวก,13.5177,99.9551,ตลาด,07:00-17:00,ฟรี,032-123-456"""
        
        # Mock the HTTP request
        class MockResponse:
            def __init__(self, content):
                self.content = content.encode('utf-8')
            
            def raise_for_status(self):
                pass
        
        with unittest.mock.patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(sample_csv)
            
            # Run ETL with sample data
            result = ETLOrchestrator.run_tat_csv_etl(
                csv_url="http://sample.com/attractions.csv",
                timeout=30,
                enable_geocoding=False
            )
        
        print("✅ Sample data ETL completed!")
        print()
        print("📈 Results:")
        print(f"   • Total processed: {result.get('total_processed', 0)}")
        print(f"   • Successfully saved: {result.get('saved', 0)}")
        print(f"   • Updated: {result.get('updated', 0)}")
        print(f"   • Skipped (duplicates): {result.get('skipped', 0)}")
        print(f"   • Errors: {result.get('errors', 0)}")
        
        print()
        print("🎯 Sample attractions processed:")
        print("   • วัดพระแก้ว (กรุงเทพมหานคร)")
        print("   • อุทยานประวัติศาสตร์สุโขทัย (สุโขทัย)")
        print("   • ตลาดน้ำดำเนินสะดวก (ราชบุรี)")
        
        return 0
        
    except Exception as e:
        print(f"❌ Sample data demo failed: {e}")
        logger.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Sample data demo (no network required)")
    print("2. Real TAT Open Data (requires network)")
    print()
    
    choice = input("Enter choice (1 or 2, default=1): ").strip() or "1"
    print()
    
    if choice == "1":
        sys.exit(demo_with_sample_data())
    elif choice == "2":
        sys.exit(main())
    else:
        print("Invalid choice. Using sample data demo.")
        sys.exit(demo_with_sample_data())