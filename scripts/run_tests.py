#!/usr/bin/env python3
"""
Test runner for the MarketMind configuration system tests.

This script runs unit, integration, security, and performance tests,
and generates a coverage report.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = PROJECT_ROOT / "packages"
COVERAGE_DIR = PROJECT_ROOT / "coverage"
TEST_DIR = PACKAGE_DIR / "shared" / "tests"

# Test categories
TEST_CATEGORIES = ["unit", "integration", "security", "performance"]


def run_tests(test_category: str, verbose: bool = False) -> Tuple[bool, Dict]:
    """Run tests for a specific category and return results."""
    print(f"\n{'='*50}")
    print(f"Running {test_category} tests...")
    print(f"{'='*50}")

    # Create coverage directory if it doesn't exist
    COVERAGE_DIR.mkdir(exist_ok=True)

    # Determine the test directory
    test_dir = TEST_DIR / test_category
    if not test_dir.exists():
        print(f"Warning: Test directory not found: {test_dir}")
        return False, {}

    # Build the pytest command
    cmd = [
        "pytest",
        "-v" if verbose else "-q",
        "--cov=packages.shared.config",
        f"--cov-report=html:{COVERAGE_DIR}/{test_category}",
        "--cov-report=term-missing",
        "--durations=10",
        str(test_dir),
    ]

    # Add performance-specific options
    if test_category == "performance":
        cmd.extend(["--benchmark-only", "--benchmark-json=benchmark.json"])

    # Run the tests
    start_time = time.time()
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    elapsed = time.time() - start_time

    # Check if tests passed
    passed = result.returncode == 0

    # Load benchmark results if available
    benchmark_results = {}
    if test_category == "performance" and Path("benchmark.json").exists():
        try:
            with open("benchmark.json", "r") as f:
                benchmark_results = json.load(f)
            os.remove("benchmark.json")
        except Exception as e:
            print(f"Error loading benchmark results: {e}")

    # Return test results
    return passed, {
        "test_count": 0,  # Would be parsed from pytest output in a real implementation
        "passed": passed,
        "elapsed_time": elapsed,
        "benchmark": benchmark_results,
    }


def generate_coverage_report():
    """Generate a combined coverage report."""
    print("\n" + "=" * 50)
    print("Generating combined coverage report...")
    print("=" * 50)

    # In a real implementation, we would combine coverage from all test runs
    # For now, we'll just print a summary
    print("\nCoverage reports are available in the 'coverage' directory.")
    print("Open coverage/index.html in a web browser to view the full report.")


def print_summary(results: Dict[str, Dict]):
    """Print a summary of test results."""
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for category, result in results.items():
        status = "PASSED" if result.get("passed", False) else "FAILED"
        print(f"{category.upper():<12} {status:<6} {result.get('elapsed_time', 0):.2f}s")
        all_passed = all_passed and result.get("passed", False)

    print("\n" + "=" * 50)
    print("OVERALL STATUS: " + ("PASSED" if all_passed else "FAILED"))
    print("=" * 50)

    if not all_passed:
        sys.exit(1)


def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description="Run MarketMind configuration system tests.")
    parser.add_argument(
        "--category",
        choices=TEST_CATEGORIES + ["all"],
        default="all",
        help="Test category to run (default: all)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Determine which categories to run
    categories = [args.category] if args.category != "all" else TEST_CATEGORIES

    # Run tests for each category
    results = {}
    for category in categories:
        if category in TEST_CATEGORIES:
            passed, result = run_tests(category, args.verbose)
            results[category] = result

    # Generate combined coverage report
    if len(categories) > 1 or categories[0] == "all":
        generate_coverage_report()

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
