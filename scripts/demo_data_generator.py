"""
Demo data generator for Sentinel
Creates realistic attack scenarios for demonstration
"""
import asyncio
import json
import random
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sentinel_agent import sentinel_agent


class DemoScenarioGenerator:
    """Generates realistic attack scenarios for demonstration"""
    
    def __init__(self):
        self.attack_scenarios = [
            "credential_stuffing",
            "lateral_movement", 
            "data_exfiltration",
            "privilege_escalation"
        ]
    
    async def generate_credential_stuffing_scenario(self):
        """Generate a credential stuffing attack scenario"""
        print("🎭 Generating credential stuffing attack scenario...")
        
        # Attacker profile
        attacker_ip = "203.0.113.15"
        target_users = ["alice.johnson", "bob.smith", "charlie.brown"]
        
        events = []
        
        # Stage 1: Initial probing (2 months ago)
        base_time = datetime.utcnow() - timedelta(days=60)
        
        for user in target_users:
            event = {
                "event_type": "authentication",
                "action": "login_attempt",
                "source_ip": attacker_ip,
                "username": user,
                "timestamp": base_time.isoformat(),
                "auth": {
                    "success": False,
                    "method": "password",
                    "attempts": 1
                },
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "geo_location": {
                    "country": "CN",
                    "city": "Beijing"
                }
            }
            events.append(event)
            
            # Process through Sentinel
            result = await sentinel_agent.process_event(event)
            print(f"   Processed probe for {user}: Threat Score {result['threat_score']}")
        
        # Stage 2: Credential stuffing campaign (1 week ago)  
        campaign_time = datetime.utcnow() - timedelta(days=7)
        
        print("   Executing credential stuffing campaign...")
        for user in target_users:
            for attempt in range(random.randint(5, 15)):
                event = {
                    "event_type": "authentication",
                    "action": "login_attempt",
                    "source_ip": attacker_ip,
                    "username": user,
                    "timestamp": (campaign_time + timedelta(minutes=attempt*2)).isoformat(),
                    "auth": {
                        "success": False if attempt < 10 else random.choice([False, True]),
                        "method": "password",
                        "attempts": attempt + 1
                    },
                    "user_agent": "python-requests/2.25.1",  # Automated tool
                    "geo_location": {
                        "country": "CN",
                        "city": "Beijing"
                    }
                }
                events.append(event)
                
                result = await sentinel_agent.process_event(event)
                if result["threat_score"] > 5:
                    print(f"   🚨 HIGH THREAT detected for {user}: Score {result['threat_score']}")
        
        # Stage 3: Successful login and data access (today)
        success_time = datetime.utcnow() - timedelta(hours=2)
        
        successful_event = {
            "event_type": "authentication",
            "action": "login_attempt",
            "source_ip": attacker_ip,
            "username": "alice.johnson",
            "timestamp": success_time.isoformat(),
            "auth": {
                "success": True,
                "method": "password",
                "attempts": 1
            },
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "geo_location": {
                "country": "CN", 
                "city": "Beijing"
            }
        }
        
        result = await sentinel_agent.process_event(successful_event)
        print(f"   🎯 SUCCESSFUL LOGIN detected: Threat Score {result['threat_score']}")
        print(f"   Action taken: {result['action_taken']}")
        
        return events
    
    async def generate_lateral_movement_scenario(self):
        """Generate lateral movement attack scenario"""
        print("🎭 Generating lateral movement scenario...")
        
        # Compromise progression
        compromised_user = "diana.prince"
        internal_ips = ["192.168.1.100", "192.168.1.150", "192.168.1.200"]
        
        events = []
        
        # Stage 1: Initial compromise
        initial_time = datetime.utcnow() - timedelta(days=14)
        
        # Normal login
        event = {
            "event_type": "authentication", 
            "action": "login_attempt",
            "source_ip": "192.168.1.100",
            "username": compromised_user,
            "timestamp": initial_time.isoformat(),
            "auth": {"success": True, "method": "password"},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        result = await sentinel_agent.process_event(event)
        events.append(event)
        
        # Stage 2: Reconnaissance (1 week ago)
        recon_time = datetime.utcnow() - timedelta(days=7)
        
        for target_ip in internal_ips:
            event = {
                "event_type": "network",
                "action": "port_scan",
                "source_ip": "192.168.1.100",  # From compromised machine
                "username": compromised_user,
                "timestamp": recon_time.isoformat(),
                "network": {
                    "destination_ip": target_ip,
                    "ports": [22, 80, 443, 3389, 445],
                    "protocol": "tcp"
                }
            }
            result = await sentinel_agent.process_event(event)
            events.append(event)
            print(f"   Port scan to {target_ip}: Threat Score {result['threat_score']}")
        
        # Stage 3: Lateral movement attempts (3 days ago)
        lateral_time = datetime.utcnow() - timedelta(days=3)
        
        for i, target_ip in enumerate(internal_ips):
            event = {
                "event_type": "authentication",
                "action": "lateral_login_attempt", 
                "source_ip": target_ip,
                "username": compromised_user,
                "timestamp": (lateral_time + timedelta(hours=i)).isoformat(),
                "auth": {
                    "success": i == len(internal_ips) - 1,  # Last attempt succeeds
                    "method": "ntlm"
                },
                "lateral_movement": {
                    "source_host": "192.168.1.100",
                    "technique": "pass_the_hash"
                }
            }
            result = await sentinel_agent.process_event(event)
            events.append(event)
            
            if result["threat_score"] > 6:
                print(f"   🚨 LATERAL MOVEMENT detected to {target_ip}: Score {result['threat_score']}")
        
        return events
    
    async def run_demo_scenario(self, scenario_name: str):
        """Run a specific demo scenario"""
        print(f"🚀 Starting demo scenario: {scenario_name}")
        
        # Initialize Sentinel
        await sentinel_agent.initialize()
        
        if scenario_name == "credential_stuffing":
            events = await self.generate_credential_stuffing_scenario()
        elif scenario_name == "lateral_movement":
            events = await self.generate_lateral_movement_scenario()
        else:
            print(f"Unknown scenario: {scenario_name}")
            return
        
        print(f"✅ Demo scenario completed: {len(events)} events processed")
        
        # Get dashboard data to show results
        dashboard_data = await sentinel_agent.get_dashboard_data()
        print("\n📊 Dashboard Summary:")
        print(f"   Total events (24h): {dashboard_data['statistics']['total_events_24h']}")
        print(f"   High threat events: {dashboard_data['statistics']['high_threat_events']}")
        print(f"   Average threat score: {dashboard_data['statistics']['average_threat_score']}")
        
        return events


async def main():
    """Main demo runner"""
    print("🛡️  Sentinel Demo Data Generator")
    print("=" * 50)
    
    generator = DemoScenarioGenerator()
    
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        print("Available scenarios:")
        for scenario in generator.attack_scenarios:
            print(f"  - {scenario}")
        scenario = input("\nSelect scenario: ")
    
    if scenario in generator.attack_scenarios:
        await generator.run_demo_scenario(scenario)
    else:
        print(f"Invalid scenario: {scenario}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())