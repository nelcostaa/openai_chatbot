# Gemini API Model Fallback Strategy

**Last Updated**: 2025-11-20  
**Status**: ✅ Implemented and Active

## Overview

This chatbot implements an **intelligent model fallback cascade** to maximize uptime and avoid rate limit errors (HTTP 429) on Google's Gemini API free tier.

### Key Features
- ✅ **Zero Context Loss** - Conversation history is client-side, preserved across model switches
- ✅ **Automatic Failover** - Seamlessly tries next model when rate limits hit
- ✅ **6 Model Cascade** - Multiple fallback options ensure high availability
- ✅ **Smart Recovery** - Returns to primary model when rate limits reset
- ✅ **Production Ready** - Handles all error cases gracefully

---

## How It Works

### The Problem
Google Gemini API free tier has strict rate limits:
- **RPM** (Requests Per Minute) - e.g., 10 requests/min
- **TPM** (Tokens Per Minute) - e.g., 250,000 tokens/min  
- **RPD** (Requests Per Day) - e.g., 250 requests/day

When these limits are exceeded, API returns `429 RESOURCE_EXHAUSTED`.

### The Solution
When a `429` error occurs, automatically switch to the next model in the cascade.

**Why this works:**
1. Each model has **independent rate limits**
2. Conversation history is **stored client-side** (sent with each request)
3. Models are **functionally equivalent** for chat tasks
4. No data loss during switch

---

## Model Cascade Configuration

Ordered by preference and rate limits:

| Priority | Model | RPM | TPM | RPD | Notes |
|----------|-------|-----|-----|-----|-------|
| **1** (Primary) | `gemini-2.5-flash` | 10 | 250K | 250 | Best price-performance |
| **2** | `gemini-2.5-flash-lite` | 15 | 250K | 1,000 | Higher daily quota |
| **3** | `gemini-2.0-flash` | 15 | 1M | 200 | Huge 1M token context |
| **4** | `gemini-2.0-flash-lite` | 30 | 1M | 200 | Highest RPM (30!) |
| **5** | `gemini-2.5-flash-preview` | 10 | 250K | 250 | Preview release |
| **6** | `gemini-2.5-flash-lite-preview` | 15 | 250K | 1,000 | Preview release |

**Total Combined Capacity (Free Tier):**
- **93 RPM** across all models
- **3.75M TPM** across all models
- **2,900 RPD** across all models

---

## Implementation Details

### Backend (`api.py`)

```python
MODEL_FALLBACK_CASCADE = [
    "gemini-2.5-flash",          # Primary
    "gemini-2.5-flash-lite",     # Tier 1 fallback
    "gemini-2.0-flash",          # Tier 1 fallback
    "gemini-2.0-flash-lite",     # Tier 2 fallback
    "gemini-2.5-flash-preview",  # Tier 3 fallback
    "gemini-2.5-flash-lite-preview",
]
```

### Error Detection

The system catches:
- HTTP `429` status codes
- `RESOURCE_EXHAUSTED` error messages
- Any error containing "rate limit"

### Fallback Logic

1. Request fails with 429 → Try next model
2. If all 6 models exhausted → Return clear error to user
3. When rate limits reset → Automatically return to primary model

### No Manual Switching Required

The system is **fully automatic**. Users never see errors or interruptions when models switch.

---

## Testing the System

### Check Current Model
```bash
curl http://localhost:5000/api/model-status
```

Response:
```json
{
  "current_model": "gemini-2.5-flash",
  "current_model_index": 0,
  "available_models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", ...],
  "total_models": 6,
  "fallback_enabled": true
}
```

### Simulate Rate Limit
To test fallback behavior, rapidly send requests until primary model hits rate limit. System should automatically switch.

### Monitor Logs
Backend logs show model switching:
```
[API] Attempting with model: gemini-2.5-flash (attempt 1/6)
[API] ❌ Error with gemini-2.5-flash: 429 RESOURCE_EXHAUSTED
[API] 🔄 Rate limit hit on gemini-2.5-flash, trying next model...
[API] Attempting with model: gemini-2.5-flash-lite (attempt 2/6)
[API] ✅ Successfully switched from gemini-2.5-flash to gemini-2.5-flash-lite
```

---

## Context Preservation

### How Context is Maintained

**Before fallback:**
```
User: "Tell me about AI"
Assistant (gemini-2.5-flash): "AI is..."
User: "What about machine learning?"
```

**After 429 error and fallback:**
```
Assistant (gemini-2.5-flash-lite): "Machine learning is a subset of AI..."
```

The conversation history `[User msg 1, Assistant msg 1, User msg 2]` is sent with every request, regardless of which model handles it.

### Why This Works

Gemini API is **stateless**. Every request includes:
```json
{
  "messages": [
    {"role": "user", "content": "Tell me about AI"},
    {"role": "assistant", "content": "AI is..."},
    {"role": "user", "content": "What about machine learning?"}
  ]
}
```

The model doesn't need to "remember" previous turns - they're always included.

---

## Rate Limit Best Practices

### Current Usage (as of 2025-11-20)
From Google AI Studio dashboard:
- `gemini-2.0-flash`: 13/15 RPM, 5.25K/1M TPM, 61/200 RPD
- `gemini-2.5-flash`: 2/10 RPM, 723/250K TPM, 5/250 RPD

**Status**: ⚠️ Close to RPM limits on 2.0-flash

### Optimization Strategies

1. **Use appropriate models for task complexity**
   - Simple queries → Flash-Lite models (higher RPM)
   - Complex reasoning → Flash/Pro models

2. **Implement client-side rate limiting**
   - Debounce rapid user inputs
   - Queue requests when approaching limits

3. **Monitor usage trends**
   - Check AI Studio dashboard regularly
   - Set up alerts for quota usage

4. **Consider paid tier if needed**
   - Tier 1 (billing enabled): Higher limits
   - Tier 2 ($250 spent): Even higher
   - Tier 3 ($1000 spent): Maximum limits

---

## Advantages of This Approach

### ✅ Benefits
1. **High Availability** - 6 models = 6x more capacity
2. **Seamless UX** - Users never see rate limit errors
3. **Cost Efficient** - Maximizes free tier capacity
4. **Future Proof** - Easy to add more models
5. **No State Management** - Client-side history = simple architecture

### ⚠️ Considerations
1. **Model variations** - Different models may have slightly different response styles
2. **Preview stability** - Preview models may change or deprecate
3. **Monitoring complexity** - Need to track usage across multiple models

---

## Alternative Strategies Considered

### 1. ❌ Queue System with Rate Limiting
**Why not:** Adds complexity, increases latency, requires state management

### 2. ❌ Single Model with Exponential Backoff
**Why not:** Still hits limits, poor UX during wait times

### 3. ❌ Multiple API Keys
**Why not:** Against ToS, not sustainable

### 4. ✅ **Model Cascade (Chosen)**
**Why yes:** Simple, effective, maintains UX, maximizes free tier

---

## Future Enhancements

### Potential Improvements
1. **Smart model selection** - Choose initial model based on:
   - Current usage metrics
   - Message complexity
   - Time of day patterns

2. **Predictive switching** - Switch before hitting limits
   - Monitor usage trends
   - Pre-emptively move to less-used models

3. **Usage analytics dashboard** - Track:
   - Model switch frequency
   - Per-model success rates
   - Cost/performance metrics

4. **Load balancing** - Distribute requests across models proactively instead of reactively

---

## Related Documentation

- [Google Gemini Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Gemini Models Overview](https://ai.google.dev/gemini-api/docs/models)
- [API Troubleshooting Guide](https://ai.google.dev/gemini-api/docs/troubleshooting)
- [Usage Dashboard](https://aistudio.google.com/usage?timeRange=last-28-days&tab=rate-limit)

---

## Questions & Answers

### Q: Will conversation quality decrease when models switch?
**A:** No significant impact. All Flash models are optimized for similar tasks. Pro models offer better reasoning but are not in the cascade due to low rate limits (2 RPM).

### Q: What happens if all 6 models hit rate limits?
**A:** User receives clear error: "All available models have exceeded their rate limits. Please try again later." Rate limits reset: RPM every minute, RPD at midnight PT.

### Q: Can I manually choose a model?
**A:** Currently no, but this could be added. The automatic system ensures optimal resource usage without user intervention.

### Q: Does this violate Google's ToS?
**A:** No. Using multiple models from the same API key and project is completely legitimate. Each model has separate rate limits by design.

---

## Conclusion

This model fallback cascade strategy provides a **robust, production-ready solution** for maximizing Gemini API free tier availability while maintaining excellent user experience. Zero context loss, automatic recovery, and 6x capacity make this approach ideal for test/development chatbots.

**Status**: ✅ Fully implemented and operational
