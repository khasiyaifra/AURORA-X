# Translation architecture

The API accepts source and target language codes and preserves original message text. Supported UI languages are English, Hindi, Kannada, Tamil, Telugu, Malayalam, Bengali, Marathi and Urdu.

No translation credentials are configured by default. The endpoint explicitly returns 503 unavailable rather than presenting fallback text as a successful translation. An external provider adapter can be added behind `TRANSLATION_PROVIDER`.
