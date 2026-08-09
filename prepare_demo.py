#!/usr/bin/env python3
"""
Sentinel Demo Preparation Script
Ensures system is ready for perfect video demo recording
"""
import requests
import json
import time
import os
import subprocess
import sys
from datetime import datetime

def check_servers():
    """Check if both servers are running"""
    print("🔍 Checking server status...")
    
    try:
        # Check API server
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server (port 8000): Running")
        else:
            print("❌ API Server: Not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ API Server (port 8000): Not running")
        return False
    
    try:
        # Check frontend server
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Server (port 3000): Running")
        else:
            print("❌ Frontend Server: Not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Frontend Server (port 3000): Not running")
        return False
    
    return True

def test_simulation():
    """Test that simulation endpoints work correctly"""
    print("\n🧪 Testing simulation functionality...")
    
    try:
        response = requests.post(
            "http://localhost:8000/simulate",
            headers={"Content-Type": "application/json"},
            json={"event_type": "suspicious"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("simulation_result", {}).get("success"):
                threat_score = data["simulation_result"]["threat_score"]
                action_taken = data["simulation_result"]["action_taken"]
                print(f"✅ Simulation working - Threat Score: {threat_score}, Action: {action_taken}")
                return True
            else:
                print("❌ Simulation failed - check server logs")
                return False
        else:
            print(f"❌ Simulation endpoint error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Simulation test failed: {e}")
        return False

def generate_baseline_events():
    """Generate some baseline events for better demo"""
    print("\n📊 Generating baseline demo events...")
    
    event_types = [
        {"event_type": "normal", "description": "Normal event"},
        {"event_type": "suspicious", "description": "Suspicious event"},
        {"event_type": "normal", "description": "Normal event"},
    ]
    
    for i, event in enumerate(event_types, 1):
        try:
            print(f"   Creating event {i}/3: {event['description']}")
            response = requests.post(
                "http://localhost:8000/simulate",
                headers={"Content-Type": "application/json"},
                json=event,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    threat_score = data["simulation_result"]["threat_score"]
                    print(f"   ✅ Event created - Threat Score: {threat_score}")
                else:
                    print(f"   ⚠️  Event creation warning")
            
            time.sleep(1)  # Brief pause between events
            
        except Exception as e:
            print(f"   ❌ Failed to create event {i}: {e}")
    
    print("✅ Baseline events created")

def check_recent_events():
    """Verify we have recent events to show in demo"""
    print("\n📋 Checking recent events for demo...")
    
    try:
        response = requests.get("http://localhost:8000/events?hours=24&limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            if len(events) >= 3:
                print(f"✅ Found {len(events)} recent events for demo")
                
                # Show summary of events
                for i, event in enumerate(events[:3], 1):
                    threat_score = event.get("threat_score", "unknown")
                    action = event.get("action_taken", "unknown")
                    print(f"   Event {i}: Score {threat_score}, Action: {action}")
                return True
            else:
                print(f"⚠️  Only {len(events)} events found - consider generating more")
                return False
        else:
            print("❌ Could not fetch recent events")
            return False
            
    except Exception as e:
        print(f"❌ Error checking events: {e}")
        return False

def optimize_browser_display():
    """Provide browser optimization instructions"""
    print("\n🌐 Browser optimization for demo recording:")
    print("   1. Open Chrome/Safari in private/incognito mode")
    print("   2. Navigate to: http://localhost:3000")
    print("   3. Press F11 (or Cmd+Ctrl+F on Mac) for fullscreen")
    print("   4. Set zoom to 110% for better readability")
    print("   5. Hide bookmarks bar (Cmd+Shift+B)")
    print("   6. Close developer tools if open")
    
def display_demo_checklist():
    """Display final demo preparation checklist"""
    print("\n📋 DEMO RECORDING CHECKLIST:")
    print("   🎬 BEFORE RECORDING:")
    print("      □ Close all unnecessary applications")
    print("      □ Turn on 'Do Not Disturb' mode")
    print("      □ Check audio input levels")
    print("      □ Practice script once more")
    print("      □ Have water nearby for clear speech")
    print()
    print("   🎯 DURING RECORDING:")
    print("      □ Speak 20% slower than normal")
    print("      □ Pause after key points")
    print("      □ Click 'Simulate Suspicious Event' confidently")
    print("      □ Point to threat scores and reasoning")
    print("      □ Show real-time updates happening")
    print()
    print("   ⚡ KEY DEMO POINTS:")
    print("      □ 'From 207 days to 5 minutes detection'")
    print("      □ 'Memory-driven threat correlation'")
    print("      □ 'Automatic IP blocking action'")
    print("      □ 'Gets smarter with every event'")

def display_quick_commands():
    """Show useful commands for demo"""
    print("\n⚡ QUICK DEMO COMMANDS:")
    print("   # Test simulation manually:")
    print("   curl -X POST http://localhost:8000/simulate -H 'Content-Type: application/json' -d '{\"event_type\": \"suspicious\"}' | jq")
    print()
    print("   # Check recent events:")
    print("   curl http://localhost:8000/events?limit=3 | jq '.events[0]'")
    print()
    print("   # Quick health check:")
    print("   curl http://localhost:8000/health")

def main():
    """Main demo preparation workflow"""
    print("🛡️  SENTINEL DEMO PREPARATION")
    print("=" * 50)
    
    # Check if servers are running
    if not check_servers():
        print("\n❌ Servers not running! Please start them first:")
        print("   Terminal 1: python local_server.py")
        print("   Terminal 2: cd frontend && npm start")
        return False
    
    # Test simulation functionality  
    if not test_simulation():
        print("\n❌ Simulation not working! Check server logs.")
        return False
    
    # Generate baseline events
    generate_baseline_events()
    
    # Check we have events to show
    check_recent_events()
    
    # Display optimization tips
    optimize_browser_display()
    
    # Display final checklist
    display_demo_checklist()
    
    # Show useful commands
    display_quick_commands()
    
    print("\n" + "=" * 50)
    print("🚀 SYSTEM READY FOR DEMO RECORDING!")
    print("   Open http://localhost:3000 and start filming!")
    print("🎬 Break a leg! Show them how memory saves millions! 🛡️")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Demo preparation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)