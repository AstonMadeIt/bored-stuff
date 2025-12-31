# DraftKings Client Setup

## ✅ **Installation:**

The DraftKings Python client is available on PyPI as `draft-kings`:

```bash
pip3 install draft-kings --user
```

**Note:** The package name on PyPI is `draft-kings` (with hyphen), but you import it as `draft_kings` (with underscore).

## 📦 **Package Details:**

- **PyPI Package**: `draft-kings`
- **Import Name**: `draft_kings.client.DraftKingsClient`
- **GitHub**: https://github.com/jaebradley/draftkings_client
- **Documentation**: https://jaebradley.github.io/draftkings_client

## 🔧 **Usage:**

```python
from draft_kings.client import DraftKingsClient

client = DraftKingsClient()
# Use client to fetch DraftKings data
```

## ⚠️ **Important Notes:**

1. **Optional**: DraftKings client is **optional** - the system works perfectly fine without it using ESPN API instead.

2. **No Authentication Required**: DraftKings' public endpoints don't require authentication, but they're not officially documented.

3. **No Guarantees**: DraftKings makes no guarantees about their public API, so endpoints may change without notice.

4. **Current Status**: The system gracefully handles DraftKings being unavailable and uses ESPN API as the primary data source.

## ✅ **Verification:**

After installation, verify it works:

```bash
python3 -c "from draft_kings.client import DraftKingsClient; print('✅ DraftKings client installed!')"
```

## 🎯 **Current Integration:**

The `automated_validation_system.py` automatically detects if DraftKings is available and uses it if present. If not, it falls back to ESPN API (which is free and reliable).

**No action needed** - the system works either way!


