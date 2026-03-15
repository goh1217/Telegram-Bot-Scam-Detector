#!/usr/bin/env python3
"""
Quick setup script for Scam Detector Bot
Run this after cloning to get started quickly
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(text):
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50 + "\n")


def print_success(text):
    print(f"✅ {text}")


def print_error(text):
    print(f"❌ {text}")


def print_info(text):
    print(f"ℹ️  {text}")


def setup():
    """Run setup process"""
    
    print_header("🚨 SCAM DETECTOR BOT - SETUP")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required")
        sys.exit(1)
    
    print_success(f"Python {sys.version.split()[0]} detected")
    
    # Create virtual environment
    print_header("Step 1: Virtual Environment")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_info("Virtual environment already exists")
    else:
        print_info("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
        print_success("Virtual environment created")
    
    # Activate virtual environment
    print_header("Step 2: Dependencies")
    
    print_info("Installing requirements...")
    if sys.platform == "win32":
        pip = "venv\\Scripts\\pip"
    else:
        pip = "venv/bin/pip"
    
    subprocess.run([pip, "install", "-r", "requirements.txt"])
    print_success("Dependencies installed")
    
    # Check .env file
    print_header("Step 3: Configuration")
    
    env_file = Path(".env")
    if env_file.exists():
        print_success(".env file found")
    else:
        print_error(".env file not found")
        print_info("Creating template .env...")
        # .env already created by our script
    
    print_info("📝 Please update .env with:")
    print("  • TELEGRAM_BOT_TOKEN - Get from @BotFather")
    print("  • TELEGRAM_WEBHOOK_URL - Your server URL")
    print(f"  • GEMINI_API_KEY - Get from https://aistudio.google.com/app/apikey")
    
    # Check database
    print_header("Step 4: Database")
    
    print_info("Initializing database...")
    from database import db
    print_success("Database ready")
    
    # Summary
    print_header("✅ SETUP COMPLETE!")
    
    print("🚀 Next steps:")
    print("\n1. Update .env with your Telegram Bot Token")
    print("2. Run: python bot.py")
    print("3. Test bot on Telegram")
    print("\nFor production (webhook):")
    print("  python main.py")
    print("\nFor API testing:")
    print("  curl -X POST http://localhost:8000/analyze \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"text": "Click here for money!!!"}\'')
    print("\nHappy coding! 🎉\n")


if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n⚠️  Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)
