# Data Strategy

## Dataset Decision

The v2 target dataset is Coveo SIGIR eCom 2021.

The priority is ML recommender credibility. Coveo is preferred because it contains real anonymized e-commerce sessions with product detail events, add-to-cart events, purchases, searches, timestamps, categories, price buckets, and product content vectors.

`Online Retail II` remains as a v1 baseline reference only.

## Cleaning and Parsing Rules

- Load `browsing_train.csv`, `search_train.csv`, and `sku_to_content.csv`.
- Parse timestamps and order events inside each `session_id_hash`.
- Normalize product actions such as detail, add, remove, and purchase.
- Keep product-level events for recommendation modeling.
- Join product events with `sku_to_content.csv` on `product_sku_hash`.
- Preserve search result products and clicked products when available.
- Build observed session prefixes and future suffix labels.
- Keep future suffix events out of feature computation to avoid leakage.

## Modeling Approach

We build a session-product ranking dataset:

Each row represents:

```text
(session_id_hash, candidate_product_sku_hash, cutoff_event_index)
```

Target:

- 1 if the product appears in future target events after the session cutoff
- 0 if the product is a candidate but does not appear in future target events

The strongest target is future purchase, but intermediate versions can predict future product detail or add-to-cart events.

## Feature Ideas

### Session features

- number of observed events
- number of observed product interactions
- number of unique products observed
- elapsed session time
- last observed event type
- whether the session includes search
- whether the session includes add-to-cart

### Product features

- global view count
- global add-to-cart count
- global purchase count
- conversion proxy
- category hash
- price bucket
- text vector
- image vector

### Session-product interaction features

- candidate seen in observed prefix
- candidate added to cart in observed prefix
- candidate shown in search results
- candidate clicked from search results
- same category as observed products
- co-visit score
- co-cart score
- co-purchase score
- content-vector similarity
- price-bucket fit

## Negative Sampling

- Sample random products not present in the future target set.
- Add hard negatives from popular products.
- Add hard negatives from same-category products.
- Add hard negatives from search results that were shown but not clicked.
- Add hard negatives from co-visited or co-carted products that were not future targets.

## Evaluation

The main evaluation should use recommender ranking metrics:

- Precision@K
- Recall@K
- MAP@K
- NDCG@K
- HitRate@K
- Catalog coverage

Classification metrics can remain secondary, but they should not be the primary success measure.

## Demo Layer

Because Coveo is anonymized, the app will use a reconstructed marketplace layer:

- readable demo product names
- readable demo categories
- generated or placeholder product images
- display prices derived from price buckets
- clear disclosure that visuals are reconstructed for presentation
