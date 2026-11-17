# Universal search

Search is performed against the SQLAlchemy `products` table. The local engine extracts category and budget using regular expressions, tolerates limited spelling differences with sequence matching and ranks by textual match plus available inventory.

Every result includes an explainable reason list. Unsuitable products are excluded by category and budget. Alternative products are selected from the same category.

The current implementation has no embedding or vector column. It is intentionally reliable and auditable. pgvector can be evaluated later, but is not claimed as implemented.
