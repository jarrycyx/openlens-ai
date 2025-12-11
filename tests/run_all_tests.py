#!/usr/bin/env python3
"""
Run all unit tests for openlens_ai agents
"""

import unittest
import sys
import os
import datetime
from io import StringIO
from pathlib import Path
import shutil

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_all_tests():
    """Discover and run all unit tests"""
    # Discover all tests in the unit directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create output directory for logs
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'tests')
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a timestamp for this test run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(output_dir, f"test_run_{timestamp}.log")
    
    # Capture test output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream, 
        verbosity=2, 
        failfast=False
    )
    
    print(f"开始运行测试，日志将保存到: {log_file}")
    
    # Run tests
    result = runner.run(suite)
    
    # Write output to log file
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"测试运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        f.write(stream.getvalue())
        f.write("\n" + "=" * 70 + "\n")
        f.write(f"测试结果: {'通过' if result.wasSuccessful() else '失败'}\n")
        f.write(f"运行测试数: {result.testsRun}\n")
        
        if result.failures:
            f.write(f"\n失败测试数: {len(result.failures)}\n")
            for test, traceback in result.failures:
                f.write(f"\n失败测试: {test}\n")
                f.write(f"失败详情:\n{traceback}\n")
        
        if result.errors:
            f.write(f"\n错误测试数: {len(result.errors)}\n")
            for test, traceback in result.errors:
                f.write(f"\n错误测试: {test}\n")
                f.write(f"错误详情:\n{traceback}\n")
    
    # Print summary to console
    print(f"\n测试完成，详细日志保存在: {log_file}")
    print(f"总测试数: {result.testsRun}")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    # Print detailed failure information to console
    if not result.wasSuccessful():
        print("\n测试失败详情:")
        for test, traceback in result.failures:
            print(f"\n失败测试: {test}")
            print(f"失败原因:\n{traceback}")
        
        for test, traceback in result.errors:
            print(f"\n错误测试: {test}")
            print(f"错误详情:\n{traceback}")
    
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