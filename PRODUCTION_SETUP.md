# Production Setup Guide

## Overview

This is a **production-ready** NFL prediction system with:
- ✅ Database persistence (SQLite)
- ✅ REST API (Flask)
- ✅ Automated scheduling
- ✅ Real-time dashboard
- ✅ Monitoring & logging

## Architecture

```
┌─────────────────┐
│  Scheduler      │  ← Automated jobs (cron-like)
└────────┬────────┘
         │
┌────────▼────────┐
│  API Server     │  ← REST API (Flask)
└────────┬────────┘
         │
┌────────▼────────┐
│  Database       │  ← SQLite (can upgrade to PostgreSQL)
└─────────────────┘
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python3 database.py
```

### 3. Start API Server
```bash
python3 api_server.py
```

Server runs on: `http://localhost:5000`

### 4. Start Scheduler (Optional)
```bash
python3 scheduler.py
```

## API Endpoints

### Get Upcoming Predictions
```bash
curl http://localhost:5000/api/predictions/upcoming
```

### Get High-Confidence Predictions
```bash
curl http://localhost:5000/api/predictions/high-confidence
```

### Get Completed Games
```bash
curl http://localhost:5000/api/results/completed
```

### Get Metrics
```bash
curl http://localhost:5000/api/metrics
```

### Generate Predictions (Manual)
```bash
curl -X POST http://localhost:5000/api/predictions/generate
```

### Update Results (Manual)
```bash
curl -X POST http://localhost:5000/api/results/update
```

## Automated Workflow

The scheduler automatically:
1. **8:00 AM Daily**: Generate predictions for today's games
2. **Thu-Sun 1:00 PM**: Update game results
3. **Sunday 5:00 PM & 9:00 PM**: Update results (games finishing)
4. **Monday 9:00 AM**: Final update for Sunday games
5. **Every 30 min**: Health check

## Production Deployment

### Option 1: Systemd Service (Linux/Mac)

Create `/etc/systemd/system/nfl-predictions.service`:

```ini
[Unit]
Description=NFL Prediction API Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/nfl-predictions
ExecStart=/usr/bin/python3 /path/to/nfl-predictions/api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl start nfl-predictions
sudo systemctl enable nfl-predictions
```

### Option 2: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python3", "api_server.py"]
```

Build & run:
```bash
docker build -t nfl-predictions .
docker run -p 5000:5000 nfl-predictions
```

### Option 3: Cloud (AWS/GCP/Azure)

1. **API Server**: Deploy to EC2/Cloud Run/App Service
2. **Scheduler**: Use CloudWatch Events / Cloud Scheduler
3. **Database**: Upgrade to RDS/Cloud SQL

## Monitoring

### Logs
- API logs: Console output
- Scheduler logs: `scheduler.log`

### Health Check
```bash
curl http://localhost:5000/health
```

### Metrics Dashboard
Access dashboard at: `http://localhost:5000/`

## Database Schema

### predictions
- Stores all predictions
- Indexed by date and teams
- Unique constraint on (date, away_team, home_team)

### results
- Stores actual game outcomes
- Linked to predictions via date + teams

### metrics
- Daily performance metrics
- Calculated automatically

## Upgrading to PostgreSQL

1. Install psycopg2:
```bash
pip install psycopg2-binary
```

2. Update `database.py`:
```python
import psycopg2
# Change connection string
conn = psycopg2.connect("dbname=nfl user=postgres")
```

## Frontend Integration

The API serves JSON, perfect for:
- React/Vue/Angular dashboards
- Mobile apps
- Slack/Discord bots
- Email reports

Example React fetch:
```javascript
fetch('http://localhost:5000/api/predictions/high-confidence')
  .then(res => res.json())
  .then(data => console.log(data.data));
```

## Troubleshooting

**API won't start:**
- Check port 5000 is available
- Verify Flask is installed
- Check logs for errors

**Scheduler not running:**
- Verify schedule library installed
- Check scheduler.log
- Ensure API server is running

**No predictions:**
- Check model files exist (`models/catboost_model.pkl`)
- Verify ESPN API accessible
- Check database initialized

## Next Steps

1. **Add Authentication**: Protect API endpoints
2. **Rate Limiting**: Prevent abuse
3. **Caching**: Redis for frequently accessed data
4. **Alerts**: Email/Slack notifications for high-confidence games
5. **Analytics**: Track ROI, betting units, etc.


