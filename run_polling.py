"""
Quick Start Scripts for Different Deployment Methods
"""

# run_polling.py - Local testing with polling
if __name__ == "__main__":
    import os
    import logging
    from dotenv import load_dotenv
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    from detector.risk_engine import RiskEngine
    from database import db
    from telegram import Update
    from telegram.ext import ContextTypes
    
    load_dotenv()
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        exit(1)
    
    risk_engine = RiskEngine()
    
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name
        db.add_user(chat_id, user_name)
        
        msg = f"""
👋 Welcome {user_name}!

Send me suspicious messages to analyze them for scams.

/help - Show all commands
/stats - Your statistics
        """
        await update.message.reply_text(msg)
    
    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = """
📖 Commands:
/start - Start bot
/help - This message
/stats - Your stats
/add_family <id> <name> - Add family
/list_family - Show family

Just send any text to analyze!
        """
        await update.message.reply_text(msg)
    
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = db.get_user(chat_id)
        
        if not user:
            db.add_user(chat_id)
            user = db.get_user(chat_id)
        
        text = update.message.text
        
        processing = await update.message.reply_text("🔍 Analyzing...")
        
        try:
            result = risk_engine.calculate_final_risk(text)
            
            db.log_detection(
                user['user_id'],
                text,
                result['rule_score'],
                result['ai_score'],
                result['final_score'],
                result['risk_level'],
                result['final_score'] > 70
            )
            
            emoji = "✅" if result['risk_level'] == "SAFE" else "⚠️" if result['risk_level'] == "WARNING" else "🚨"
            
            report = f"{emoji} Risk Score: {result['final_score']}/100\n"
            report += f"Status: {result['risk_level']}\n\n"
            
            if result['rule_indicators']:
                report += "Detected:\n"
                for ind in result['rule_indicators'][:3]:
                    report += f"• {ind}\n"
            
            if result['ai_analysis']:
                report += f"\nAI Type: {result['ai_analysis']['scam_type']}\n"
                report += f"Reason: {result['ai_analysis']['reason']}\n"
            
            report += f"\n{result['recommendation']}"
            
            await processing.delete()
            await update.message.reply_text(report)
            
        except Exception as e:
            await processing.delete()
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user = db.get_user(chat_id)
        
        if not user:
            await update.message.reply_text("Not registered. Use /start")
            return
        
        stats_data = db.get_user_stats(user['user_id'])
        msg = f"""
📊 Your Stats
Analyzed: {stats_data['total_detections']}
Alerts: {stats_data['alerts']}
Avg Score: {stats_data['avg_score']}/100
        """
        await update.message.reply_text(msg)
    
    # Build app
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bot starting (polling mode)...")
    print("Send /start to the bot to begin testing")
    print("Press Ctrl+C to stop\n")
    
    app.run_polling()
