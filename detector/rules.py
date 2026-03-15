"""
Rule-Based Scam Detection
Fast pattern matching for common scam indicators
"""

import re
from typing import Dict, List


class RuleDetector:
    """Rule-based scam detection using keywords and patterns"""
    
    # Scam Keywords by Category
    URGENT_KEYWORDS = [
        "urgent", "immediately", "right now", "asap", "within 24 hours",
        "act fast", "limited time", "don't delay", "hurry", "deadline"
    ]
    
    MONEY_KEYWORDS = [
        "transfer", "payment", "refund", "withdraw", "deposit", "crypt",
        "prize", "reward", "million", "dollar", "rupiah", "peso", "baht"
    ]
    
    OTP_KEYWORDS = [
        "otp", "pin", "password", "code", "verify", "confirm", "password",
        "secret code", "authentication code", "one time password"
    ]
    
    ACCOUNT_KEYWORDS = [
        "account locked", "verify account", "confirm identity", "update info",
        "unfreeze account", "activate account", "suspend", "deactivate"
    ]
    
    IMPERSONATION_KEYWORDS = [
        "bank", "police", "government", "support", "admin", "manager",
        "official", "federal", "commissioner", "authority"
    ]
    
    PHISHING_KEYWORDS = [
        "click link", "click here", "verify link", "open link",
        "download app", "install now"
    ]
    
    def __init__(self):
        self.link_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.shortened_link_pattern = re.compile(r'(bit\.ly|tinyurl|short\.link|ow\.ly|goo\.gl)')
    
    def rule_based_score(self, text: str) -> Dict:
        """
        Calculate scam score based on rules
        Returns score (0-100) and breakdown
        """
        score = 0
        text_lower = text.lower()
        detected_indicators = []
        
        # Urgent Keywords (20 points each, max 40)
        urgent_count = sum(1 for kw in self.URGENT_KEYWORDS if kw in text_lower)
        if urgent_count > 0:
            urgent_score = min(urgent_count * 20, 40)
            score += urgent_score
            detected_indicators.append(f"Urgent language ({urgent_count} keywords)")
        
        # Money Keywords (15 points each, max 30)
        money_count = sum(1 for kw in self.MONEY_KEYWORDS if kw in text_lower)
        if money_count > 0:
            money_score = min(money_count * 15, 30)
            score += money_score
            detected_indicators.append(f"Money-related words ({money_count} keywords)")
        
        # OTP/Password Keywords (25 points each, max 50)
        otp_count = sum(1 for kw in self.OTP_KEYWORDS if kw in text_lower)
        if otp_count > 0:
            otp_score = min(otp_count * 25, 50)
            score += otp_score
            detected_indicators.append(f"Requests sensitive info ({otp_count} keywords)")
        
        # Account Security Keywords (20 points each, max 40)
        account_count = sum(1 for kw in self.ACCOUNT_KEYWORDS if kw in text_lower)
        if account_count > 0:
            account_score = min(account_count * 20, 40)
            score += account_score
            detected_indicators.append(f"Account issues mentioned ({account_count} keywords)")
        
        # Impersonation (20 points)
        impersonation_count = sum(1 for kw in self.IMPERSONATION_KEYWORDS if kw in text_lower)
        if impersonation_count > 0:
            score += 20
            detected_indicators.append("Possible authority impersonation")
        
        # URL Detection (30 points)
        links = self.link_pattern.findall(text)
        if links:
            score += 30
            detected_indicators.append(f"Contains suspicious links ({len(links)} link(s))")
        
        # Shortened URL (35 points - high risk)
        shortened_links = self.shortened_link_pattern.findall(text)
        if shortened_links:
            score += 35
            detected_indicators.append("Contains shortened links")
        
        # Phishing Keywords (25 points)
        phishing_count = sum(1 for kw in self.PHISHING_KEYWORDS if kw in text_lower)
        if phishing_count > 0:
            score += 25
            detected_indicators.append("Asks to click suspicious links")
        
        # Excessive special characters or CAPS (potential scam trait)
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if caps_ratio > 0.5:
            score += 15
            detected_indicators.append("Excessive capitalization")
        
        # Suspicious patterns
        if "!!!" in text or "???" in text:
            score += 10
            detected_indicators.append("Excessive punctuation")
        
        # Cap at 100
        final_score = min(score, 100)
        
        return {
            "score": final_score,
            "indicators": detected_indicators,
            "confidence": "high" if len(detected_indicators) >= 2 else "medium" if len(detected_indicators) == 1 else "low"
        }
    
    def get_rule_breakdown(self, text: str) -> str:
        """Return human-readable breakdown of rule detections"""
        result = self.rule_based_score(text)
        
        breakdown = f"📋 Rule-Based Detection:\n"
        breakdown += f"Score: {result['score']}/100\n"
        breakdown += f"Confidence: {result['confidence']}\n"
        
        if result['indicators']:
            breakdown += "\nDetected:\n"
            for indicator in result['indicators']:
                breakdown += f"  • {indicator}\n"
        else:
            breakdown += "No high-risk patterns detected.\n"
        
        return breakdown


def rule_based_score(text: str) -> int:
    """Legacy function for compatibility - returns score only"""
    detector = RuleDetector()
    result = detector.rule_based_score(text)
    return result["score"]
