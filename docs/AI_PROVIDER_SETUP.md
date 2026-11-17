# AI provider setup

Set optional variables in `backend/.env`:

```text
AI_PROVIDER=openai-compatible
AI_API_URL=https://provider.example/v1/chat/completions
AI_API_KEY=your-provider-secret
AI_MODEL=provider-model-name
AI_TIMEOUT_SECONDS=15
AI_RATE_LIMIT_PER_MINUTE=20
```

Keep `AI_PROVIDER=local` or leave the provider fields empty for deterministic fallback behavior. The fallback is clearly labelled in API responses.

The provider must expose an OpenAI-compatible chat completions JSON endpoint. API keys stay server-side and must not be placed in `VITE_*` variables. Response parsing validates JSON objects and provider HTTP/timeout failures fall back to labelled local output for supported seller tools.
