#!/usr/bin/env python3
"""
Sentinel Load Testing - 100 Users Concurrent Test
Tests system performance with realistic threat scenarios
"""
import requests
import time
import json
import concurrent.futures
import statistics
from datetime import datetime
from typing import List, Dict, Tuple
import sys

API_BASE = "http://localhost:8000"

# User profiles for diverse testing
USER_PROFILES = {
    "low_threat": {
        "threat_level": 1,
        "auth_success": True,
        "attempts": 1,
        "ips": ["192.168.1.", "10.0.0.", "172.16.0."],
        "countries": ["United States", "United Kingdom", "Germany"],
    },
    "medium_threat": {
        "threat_level": 5,
        "auth_success": False,
        "attempts": 3,
        "ips": ["203.0.113.", "198.51.100."],
        "countries": ["Russia", "China"],
    },
    "high_threat": {
        "threat_level": 8,
        "auth_success": False,
        "attempts": 8,
        "ips": ["192.0.2.", "203.0.113."],
        "countries": ["Unknown", "Suspicious"],
    },
}

class SentinelLoadTest:
    def __init__(self, num_users: int = 100):
        self.num_users = num_users
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    def generate_users(self) -> List[Dict]:
        """Generate 100 unique users with varied threat levels"""
        users = []
        threat_types = list(USER_PROFILES.keys())
        
        for i in range(1, self.num_users + 1):
            # Distribute threat levels: 60% low, 25% medium, 15% high
            if i % 100 < 60:
                threat_type = "low_threat"
            elif i % 100 < 85:
                threat_type = "medium_threat"
            else:
                threat_type = "high_threat"
            
            profile = USER_PROFILES[threat_type]
            ip_prefix = profile["ips"][i % len(profile["ips"])]
            ip_suffix = (i % 254) + 1
            country = profile["countries"][i % len(profile["countries"])]
            
            user = {
                "user_id": i,
                "username": f"user{i:03d}@sentinel.local",
                "email": f"user{i:03d}@sentinel.local",
                "source_ip": f"{ip_prefix}{ip_suffix}",
                "country": country,
                "threat_type": threat_type,
                "profile": profile,
            }
            
            users.append(user)
        
        return users
    
    def create_event(self, user: Dict) -> Tuple[bool, float, str, Dict]:
        """Create a single event and measure response time"""
        profile = user["profile"]
        
        event_data = {
            "event_data": {
                "event_type": "authentication",
                "action": "login_attempt",
                "source_ip": user["source_ip"],
                "username": user["username"],
                "timestamp": datetime.utcnow().isoformat(),
                "auth": {
                    "success": profile["auth_success"],
                    "method": "password",
                    "attempts": profile["attempts"],
                },
                "user_agent": "Sentinel Load Test / Python",
                "geo_location": {
                    "country": user["country"],
                    "city": "Load Test",
                },
            }
        }
        
        start = time.time()
        try:
            response = requests.post(
                f"{API_BASE}/simulate",
                headers={"Content-Type": "application/json"},
                json=event_data,
                timeout=30,
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data["simulation_result"]
                    return (
                        True,
                        elapsed,
                        result.get("action_taken", "unknown"),
                        {
                            "threat_score": result.get("threat_score", 0),
                            "reasoning": result.get("reasoning", ""),
                        },
                    )
                else:
                    return False, elapsed, "error", {}
            else:
                return False, elapsed, f"http_{response.status_code}", {}
        
        except requests.exceptions.Timeout:
            return False, 30.0, "timeout", {}
        except Exception as e:
            return False, time.time() - start, f"error: {str(e)}", {}
    
    def run_sequential_test(self) -> Dict:
        """Run sequential load test - one user after another"""
        print("\n" + "="*70)
        print("🔄 SEQUENTIAL LOAD TEST - 100 Users")
        print("="*70)
        print("Creating 100 events sequentially...\n")
        
        users = self.generate_users()
        self.start_time = time.time()
        
        for i, user in enumerate(users, 1):
            success, elapsed, action, result = self.create_event(user)
            
            self.results.append({
                "user_id": user["user_id"],
                "username": user["username"],
                "threat_type": user["threat_type"],
                "success": success,
                "response_time": elapsed,
                "action": action,
                "threat_score": result.get("threat_score", 0),
            })
            
            if not success:
                self.errors.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "error": action,
                })
            
            # Progress indicator
            if i % 10 == 0:
                print(f"✅ {i}/100 events created - Avg response: {statistics.mean([r['response_time'] for r in self.results]):.2f}s")
        
        self.end_time = time.time()
        return self.generate_report()
    
    def run_concurrent_test(self, workers: int = 10) -> Dict:
        """Run concurrent load test - multiple users simultaneously"""
        print("\n" + "="*70)
        print(f"⚡ CONCURRENT LOAD TEST - 100 Users ({workers} workers)")
        print("="*70)
        print(f"Creating 100 events with {workers} concurrent workers...\n")
        
        users = self.generate_users()
        self.start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self.create_event, user) for user in users]
            
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                try:
                    success, elapsed, action, result = future.result(timeout=40)
                    user_idx = i - 1
                    user = users[user_idx]
                    
                    self.results.append({
                        "user_id": user["user_id"],
                        "username": user["username"],
                        "threat_type": user["threat_type"],
                        "success": success,
                        "response_time": elapsed,
                        "action": action,
                        "threat_score": result.get("threat_score", 0),
                    })
                    
                    if not success:
                        self.errors.append({
                            "user_id": user["user_id"],
                            "username": user["username"],
                            "error": action,
                        })
                    
                    if i % 10 == 0:
                        print(f"✅ {i}/100 events created")
                
                except Exception as e:
                    self.errors.append({
                        "user_id": i,
                        "error": str(e),
                    })
        
        self.end_time = time.time()
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_time = self.end_time - self.start_time
        successful = len([r for r in self.results if r["success"]])
        failed = len(self.errors)
        
        response_times = [r["response_time"] for r in self.results if r["success"]]
        threat_scores = [r["threat_score"] for r in self.results if r["success"]]
        
        actions = {}
        for r in self.results:
            action = r["action"]
            actions[action] = actions.get(action, 0) + 1
        
        report = {
            "total_requests": len(self.results),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(self.results) * 100) if self.results else 0,
            "total_time": total_time,
            "throughput": successful / total_time if total_time > 0 else 0,
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 0 else 0,
                "p99": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 0 else 0,
            },
            "threat_analysis": {
                "avg_score": statistics.mean(threat_scores) if threat_scores else 0,
                "high_threats": len([s for s in threat_scores if s >= 7]),
                "medium_threats": len([s for s in threat_scores if 4 <= s < 7]),
                "low_threats": len([s for s in threat_scores if s < 4]),
            },
            "actions_taken": actions,
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted test report"""
        print("\n" + "="*70)
        print("📊 LOAD TEST REPORT")
        print("="*70)
        
        print(f"\n✅ SUCCESS METRICS:")
        print(f"   Total Requests: {report['total_requests']}")
        print(f"   Successful: {report['successful']}")
        print(f"   Failed: {report['failed']}")
        print(f"   Success Rate: {report['success_rate']:.1f}%")
        
        print(f"\n⏱️  PERFORMANCE METRICS:")
        print(f"   Total Time: {report['total_time']:.2f} seconds")
        print(f"   Throughput: {report['throughput']:.2f} requests/second")
        print(f"   Response Times:")
        print(f"      Min: {report['response_times']['min']:.2f}s")
        print(f"      Max: {report['response_times']['max']:.2f}s")
        print(f"      Avg: {report['response_times']['avg']:.2f}s")
        print(f"      P95: {report['response_times']['p95']:.2f}s")
        print(f"      P99: {report['response_times']['p99']:.2f}s")
        
        print(f"\n🎯 THREAT ANALYSIS:")
        print(f"   Average Threat Score: {report['threat_analysis']['avg_score']:.1f}/10")
        print(f"   High Threats (7-10): {report['threat_analysis']['high_threats']}")
        print(f"   Medium Threats (4-6): {report['threat_analysis']['medium_threats']}")
        print(f"   Low Threats (0-3): {report['threat_analysis']['low_threats']}")
        
        print(f"\n🔒 ACTIONS TAKEN:")
        for action, count in report['actions_taken'].items():
            print(f"   {action}: {count}")
        
        print("\n" + "="*70)
    
    def export_results(self, filename: str = "load_test_results.json"):
        """Export results to JSON file"""
        export_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_config": {
                "num_users": self.num_users,
                "api_base": API_BASE,
            },
            "results": self.results,
            "errors": self.errors,
        }
        
        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n📁 Results exported to: {filename}")

def main():
    """Main test execution"""
    print("\n🛡️  SENTINEL LOAD TEST")
    print("="*70)
    print("Testing Sentinel with 100 concurrent users\n")
    
    print("Test Options:")
    print("  1. Sequential (one user at a time)")
    print("  2. Concurrent (10 workers)")
    print("  3. Heavy Concurrent (20 workers)")
    print("  4. Both sequential and concurrent")
    
    choice = input("\nChoose test type (1-4): ").strip()
    
    tester = SentinelLoadTest(num_users=100)
    
    if choice in ["1", "4"]:
        print("\n⏳ Starting sequential test...")
        report = tester.run_sequential_test()
        tester.print_report(report)
        tester.export_results("load_test_sequential.json")
    
    if choice in ["2", "3", "4"]:
        workers = 10 if choice == "2" else 20
        tester = SentinelLoadTest(num_users=100)  # Reset for concurrent test
        print(f"\n⏳ Starting concurrent test with {workers} workers...")
        report = tester.run_concurrent_test(workers=workers)
        tester.print_report(report)
        tester.export_results(f"load_test_concurrent_{workers}w.json")
    
    print("\n✅ Load testing complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Load test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
