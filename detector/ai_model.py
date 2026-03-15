"""
AI-Based Scam Detection using Google Gemini API
Advanced classification with explainability
"""

import os
import json
import logging
from typing import Dict
import google.generativeai as genai


logger = logging.getLogger(__name__)


class AIScamDetector:
    """AI-powered scam detection using Gemini 2.5 Flash"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini API"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_message(self, text: str) -> Dict:
        """
        Analyze message using Gemini AI
        Returns: score (0-100), reason, and confidence
        """
        try:
            prompt = f"""You are a STRICT professional scam detection system. Your job is to identify ACTUAL SCAMS, not normal friendly messages.

SCAM INDICATORS (High Risk):
- Urgent pressure + money/link requests: "Click now! Verify account or it's locked!"
- Fake authority impersonation: "I'm from your bank"
- Money/payment requests with urgency: "Send money immediately or lose access"
- OTP/authentication code requests: "Please give me your verification code"
- Phishing links with urgency: "Click this shortened link to confirm identity"
- Account lockout threats + verification requests
- Prize/lottery scams: "You won! Claim now!"
- Fake investment opportunities

NOT SCAMS (Normal Messages):
- Someone greeting you after a long time
- Casual conversation with all caps (just enthusiasm!)
- Normal friendly banter
- Regular catch-up messages
- Messages without requests for sensitive data, money, or urgent action

IMPORTANT: Only flag as HIGH RISK if there's:
1. Actual request for money/data/clicking links AND
2. Urgency or deception

Analyze this message carefully. If it's just a friendly message, score it LOW.

Message: "{text}"

Return ONLY this JSON format:
{{
    "risk_score": <0-100>,
    "reason": "<brief explanation>",
    "scam_type": "<phishing/financial/impersonation/urgent_money/otp_request/other/none>",
    "confidence": "<high/medium/low>"
}}"""
            
            response = self.model.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            result = json.loads(json_str)
            
            return {
                "score": int(result.get("risk_score", 50)),
                "reason": result.get("reason", "Unable to determine"),
                "scam_type": result.get("scam_type", "unknown"),
                "confidence": result.get("confidence", "low"),
                "success": True
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {
                "score": 50,
                "reason": "Analysis incomplete",
                "scam_type": "unknown",
                "confidence": "low",
                "success": False
            }
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                "score": 30,
                "reason": "Temporary analysis unavailable",
                "scam_type": "unknown",
                "confidence": "low",
                "success": False
            }
    
    def get_detailed_analysis(self, text: str) -> str:
        """Return detailed human-readable analysis"""
        result = self.analyze_message(text)
        
        analysis = f"🤖 AI Analysis Results:\n"
        analysis += f"Risk Score: {result['score']}/100\n"
        analysis += f"Scam Type: {result['scam_type'].upper()}\n"
        analysis += f"Confidence: {result['confidence'].upper()}\n"
        analysis += f"\n💭 Reasoning:\n{result['reason']}\n"
        
        if not result['success']:
            analysis += "\n⚠️ Note: Analysis had issues, treat with caution"
        
        return analysis


def ai_analyze(text: str) -> int:
    """Legacy function for compatibility - returns score only"""
    try:
        detector = AIScamDetector()
        result = detector.analyze_message(text)
        return result["score"]
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return 50  # Default medium score on error
