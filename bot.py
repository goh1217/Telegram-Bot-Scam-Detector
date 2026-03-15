"""
Telegram Bot Logic
Handles user interactions and bot commands
"""

import logging
from typing import Dict, Optional
from telegram import Update, Chat
from telegram.ext import Application, ContextTypes
from detector.risk_engine import RiskEngine
from database import db


logger = logging.getLogger(__name__)


class ScamDetectorBot:
    """Telegram bot for scam detection"""
    
    def __init__(self, token: str):
        self.token = token
        self.risk_engine = RiskEngine()
        self.app = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup command and message handlers"""
        from telegram.ext import CommandHandler, MessageHandler, filters
        
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("add_family", self.add_family_command))
        self.app.add_handler(CommandHandler("list_family", self.list_family_command))
        
        # Messages
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.analyze_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name
        
        # Add user to database
        db.add_user(chat_id, user_name)
        
        welcome_msg = f"""
👋 Welcome {user_name}!

I'm your Scam Detection Bot. Send me any suspicious message, and I'll analyze it for scam indicators.

🎯 Features:
• 🔍 Rule-based scam detection
• 🤖 AI-powered analysis
• 👨‍👩‍👧 Family notifications
• 📊 Statistics tracking

📝 Commands:
/help - Show all commands
/stats - View your detection statistics
/add_family - Add family member for alerts
/list_family - List family members

Just send me any text you want to check! 🚀
        """
        
        await update.message.reply_text(welcome_msg)
        logger.info(f"New user started: {chat_id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = """
📖 HELP & COMMANDS

🔍 ANALYZE MESSAGE:
Just send any text and I'll check it for scam indicators.

📋 COMMANDS:
/start - Start the bot
/help - Show this message
/stats - View your stats
/add_family <chat_id> <name> <relationship>
  Example: /add_family 123456789 Mom Mother
/list_family - Show your family list

🎯 RISK LEVELS:
✅ SAFE (0-40): Appears legitimate
⚠️ WARNING (41-70): Use caution, verify first
🚨 ALERT (71-100): High risk, don't interact

📊 How It Works:
1. Rule-based detection (keyword patterns, links, etc.)
2. AI analysis using Google Gemini
3. Combined final score
4. Family notifications on high-risk messages

Need help? Contact support or reply to this bot.
        """
        
        await update.message.reply_text(help_msg)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        chat_id = update.effective_chat.id
        user = db.get_user(chat_id)
        
        if not user:
            await update.message.reply_text("❌ User not found. Use /start first.")
            return
        
        stats = db.get_user_stats(user['user_id'])
        
        stats_msg = f"""
📊 YOUR STATISTICS

Total Messages Analyzed: {stats['total_detections']}
🚨 High-Risk Alerts: {stats['alerts']}
⚠️ Warnings: {stats['warnings']}
👨‍👩‍👧 Family Alerts Sent: {stats['family_alerts']}

Average Risk Score: {stats['avg_score']}/100
        """
        
        await update.message.reply_text(stats_msg)
        logger.info(f"Stats requested by {chat_id}")
    
    async def add_family_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_family command"""
        chat_id = update.effective_chat.id
        user = db.get_user(chat_id)
        
        if not user:
            await update.message.reply_text("❌ User not found. Use /start first.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "📝 Usage: /add_family <family_chat_id> <name> [relationship]\n"
                "Example: /add_family 123456789 Mom Mother"
            )
            return
        
        try:
            family_chat_id = int(context.args[0])
            name = context.args[1]
            relationship = context.args[2] if len(context.args) > 2 else "Family"
            
            if db.add_family_member(user['user_id'], family_chat_id, name, relationship):
                await update.message.reply_text(
                    f"✅ Added {name} ({relationship}) for notifications!"
                )
                logger.info(f"Family member added for user {chat_id}")
            else:
                await update.message.reply_text("❌ Error adding family member")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid chat ID. Must be a number.")
        except Exception as e:
            logger.error(f"Error adding family: {e}")
            await update.message.reply_text("❌ Error occurred")
    
    async def list_family_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list_family command"""
        chat_id = update.effective_chat.id
        user = db.get_user(chat_id)
        
        if not user:
            await update.message.reply_text("❌ User not found. Use /start first.")
            return
        
        family = db.get_family_members(user['user_id'])
        
        if not family:
            await update.message.reply_text(
                "👨‍👩‍👧 No family members added yet.\n\n"
                "Add family: /add_family <chat_id> <name> [relationship]"
            )
            return
        
        family_list = "👨‍👩‍👧 YOUR FAMILY MEMBERS:\n\n"
        for member in family:
            family_list += f"• {member['name']} ({member.get('relationship', 'Family')})\n"
            family_list += f"  ID: {member['family_chat_id']}\n\n"
        
        await update.message.reply_text(family_list)
    
    async def analyze_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Analyze incoming message for scams"""
        chat_id = update.effective_chat.id
        user = db.get_user(chat_id)
        
        if not user:
            db.add_user(chat_id)
            user = db.get_user(chat_id)
        
        message_text = update.message.text
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔍 Analyzing message...")
        
        try:
            # Get comprehensive risk assessment
            result = self.risk_engine.calculate_final_risk(message_text)
            
            # Log detection
            db.log_detection(
                user['user_id'],
                message_text,
                result['rule_score'],
                result['ai_score'],
                result['final_score'],
                result['risk_level'],
                result['final_score'] > 70
            )
            
            # Generate report
            report = self._format_report(result)
            
            # Delete processing message and send report
            await processing_msg.delete()
            await update.message.reply_text(report, parse_mode="MarkdownV2")
            
            # Alert family if high risk
            if result['final_score'] > 70:
                await self._alert_family(user['user_id'], message_text, result)
            
            logger.info(f"Message analyzed for {chat_id}: score={result['final_score']}")
            
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            await processing_msg.delete()
            await update.message.reply_text(
                "❌ Error analyzing message. Please try again."
            )
    
    def _format_report(self, result: Dict) -> str:
        """Format analysis report for Telegram"""
        emoji_map = {
            "SAFE": "✅",
            "WARNING": "⚠️",
            "ALERT": "🚨"
        }
        
        report = f"{emoji_map[result['risk_level']]} *SCAM DETECTION REPORT*\n"
        report += f"═══════════════════════════\n\n"
        
        # Final Score
        report += f"🎯 *Risk Score:* `{result['final_score']}/100`\n"
        report += f"📊 *Status:* *{result['risk_level']}*\n\n"
        
        # Breakdown
        report += f"📈 *Score Breakdown:*\n"
        report += f"  • Rules: `{result['rule_score']}/100`\n"
        report += f"  • AI: `{result['ai_score']}/100`\n\n"
        
        # Indicators
        if result['rule_indicators']:
            report += f"🔴 *Red Flags:*\n"
            for indicator in result['rule_indicators']:
                report += f"  • {indicator}\n"
            report += "\n"
        
        # AI Analysis
        if result['ai_analysis']:
            report += f"🤖 *AI Analysis:*\n"
            ai = result['ai_analysis']
            report += f"  • Type: `{ai.get('scam_type', 'Unknown')}`\n"
            report += f"  • Reason: _{ai.get('reason', 'N/A')}_\n\n"
        
        # Recommendation
        report += f"💡 *Action:*\n"
        report += f"_{result['recommendation']}_"
        
        return report
    
    async def _alert_family(self, user_id: int, message: str, result: Dict):
        """Send alert to family members"""
        from telegram import Bot
        
        family = db.get_family_members(user_id)
        if not family:
            return
        
        bot = Bot(token=self.token)
        
        alert_msg = f"""
🚨 *SCAM ALERT!*

Risk Score: *{result['final_score']}/100* 
Status: *{result['risk_level']}*

Type: `{result['ai_analysis'].get('scam_type', 'Unknown').upper()}`

⚠️ DANGEROUS MESSAGE DETECTED

Please ensure the user doesn't:
✗ Click any links
✗ Share personal info
✗ Follow instructions
✗ Send money

Contact the user immediately!

Message preview:
`{message[:150]}{'...' if len(message) > 150 else ''}`
        """
        
        for member in family:
            try:
                await bot.send_message(
                    chat_id=member['family_chat_id'],
                    text=alert_msg,
                    parse_mode="MarkdownV2"
                )
                logger.info(f"Family alert sent to {member['family_chat_id']}")
            except Exception as e:
                logger.error(f"Error sending family alert: {e}")
    
    def run(self):
        """Start the bot"""
        logger.info("🤖 Scam Detector Bot starting...")
        self.app.run_polling()
