"""
FastAPI Server with Telegram Webhook Integration
Receives updates from Telegram and processes them
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import scam detection engine
try:
    from detector.risk_engine import RiskEngine
    from database import db
    risk_engine = RiskEngine()
    logger.info("✅ Risk Engine loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading Risk Engine: {e}")
    risk_engine = None

# Initialize FastAPI app
app = FastAPI(
    title="🚨 Scam Detector Bot",
    description="Multi-layer scam detection bot for Telegram",
    version="1.0.0"
)

# Get configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8000))
WEBHOOK_PATH = "/telegram-webhook"

# Store user conversation contexts
user_conversations = {}  # {user_id: [messages]}
user_question_sessions = {}  # {user_id: {"message": text, "answers": [], "question_index": 0}}

logger.info("✅ FastAPI Server initialized")
logger.info(f"📡 Webhook URL: {TELEGRAM_WEBHOOK_URL}")
logger.info(f"🔑 Bot Token: {TELEGRAM_BOT_TOKEN[:20]}..." if TELEGRAM_BOT_TOKEN else "⚠️  No bot token set")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "✅ Running",
        "service": "Scam Detector Bot",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "service": "🚨 Scam Detector Bot",
        "version": "1.0.0",
        "status": "🟢 Running",
        "endpoints": {
            "health": "GET /health",
            "webhook": f"POST {WEBHOOK_PATH}",
            "root": "GET /"
        },
        "webhook_info": {
            "url": TELEGRAM_WEBHOOK_URL + WEBHOOK_PATH,
            "bot": "@SafePolis_bot"
        }
    }


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """Receive Telegram webhook updates"""
    import requests
    
    try:
        data = await request.json()
        
        # Extract message info
        update_id = data.get("update_id")
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        from_user = message.get("from", {}).get("first_name", "User")
        user_id = message.get("from", {}).get("id")
        
        logger.info(f"📩 Received update {update_id}")
        logger.info(f"👤 From: {from_user} (Chat: {chat_id}, User: {user_id})")
        logger.info(f"📝 Message: {text[:100] if text else '(no text)'}")
        
        # Send response based on message
        if text and chat_id:
            response_text = None
            
            # **IMPORTANT**: Check MORE SPECIFIC commands FIRST to avoid prefix matching issues
            # For example, /start_collecting must be checked BEFORE /start
            
            if text.startswith("/start_collecting"):
                user_conversations[user_id] = []
                response_text = """
🎯 Collection Mode Started

Send messages you want to analyze:
- Type your messages
- When done, send /analyze_conversation

I'll analyze the entire conversation for scam patterns!
                """
            elif text.startswith("/analyze_conversation"):
                if user_id in user_conversations and user_conversations[user_id]:
                    # Analyze all messages in conversation
                    all_messages = " ".join(user_conversations[user_id])
                    
                    if risk_engine:
                        result = risk_engine.calculate_final_risk(all_messages)
                        
                        emoji_map = {"SAFE": "✅", "WARNING": "⚠️", "ALERT": "🚨"}
                        emoji = emoji_map.get(result['risk_level'], "❓")
                        
                        response_text = f"""{emoji} CONVERSATION ANALYSIS REPORT

🎯 Overall Risk Score: {result['final_score']}/100
📊 Status: {result['risk_level']}

📈 Score Breakdown:
  • Rule-Based: {result['rule_score']}/100
  • AI Analysis: {result['ai_score']}/100

🔴 Detected Patterns:
"""
                        if result['rule_indicators']:
                            for indicator in result['rule_indicators'][:5]:
                                response_text += f"  • {indicator}\n"
                        else:
                            response_text += "  • No high-risk patterns detected\n"
                        
                        response_text += f"\n💡 Recommendation:\n{result['recommendation']}\n"
                        
                        # DEBUG: Show family alert status
                        debug_info = "\n📋 FAMILY ALERT STATUS:\n"
                        try:
                            user_data = db.get_user(chat_id)
                            if user_data:
                                family_members = db.get_family_members(user_data['user_id'])
                                debug_info += f"  ✓ Family members found: {len(family_members)}\n"
                                for member in family_members:
                                    is_active = db.is_user_active(member['family_chat_id'])
                                    status = "✅ Active" if is_active else "❌ NOT started bot"
                                    debug_info += f"    • {member['name']} ({member['family_chat_id']}): {status}\n"
                            else:
                                debug_info += "  ⚠️  User not found in database\n"
                        except Exception as e:
                            debug_info += f"  ❌ Error loading family info: {e}\n"
                        
                        if result['final_score'] > 70:
                            debug_info += f"  ✅ Score ({result['final_score']}) > 70: Alerts SHOULD be sent\n"
                        else:
                            debug_info += f"  ⚠️  Score ({result['final_score']}) <= 70: No alerts sent\n"
                        
                        response_text += debug_info
                        
                        # **SEND ALERTS TO FAMILY IF HIGH-RISK**
                        should_alert_family = result['final_score'] > 70
                        if should_alert_family and db:
                            try:
                                user_data = db.get_user(chat_id)
                                if user_data:
                                    family_members = db.get_family_members(user_data['user_id'])
                                    if family_members:
                                        for member in family_members:
                                            alert_message = f"""
🚨 SCAM ALERT FOR {from_user}!

⚠️ Your family member received suspicious messages in a conversation:

📱 Messages: "{all_messages[:150]}..."

🎯 Overall Risk Score: {result['final_score']}/100
📊 Status: {result['risk_level']}

🔴 Red Flags Detected:
"""
                                            if result['rule_indicators']:
                                                for indicator in result['rule_indicators'][:3]:
                                                    alert_message += f"  • {indicator}\n"
                                            
                                            alert_message += f"""
💡 Recommendation:
{result['recommendation']}

🛡️ Please verify with {from_user} about this conversation!
                                            """
                                            
                                            # Check if family member is active (started bot)
                                            if db.is_user_active(member['family_chat_id']):
                                                # Send to family member
                                                try:
                                                    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                                    family_payload = {
                                                        "chat_id": member['family_chat_id'],
                                                        "text": alert_message.strip()
                                                    }
                                                    family_response = requests.post(send_url, json=family_payload)
                                                    if family_response.status_code == 200:
                                                        logger.info(f"✅ Conversation alert sent to {member['name']}")
                                                    else:
                                                        logger.warning(f"⚠️ Failed to send alert to {member['name']}: {family_response.status_code}")
                                                except Exception as e:
                                                    logger.error(f"Error sending family alert: {e}")
                                            else:
                                                logger.warning(f"⚠️ {member['name']} ({member['family_chat_id']}) hasn't started bot - cannot send alert. They need to /start the bot first!")
                            except Exception as e:
                                logger.error(f"Error getting family members for conversation: {e}")
                        
                        # Clear conversation
                        del user_conversations[user_id]
                    else:
                        response_text = "❌ Analysis engine not available"
                else:
                    response_text = "📭 No messages collected. Use /start_collecting first!"
            
            elif text.startswith("/add_family"):
                # Parse: /add_family <family_id> <name> <relation>
                parts = text.split()
                if len(parts) >= 4:
                    family_id = parts[1]
                    name = parts[2]
                    relation = " ".join(parts[3:])  # In case relation has spaces
                    
                    if db:
                        try:
                            user_data = db.get_user(chat_id)
                            if not user_data:
                                db.add_user(chat_id, from_user)
                                user_data = db.get_user(chat_id)
                            
                            if user_data:
                                db.add_family_member(user_data['user_id'], family_id, relation, name)
                                response_text = f"""
✅ Family Member Added!

👤 Name: {name}
🤝 Relation: {relation}
📱 ID: {family_id}

✨ When high-risk scams are detected, they'll receive alerts!
                                """
                            else:
                                response_text = "❌ Error creating user profile"
                        except Exception as e:
                            logger.error(f"Error adding family: {e}")
                            response_text = f"❌ Error: {str(e)}"
                    else:
                        response_text = "❌ Database not available"
                else:
                    response_text = """
❌ Invalid format!

Correct format: /add_family <family_id> <name> <relation>

Example: /add_family angelNg0125 LeeLing Daughter
Example: /add_family 123456789 Mom Mother
                    """
            
            elif text.startswith("/list_family"):
                # List family members
                if db:
                    try:
                        user_data = db.get_user(chat_id)
                        if user_data:
                            family_members = db.get_family_members(user_data['user_id'])
                            if family_members:
                                response_text = "👨‍👩‍👧 FAMILY MEMBERS:\n\n"
                                for member in family_members:
                                    response_text += f"👤 {member['name']}\n"
                                    response_text += f"   Relation: {member['relationship']}\n"
                                    response_text += f"   ID: {member['family_chat_id']}\n\n"
                                response_text += "When you get HIGH-RISK alerts, they'll be notified!"
                            else:
                                response_text = """
👨‍👩‍👧 Family Members:

No family members added yet.

Use: /add_family <id> <name> <relation>
Example: /add_family 123456789 Mom Mother
                                """
                        else:
                            response_text = "Please use /start first to create your profile"
                    except Exception as e:
                        logger.error(f"Error listing family: {e}")
                        response_text = "❌ Error retrieving family members"
                else:
                    response_text = "Database not available"
            
            elif text.startswith("/ask_details"):
                # Interactive questioning mode
                if user_id in user_question_sessions:
                    session = user_question_sessions[user_id]
                    
                    # List of clarifying questions
                    questions = [
                        "❓ Who sent this message? (friend/family/stranger/business/unknown)",
                        "❓ What are they asking you to do?",
                        "❓ Is there urgency or pressure? (yes/no)",
                        "❓ Are they asking for personal info, money, or passwords? (yes/no)",
                        "❓ Do they claim to represent a trusted organization? (yes/no)"
                    ]
                    
                    # Start from first question
                    session['question_index'] = 0
                    response_text = f"""
📋 INTERACTIVE DEEP ANALYSIS

Message: "{session['message'][:100]}..."

{questions[0]}

Type your answer and I'll ask the next question:
                    """
                else:
                    response_text = """
❓ No WARNING message to analyze.

How to use /ask_details:
1. Send a message to analyze
2. If it gets WARNING (⚠️) status try /ask_details
3. Answer clarifying questions
4. Get more accurate result!

Send any message first, then use /ask_details
                    """
            
            elif text.startswith("/help"):
                response_text = """
📖 HELP

/start - Start bot
/help - Show commands
/get_id - Get your chat ID (for adding family)
/stats - View statistics
/start_collecting - Begin collecting messages
/analyze_conversation - Analyze collected messages
/ask_details - Interactive detailed analysis
/clear - Clear messages
/add_family <id> <name> <relation> - Add family
/list_family - Show family members

🚨 Risk Levels:
✅ SAFE (0-40)
⚠️ WARNING (41-70)  
🚨 ALERT (71-100)

Send any message for instant scam analysis!
                """
            
            elif text.startswith("/get_id"):
                response_text = f"""
🆔 YOUR TELEGRAM IDs:

**Your Chat ID:** {chat_id}
**Your User ID:** {user_id}
**Your Name:** {from_user}

ℹ️ Use the Chat ID ({chat_id}) when adding family members!

Example: /add_family {chat_id} Mom Mother

📌 To add family members:
1. Have them send /get_id to the bot to get THEIR chat ID
2. Then you send: /add_family <their_chat_id> <their_name> <relation>
3. They'll receive alerts automatically!
                """
            
            elif text.startswith("/clear"):
                if user_id in user_conversations:
                    del user_conversations[user_id]
                    response_text = "✅ Messages cleared!"
                else:
                    response_text = "✅ No messages to clear"
            
            elif text.startswith("/stats"):
                if db:
                    try:
                        user_data = db.get_user(chat_id)
                        if user_data:
                            stats = db.get_user_stats(user_data['user_id'])
                            response_text = f"""
📊 YOUR STATISTICS

Total Messages Analyzed: {stats['total_detections']}
🚨 High-Risk Alerts: {stats['alerts']}
⚠️ Warnings: {stats['warnings']}
👨‍👩‍👧 Family Alerts Sent: {stats['family_alerts']}
Average Risk Score: {stats['avg_score']}/100
                        """
                        else:
                            response_text = "📝 No data yet. Start using the bot to collect stats!"
                    except:
                        response_text = "📝 Statistics not available yet"
                else:
                    response_text = "Database not available"
            
            elif text.startswith("/start"):
                # **REGISTER USER IN DATABASE WHEN THEY START BOT**
                if db:
                    try:
                        user_data = db.get_user(chat_id)
                        if not user_data:
                            db.add_user(chat_id, from_user)
                            logger.info(f"✅ New user registered: {from_user} (Chat ID: {chat_id})")
                        else:
                            logger.info(f"ℹ️  User already registered: {from_user}")
                    except Exception as e:
                        logger.error(f"Error registering user: {e}")
                
                response_text = """
👋 Welcome to Scam Detector Bot!

I can analyze messages for scam indicators using AI + rule-based detection.

**Commands:**
/help - Show commands
/get_id - Get your chat ID (for adding to family alerts)
/stats - Your statistics  
/start_collecting - Begin collecting messages
/analyze_conversation - Analyze all collected messages
/clear - Clear current messages

**How to use:**
1. Send /start_collecting to begin
2. Send messages you want to analyze
3. Send /analyze_conversation to get full report

Or just send single messages for instant analysis!
                """
            
            else:
                # For regular messages - instant analysis, collect, or answer questions
                if user_id in user_question_sessions:
                    # User is answering interactive questions
                    session = user_question_sessions[user_id]
                    session['answers'].append(text)
                    session['question_index'] += 1
                    
                    questions = [
                        "❓ Who sent this message? (friend/family/stranger/business/unknown)",
                        "❓ What are they asking you to do?",
                        "❓ Is there urgency or pressure? (yes/no)",
                        "❓ Are they asking for personal info, money, or passwords? (yes/no)",
                        "❓ Do they claim to represent a trusted organization? (yes/no)"
                    ]
                    
                    if session['question_index'] < len(questions):
                        # Next question
                        response_text = f"{questions[session['question_index']]}\n\n(Reply with your answer)"
                    else:
                        # All questions answered - re-analyze
                        context_info = f"""
Additional Context:
- Sender: {session['answers'][0] if len(session['answers']) > 0 else 'Unknown'}
- Request: {session['answers'][1][:80] if len(session['answers']) > 1 else 'Unknown'}
- Urgency: {session['answers'][2] if len(session['answers']) > 2 else 'Unknown'}
- Data/Money Request: {session['answers'][3] if len(session['answers']) > 3 else 'Unknown'}
- Impersonation: {session['answers'][4] if len(session['answers']) > 4 else 'Unknown'}
                        """
                        
                        if risk_engine:
                            result = risk_engine.calculate_final_risk(session['message'])
                            
                            emoji_map = {"SAFE": "✅", "WARNING": "⚠️", "ALERT": "🚨"}
                            emoji = emoji_map.get(result['risk_level'], "❓")
                            
                            response_text = f"""{emoji} DETAILED ANALYSIS REPORT

Original Message: "{session['message'][:80]}..."

{context_info}

🎯 Final Risk Score: {result['final_score']}/100
📊 Status: {result['risk_level']}

📈 Score Breakdown:
  • Rule-Based: {result['rule_score']}/100
  • AI Analysis: {result['ai_score']}/100

💡 Verdict:
{result['recommendation']}

TIP: If urgency + money/data request = LIKELY SCAM! Be careful!
                            """
                        
                        # **SEND ALERTS TO FAMILY IF HIGH-RISK**
                        should_alert_family = result['final_score'] > 70
                        if should_alert_family and db:
                            try:
                                user_data = db.get_user(chat_id)
                                if user_data:
                                    family_members = db.get_family_members(user_data['user_id'])
                                    if family_members:
                                        for member in family_members:
                                            alert_message = f"""
🚨 DETAILED ANALYSIS ALERT FOR {from_user}!

⚠️ Your family member investigated a suspicious message:

📱 Message: "{session['message'][:150]}..."

🎯 Final Risk Score: {result['final_score']}/100
📊 Status: {result['risk_level']}

📋 Analysis Details:
{context_info}

📈 Score Breakdown:
  • Rule-Based: {result['rule_score']}/100
  • AI Analysis: {result['ai_score']}/100

💡 Recommendation:
{result['recommendation']}

🛡️ Please verify with {from_user} about this message!
                                            """
                                            
                                            # Check if family member is active (started bot)
                                            if db.is_user_active(member['family_chat_id']):
                                                # Send to family member
                                                try:
                                                    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                                    family_payload = {
                                                        "chat_id": member['family_chat_id'],
                                                        "text": alert_message.strip()
                                                    }
                                                    family_response = requests.post(send_url, json=family_payload)
                                                    if family_response.status_code == 200:
                                                        logger.info(f"✅ Detailed analysis alert sent to {member['name']}")
                                                    else:
                                                        logger.warning(f"⚠️ Failed to send to {member['name']}: {family_response.status_code}")
                                                except Exception as e:
                                                    logger.error(f"Error sending family alert: {e}")
                                            else:
                                                logger.warning(f"⚠️ {member['name']} ({member['family_chat_id']}) hasn't started bot yet!")
                            except Exception as e:
                                logger.error(f"Error getting family members for detailed analysis: {e}")
                        
                        del user_question_sessions[user_id]
                
                elif user_id in user_conversations:
                    # Collecting mode - add message to list
                    user_conversations[user_id].append(text)
                    response_text = f"""
📝 Message collected! ({len(user_conversations[user_id])} total)

Send more messages or /analyze_conversation to analyze all
                    """
                else:
                    # Instant analysis mode
                    if risk_engine:
                        try:
                            result = risk_engine.calculate_final_risk(text)
                            
                            emoji_map = {"SAFE": "✅", "WARNING": "⚠️", "ALERT": "🚨"}
                            emoji = emoji_map.get(result['risk_level'], "❓")
                            
                            response_text = f"""{emoji} SCAM DETECTION REPORT

🎯 Risk Score: {result['final_score']}/100
📊 Status: {result['risk_level']}

📈 Breakdown:
  Rules: {result['rule_score']}/100
  AI: {result['ai_score']}/100

🔴 Red Flags:
"""
                            if result['rule_indicators']:
                                for indicator in result['rule_indicators'][:3]:
                                    response_text += f"  • {indicator}\n"
                            else:
                                response_text += "  • None detected\n"
                            
                            if result['ai_analysis']:
                                response_text += f"\n🤖 AI Analysis:\n"
                                response_text += f"Type: {result['ai_analysis'].get('scam_type', 'Unknown').upper()}\n"
                                response_text += f"Reason: {result['ai_analysis'].get('reason', 'N/A')}\n"
                            
                            response_text += f"\n💡 Action:\n{result['recommendation']}"
                            
                            # Check if ALERT level (high risk) and add debug info
                            if result['final_score'] > 70:
                                response_text += "\n\n📋 FAMILY ALERT STATUS:\n"
                                try:
                                    user_data = db.get_user(chat_id)
                                    if user_data:
                                        family_members = db.get_family_members(user_data['user_id'])
                                        response_text += f"  ✓ Family members: {len(family_members)}\n"
                                        for member in family_members:
                                            is_active = db.is_user_active(member['family_chat_id'])
                                            status = "✅ Active" if is_active else "❌ NOT started"
                                            response_text += f"    • {member['name']}: {status}\n"
                                        response_text += "  ✅ Alerts will be sent to active members!\n"
                                    else:
                                        response_text += "  ⚠️  User profile not found\n"
                                except Exception as e:
                                    response_text += f"  ❌ Error: {e}\n"
                            
                            # For WARNING level, suggest asking details and setup session
                            if result['risk_level'] == 'WARNING':
                                response_text += "\n💭 Not sure? Try /ask_details for interactive analysis!"
                                # Initialize question session for this message
                                user_question_sessions[user_id] = {
                                    "message": text,
                                    "answers": [],
                                    "question_index": 0
                                }
                            
                            # Log to database
                            if db:
                                try:
                                    user_data = db.get_user(chat_id)
                                    if not user_data:
                                        db.add_user(chat_id, from_user)
                                        user_data = db.get_user(chat_id)
                                    
                                    if user_data:
                                        should_alert = result['final_score'] > 70
                                        db.log_detection(
                                            user_data['user_id'],
                                            text,
                                            result['rule_score'],
                                            result['ai_score'],
                                            result['final_score'],
                                            result['risk_level'],
                                            should_alert
                                        )
                                        
                                        # **SEND ALERTS TO FAMILY IF HIGH-RISK**
                                        if should_alert:
                                            try:
                                                family_members = db.get_family_members(user_data['user_id'])
                                                if family_members:
                                                    for member in family_members:
                                                        alert_message = f"""
🚨 SCAM ALERT FOR {from_user}!

⚠️ Your family member received a suspicious message:

📱 Message: "{text[:150]}..."

🎯 Risk Score: {result['final_score']}/100
📊 Status: {result['risk_level']}

🔴 Red Flags Detected:
"""
                                                        if result['rule_indicators']:
                                                            for indicator in result['rule_indicators'][:3]:
                                                                alert_message += f"  • {indicator}\n"
                                                        
                                                        alert_message += f"""
💡 Recommendation:
{result['recommendation']}

🛡️ Please verify with {from_user} about this message!
                                                        """
                                                        
                                                        # Check if family member is active (started bot)
                                                        if db.is_user_active(member['family_chat_id']):
                                                            # Send to family member
                                                            try:
                                                                send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                                                family_payload = {
                                                                    "chat_id": member['family_chat_id'],
                                                                    "text": alert_message.strip()
                                                                }
                                                                family_response = requests.post(send_url, json=family_payload)
                                                                logger.info(f"📤 Sending alert to {member['name']} (ID: {member['family_chat_id']}) - Status: {family_response.status_code}")
                                                                
                                                                if family_response.status_code == 200:
                                                                    logger.info(f"✅ Alert sent to family member {member['name']}")
                                                                else:
                                                                    logger.warning(f"⚠️ Failed to send alert to {member['name']}: {family_response.text}")
                                                            except Exception as family_send_err:
                                                                logger.error(f"❌ Error sending family alert: {family_send_err}")
                                                        else:
                                                            logger.warning(f"⚠️ {member['name']} ({member['family_chat_id']}) hasn't started bot - cannot send alert!")
                                            except Exception as family_err:
                                                logger.error(f"Error getting family members: {family_err}")
                                except Exception as log_err:
                                    logger.error(f"Error logging: {log_err}")
                        
                        except Exception as analysis_err:
                            logger.error(f"Analysis error: {analysis_err}")
                            response_text = f"❌ Analysis failed: {str(analysis_err)}"
                    else:
                        response_text = "❌ Scam detection engine not available"
            
            # Send response
            if response_text:
                send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": response_text.strip()
                }
                
                response = requests.post(send_url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Message sent to chat {chat_id}")
                else:
                    logger.error(f"❌ Failed to send message: {response.text}")
        
        return JSONResponse({"ok": True})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Scam Detector Bot FastAPI Server")
    logger.info(f"📡 Listening on http://0.0.0.0:{WEBHOOK_PORT}")
    logger.info(f"🔗 Webhook path: {WEBHOOK_PATH}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="info"
    )
