#!/usr/bin/env python3
"""
Run all unit tests for openlens_ai agents
"""

import unittest
import sys
import os
import datetime
import io
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class LoggingTestRunner:
    """Custom test runner that logs each test to a separate file"""
    
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.test_results = []
        self.total_tests = 0
        self.failures = 0
        self.errors = 0
        self.skipped = 0
        
    def run(self, test_suite):
        """Run the test suite and log each test"""
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Count total tests
        self.total_tests = test_suite.countTestCases()
        print(f"发现 {self.total_tests} 个测试用例")
        
        # Run each test case individually
        for test_case in self._iterate_test_cases(test_suite):
            self._run_single_test(test_case)
        
        # Print summary
        self._print_summary()
        
        # Return a mock result object
        return self._create_result()
    
    def _iterate_test_cases(self, test_suite):
        """Iterate through all test cases in the suite"""
        if isinstance(test_suite, unittest.TestCase):
            yield test_suite
        else:
            for test in test_suite:
                if isinstance(test, unittest.TestCase):
                    yield test
                else:
                    yield from self._iterate_test_cases(test)
    
    def _run_single_test(self, test_case):
        """Run a single test case and log its output"""
        # Create a test-specific log file
        test_name = f"{test_case.__class__.__name__}.{test_case._testMethodName}"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.output_dir, f"{test_name}_{timestamp}.log")
        
        # Capture output
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=2,
            failfast=False
        )
        
        # Create a test suite with just this test
        suite = unittest.TestSuite()
        suite.addTest(test_case)
        
        # Run the test
        result = runner.run(suite)
        
        # Write output to log file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"测试名称: {test_name}\n")
            f.write(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            f.write(stream.getvalue())
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"测试结果: {'通过' if result.wasSuccessful() else '失败'}\n")
            f.write(f"运行时间: {result.testsRun} 个测试\n")
            
            if result.failures:
                f.write(f"失败数量: {len(result.failures)}\n")
                for test, traceback in result.failures:
                    f.write(f"\n失败详情:\n{traceback}\n")
            
            if result.errors:
                f.write(f"错误数量: {len(result.errors)}\n")
                for test, traceback in result.errors:
                    f.write(f"\n错误详情:\n{traceback}\n")
        
        # Update counters
        if result.failures:
            self.failures += len(result.failures)
        if result.errors:
            self.errors += len(result.errors)
        if result.skipped:
            self.skipped += len(result.skipped)
        
        # Store test result
        self.test_results.append({
            'name': test_name,
            'success': result.wasSuccessful(),
            'log_file': log_file
        })
        
        # Print progress to console
        status = "✓" if result.wasSuccessful() else "✗"
        print(f"{status} {test_name} -> {log_file}")
    
    def _print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "=" * 70)
        print("测试总结:")
        print(f"总测试数: {self.total_tests}")
        print(f"通过: {self.total_tests - self.failures - self.errors}")
        print(f"失败: {self.failures}")
        print(f"错误: {self.errors}")
        print(f"跳过: {self.skipped}")
        print("=" * 70)
        
        # Print failed tests
        if self.failures > 0 or self.errors > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']} -> {result['log_file']}")
    
    def _create_result(self):
        """Create a mock result object"""
        class MockResult:
            def __init__(self, was_successful, failures, errors, tests_run):
                self.wasSuccessful = was_successful
                self.failures = failures
                self.errors = errors
                self.testsRun = tests_run
        
        return MockResult(
            was_successful=(self.failures == 0 and self.errors == 0),
            failures=[],
            errors=[],
            tests_run=self.total_tests
        )


def run_all_tests():
    """Discover and run all unit tests"""
    # Discover all tests in the unit directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create output directory for logs
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'tests')
    
    # Run tests with logging
    runner = LoggingTestRunner(output_dir)
    result = runner.run(suite)
    
    # Return the result
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running all unit tests for openlens_ai agents...")
    success = run_all_tests()
    
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)