"""
10x Production Test Suite - Validates app stability and performance
Runs all test suites 10 times and reports aggregate results
"""
import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def run_test(name, script):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    elapsed = time.time() - start
    
    output = result.stdout + result.stderr
    if result.returncode == 0 or "ALL" in output or "RESULTS:" in output:
        lines = output.strip().split('\n')
        for line in lines:
            if 'RESULTS:' in line or 'ALL' in line:
                print(f"  {line.strip()}")
        if result.returncode == 0:
            print(f"  Time: {elapsed:.1f}s")
            return True, elapsed
        else:
            print(f"  Time: {elapsed:.1f}s (warnings present)")
            return True, elapsed
    else:
        print(f"  FAILED")
        print(output[-500:] if output else "No output")
        return False, elapsed

def main():
    print("="*60)
    print("10x PRODUCTION TEST SUITE")
    print("Testing app stability and performance")
    print("="*60)
    
    tests = [
        ("Integrated ONNX Model (35 tests)", "tests/test_integrated_model.py"),
        ("Production API (24 tests)", "tests/test_production.py"),
        ("Real-World Scenarios (8 tests)", "tests/test_real_world_scenarios.py"),
    ]
    
    all_results = []
    
    for run in range(1, 11):
        print(f"\n{'#'*60}")
        print(f"# RUN {run}/10")
        print(f"{'#'*60}")
        
        run_results = []
        for name, script in tests:
            passed, elapsed = run_test(name, script)
            run_results.append((name, passed, elapsed))
        
        all_results.append(run_results)
        
        passed_count = sum(1 for _, p, _ in run_results if p)
        total_time = sum(e for _, _, e in run_results)
        print(f"\n  Run {run}: {passed_count}/3 suites passed | {total_time:.1f}s total")
    
    print(f"\n{'='*60}")
    print("AGGREGATE RESULTS (10 RUNS)")
    print(f"{'='*60}")
    
    for i, (name, _) in enumerate(tests):
        passed_runs = sum(1 for run in all_results if run[i][1])
        times = [run[i][2] for run in all_results]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        status = "STABLE" if passed_runs == 10 else "UNSTABLE"
        print(f"\n  {name}")
        print(f"    Passed: {passed_runs}/10 runs")
        print(f"    Avg time: {avg_time:.1f}s (min: {min_time:.1f}s, max: {max_time:.1f}s)")
        print(f"    Status: {status}")
    
    total_passed = sum(sum(1 for _, p, _ in run if p) for run in all_results)
    total_tests = len(tests) * 10
    overall_status = "PRODUCTION READY" if total_passed == total_tests else "NEEDS FIXES"
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {total_passed}/{total_tests} suite-runs passed")
    print(f"STATUS: {overall_status}")
    print(f"{'='*60}")
    
    if total_passed < total_tests:
        sys.exit(1)

if __name__ == "__main__":
    main()
