"""
Risk Engine: Combines rule-based and AI scores for final assessment
"""

from typing import Dict
from detector.rules import RuleDetector
from detector.ai_model import AIScamDetector
import logging


logger = logging.getLogger(__name__)


class RiskEngine:
    """Combines multiple detection methods for comprehensive risk assessment"""
    
    # Risk Thresholds
    RISK_LEVELS = {
        "safe": (0, 40),
        "warning": (41, 70),
        "alert": (71, 100)
    }
    
    def __init__(self):
        self.rule_detector = RuleDetector()
        try:
            self.ai_detector = AIScamDetector()
            self.ai_available = True
        except Exception as e:
            logger.warning(f"AI detector unavailable: {e}")
            self.ai_available = False
    
    def calculate_final_risk(self, text: str) -> Dict:
        """
        Calculate comprehensive risk score
        Combines rule-based (40%) and AI (60%) scores
        """
        # Get rule score
        rule_result = self.rule_detector.rule_based_score(text)
        rule_score = rule_result["score"]
        
        # Get AI score (if available)
        ai_score = 50  # Default neutral
        ai_result = None
        
        if self.ai_available:
            ai_result = self.ai_detector.analyze_message(text)
            ai_score = ai_result["score"]
        
        # Combine scores: Rule (40%) + AI (60%)
        final_score = int((rule_score * 0.4) + (ai_score * 0.6))
        
        # Determine risk level
        risk_level = self._get_risk_level(final_score)
        
        return {
            "final_score": final_score,
            "rule_score": rule_score,
            "ai_score": ai_score,
            "risk_level": risk_level,
            "rule_indicators": rule_result["indicators"],
            "ai_analysis": ai_result,
            "recommendation": self._get_recommendation(final_score, risk_level)
        }
    
    def _get_risk_level(self, score: int) -> str:
        """Determine risk level from score"""
        if score <= 40:
            return "SAFE"
        elif score <= 70:
            return "WARNING"
        else:
            return "ALERT"
    
    def _get_recommendation(self, score: int, risk_level: str) -> str:
        """Generate actionable recommendation"""
        if risk_level == "SAFE":
            return "Message appears legitimate. No action needed."
        elif risk_level == "WARNING":
            return "Use caution! Verify information before taking action."
        else:
            return "DANGER! Do not click links or share personal information. Alert family immediately."
    
    def get_formatted_report(self, text: str, show_details: bool = True) -> str:
        """Generate human-readable risk report"""
        result = self.calculate_final_risk(text)
        
        # Risk level emoji
        emoji_map = {
            "SAFE": "✅",
            "WARNING": "⚠️",
            "ALERT": "🚨"
        }
        
        report = f"{emoji_map[result['risk_level']]} SCAM DETECTION REPORT\n"
        report += f"{'='*40}\n\n"
        
        # Final Score
        report += f"🎯 FINAL RISK SCORE: {result['final_score']}/100\n"
        report += f"📊 Status: {result['risk_level']}\n\n"
        
        # Score Breakdown
        if show_details:
            report += f"📈 Score Breakdown:\n"
            report += f"  • Rule-Based: {result['rule_score']}/100\n"
            report += f"  • AI Analysis: {result['ai_score']}/100\n\n"
        
        # Rule Indicators
        if result['rule_indicators']:
            report += f"🔴 Detected Red Flags:\n"
            for indicator in result['rule_indicators']:
                report += f"  • {indicator}\n"
            report += "\n"
        
        # AI Analysis
        if result['ai_analysis'] and show_details:
            report += f"🤖 AI Analysis:\n"
            report += f"  • Type: {result['ai_analysis'].get('scam_type', 'Unknown').upper()}\n"
            report += f"  • Reason: {result['ai_analysis'].get('reason', 'N/A')}\n\n"
        
        # Recommendation
        report += f"💡 Recommendation:\n"
        report += f"{result['recommendation']}\n"
        
        return report
    
    def should_alert_family(self, score: int) -> bool:
        """Determine if family should be alerted"""
        return score > 70
    
    def get_alert_message(self, text: str, user_name: str = "User") -> str:
        """Generate family alert message"""
        result = self.calculate_final_risk(text)
        
        alert = f"🚨 SCAM ALERT for {user_name}!\n\n"
        alert += f"Risk Score: {result['final_score']}/100 ({result['risk_level']})\n\n"
        alert += f"Suspected Type: {result['ai_analysis']['scam_type'].upper() if result['ai_analysis'] else 'Unknown'}\n\n"
        alert += f"⚠️ {result['recommendation']}\n\n"
        alert += f"Message Content:\n\"{text[:200]}{'...' if len(text) > 200 else ''}\"\n"
        
        return alert


def final_risk(rule_score: int, ai_score: int) -> int:
    """
    Legacy function for compatibility
    Combine scores: Rule (40%) + AI (60%)
    """
    return int((rule_score * 0.4) + (ai_score * 0.6))
