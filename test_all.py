#!/usr/bin/env python3
"""
Test Suite for Scam Detector Bot
Run this to test all components
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from detector.rules import RuleDetector
from detector.ai_model import AIScamDetector
from detector.risk_engine import RiskEngine


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_rule_detector():
    """Test rule-based detection"""
    print_section("🧪 Testing Rule-Based Detection")
    
    detector = RuleDetector()
    
    test_cases = [
        ("This is a normal message about weather", "SAFE", 0),
        ("Click link now!!! http://bit.ly/verify123", "WARNING", 30),
        ("URGENT! Verify your bank OTP immediately! http://malicious.com", "ALERT", 85),
        ("Your account is locked. Confirm via link asap.", "ALERT", 80),
    ]
    
    for text, expected_level, expected_min_score in test_cases:
        result = detector.rule_based_score(text)
        score = result["score"]
        indicators = result["indicators"]
        
        print(f"Text: \"{text[:50]}...\"")
        print(f"Score: {score}/100")
        print(f"Indicators: {indicators}")
        print()


def test_ai_detector():
    """Test AI detection"""
    print_section("🤖 Testing AI Detector")
    
    try:
        detector = AIScamDetector()
        
        test_cases = [
            "Click here to claim your free prize!",
            "Meeting at 2pm tomorrow",
            "Verify your password immediately",
        ]
        
        for text in test_cases:
            print(f"Analyzing: \"{text}\"")
            result = detector.analyze_message(text)
            print(f"  Score: {result['score']}/100")
            print(f"  Type: {result['scam_type'].upper()}")
            print(f"  Reason: {result['reason']}")
            print()
            
    except Exception as e:
        print(f"❌ AI Detector Error: {e}")
        print("⚠️  Make sure GEMINI_API_KEY is set in .env")


def test_risk_engine():
    """Test combined risk engine"""
    print_section("⚙️  Testing Risk Engine")
    
    engine = RiskEngine()
    
    test_cases = [
        "Hi, how are you?",
        "Update your bank details at http://bank.com urgently",
        "CLICK NOW: Your account is LOCKED! OTP: Send it NOW!!!",
    ]
    
    for text in test_cases:
        print(f"Message: \"{text}\"")
        result = engine.calculate_final_risk(text)
        
        print(f"Final Score: {result['final_score']}/100")
        print(f"Rule: {result['rule_score']} | AI: {result['ai_score']}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Recommendation: {result['recommendation']}")
        print()


def test_database():
    """Test database operations"""
    print_section("💾 Testing Database")
    
    from database import Database
    
    try:
        db = Database("test_scam_detector.db")
        
        # Add user
        db.add_user(12345, "Test User")
        print("✅ User added")
        
        # Get user
        user = db.get_user(12345)
        print(f"✅ User retrieved: {user}")
        
        # Add family member
        db.add_family_member(1, 67890, "Mom", "Mother")
        print("✅ Family member added")
        
        # Get family
        family = db.get_family_members(1)
        print(f"✅ Family members: {family}")
        
        # Log detection
        db.log_detection(1, "Test message", 50, 60, 56, "WARNING")
        print("✅ Detection logged")
        
        # Get stats
        stats = db.get_user_stats(1)
        print(f"✅ Stats: {stats}")
        
        # Clean up test database
        import os
        os.remove("test_scam_detector.db")
        print("✅ Test database cleaned up")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")


def demo_analysis():
    """Run full demonstration"""
    print_section("🎬 Full Analysis Demonstration")
    
    engine = RiskEngine()
    
    # Example suspicious message
    suspicious_message = """
    ⚠️ URGENT SECURITY ALERT ⚠️
    
    Your bank account has been compromised!
    
    CLICK HERE IMMEDIATELY: http://bit.ly/secure-bank-9384
    
    Verify your account within 24 hours or it will be frozen!
    
    Enter your OTP code when prompted.
    
    Reply with: YES to proceed
    """
    
    print("Analyzing suspicious message...\n")
    result = engine.calculate_final_risk(suspicious_message)
    
    print(engine.get_formatted_report(suspicious_message, show_details=True))


def main():
    """Run all tests"""
    print("\n🚨 SCAM DETECTOR BOT - TEST SUITE\n")
    
    try:
        print("1️⃣  Testing Rule-Based Detection...")
        test_rule_detector()
        
        print("\n2️⃣  Testing AI Detector...")
        test_ai_detector()
        
        print("\n3️⃣  Testing Risk Engine...")
        test_risk_engine()
        
        print("\n4️⃣  Testing Database...")
        test_database()
        
        print("\n5️⃣  Demo: Full Analysis...")
        demo_analysis()
        
        print_section("✅ All Tests Completed!")
        
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
