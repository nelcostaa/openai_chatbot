# Quick Reference - Model Fallback System

## 🚀 Quick Start

```bash
# Start backend with fallback system
cd /home/nelso/Documents/openai_chatbot/backend
python3 api.py
```

## 📊 Check Status

```bash
# See current active model
curl http://localhost:5000/api/model-status
```

## 📈 Your Current Usage (2025-11-20)

| Model | RPM | TPM | RPD | Status |
|-------|-----|-----|-----|--------|
| gemini-2.0-flash | 13/15 | 5.25K/1M | 61/200 | ⚠️ High |
| gemini-2.5-flash | 2/10 | 723/250K | 5/250 | ✅ Good |

## 🔄 Fallback Cascade Order

1. **gemini-2.5-flash** ← Primary
2. gemini-2.5-flash-lite
3. gemini-2.0-flash
4. gemini-2.0-flash-lite
5. gemini-2.5-flash-preview
6. gemini-2.5-flash-lite-preview

## 📝 What to Watch For

### ✅ Normal Operation
```
[API] Attempting with model: gemini-2.5-flash (attempt 1/6)
[API] ✅ Success with gemini-2.5-flash
```

### 🔄 Fallback Triggered
```
[API] ❌ Error with gemini-2.5-flash: 429 RESOURCE_EXHAUSTED
[API] 🔄 Rate limit hit, trying next model...
[API] ✅ Successfully switched to gemini-2.5-flash-lite
```

### ⚠️ All Models Exhausted (Rare)
```
[API] ⚠️ All models exhausted! All 6 models hit rate limits.
```

## 🎯 Key Points

- ✅ **Context preserved** - Conversations never lost
- ✅ **Automatic** - No manual intervention needed
- ✅ **6x capacity** - 93 RPM total vs 10 RPM single model
- ✅ **Free tier** - Still $0 cost
- ✅ **Production ready** - Handles all edge cases

## 📚 Full Documentation

- Technical: `docs/MODEL_FALLBACK_STRATEGY.md`
- Summary: `docs/IMPLEMENTATION_SUMMARY.md`
- Google Docs: https://ai.google.dev/gemini-api/docs/rate-limits

## 🔗 Useful Links

- [Usage Dashboard](https://aistudio.google.com/usage?timeRange=last-28-days&tab=rate-limit)
- [Rate Limits Docs](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Models Overview](https://ai.google.dev/gemini-api/docs/models)
- [Troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting)
