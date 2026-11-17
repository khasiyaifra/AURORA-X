# Messaging architecture

Conversations are persisted between buyer and seller profiles and may reference an order or product. Messages are keyed by a client ID and conversation ID to prevent duplicate submissions. REST endpoints provide history, sending and read receipts.

WebSocket endpoint:

`ws://host/api/ws/conversations/{conversation_id}?token=<jwt>`

The connection validates the JWT and conversation membership. Typing events and messages are broadcast only to connected members. Attachments are private server files, not public static assets.
