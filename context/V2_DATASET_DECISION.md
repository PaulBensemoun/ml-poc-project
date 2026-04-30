# V2 Dataset Decision

## Decision

For the v2, the recommended path is:

**Switch the recommender core to the Coveo SIGIR eCom 2021 dataset.**

The project priority is now ML/recommender credibility, not visual catalog completeness. Coveo is the best target dataset because it is closer to a real e-commerce recommendation environment: session-level behavior, product detail events, add-to-cart events, purchases, search interactions, timestamps, product categories, price information, and text/image content representations.

`Online Retail II` remains useful as a historical baseline and fallback, but it should no longer drive the v2 architecture.

The visual marketplace layer can be reconstructed for demonstration. The app must explicitly say that product names/images are demo-facing representations, while the ML recommender is trained and evaluated on real anonymized e-commerce behavior.

Therefore, the best v2 strategy is:

1. Use Coveo SIGIR eCom 2021 for the recommender pipeline.
2. Model session-based recommendation from views/searches/adds/purchases.
3. Use ranking metrics and realistic candidate generation.
4. Build a separate demo catalog layer for readable product cards.
5. Keep `Online Retail II` only as a v1 baseline reference.

## Target Dataset: Coveo SIGIR eCom 2021

Source:

- `browsing_train.csv`
- `search_train.csv`
- `sku_to_content.csv`

The dataset contains:

| Capability | Coveo support |
| --- | --- |
| Product views / detail events | Yes |
| Add-to-cart events | Yes |
| Purchases | Yes |
| Session IDs | Yes |
| Timestamps | Yes |
| Search queries | Yes, vectorized |
| Search result impressions | Yes |
| Clicked search results | Yes |
| Product categories | Yes, hashed category tree |
| Price information | Yes, price bucket |
| Product text metadata | Yes, vectorized description |
| Product image metadata | Yes, vectorized image representation |
| Human-readable product names | No |
| Raw product photos | No |

This is the strongest public option for defending the recommender logic because it supports realistic in-session prediction and implicit feedback beyond purchases.

## Legacy Dataset Summary: Online Retail II

The previous v1 project used:

- `data/online_retail_II.csv`

Columns:

- `Invoice`
- `StockCode`
- `Description`
- `Quantity`
- `InvoiceDate`
- `Price`
- `Customer ID`
- `Country`

Audit from the local file:

| Metric | Value |
| --- | ---: |
| Raw rows | 1,067,371 |
| Clean rows after current filters | 805,549 |
| Missing customer IDs | 243,007 |
| Missing descriptions | 4,382 |
| Date range | 2009-12-01 to 2011-12-09 |
| Unique customers | 5,878 |
| Unique products | 4,631 |
| Unique invoices | 36,969 |
| Distinct customer-product pairs | 481,932 |
| Customer-product matrix density | 1.77% |
| Countries | 41 |
| Dominant market | United Kingdom |

This remains a useful scale for a local transaction-based recommender baseline. However, it lacks views, carts, sessions, searches, categories, and product content. It should be treated as v1 context, not the v2 target.

## What Online Retail II Supports Well as a Baseline

### Transaction-based personalization

The dataset contains real purchase events. This supports recommendation scenarios such as:

- Next product for an existing customer.
- Cross-sell based on previous purchases.
- Repeat purchase and replenishment candidates.
- Popular products by customer value segment.
- Country-level or market-level differences.

### Temporal validation

The `InvoiceDate` column makes it possible to train on past transactions and evaluate on future purchases. This is essential for a credible recommender.

### Customer features

The transaction history supports:

- Recency.
- Frequency.
- Monetary value.
- Average basket value.
- Number of invoices.
- Product diversity.
- Country.
- Preferred price range.
- Preferred categories if categories are derived.

### Product features

The transaction history supports:

- Product popularity.
- Average price.
- Revenue contribution.
- Repeat purchase frequency.
- Co-purchase patterns.
- High-value customer share.
- Country concentration.

### Interaction features

The dataset supports:

- Whether a customer already bought a product.
- How often a customer bought a product.
- Time since last customer-product purchase.
- Similarity between the customer's purchase history and product co-purchase neighborhoods.

## Why Online Retail II Is Not Enough for the V2 Priority

### Product images

There are no image URLs. A marketplace-like demo needs a separate image strategy:

- Curated mapping for top products.
- Generated category-level placeholder images.
- Generic image assets by product cluster.
- A manually maintained `product_catalog_enriched.csv`.

### Clean product categories

There is no category column. Product descriptions can be used to infer rough categories, but this requires custom rules or lightweight NLP.

### Clickstream behavior

The dataset only captures purchases. It does not include:

- Product views.
- Searches.
- Add-to-cart events.
- Abandoned carts.
- Impressions.
- Recommendation exposure logs.

This means the recommender would remain a purchase-history recommender, not a full behavioral personalization engine. Since the new priority is ML recommender credibility, this is now a blocking limitation rather than a minor trade-off.

### Explicit negative feedback

A missing purchase does not mean dislike. Negative examples must be sampled carefully and documented as training assumptions.

### Product metadata quality

Descriptions are short and sometimes noisy. Some stock codes may represent non-standard items, discounts, postage, or administrative entries. Additional cleaning is required before the final demo.

## Options Compared

### Option A: Keep Online Retail II unchanged

This is the fastest option, but it is rejected for v2.

Pros:

- No data migration.
- Existing code already works.
- Real transactions and timestamps.

Cons:

- No product images.
- Limited feature richness.
- Weak marketplace presentation.
- Current random split and classification metrics are not enough.

Verdict:

Useful for a baseline, insufficient for the new ML-first ambition.

### Option B: Keep and enrich Online Retail II

This was the previous recommendation, but it is no longer the best option after prioritizing recommender credibility above visual completeness.

Pros:

- Preserves the current working base.
- Keeps real purchase behavior.
- Allows a credible temporal recommender evaluation.
- Enables a polished marketplace demo through a separate catalog enrichment layer.
- Scope remains manageable in a local Streamlit project.

Cons:

- Product categories and images must be created or mapped.
- The project must be honest that it is not using clickstream events.
- Some recommendations may be biased toward popular historical purchases.

Verdict:

Good compromise, but weaker than Coveo for behavioral recommendation because it still lacks views, carts, searches, and sessions.

### Option C: Replace with Coveo SIGIR eCom 2021

This is now the recommended option.

Pros:

- Real session-based e-commerce behavior.
- Product detail events, add-to-cart events, purchases, and searches.
- Search results clicked and not clicked, which improves negative signal quality.
- Timestamps suitable for sequential/session validation.
- Product categories, price buckets, text vectors, and image vectors.
- Strong fit for next interaction, next product, cart conversion, and recommendation ranking tasks.

Cons:

- Product IDs and categories are anonymized.
- Text and image metadata are vectorized, not raw marketing content.
- The visual demo layer must reconstruct product cards.
- Heavier data processing than the current CSV.

Verdict:

Best choice for limiting technical objections about recommender realism.

### Other Alternatives

| Dataset | Strengths | Weaknesses |
| --- | --- | --- |
| Coveo SIGIR eCom 2021 | Views, add-to-cart, purchases, searches, sessions, timestamps, categories, price, text/image vectors | Anonymized, no raw product names/images |
| RetailRocket | Real e-commerce events with views, add-to-cart, transactions, item properties, category tree | Hashed item properties, no product images, fewer human-readable product details |
| Amazon Reviews 2023 | Rich metadata, categories, prices, images, user-item reviews, bought-together links | Very large, review-based rather than direct purchase logs, heavier engineering |
| H&M Personalized Fashion Recommendations | Fashion domain, customers, articles, transactions, rich article metadata, image ecosystem | Larger project shift, more complex data loading and asset handling |
| RecSys Challenge 2022 Dressipi | Session-based fashion recommendation with item features and purchases | Session prediction task, no direct customer marketplace narrative, more specialized |

Verdict:

Coveo is the best ML-first choice. H&M is the best visual-marketplace choice. Since the stated priority is recommender performance and coherence, choose Coveo.

## Recommended Enrichment Layer

Create a new file in a later implementation phase for the demo layer:

- `data/coveo_product_catalog_demo.csv`

Suggested columns:

| Column | Purpose |
| --- | --- |
| `product_sku_hash` | Join key with Coveo product metadata |
| `demo_product_name` | Human-readable display name reconstructed for the app |
| `demo_category` | Readable category derived from hashed category or clustering |
| `price_bucket` | Original Coveo price bucket |
| `display_price` | Demo-facing representative price |
| `image_url` | Generated, placeholder, or curated demo image |
| `image_source` | Generated, placeholder, curated, or external |
| `description_short` | UI-friendly demo description |
| `is_demo_ready` | Whether the item can appear in the polished demo |

This table should not be presented as raw source data. It is a presentation layer that makes anonymized products understandable in the app. The app should explicitly disclose this.

## Cleaning Priorities for V2

For Coveo, the priorities are:

- Parse browsing events into session sequences.
- Normalize event types and product actions.
- Separate product detail, add-to-cart, remove, purchase, and non-product page events.
- Join product events with `sku_to_content.csv`.
- Validate timestamp ordering within sessions.
- Build train/validation/test splits by time or challenge-style session truncation.
- Keep search interactions and clicked/not-clicked products for advanced features.
- Create a demo-ready product subset without reducing the ML training universe.

## Dataset Decision Criteria

Use these criteria before replacing the dataset:

| Criterion | Coveo SIGIR eCom 2021 | Required for V2 |
| --- | --- | --- |
| Session ID | Yes | Required |
| Product/item ID | Yes | Required |
| Timestamps | Yes | Required |
| Product views | Yes | Required for ML-first recommender |
| Add-to-cart events | Yes | Required for strong behavioral signal |
| Purchases | Yes | Required |
| Search behavior | Yes | Strong differentiator |
| Product categories | Yes, hashed | Required |
| Price information | Yes, bucketed | Useful |
| Text metadata | Yes, vectorized | Useful |
| Image metadata | Yes, vectorized | Useful |
| Raw product images | No | Demo layer can reconstruct |
| Human-readable names | No | Demo layer can reconstruct |

## Final Recommendation

Replace the v2 target dataset with Coveo SIGIR eCom 2021.

The project should be framed as:

> A session-based e-commerce recommender trained on real anonymized shopping behavior, including product views, searches, add-to-cart events, purchases, timestamps, and product metadata.

The app should also state:

> Product names and visuals in the marketplace demo are reconstructed for presentation because the source dataset is anonymized. The ML pipeline uses the original behavioral and product-content signals.

The recommended wording for the final project:

> We use Coveo SIGIR eCom 2021 as a real session-based e-commerce foundation. The recommender is evaluated offline by predicting future session interactions and purchases with ranking metrics. The marketplace interface is a credible demonstration layer built on top of anonymized product IDs and metadata.

## Decision Log

| Decision | Status |
| --- | --- |
| Use Coveo SIGIR eCom 2021 as v2 recommender dataset | Accepted |
| Treat Online Retail II as v1 baseline only | Accepted |
| Build a reconstructed demo catalog for product cards | Accepted |
| Clearly disclose reconstructed visuals in the app | Accepted |
| Use H&M only if visual marketplace realism becomes the top priority | Fallback |
