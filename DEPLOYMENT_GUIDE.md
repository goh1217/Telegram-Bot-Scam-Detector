# 🚀 DEPLOYMENT GUIDE - Scam Detector Bot

## Local Testing (Fast Start)

### Step 1: Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "ScamDetector")
4. Choose a username (e.g., "scam_detector_bot")
5. Copy the token provided

### Step 2: Update .env

```env
TELEGRAM_BOT_TOKEN=your_token_here_from_botfather
```

### Step 3: Run Bot

```bash
python run_polling.py
```

Your bot is now live on Telegram! 🎉

---

## Production Deployment (Webhook)

### Option 1: Heroku (Recommended for Hackathon)

```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-scam-detector

# Add environment variables
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set TELEGRAM_WEBHOOK_URL=https://your-scam-detector.herokuapp.com

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### Option 2: DigitalOcean App Platform

1. Connect your GitHub repo
2. Create new App
3. Set environment variables
4. Deploy

Webhook URL: `https://your-app.ondigitalocean.app/telegram-webhook`

### Option 3: AWS Lambda + API Gateway

1. Package as ZIP
2. Create Lambda function
3. Add API Gateway trigger
4. Get webhook URL
5. Update .env

### Option 4: Docker Container

**Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

**Build & Run:**

```bash
docker build -t scam-detector .
docker run -e TELEGRAM_BOT_TOKEN=your_token -p 8000:8000 scam-detector
```

---

## Testing Your Bot

### 1. Test Locally First

```bash
python run_polling.py
```

Send test message to your bot on Telegram.

### 2. Test API Directly

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "URGENT! Click here to verify account immediately!!!"}'
```

### 3. Health Check

```bash
curl http://localhost:8000/health
```

---

## Production Checklist

- [ ] Bot token obtained from @BotFather
- [ ] .env file configured with all variables
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized
- [ ] Local testing passed (`python run_polling.py`)
- [ ] API tested (`curl /analyze`)
- [ ] Deployed to production
- [ ] Webhook URL set correctly
- [ ] Bot responds in Telegram
- [ ] Family notification system tested
- [ ] Statistics tracking verified
- [ ] Database backups configured

---

## Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ | `123456:ABC-DEF...` |
| `TELEGRAM_WEBHOOK_URL` | ⚠️ | `https://your-domain.com` |
| `GEMINI_API_KEY` | ✅ | Get from https://aistudio.google.com/app/apikey |
| `WEBHOOK_PORT` | ❌ | `8000` (default) |
| `DATABASE_URL` | ❌ | `sqlite:///./scam_detector.db` |

---

## Monitoring & Logs

### Local Testing
```bash
python run_polling.py
# Logs appear in console
```

### Production (Heroku)
```bash
heroku logs --tail
```

### Production (Docker)
```bash
docker logs container_id -f
```

---

## Scaling Considerations

### Database
- Start with SQLite (file-based)
- Scale to PostgreSQL for production
- Add connection pooling

### API Load
- Use Gunicorn/Uvicorn with workers
- Add load balancer (nginx)
- Enable caching

### AI Model
- Batch requests if possible
- Add request queuing
- Monitor Gemini API quota

---

## Troubleshooting

### Bot Not Responding

```bash
# Check token
echo $TELEGRAM_BOT_TOKEN

# Test bot manually
curl -F "url=https://your-domain/telegram-webhook" \
  https://api.telegram.org/bot$TOKEN/setWebhook
```

### Webhook Issues

```bash
# Get webhook info
curl https://api.telegram.org/bot$TOKEN/getWebhookInfo
```

### Database Locked
```bash
# Reset database
rm scam_detector.db
# Will recreate on next run
```

---

## Next Steps for Hackathon

1. **Local Demo**: Show judges working bot on laptop
2. **Live Demo**: Deploy to Heroku/DigitalOcean
3. **Present Features**:
   - Send test message → shows analysis
   - Demonstrate family alerts
   - Show statistics
4. **Q&A Prepared**:
   - How detection works
   - Why hybrid approach
   - Scalability plan
   - Future improvements

---

## Support

- Check logs first
- Review .env configuration
- Verify Telegram bot token
- Test API endpoints
- Review README.md

Good luck! 🎉
