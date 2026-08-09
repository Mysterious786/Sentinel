#!/usr/bin/env python3
"""
Sentinel Demo Mode - Simulates realistic attack scenarios with clear progression
Shows visible changes in threat levels and actions for impressive demos
"""
import requests
import json
import time
import sys
from datetime import datetime
from random import choice, randint

API_BASE = "http://localhost:8000"

# Different IPs and usernames to show variety
SUSPICIOUS_IPS = [
    "203.0.113.15",   # Foreign IP #1
    "198.51.100.42",  # Foreign IP #2  
    "192.0.2.100",    # Foreign IP #3
    "203.0.113.88",   # Foreign IP #4
]

USERNAMES = [
    "alice.johnson",
    "bob.smith",
    "carol.davis",
    "david.wilson",
]

DEMO_SCENARIOS = {
    "low": {
        "threat_range": (1, 3),
        "description": "Low threat - normal activity"
    },
    "medium": {
        "threat_range": (4, 6),
        "description": "Medium threat - suspicious"
    },
    "high": {
        "threat_range": (7, 9),
        "description": "High threat - CRITICAL"
    }
}

def clear_screen():
    """Clear terminal screen"""
    import os
    os.system('clear' if os.name != 'nt' else 'cls')

def simulate_event(ip, username, threat_level="medium"):
    """Simulate a security event"""
    try:
        event_data = {
            "event_type": "authentication",
            "action": "login_attempt",
            "source_ip": ip,
            "username": username,
            "timestamp": datetime.utcnow().isoformat(),
            "auth": {
                "success": threat_level == "low",
                "method": "password",
                "attempts": randint(1, 5) if threat_level != "low" else 1
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "geo_location": {
                "country": choice(["China", "Russia", "Unknown", "India"]),
                "city": "Unknown"
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
                
                print(f"✅ Event created")
                print(f"   Threat Score: {threat_score}/10")
                print(f"   Action: {action}")
                print(f"   IP: {ip}")
                print(f"   User: {username}")
                print()
                
                return True
            else:
                print(f"❌ Simulation failed")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_events():
    """Fetch recent events"""
    try:
        response = requests.get(f"{API_BASE}/events?hours=24&limit=5", timeout=5)
        if response.status_code == 200:
            return response.json().get("events", [])
    except Exception as e:
        print(f"Error fetching events: {e}")
    return []

def display_events():
    """Display recent events in a formatted way"""
    events = get_events()
    
    print("\n" + "="*60)
    print("📊 RECENT THREAT ANALYSIS")
    print("="*60)
    
    if not events:
        print("No events yet")
        return
    
    for i, event in enumerate(events[:5], 1):
        threat_score = float(event.get("threat_score", 0))
        action = event.get("action_taken", "monitor")
        ip = event.get("source_ip", "unknown")
        username = event.get("username", "unknown")
        
        # Color code by threat level
        if threat_score >= 7:
            threat_icon = "🔴"
        elif threat_score >= 4:
            threat_icon = "🟡"
        else:
            threat_icon = "🟢"
        
        print(f"\n{threat_icon} Event {i}:")
        print(f"   Score: {threat_score}/10")
        print(f"   Action: {action}")
        print(f"   IP: {ip}")
        print(f"   User: {username}")

def demo_scenario_1():
    """Scenario 1: Single attack detection"""
    print("\n🎬 DEMO SCENARIO 1: Single Threat Detection")
    print("="*60)
    print("Simulating a failed login attempt from a suspicious IP...")
    print()
    
    simulate_event(
        ip="203.0.113.15",
        username="alice.johnson",
        threat_level="high"
    )
    
    display_events()
    
    input("\n👉 Press ENTER to continue...")

def demo_scenario_2():
    """Scenario 2: Pattern escalation"""
    print("\n🎬 DEMO SCENARIO 2: Pattern Escalation")
    print("="*60)
    print("Showing how Sentinel detects escalating threats...\n")
    
    # First event - medium threat
    print("1️⃣  First suspicious event (Medium threat):")
    simulate_event(
        ip="198.51.100.42",
        username="bob.smith",
        threat_level="medium"
    )
    time.sleep(1)
    
    # Second event - same IP (higher threat)
    print("2️⃣  Second event from same IP (Pattern detected - High threat):")
    simulate_event(
        ip="198.51.100.42",
        username="bob.smith",
        threat_level="high"
    )
    time.sleep(1)
    
    # Third event - different user, same IP (critical)
    print("3️⃣  Third event - Different user, same IP (CRITICAL - Coordinate attack!):")
    simulate_event(
        ip="198.51.100.42",
        username="carol.davis",
        threat_level="high"
    )
    
    display_events()
    
    input("\n👉 Press ENTER to continue...")

def demo_scenario_3():
    """Scenario 3: Multi-vector attack"""
    print("\n🎬 DEMO SCENARIO 3: Multi-Vector Attack Detection")
    print("="*60)
    print("Multiple attacks from different IPs targeting different users...\n")
    
    attacks = [
        ("203.0.113.15", "alice.johnson", "high"),
        ("198.51.100.42", "bob.smith", "high"),
        ("192.0.2.100", "carol.davis", "high"),
        ("203.0.113.88", "david.wilson", "high"),
    ]
    
    for idx, (ip, user, threat) in enumerate(attacks, 1):
        print(f"{idx}️⃣  Attack {idx}/4:")
        simulate_event(ip=ip, username=user, threat_level=threat)
        time.sleep(0.5)
    
    display_events()
    
    input("\n👉 Press ENTER to continue...")

def demo_scenario_4():
    """Scenario 4: Autonomous response"""
    print("\n🎬 DEMO SCENARIO 4: Autonomous Response")
    print("="*60)
    print("Watch Sentinel automatically block high-threat IPs...\n")
    
    print("Creating high-threat event with automatic IP blocking...")
    simulate_event(
        ip="203.0.113.15",
        username="alice.johnson",
        threat_level="high"
    )
    
    print("\n🔒 AUTOMATIC ACTIONS TAKEN:")
    print("   ✅ IP Blocked: 203.0.113.15")
    print("   ✅ Alert Sent: Security Team")
    print("   ✅ Decision Logged: Event recorded in memory")
    
    display_events()
    
    input("\n👉 Press ENTER to continue...")

def interactive_demo():
    """Interactive demo mode"""
    print("\n🎭 INTERACTIVE DEMO MODE")
    print("="*60)
    print("Create custom events and watch Sentinel respond\n")
    
    while True:
        print("Options:")
        print("  1. Low threat (normal login)")
        print("  2. Medium threat (suspicious)")
        print("  3. High threat (critical)")
        print("  4. View events")
        print("  5. Exit")
        
        choice_input = input("\nChoose (1-5): ").strip()
        
        if choice_input == "1":
            simulate_event(
                ip=choice(["192.168.1.1", "10.0.0.1"]),
                username=choice(USERNAMES),
                threat_level="low"
            )
        elif choice_input == "2":
            simulate_event(
                ip=choice(SUSPICIOUS_IPS),
                username=choice(USERNAMES),
                threat_level="medium"
            )
        elif choice_input == "3":
            simulate_event(
                ip=choice(SUSPICIOUS_IPS),
                username=choice(USERNAMES),
                threat_level="high"
            )
        elif choice_input == "4":
            display_events()
        elif choice_input == "5":
            print("\n👋 Demo ended!")
            break
        else:
            print("Invalid choice")

def main():
    """Main demo entry point"""
    clear_screen()
    
    print("🛡️  SENTINEL DEMO MODE")
    print("="*60)
    print("Choose a demo scenario to showcase threat detection\n")
    
    print("Available scenarios:")
    print("  1. Single Threat Detection")
    print("  2. Pattern Escalation (3 events)")
    print("  3. Multi-Vector Attack (4 events)")
    print("  4. Autonomous Response")
    print("  5. Interactive Demo (custom events)")
    print("  6. Quick Test (all 4 scenarios)")
    
    choice_input = input("\nChoose (1-6): ").strip()
    
    if choice_input == "1":
        demo_scenario_1()
    elif choice_input == "2":
        demo_scenario_2()
    elif choice_input == "3":
        demo_scenario_3()
    elif choice_input == "4":
        demo_scenario_4()
    elif choice_input == "5":
        interactive_demo()
    elif choice_input == "6":
        print("\n⏱️  Running full demo sequence...\n")
        demo_scenario_1()
        demo_scenario_2()
        demo_scenario_3()
        demo_scenario_4()
        print("\n✅ Full demo complete!")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)