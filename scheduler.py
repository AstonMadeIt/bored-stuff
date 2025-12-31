#!/usr/bin/env python3
"""
Automated Scheduler for NFL Predictions
Runs predictions and updates automatically
"""

import schedule
import time
import requests
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

API_BASE = 'http://localhost:5000'

def generate_predictions():
    """Generate predictions for today"""
    try:
        logging.info("🔄 Generating predictions...")
        response = requests.post(f'{API_BASE}/api/predictions/generate')
        if response.json()['success']:
            logging.info(f"✅ {response.json()['message']}")
        else:
            logging.error(f"❌ Error: {response.json().get('error')}")
    except Exception as e:
        logging.error(f"❌ Failed to generate predictions: {e}")

def update_results():
    """Update game results"""
    try:
        logging.info("🔄 Updating game results...")
        response = requests.post(f'{API_BASE}/api/results/update')
        if response.json()['success']:
            logging.info(f"✅ {response.json()['message']}")
        else:
            logging.error(f"❌ Error: {response.json().get('error')}")
    except Exception as e:
        logging.error(f"❌ Failed to update results: {e}")

def health_check():
    """Check API health"""
    try:
        response = requests.get(f'{API_BASE}/health')
        if response.status_code == 200:
            logging.info("✅ API is healthy")
        else:
            logging.warning("⚠️  API health check failed")
    except Exception as e:
        logging.error(f"❌ API health check failed: {e}")

# Schedule jobs
# Generate predictions every morning at 8 AM
schedule.every().day.at("08:00").do(generate_predictions)

# Update results every hour during game days (Thu-Sun)
schedule.every().thursday.at("13:00").do(update_results)
schedule.every().friday.at("13:00").do(update_results)
schedule.every().saturday.at("13:00").do(update_results)
schedule.every().sunday.at("13:00").do(update_results)
schedule.every().sunday.at("17:00").do(update_results)
schedule.every().sunday.at("21:00").do(update_results)
schedule.every().monday.at("09:00").do(update_results)  # Final Monday update

# Health check every 30 minutes
schedule.every(30).minutes.do(health_check)

if __name__ == '__main__':
    logging.info("="*80)
    logging.info("⏰ NFL Prediction Scheduler Started")
    logging.info("="*80)
    logging.info("\n📅 Scheduled Jobs:")
    logging.info("  - Generate predictions: Daily at 8:00 AM")
    logging.info("  - Update results: Thu-Sun at 1:00 PM, Sun at 5:00 PM & 9:00 PM, Mon at 9:00 AM")
    logging.info("  - Health check: Every 30 minutes")
    logging.info("\n⏳ Running scheduler...")
    logging.info("="*80)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


