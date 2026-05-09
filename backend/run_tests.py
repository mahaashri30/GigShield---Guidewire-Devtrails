#!/usr/bin/env python3
"""
Quick test runner for Phase 1-6 implementations.
Tests can be run without database setup or AWS credentials.

Usage:
    python backend/run_tests.py                  # Run all tests
    python backend/run_tests.py pricing          # Run Phase 2 tests
    python backend/run_tests.py fraud            # Run Phase 3 tests
    python backend/run_tests.py inactivity       # Run Phase 4 tests
    python backend/run_tests.py loss_ratio       # Run Phase 5 tests
    python backend/run_tests.py dss              # Run Phase 6 tests
    python backend/run_tests.py e2e              # Run E2E tests
"""

import sys
import subprocess

def run_tests(test_filter=None):
    """Run pytest with optional filter."""
    cmd = ["python", "-m", "pytest", "backend/tests/test_phase_implementations.py", "-v", "--tb=short"]
    
    if test_filter:
        test_mapping = {
            "pricing": "TestPricingEngine",
            "fraud": "TestFraudDetection",
            "inactivity": "TestInactivityValidation",
            "loss_ratio": "TestLossRatioAggregation",
            "dss": "TestDisruptionSeverityScore",
            "e2e": "TestEndToEndClaimFlow",
        }
        
        if test_filter in test_mapping:
            cmd.append(f"-k={test_mapping[test_filter]}")
            print(f"\n📋 Running {test_filter.upper()} tests ({test_mapping[test_filter]})...\n")
        else:
            print(f"❌ Unknown test filter: {test_filter}")
            print(f"   Available: {', '.join(test_mapping.keys())}")
            return 1
    else:
        print("\n📋 Running ALL tests (Phases 2-6)...\n")
    
    result = subprocess.run(cmd, cwd=".")
    return result.returncode

if __name__ == "__main__":
    test_filter = sys.argv[1] if len(sys.argv) > 1 else None
    exit_code = run_tests(test_filter)
    sys.exit(exit_code)
