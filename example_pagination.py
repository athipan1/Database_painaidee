#!/usr/bin/env python3
"""
Example showing how to use the new pagination features.
"""
import sys
import os
from unittest.mock import patch

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def example_basic_usage():
    """Show basic pagination usage"""
    print("=== Basic Pagination Usage ===")
    
    from app.utils.fetch import fetch_all_paginated_data, fetch_paginated_data
    
    # Mock API responses for demonstration
    mock_responses = [
        [{"id": 1, "title": "Post 1"}, {"id": 2, "title": "Post 2"}],  # Page 1
        [{"id": 3, "title": "Post 3"}],  # Page 2
        []  # Page 3 (empty, stops pagination)
    ]
    
    with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
        mock_fetch.side_effect = mock_responses
        
        # Fetch all paginated data at once
        all_items = fetch_all_paginated_data(
            base_url="https://api.example.com/posts",
            page_size=2,
            max_pages=10,
            page_param='page',
            limit_param='limit'
        )
        
        print(f"Total items fetched: {len(all_items)}")
        for item in all_items:
            print(f"  - {item['title']}")
    
    print()


def example_memory_efficient():
    """Show memory-efficient page-by-page processing"""
    print("=== Memory-Efficient Page-by-Page Processing ===")
    
    from app.utils.fetch import fetch_paginated_data
    
    # Mock API responses for demonstration
    mock_responses = [
        {"data": [{"id": 1, "title": "Item 1"}, {"id": 2, "title": "Item 2"}]},  # Page 1
        {"data": [{"id": 3, "title": "Item 3"}]},  # Page 2
        {"data": []}  # Page 3 (empty data array)
    ]
    
    with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
        mock_fetch.side_effect = mock_responses
        
        total_processed = 0
        for page_num, items in fetch_paginated_data(
            base_url="https://api.example.com/data",
            page_size=2,
            max_pages=5
        ):
            print(f"Processing page {page_num}: {len(items)} items")
            for item in items:
                print(f"  - Processing: {item['title']}")
                total_processed += 1
                # Here you could process each item individually
                # and free memory before processing the next page
        
        print(f"Total items processed: {total_processed}")
    
    print()


def example_extractor_usage():
    """Show how to use the enhanced ExternalAPIExtractor"""
    print("=== Enhanced ExternalAPIExtractor Usage ===")
    
    from extractors.external_api import ExternalAPIExtractor
    
    # Mock API responses
    mock_responses = [
        [{"id": 1, "title": "Article 1", "body": "Content 1", "userId": 1}],
        [{"id": 2, "title": "Article 2", "body": "Content 2", "userId": 2}],
        []
    ]
    
    with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
        mock_fetch.side_effect = mock_responses
        
        # Create extractor with pagination enabled
        extractor = ExternalAPIExtractor(
            api_url="https://api.example.com/articles",
            enable_pagination=True,
            page_size=1,
            max_pages=5,
            page_param='page',
            limit_param='limit'
        )
        
        print("Method 1: Extract all data at once")
        all_data = extractor.extract()
        print(f"Extracted {len(all_data)} items")
        
        # Reset mock for next test
        mock_fetch.side_effect = mock_responses
        
        print("\nMethod 2: Extract page by page (memory efficient)")
        for page_num, page_data in extractor.extract_paginated():
            print(f"Page {page_num}: {len(page_data)} items")
    
    print()


def example_configuration():
    """Show configuration options"""
    print("=== Configuration Options ===")
    
    from app.config import Config
    
    config = Config()
    
    print("Pagination settings:")
    print(f"  PAGINATION_ENABLED: {config.PAGINATION_ENABLED}")
    print(f"  PAGINATION_PAGE_SIZE: {config.PAGINATION_PAGE_SIZE}")
    print(f"  PAGINATION_MAX_PAGES: {config.PAGINATION_MAX_PAGES}")
    
    print("\nEnvironment variables you can set:")
    print("  PAGINATION_ENABLED=true/false")
    print("  PAGINATION_PAGE_SIZE=20")
    print("  PAGINATION_MAX_PAGES=100")
    
    print()


def example_etl_usage():
    """Show ETL usage with pagination"""
    print("=== ETL with Pagination ===")
    
    from etl_orchestrator import ETLOrchestrator
    
    print("ETL Orchestrator now supports these parameters:")
    print("  api_url: The API endpoint")
    print("  enable_pagination: True/False")
    print("  page_size: Items per page")
    print("  max_pages: Maximum pages to fetch")
    print("  use_memory_efficient: True for page-by-page processing")
    
    print("\nExample usage:")
    print("""
    result = ETLOrchestrator.run_external_api_etl(
        api_url="https://api.example.com/data",
        enable_pagination=True,
        page_size=50,
        max_pages=10,
        use_memory_efficient=True
    )
    """)
    
    print()


def main():
    """Run all examples"""
    print("🚀 Pagination Implementation Examples\n")
    
    examples = [
        example_configuration,
        example_basic_usage,
        example_memory_efficient,
        example_extractor_usage,
        example_etl_usage,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"❌ Example {example.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("✅ All examples completed!")
    print("\n📚 Key Benefits:")
    print("  • Reduced memory usage with page-by-page processing")
    print("  • Configurable pagination parameters")
    print("  • Support for different API response formats")
    print("  • Backward compatibility maintained")
    print("  • Built-in retry logic with exponential backoff")
    print("  • Safety limits to prevent infinite pagination")


if __name__ == '__main__':
    main()