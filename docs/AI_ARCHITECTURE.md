# AI architecture

Stage 4 uses a provider-abstraction layer. `AIProvider.generate` supports a configured OpenAI-compatible JSON endpoint and otherwise uses deterministic catalogue logic.

AI operations are separate from commerce mutations:

- Search extracts intent and ranks actual `Product` records.
- Copilot searches and compares records but never purchases.
- Comparison uses persisted product fields.
- Seller tools produce advisory listing content.
- Recommendations use category affinity and purchase history.
- TrustShield produces explainable rule warnings with human-review actions.

Usage and sanitized response logs are stored in `ai_usage` and `ai_response_logs`. Personal AI features require buyer authentication; seller tools require seller authentication.
