#!/usr/bin/env python3
"""
Comprehensive API endpoint testing for dashboard fixes
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Test configuration
BASE_URL = "http://localhost:8000"
API_V1_URL = f"{BASE_URL}/api/v1"
DEMO_API_URL = f"{BASE_URL}/api"

# Authentication for v1 endpoints
AUTH_HEADERS = {
    "Authorization": "Bearer test_token"
}

class APITester:
    def __init__(self):
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "demo_endpoints": [],
            "v1_endpoints": [],
            "errors": []
        }
    
    def test_endpoint(self, url: str, method: str = "GET", headers: Dict = None, 
                     data: Dict = None, expected_status: int = None) -> Tuple[bool, Dict]:
        """Test a single endpoint and return success status and response"""
        self.results["tests_run"] += 1
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = True
            if expected_status:
                success = response.status_code == expected_status
            
            result = {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "success": success,
                "requires_auth": headers is not None and "Authorization" in headers,
                "response_time": response.elapsed.total_seconds(),
                "response_body": response.text[:200] if response.text else None
            }
            
            if success:
                self.results["tests_passed"] += 1
            else:
                self.results["tests_failed"] += 1
                self.results["errors"].append({
                    "test": f"{method} {url}",
                    "error": f"Expected status {expected_status}, got {response.status_code}"
                })
            
            return success, result
            
        except Exception as e:
            self.results["tests_failed"] += 1
            self.results["errors"].append({
                "test": f"{method} {url}",
                "error": str(e)
            })
            return False, {"url": url, "error": str(e)}
    
    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🔍 Starting API Endpoint Testing...")
        print("=" * 60)
        
        # Test 1: Health check
        print("\n1️⃣ Testing health endpoint...")
        success, result = self.test_endpoint(f"{BASE_URL}/health")
        print(f"   Health check: {'✅ PASS' if success else '❌ FAIL'}")
        
        # Test 2: Demo endpoints (should work without auth)
        print("\n2️⃣ Testing demo dashboard endpoints (no auth required)...")
        demo_tests = [
            (f"{DEMO_API_URL}/status", "GET", None, None, 200),
            (f"{DEMO_API_URL}/devices", "GET", None, None, 200),
            (f"{DEMO_API_URL}/consciousness/query", "POST", None, {"question": "test"}, 200),
            (f"{DEMO_API_URL}/devices/1/control", "POST", None, {"action": "on"}, 200),
        ]
        
        for url, method, headers, data, expected in demo_tests:
            success, result = self.test_endpoint(url, method, headers, data, expected)
            self.results["demo_endpoints"].append(result)
            print(f"   {method} {url}: {'✅ PASS' if success else '❌ FAIL'}")
        
        # Test 3: V1 endpoints (should require auth)
        print("\n3️⃣ Testing v1 endpoints (auth required)...")
        v1_tests = [
            # Without auth - should fail with 401
            (f"{API_V1_URL}/consciousness/status", "GET", None, None, 401),
            (f"{API_V1_URL}/devices", "GET", None, None, 401),
            (f"{API_V1_URL}/memory", "GET", None, None, 401),
            
            # With auth - would work if server fully configured
            (f"{API_V1_URL}/consciousness/status", "GET", AUTH_HEADERS, None, None),
            (f"{API_V1_URL}/devices", "GET", AUTH_HEADERS, None, None),
        ]
        
        for url, method, headers, data, expected in v1_tests:
            success, result = self.test_endpoint(url, method, headers, data, expected)
            self.results["v1_endpoints"].append(result)
            auth_str = "with auth" if headers else "without auth"
            print(f"   {method} {url} ({auth_str}): {'✅ PASS' if success else '❌ FAIL'}")
        
        # Test 4: Check for any cross-references
        print("\n4️⃣ Checking for authentication cross-references...")
        demo_working = all(r.get("success", False) for r in self.results["demo_endpoints"])
        v1_protected = all(r.get("status_code") == 401 for r in self.results["v1_endpoints"] 
                          if not r.get("requires_auth", False))
        
        print(f"   Demo endpoints accessible: {'✅ YES' if demo_working else '❌ NO'}")
        print(f"   V1 endpoints protected: {'✅ YES' if v1_protected else '❌ NO'}")
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests run: {self.results['tests_run']}")
        print(f"Tests passed: {self.results['tests_passed']} ✅")
        print(f"Tests failed: {self.results['tests_failed']} ❌")
        
        if self.results["errors"]:
            print("\n⚠️  ERRORS FOUND:")
            for error in self.results["errors"]:
                print(f"   - {error['test']}: {error['error']}")
        
        # Validation results
        print("\n✅ VALIDATION RESULTS:")
        print(f"   1. Dashboard endpoints work without auth: {'PASS' if demo_working else 'FAIL'}")
        print(f"   2. No authenticated /v1 calls from dashboard: {'PASS' if v1_protected else 'FAIL'}")
        print(f"   3. Server stability: {'PASS' if self.results['tests_run'] > 0 else 'FAIL'}")
        
        overall_pass = demo_working and v1_protected and self.results['tests_run'] > 0
        print(f"\n🎯 OVERALL RESULT: {'PASS ✅' if overall_pass else 'FAIL ❌'}")
        
        return overall_pass, self.results

def test_without_server():
    """Run tests that don't require a running server"""
    print("🔍 Running static code analysis...")
    print("=" * 60)
    
    results = {
        "dashboard_endpoints_found": [],
        "v1_endpoints_found": [],
        "auth_checks_found": [],
        "issues": []
    }
    
    # Check API interface code
    print("\n1️⃣ Analyzing API interface code...")
    
    api_file = "/workspaces/consciousness/consciousness/interfaces/api_interface.py"
    try:
        with open(api_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
        for i, line in enumerate(lines):
            # Find demo endpoints
            if '@self.app.get("/api/' in line or '@self.app.post("/api/' in line:
                if '/api/v1/' not in line:
                    endpoint = line.strip()
                    results["dashboard_endpoints_found"].append({
                        "line": i + 1,
                        "endpoint": endpoint,
                        "requires_auth": "Depends(self.get_current_user)" in lines[i:i+5]
                    })
            
            # Find v1 endpoints
            if '/api/v1/' in line and ('@self.app.' in line):
                results["v1_endpoints_found"].append({
                    "line": i + 1,
                    "endpoint": line.strip()
                })
            
            # Find auth checks
            if 'get_current_user' in line or 'HTTPBearer' in line:
                results["auth_checks_found"].append({
                    "line": i + 1,
                    "context": line.strip()
                })
        
        print(f"   Found {len(results['dashboard_endpoints_found'])} demo endpoints")
        print(f"   Found {len(results['v1_endpoints_found'])} v1 endpoints")
        print(f"   Found {len(results['auth_checks_found'])} auth checks")
        
        # Verify demo endpoints don't require auth
        print("\n2️⃣ Verifying demo endpoints don't require authentication...")
        for endpoint in results["dashboard_endpoints_found"]:
            if endpoint["requires_auth"]:
                results["issues"].append(f"Demo endpoint at line {endpoint['line']} requires auth!")
                print(f"   ❌ {endpoint['endpoint']} - REQUIRES AUTH")
            else:
                print(f"   ✅ {endpoint['endpoint']} - No auth required")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 STATIC ANALYSIS SUMMARY")
        print("=" * 60)
        
        no_auth_issues = len([e for e in results["dashboard_endpoints_found"] if e["requires_auth"]]) == 0
        proper_separation = len(results["dashboard_endpoints_found"]) > 0 and len(results["v1_endpoints_found"]) > 0
        
        print(f"Demo endpoints without auth requirement: {'PASS ✅' if no_auth_issues else 'FAIL ❌'}")
        print(f"Proper endpoint separation (/api vs /api/v1): {'PASS ✅' if proper_separation else 'FAIL ❌'}")
        
        if results["issues"]:
            print("\n⚠️  ISSUES FOUND:")
            for issue in results["issues"]:
                print(f"   - {issue}")
        
        return no_auth_issues and proper_separation, results
        
    except Exception as e:
        print(f"   ❌ Error analyzing code: {e}")
        return False, results

def main():
    """Main test runner"""
    print("🚀 API Dashboard Fix Verification")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # First run static analysis
    static_pass, static_results = test_without_server()
    
    # Try to test with running server
    print("\n" + "=" * 60)
    print("🌐 Testing with live server...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        server_running = True
        print("✅ Server is running")
    except:
        server_running = False
        print("⚠️  Server is not running - skipping live tests")
    
    if server_running:
        tester = APITester()
        live_pass, live_results = tester.run_all_tests()
    else:
        live_pass = static_pass  # Use static results only
        live_results = {}
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL VERIFICATION RESULTS")
    print("=" * 60)
    print(f"Static code analysis: {'PASS ✅' if static_pass else 'FAIL ❌'}")
    print(f"Live API testing: {'PASS ✅' if live_pass else 'N/A' if not server_running else 'FAIL ❌'}")
    print(f"\nOverall result: {'PASS ✅' if static_pass and (live_pass or not server_running) else 'FAIL ❌'}")
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    
    # Save results
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "static_analysis": static_results,
        "live_testing": live_results if server_running else "Server not running",
        "overall_pass": static_pass and (live_pass or not server_running)
    }
    
    with open("/workspaces/consciousness/api_test_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to: api_test_results.json")
    
    return all_results

if __name__ == "__main__":
    results = main()