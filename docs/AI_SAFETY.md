# AI safety

- Personal AI endpoints require JWT authentication.
- Buyer, seller and public search permissions are checked separately.
- AI inputs are length-limited and instruction-like text is filtered.
- External provider output must be valid JSON.
- Copilot responses explicitly set `purchase_executed=false`.
- AI tools cannot change prices, inventory or order status.
- Seller recommendations remain advisory.
- TrustShield never imposes automatic penalties.
- Sensitive buyer/seller fields are not included in response logs.
- In-memory rate limiting protects AI requests; production deployments should use distributed rate limiting.
