# Coveo Data Audit Summary

## Purpose

This document summarizes the conclusions from the initial audit of the **Coveo SIGIR eCom 2021** dataset.

It is intended to become the reference source for the future Streamlit pages:

- **Dataset & Insights**
- **Training & Validation**
- **Impact & Limitations**

The detailed machine-readable audit is available in:

- `results/coveo_data_audit.json`
- `results/coveo_data_audit.md`

## Executive Summary

The Coveo dataset is a strong fit for the v2 objective: building a credible **session-based e-commerce recommender**.

Unlike `Online Retail II`, which only contains purchases, Coveo includes real anonymized shopping sessions with product detail views, add-to-cart events, purchase events, search interactions, timestamps, and product content metadata. This makes it much more defensible for recommender modeling because the model can learn from behavioral signals that exist before the purchase.

The main trade-off is that the dataset is anonymized. Product IDs, categories, names, and visuals are not directly human-readable. Therefore, the final app should clearly separate:

- the **ML layer**, trained on real Coveo behavioral data;
- the **marketplace demo layer**, reconstructed for presentation with readable names and visuals.

## Files Audited

The audit covers the three core Coveo files:

| File | Role |
| --- | --- |
| `data/coveo/raw/browsing_train.csv` | Main browsing/session event log |
| `data/coveo/raw/search_train.csv` | Search interactions, shown products, clicked products |
| `data/coveo/raw/sku_to_content.csv` | Product metadata with category, price, text vectors, image vectors |

## Dataset Scale

| Metric | Value |
| --- | ---: |
| Browsing rows | 36,079,307 |
| Unique sessions | 4,934,699 |
| Unique products in browsing | 57,483 |
| Product event rows | 10,431,611 |
| Search rows | 819,516 |
| Search sessions | 550,100 |
| Product metadata rows | 66,386 |
| Unique products in metadata | 66,386 |

This confirms that the dataset is large enough for a serious recommender project and much closer to real e-commerce traffic than the previous transaction-only dataset.

## Browsing Event Structure

The browsing file contains both page views and product-related events.

| Event type | Count |
| --- | ---: |
| `pageview` | 25,647,696 |
| `event_product` | 10,431,611 |

Product events represent about **28.9%** of browsing rows. Page views represent the majority of events and may still be useful for session context, but the first recommender version should focus on product events.

## Product Actions

| Product action | Count |
| --- | ---: |
| `detail` | 9,707,890 |
| `add` | 329,557 |
| `remove` | 316,316 |
| `purchase` | 77,848 |

### Interpretation

- `detail` is abundant and should be the first stable signal for session-based recommendation.
- `add` is rarer but highly valuable because it indicates stronger intent.
- `purchase` is the most business-relevant target but is much rarer.
- `remove` can later help understand cart correction or negative intent.

## Session Quality

| Metric | Value |
| --- | ---: |
| Sessions with `detail` | 3,260,353 |
| Sessions with `add` | 214,684 |
| Sessions with `purchase` | 53,209 |
| Sessions with `remove` | 57,441 |

Session length distribution:

| Statistic | Events per session |
| --- | ---: |
| Min | 1 |
| P25 | 2 |
| Median | 3 |
| P75 | 8 |
| P90 | 17 |
| P95 | 27 |
| Max | 206 |

### Interpretation

Most sessions are short. The median session has only 3 events, while the top 10% of sessions have at least 17 events.

This has direct consequences for modeling:

- Session truncation must handle short sessions carefully.
- Some tasks should start with sessions that have enough observed events and future targets.
- Purchase prediction is credible but should not be the only first target because purchase sessions are sparse.
- A progressive strategy is preferable: start with future product interactions, then add add-to-cart and purchase-specific evaluation.

## Search Data

| Metric | Value |
| --- | ---: |
| Search rows | 819,516 |
| Unique search sessions | 550,100 |
| Rows with result products | 602,754 |
| Rows with clicked products | 179,495 |

### Interpretation

Search is one of the most valuable parts of the dataset because it provides intent and implicit negative feedback:

- products shown in search results;
- products clicked after search;
- products shown but not clicked.

This is useful for:

- hard negative sampling;
- search-context features;
- modeling intent in active sessions;
- explaining recommendations in the app.

Recommended app wording:

> Search interactions give the recommender stronger behavioral context than purchase-only data. The model can learn not only from what users bought, but also from what they searched, viewed, clicked, ignored, added to cart, and purchased.

## Product Metadata Coverage

| Metric | Value |
| --- | ---: |
| Product metadata rows | 66,386 |
| Unique products | 66,386 |
| Rows with description vector | 31,950 |
| Rows with image vector | 28,370 |
| Rows with non-empty price bucket | 32,038 |
| Rows with non-empty category | 32,052 |

Approximate coverage:

| Metadata field | Coverage |
| --- | ---: |
| Description vector | 48.1% |
| Image vector | 42.7% |
| Price bucket | 48.3% |
| Category | 48.3% |

### Interpretation

Product metadata is valuable but incomplete. The recommender should use it when available, but the pipeline must include fallbacks.

For modeling:

- category and price bucket can be used as product features when present;
- description and image vectors can support content similarity;
- missing metadata should not exclude products from the first recommender version;
- metadata availability itself can be used as a feature.

For the app:

- raw product names and images are not available;
- image vectors are not directly displayable storefront images;
- the marketplace demo needs a reconstructed visual catalog.

## Key Strengths of the Dataset

The dataset strongly supports the v2 ambition because it includes:

- real e-commerce sessions;
- product detail events;
- add-to-cart events;
- purchase events;
- search interactions;
- clicked and non-clicked search results;
- timestamps;
- product metadata;
- text vectors;
- image vectors;
- price buckets;
- category hashes.

This enables a more realistic recommender than the original `Online Retail II` setup.

## Key Limitations

The dataset also has important limitations that must be disclosed:

- Product IDs are anonymized.
- Category names are hashed.
- Raw product names are not available.
- Raw storefront images are not available.
- Product metadata coverage is incomplete.
- Purchase events are much rarer than product detail events.
- Most sessions are short.
- Offline metrics do not prove real business uplift without A/B testing.

Recommended app wording:

> The Coveo dataset is anonymized for privacy and confidentiality. The recommender is trained on real session behavior and product-content signals, while product names and visuals in the demo are reconstructed for presentation.

## Modeling Implications

### Recommended first modeling target

The first modeling target should not be purchase-only.

Recommended progression:

1. Predict future product `detail` interactions.
2. Add future `add` prediction.
3. Evaluate future `purchase` prediction as the strongest business target.
4. Later combine signals into a weighted relevance label.

This avoids starting with an overly sparse purchase-only task while keeping purchase as the final business objective.

### Recommended first evaluation protocol

Use session truncation:

1. Sort events by `session_id_hash` and timestamp.
2. Split each eligible session into:
   - observed prefix;
   - future suffix.
3. Use the prefix for features.
4. Use the suffix for labels.
5. Rank candidate products.
6. Evaluate whether future products appear in the top K.

### Recommended first candidate strategy

For each session, generate candidates from:

- popular products;
- products viewed in the observed prefix;
- products from search results;
- products co-visited with observed products;
- products co-carted with observed products;
- same-category products where category is available;
- content-similar products where vectors are available.

## Recommended Metrics

The primary metrics should be recommender ranking metrics:

- `Recall@10`
- `NDCG@10`
- `HitRate@10`
- `Precision@10`
- `MAP@10`
- catalog coverage

Classification metrics such as accuracy, precision, recall, and F1 can remain secondary if pointwise models are used, but they should not be the main success criteria.

## Streamlit App Content to Reuse

### Dataset summary card

```text
Coveo SIGIR eCom 2021 contains 36M anonymized browsing events across 4.9M sessions, including product views, add-to-cart events, purchases, searches, timestamps, and product metadata. This makes it suitable for realistic session-based recommendation.
```

### Why this dataset

```text
The project prioritizes recommender credibility over visual catalog completeness. Coveo is a strong fit because it captures real shopping behavior before purchase, not only completed transactions.
```

### Visual layer disclaimer

```text
The source dataset is anonymized. Product names and visuals shown in the marketplace demo are reconstructed for presentation. The ML recommender itself uses the original behavioral signals and product-content metadata.
```

### Modeling explanation

```text
The recommender observes the first part of a shopping session and ranks candidate products. Performance is measured by whether products from the future part of the session appear near the top of the recommendation list.
```

### Limitation note

```text
Purchase events are the strongest business signal but are sparse. The first model iteration may train on future product interactions and add-to-cart events, then evaluate purchases as a high-value business target.
```

## Decision for Next Step

Proceed to **Plan 3: Build the Session Parser**.

The parser should focus first on:

- `browsing_train.csv`;
- ordered events by `session_id_hash`;
- product actions `detail`, `add`, `remove`, `purchase`;
- support for a sample mode because the dataset is large.

Search integration should be planned but can be added after the first browsing-session parser is stable.
