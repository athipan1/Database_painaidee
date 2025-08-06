#!/usr/bin/env python3
"""
Comprehensive test runner for Database Painaidee project.
Runs all available tests including Pydantic schema validation and API endpoint testing.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def run_test_file(test_file_path):
    """Run a single test file and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {test_file_path}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, test_file_path], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT - Test took longer than 5 minutes")
        return False
    except Exception as e:
        print(f"💥 ERROR running test: {e}")
        return False

def main():
    """Run all tests in the project."""
    project_root = Path(__file__).parent.parent
    
    # List of test files to run (in order of priority)
    test_files = [
        "test_setup.py",
        "test_new_features.py", 
        "test_etl.py",
        "test_tat_etl.py",
        "test_backward_compatibility.py",
        "test_ai_features.py",
        "test_behavior_intelligence.py",
        "test_pagination.py",
        "test_pytest_integration.py",
        "test_real_api.py"
    ]
    
    print("🚀 Database Painaidee - Comprehensive Test Suite")
    print("="*60)
    print("Running automatic schema validation and endpoint testing...")
    print(f"Project root: {project_root}")
    
    passed_tests = []
    failed_tests = []
    skipped_tests = []
    
    # Run each test file
    for test_file in test_files:
        test_path = project_root / test_file
        
        if test_path.exists():
            success = run_test_file(test_path)
            if success:
                passed_tests.append(test_file)
            else:
                failed_tests.append(test_file)
        else:
            print(f"⚠️  SKIPPED: {test_file} (file not found)")
            skipped_tests.append(test_file)
    
    # Summary
    print("\n" + "="*60)
    print("🏁 TEST SUMMARY")
    print("="*60)
    
    total_tests = len(test_files)
    print(f"Total tests: {total_tests}")
    print(f"✅ Passed: {len(passed_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"⚠️  Skipped: {len(skipped_tests)}")
    
    if passed_tests:
        print("\n✅ Passed tests:")
        for test in passed_tests:
            print(f"  - {test}")
    
    if failed_tests:
        print("\n❌ Failed tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    if skipped_tests:
        print("\n⚠️  Skipped tests:")
        for test in skipped_tests:
            print(f"  - {test}")
    
    # Exit code
    if failed_tests:
        print(f"\n💥 {len(failed_tests)} test(s) failed!")
        sys.exit(1)
    else:
        print(f"\n🎉 All {len(passed_tests)} tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()