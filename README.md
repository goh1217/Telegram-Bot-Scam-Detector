# 🚨 Scam Detector Bot

A professional multi-layer scam detection system for Telegram that combines rule-based detection with AI classification.

## 🎯 Features

### 1. **Multi-Layer Detection**
- 🔴 **Rule-Based Detection** (40% weight)
  - Urgent keywords detection
  - Money transfer patterns
  - OTP/Password requests
  - Account security warnings
  - Authority impersonation
  - Suspicious links
  - Shortened URLs

- 🤖 **AI-Powered Analysis** (60% weight)
  - Google Gemini 2.5 Flash API
  - Scam type classification
  - Explainable predictions
  - Contextual understanding

### 2. **Risk Scoring System**
- **0-40**: ✅ SAFE - Appears legitimate
- **41-70**: ⚠️ WARNING - Use caution, verify first
- **71-100**: 🚨 ALERT - High risk, don't interact

### 3. **Family Notification System**
- Add multiple family members as alerts
- Automatic notifications for high-risk messages
- Detailed alert messages with threat analysis

### 4. **Statistics & Logging**
- Track detection history
- User statistics
- Risk trends analysis

### 5. **Bot Commands**
```
/start - Initialize bot
/help - Show all commands
/stats - View your statistics
/add_family <chat_id> <name> [relation] - Add family member
/list_family - List all family members
```

## 📁 Project Structure

```
scam-detector/
├── main.py                    # FastAPI server + webhook
├── bot.py                     # Telegram bot logic
├── database.py                # SQLite database management
│
├── detector/
│   ├── __init__.py
│   ├── rules.py              # Rule-based detection
│   ├── ai_model.py           # AI classification with Gemini
│   └── risk_engine.py        # Risk score combination
│
├── .env                       # Configuration file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. **Setup Environment**

```bash
# Clone or navigate to project
cd scam-detector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configure Environment**

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./scam_detector.db
WEBHOOK_PORT=8000
```

**Get these:**
- **Telegram Bot Token**: From [@BotFather](https://t.me/botfather) on Telegram
- **Webhook URL**: Your server domain (for production)
- **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 3. **Run the Bot**

**Option A: Local Testing (Polling)**
```bash
python bot.py
```

**Option B: Production (Webhook)**
```bash
python main.py
```

Server runs on `http://localhost:8000`

## 🔌 API Endpoints

### Health Check
```bash
GET /health
```

### Analyze Text (Direct API)
```bash
POST /analyze
Content-Type: application/json

{
  "text": "Click here to verify your bank account immediately!!!"
}
```

**Response:**
```json
{
  "success": true,
  "final_score": 85,
  "rule_score": 75,
  "ai_score": 92,
  "risk_level": "ALERT",
  "indicators": [
    "Urgent language (2 keywords)",
    "Contains suspicious links (1 link(s))",
    "Asks to click suspicious links"
  ],
  "ai_analysis": {
    "scam_type": "phishing",
    "reason": "Requests account verification with urgent language",
    "score": 92,
    "confidence": "high"
  },
  "recommendation": "DANGER! Do not click links or share personal information."
}
```

## 💡 How It Works

### Flow Diagram

```
Message Received
       ↓
Rule-Based Detection (40%)
  • Check keywords
  • Detect links
  • Pattern matching
       ↓
AI Classification (60%)
  • Send to Gemini
  • Get risk score
  • Classify type
       ↓
Risk Engine Combination
  Score = (Rule × 0.4) + (AI × 0.6)
       ↓
Decision
  • 0-40: ✅ SAFE
  • 41-70: ⚠️ WARNING  
  • 71-100: 🚨 ALERT
       ↓
  ├─→ High Risk (>70)?
  │   ├─→ Alert user
  │   └─→ Notify family
  │
  └─→ Reply with report
```

## 🎓 Example Analysis

### Input:
```
Subject: URGENT! Your bank account is LOCKED!

Click here immediately to verify: http://shortened.link/bank123
Enter your OTP code when prompted.

Reply NOW!
```

### Output:
```
🚨 SCAM DETECTION REPORT
════════════════════════════════

🎯 Final Risk Score: 88/100
📊 Status: ALERT

📈 Score Breakdown:
  • Rule-Based: 85/100
  • AI Analysis: 91/100

🔴 Detected Red Flags:
  • Urgent language (2 keywords)
  • Money-related words (1 keywords)
  • Account issues mentioned (1 keywords)
  • Contains suspicious links (1 link(s))
  • Asks to click suspicious links

🤖 AI Analysis:
  • Type: PHISHING
  • Reason: Requests account verification with urgency and suspicious link
  • Confidence: HIGH

💡 Recommendation:
DANGER! Do not click links or share personal information. Alert family immediately.
```

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,
  chat_id INTEGER UNIQUE,
  name TEXT,
  created_at TIMESTAMP,
  enabled INTEGER
);
```

### Family Members Table
```sql
CREATE TABLE family_members (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  family_chat_id INTEGER,
  relationship TEXT,
  name TEXT,
  created_at TIMESTAMP
);
```

### Detection Logs Table
```sql
CREATE TABLE detection_logs (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  message_text TEXT,
  rule_score INTEGER,
  ai_score INTEGER,
  final_score INTEGER,
  risk_level TEXT,
  alerted_family BOOLEAN,
  created_at TIMESTAMP
);
```

## 🔧 Configuration

### Adjust Risk Weights

In `detector/risk_engine.py`:
```python
# Default: Rule (40%) + AI (60%)
final_score = int((rule_score * 0.4) + (ai_score * 0.6))

# Change to your preference:
# More rules-based:
final_score = int((rule_score * 0.6) + (ai_score * 0.4))

# More AI-based:
final_score = int((rule_score * 0.2) + (ai_score * 0.8))
```

### Adjust Alert Threshold

In `main.py` or `bot.py`:
```python
# Default: Alert family if score > 70
if result['final_score'] > 70:
    await self._alert_family(...)

# Change to:
if result['final_score'] > 80:  # More strict
if result['final_score'] > 60:  # More sensitive
```

## 🚀 Deployment Options

### Option 1: Heroku
```bash
heroku create scam-detector-bot
git push heroku main
```

### Option 2: AWS Lambda + API Gateway
- Package as serverless function
- Deploy to API Gateway
- Set webhook URL in Telegram

### Option 3: Docker
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Option 4: DigitalOcean App Platform
- Create app from GitHub
- Set environment variables
- Deploy and connect to Telegram webhook

## 📝 Usage Examples

### For Telegram Users:
```
User: "Click here to verify your account: bit.ly/verify123 URGENT!!!"
Bot: 🚨 SCAM DETECTION REPORT
     Risk Score: 82/100 - ALERT
     ...
```

### For Developers (Direct API):
```python
from detector.risk_engine import RiskEngine

engine = RiskEngine()
result = engine.calculate_final_risk("Send me your OTP code now!")

print(f"Score: {result['final_score']}")
print(f"Level: {result['risk_level']}")
print(f"Recommendation: {result['recommendation']}")
```

## 🎯 Hackathon Tips

### **Impressive Features**
✅ Hybrid detection (rules + AI)
✅ Family notification system
✅ Explainable AI decisions
✅ Real-time analysis
✅ Database persistence
✅ Professional UI/UX

### **Demo Flow**
1. Show rule-based detection (fast)
2. Show AI analysis (accurate)
3. Show combined score (hybrid advantage)
4. Demo family alerts
5. Show statistics dashboard

### **What Judges Look For**
- ✅ Problem-solution fit
- ✅ Technical depth
- ✅ User experience
- ✅ Innovation (hybrid approach)
- ✅ Real-world applicability
- ✅ Clean, maintainable code

## 🐛 Troubleshooting

### Bot Not Responding
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify bot's `/start` command works
- Check logs: `tail -f bot.log`

### AI Analysis Fails
- Verify `GEMINI_API_KEY` is correct
- Check internet connection
- Review Gemini API quota limits

### Webhook Not Receiving Updates
- Ensure public URL is set correctly
- Check firewall rules
- Verify port 8000 is accessible
- Test at `/health` endpoint

### Database Errors
- Delete `scam_detector.db` to reset
- Check file permissions
- Ensure `/tmp` directory exists (on Linux)

## 📚 Resources

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Google Gemini API Docs](https://ai.google.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📄 License

MIT License - Feel free to use for hackathons and projects

## 👨‍💻 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 🏆 Hackathon Checklist

- [x] Project structure set up
- [x] Rule-based detection implemented
- [x] AI classification added
- [x] Risk engine built
- [x] Telegram bot created
- [x] FastAPI server ready
- [x] Database integration done
- [x] Family notification system
- [x] Statistics tracking
- [x] Documentation complete

**Ready to present! 🚀**

---

Made with ❤️ for the ASEAN Youth Hackathon
