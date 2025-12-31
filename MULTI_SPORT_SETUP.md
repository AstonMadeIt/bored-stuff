# Multi-Sport Prediction System

## Overview

The system now supports **both NFL and NBA** predictions!

## Installation

### 1. Install NBA API Package
```bash
pip install nba_api
```

### 2. Update Database Schema
The database automatically updates to support multiple sports when you run:
```bash
python3 database.py
```

## Usage

### Generate NFL Predictions
```bash
# Via API
curl -X POST http://localhost:5001/api/predictions/generate \
  -H "Content-Type: application/json" \
  -d '{"sport": "NFL"}'

# Or via script
python3 predict_today.py
```

### Generate NBA Predictions
```bash
# Via API
curl -X POST http://localhost:5001/api/predictions/generate \
  -H "Content-Type: application/json" \
  -d '{"sport": "NBA"}'

# Or via script
python3 nba_predictions.py
```

### Get Predictions by Sport
```bash
# NFL only
curl http://localhost:5001/api/predictions/upcoming?sport=NFL

# NBA only
curl http://localhost:5001/api/predictions/upcoming?sport=NBA

# All sports
curl http://localhost:5001/api/predictions/upcoming
```

## Database Schema

Both `predictions` and `results` tables now have a `sport` column:
- `sport`: 'NFL' or 'NBA' (defaults to 'NFL' for backward compatibility)

## API Endpoints

All endpoints now support optional `sport` parameter:

- `GET /api/predictions/upcoming?sport=NFL` - NFL predictions
- `GET /api/predictions/upcoming?sport=NBA` - NBA predictions
- `GET /api/predictions/high-confidence?sport=NBA` - High-confidence NBA
- `GET /api/results/completed?sport=NFL` - NFL results
- `POST /api/predictions/generate` with `{"sport": "NBA"}` - Generate NBA predictions

## Dashboard Updates

The dashboard automatically shows:
- **NFL predictions** (if available)
- **NBA predictions** (if available)
- **Filtered by sport** (coming soon)

## NBA Features

Currently implemented:
- ✅ Data collection via `nba_api`
- ✅ Basic feature engineering
- ✅ Prediction generation
- ✅ Database storage

Coming soon:
- ⏳ Full feature engineering (similar to NFL)
- ⏳ NBA-specific model training
- ⏳ Vegas odds integration for NBA
- ⏳ NBA-specific confidence tiers

## Example Workflow

```bash
# 1. Start API server
./start_api.sh

# 2. Generate NFL predictions
curl -X POST http://localhost:5001/api/predictions/generate \
  -H "Content-Type: application/json" \
  -d '{"sport": "NFL"}'

# 3. Generate NBA predictions
curl -X POST http://localhost:5001/api/predictions/generate \
  -H "Content-Type: application/json" \
  -d '{"sport": "NBA"}'

# 4. View all predictions
curl http://localhost:5001/api/predictions/upcoming

# 5. View dashboard
open http://localhost:5001
```

## Next Steps

1. **Train NBA-specific model** (currently uses NFL model)
2. **Add NBA Vegas odds** (TheOddsAPI supports NBA)
3. **Enhance NBA features** (similar to NFL feature engineering)
4. **Update dashboard** to filter by sport

---

**Your system now supports multiple sports!** 🏈🏀


