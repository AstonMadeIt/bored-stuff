# 📊 Dashboard Update Guide

## 🔄 How Dashboard Updates Work

### **The Flow:**
```
1. generate_all_predictions.py
   ↓
   Creates: predictions/all_predictions.json
   (Uses NEW NBA features: rest/B2B, last 10 weighted, pace, etc.)
   
2. create_apple_dashboard.py
   ↓
   Reads: predictions/all_predictions.json
   Creates: predictions/dashboard.html
   (Shows predictions with AI insights, real standings, etc.)
```

---

## ✅ Quick Update (Recommended)

### **Two Commands:**
```bash
# Step 1: Generate predictions (with enhanced NBA features)
python3 generate_all_predictions.py

# Step 2: Update dashboard
python3 create_apple_dashboard.py
```

### **Or One Command:**
```bash
./update_dashboard.sh
```

---

## 🚀 What Gets Updated

### **When you run `generate_all_predictions.py`:**
- ✅ Fetches today's NFL games
- ✅ Fetches today's NBA games
- ✅ Uses **ENHANCED NBA features** (rest/B2B, last 10 weighted, pace)
- ✅ Generates predictions with confidence scores
- ✅ Saves to `predictions/all_predictions.json`

### **When you run `create_apple_dashboard.py`:**
- ✅ Reads `predictions/all_predictions.json`
- ✅ Fetches **real NBA/NFL standings** (from APIs)
- ✅ Generates AI insights (if API key set)
- ✅ Creates `predictions/dashboard.html`
- ✅ Shows team trends, confidence, Vegas divergence

---

## 📋 Current Status

### **Dashboard is NOT live/auto-updating**
- It's a static HTML file
- You need to regenerate it after new predictions

### **To see latest predictions:**
1. Run `generate_all_predictions.py` (gets new games)
2. Run `create_apple_dashboard.py` (updates HTML)
3. Open `predictions/dashboard.html` in browser

---

## 🔍 What Changed in NBA Model

### **Old Model:**
- Last 5 games (equal weight)
- No rest/B2B detection
- No pace adjustment
- Simple averages

### **New Model (Now Active):**
- ✅ Last 10 games (recent weighted 2x)
- ✅ Rest/B2B detection
- ✅ Pace adjustment
- ✅ Net rating (offensive - defensive)
- ✅ Streak momentum

**These features are NOW being used when you run `generate_all_predictions.py`**

---

## 🎯 Testing the New NBA Features

### **1. Generate Predictions:**
```bash
python3 generate_all_predictions.py
```

**Look for in output:**
- "🔧 Engineering ENHANCED NBA features"
- "🔥 NEW FEATURES: Rest/B2B, Last 10 weighted, Pace, Net Rating, Streaks"

### **2. Check Predictions JSON:**
```bash
cat predictions/all_predictions.json | grep -A 5 "rest_advantage"
```

**Should see:**
- `rest_advantage` values (positive = home team has rest edge)
- `home_is_b2b` / `away_is_b2b` flags
- `net_rating_advantage` values

### **3. Update Dashboard:**
```bash
python3 create_apple_dashboard.py
```

**Dashboard will show:**
- Predictions with new features
- Real standings (from APIs)
- AI insights (if API key set)
- Team trends

---

## 🔄 Auto-Update Options

### **Option 1: Cron Job (Every 5 minutes)**
```bash
# Add to crontab
*/5 * * * * cd /path/to/nfl-predictions && ./update_dashboard.sh >> logs/cron.log 2>&1
```

### **Option 2: Production Pipeline**
```bash
python3 production_pipeline.py
```
Does everything: training → predictions → dashboard → continuous learning

### **Option 3: Manual (Current)**
Just run the two commands when you want fresh predictions

---

## 📊 Dashboard Features

### **What You'll See:**
- ✅ NFL & NBA predictions
- ✅ Confidence scores (High/Medium/Low)
- ✅ Vegas line divergence
- ✅ Real team records (from APIs)
- ✅ Streaks & L10 records
- ✅ AI-generated explanations
- ✅ Team trend charts
- ✅ Model vs Vegas comparison

---

## 🐛 Troubleshooting

### **Dashboard shows old predictions:**
→ Run `generate_all_predictions.py` first, then `create_apple_dashboard.py`

### **NBA features not showing:**
→ Check `predictions/all_predictions.json` - should have `rest_advantage`, etc.

### **Standings showing "N/A":**
→ API might be down, falls back to calculated data

### **AI insights not showing:**
→ Set `ANTHROPIC_API_KEY` environment variable

---

## 💡 Pro Tip

**Create an alias:**
```bash
alias update-sports="cd /path/to/nfl-predictions && python3 generate_all_predictions.py && python3 create_apple_dashboard.py && open predictions/dashboard.html"
```

Then just run:
```bash
update-sports
```

---

## ✅ Summary

**Dashboard is NOT live** - it's static HTML that needs regeneration.

**To update:**
1. `python3 generate_all_predictions.py` ← Uses NEW NBA features
2. `python3 create_apple_dashboard.py` ← Updates HTML
3. Open `predictions/dashboard.html`

**The new NBA features are NOW active** - they'll be used automatically when generating predictions! 🔥


