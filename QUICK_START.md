# 🚀 Quick Start - Run The Entire System

## **One Command to Run Everything:**

```bash
./run_system.sh
```

**This will:**
1. ✅ Generate NFL + NBA predictions (with enhanced features)
2. ✅ Update dashboard HTML
3. ✅ Update results (if games completed)
4. ✅ Generate results pages

**Output:** `predictions/dashboard.html`

---

## **Alternative: Production Pipeline**

```bash
python3 production_pipeline.py
```

**This does the same thing but with more logging and error handling.**

---

## **Step-by-Step (If You Want Control):**

```bash
# Step 1: Generate predictions
python3 generate_all_predictions.py

# Step 2: Update dashboard
python3 create_apple_dashboard.py

# Step 3: Update results (for yesterday)
python3 update_results.py

# Step 4: Generate results pages
python3 generate_results_pages.py
```

---

## **View Your Dashboard:**

```bash
open predictions/dashboard.html
```

---

## **What Gets Generated:**

### **Main Dashboard:**
- `predictions/dashboard.html` - Full prediction dashboard with AI insights

### **Results Pages:**
- `predictions/results.html` - Recent game-by-game results
- `predictions/historical-performance.html` - Performance statistics

### **Data Files:**
- `predictions/all_predictions.json` - All predictions in JSON
- `predictions/validation.db` - SQLite database with all predictions/results

---

## **Automation (Cron Jobs):**

**Set up to run automatically:**

```bash
crontab -e
```

**Add:**
```bash
# Run full system every morning at 8am
0 8 * * * cd /Users/a.fleming/nfl-predictions && ./run_system.sh >> logs/system.log 2>&1

# Update results every night at 11pm
0 23 * * * cd /Users/a.fleming/nfl-predictions && python3 update_results.py >> logs/results.log 2>&1
```

---

## **Troubleshooting:**

### **"No predictions found"**
→ Run `python3 generate_all_predictions.py` first

### **"No completed games"**
→ Normal if games haven't finished yet. Run `update_results.py` the next day.

### **"Dashboard shows old data"**
→ Regenerate: `python3 create_apple_dashboard.py`

---

## **Quick Test:**

```bash
# Test the full system
./run_system.sh

# View dashboard
open predictions/dashboard.html
```

**That's it!** 🎉
