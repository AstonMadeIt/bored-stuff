# 🧪 Quick Test - Verify AI is Working

## Step 1: Set API Key (if not already set)
```bash
export ANTHROPIC_API_KEY="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"
```

**Note:** `export` doesn't print anything - that's normal! ✅

## Step 2: Verify Key is Set
```bash
python3 -c "import os; print('✅ Set!' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set')"
```

## Step 3: Test AI Generation
```bash
python3 test_ai.py
```

You should see:
- ✅ API key found
- ✅ AI Explanation Generated
- A 5-bullet explanation in casual language

## Step 4: Generate Dashboard with AI
```bash
python3 create_apple_dashboard.py
```

Look for:
- "✅ AI insights enabled" in output
- "🤖 AI Analysis: Why This Pick?" in dashboard HTML

## Step 5: View Dashboard
```bash
open predictions/dashboard.html
```

You should see AI-generated explanations instead of structured factors!

---

## 🔧 Make API Key Permanent

Add to `~/.zshrc`:
```bash
echo 'export ANTHROPIC_API_KEY="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"' >> ~/.zshrc
source ~/.zshrc
```

Then verify:
```bash
python3 -c "import os; print('✅ Permanent!' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set')"
```

---

## 🐛 Troubleshooting

**If API key not found:**
- Make sure you ran `export` in the same terminal session
- Check: `echo $ANTHROPIC_API_KEY` (should print your key)

**If AI generation fails:**
- Check API key is valid
- Verify anthropic package: `pip3 list | grep anthropic`
- Check your credit balance at console.anthropic.com

**If dashboard shows fallback (structured factors):**
- API key not set when dashboard was generated
- Regenerate: `python3 create_apple_dashboard.py`


