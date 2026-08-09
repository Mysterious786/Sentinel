#!/usr/bin/env python3
"""
Auto Demo - Automatically generates a realistic threat sequence
Perfect for recording demo videos
"""
import requests
import time
import sys

API_BASE = "http://localhost:8000"

from datetime import datetime

def simulate_event(ip, username, description):
    """Simulate a single event"""
    try:
        event_data = {
            "event_type": "authentication",
            "action": "login_attempt",
            "source_ip": ip,
            "username": username,
            "timestamp": datetime.utcnow().isoformat(),
            "auth": {
                "success": False,
                "method": "password",
                "attempts": 3
            }
        }
        
        response = requests.post(
            f"{API_BASE}/simulate",
            headers={"Content-Type": "application/json"},
            json={"event_data": event_data},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                result = data["simulation_result"]
                threat_score = result.get("threat_score", 0)
                action = result.get("action_taken", "monitor")
                
                print(f"✅ {description}")
                print(f"   Threat: {threat_score}/10 | Action: {action} | IP: {ip}")
                return True
            else:
                print(f"❌ {description} - Failed")
                return False
        else:
            print(f"❌ API error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run auto demo"""
    print("\n🎬 SENTINEL AUTO-DEMO")
    print("="*70)
    print("Creating realistic attack sequence... Watch the dashboard update!")
    print("="*70 + "\n")
    
    # Sequence of events showing progression
    events = [
        ("203.0.113.15", "alice.johnson", "🔴 Event 1: Suspicious login from foreign IP"),
        ("203.0.113.15", "bob.smith", "🔴 Event 2: Same IP, different user - Pattern detected!"),
        ("198.51.100.42", "carol.davis", "🔴 Event 3: Second suspicious IP targeting new user"),
        ("192.0.2.100", "david.wilson", "🔴 Event 4: Coordinated multi-vector attack incoming"),
        ("203.0.113.15", "alice.johnson", "🔴 Event 5: Attacker returns to original user"),
    ]
    
    print("📊 Generating events (watch dashboard at http://localhost:3000):\n")
    
    for i, (ip, user, desc) in enumerate(events, 1):
        print(f"\n⏳ Creating event {i}/{len(events)}...")
        simulate_event(ip, user, desc)
        
        if i < len(events):
            print(f"⏳ Waiting 3 seconds for Sentinel analysis...\n")
            time.sleep(3)
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE!")
    print("="*70)
    print("\nCheck the dashboard at http://localhost:3000")
    print("You should see 5 new high-threat events with IP blocking actions\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled")
        sys.exit(0)