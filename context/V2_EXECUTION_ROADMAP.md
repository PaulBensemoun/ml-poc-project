# V2 Execution Roadmap

## Objective

This roadmap converts the v2 vision into an implementation sequence.

The goal is to avoid a full rewrite without direction. The project should evolve in controlled stages:

1. Stabilize the data decision.
2. Build a credible recommender evaluation protocol.
3. Improve feature engineering and models.
4. Add a reconstructed catalog layer for the marketplace demo.
5. Rebuild the Streamlit app as a multi-page product.
6. Polish the final narrative and delivery.

## Guiding Decision

The v2 should use:

- Coveo SIGIR eCom 2021 as the recommender foundation.
- `Online Retail II` only as a v1 baseline reference.
- A reconstructed demo catalog layer for names, images, categories, and UI-friendly product cards.
- Ranking-based recommender evaluation.
- A multi-page Streamlit app.

The priority is ML recommender credibility. The visual layer can be reconstructed, but the app must disclose this clearly.

## Phase 0: Freeze Current Baseline

### Purpose

Keep a clear reference point before changing the pipeline.

### Tasks

- Preserve the current working model evaluation flow.
- Keep current metrics in `results/model_metrics.csv` as baseline reference.
- Document that the current baseline uses random split and classification metrics.
- Document that `Online Retail II` is no longer the v2 target dataset.
- Avoid deleting the current working code until the v2 pipeline is functional.

### Deliverables

- Current model metrics referenced in documentation.
- Known limitations documented.

### Exit criteria

- The team can explain what the v1 does and why v2 is needed.

## Phase 1: Coveo Data Acquisition and Audit

### Purpose

Prepare the Coveo dataset for session-based recommendation modeling.

### Tasks

1. Download or manually place the Coveo data files.
2. Document expected raw files:
   - `browsing_train.csv`
   - `search_train.csv`
   - `sku_to_content.csv`
3. Create a reusable data audit script or notebook.
4. Profile event types and product actions.
5. Profile session lengths and timestamp ordering.
6. Profile add-to-cart and purchase frequency.
7. Profile search interactions and clicked results.
8. Profile product metadata coverage.
9. Decide the initial data subset if full data is too large for local iteration.

### Recommended files

```text
src/coveo_data.py
notebooks/coveo_data_audit.ipynb
```

### Exit criteria

- The project can load and inspect Coveo files.
- Event, session, and product metadata coverage are understood.
- The initial modeling subset is defined if needed.

## Phase 2: Session Parsing, Splitting, and Candidate Generation

### Purpose

Make evaluation closer to real deployment.

### Tasks

1. Parse Coveo browsing events into ordered sessions.
2. Join search interactions where useful.
3. Build observed session prefixes and future suffix targets.
4. Define train, validation, and test splits.
5. Generate candidate products per session.
6. Ensure future target products are included in evaluation candidates.
7. Implement negative sampling:
   - Random product negatives.
   - Popularity-based hard negatives.
   - Same-category hard negatives.
   - Search-result non-click negatives.
   - Co-visited or co-carted hard negatives.
7. Prevent leakage:
   - Compute features from observed prefix only.
   - Keep future suffix only for labels and evaluation.

### Recommended files

```text
src/sessionize.py
src/splitting.py
src/candidates.py
src/features.py
```

### Exit criteria

- A training dataset can be generated from observed session prefixes.
- A validation/test ranking dataset can be generated per session.
- No feature uses events after the cutoff.

## Phase 3: Feature Engineering V2

### Purpose

Improve signal quality and make recommendations explainable.

### Tasks

1. Session features:
   - Event count.
   - Product interaction count.
   - Unique products observed.
   - Search usage.
   - Cart presence.
   - Time elapsed.
   - Last event type.

2. Product features:
   - View count.
   - Add-to-cart count.
   - Purchase count.
   - Conversion proxy.
   - Category hash.
   - Price bucket.
   - Text vector.
   - Image vector.

3. Session-product interaction features:
   - Candidate seen in session.
   - Candidate added in session.
   - Candidate shown in search results.
   - Candidate clicked from search.
   - Category match with observed products.
   - Co-visit score.
   - Co-cart score.
   - Co-purchase score.
   - Content similarity score.

4. Explanation features:
   - Store the signals needed to explain recommendations in the demo.

### Recommended files

```text
src/features.py
src/explanations.py
```

### Exit criteria

- The model training table includes richer session, product, search, and interaction features.
- The app can explain recommendations with real feature-derived reasons.

## Phase 4: Model Training and Evaluation V2

### Purpose

Compare realistic recommender models and select a final model.

### Tasks

1. Add recommender baselines:
   - Random ranking.
   - Global popularity.
   - Recent-session baseline.
   - Co-visitation baseline.
   - Co-cart baseline.
2. Retrain existing supervised models using v2 features:
   - Logistic Regression.
   - Random Forest.
   - XGBoost.
3. Add collaborative model:
   - Start with item-item co-visit, co-cart, and co-purchase similarity.
   - Add matrix factorization only if project time allows.
4. Implement ranking metrics:
   - Precision@5 and Precision@10.
   - Recall@5 and Recall@10.
   - MAP@10.
   - NDCG@10.
   - HitRate@10.
   - Catalog coverage.
5. Save model comparison results:
   - `results/model_metrics.csv` can keep classification metrics if still needed.
   - Add `results/recommender_metrics.csv` for ranking metrics.
6. Select final model based on:
   - Ranking performance.
   - Speed.
   - Explainability.
   - Stability by session type.

### Recommended files

```text
src/recommender_metrics.py
src/recommendation.py
scripts/train_models.py
scripts/evaluate_recommenders.py
results/recommender_metrics.csv
```

### Exit criteria

- The final model is justified using recommender metrics.
- Popularity baseline is included.
- Co-visitation or co-cart baseline is included.
- The project can defend why the selected model is used in the demo.

## Phase 5: Reconstructed Marketplace Catalog

### Purpose

Create a credible visual demonstration layer without weakening the truthfulness of the ML story.

### Tasks

1. Build `data/coveo_product_catalog_demo.csv`.
2. Map hashed product IDs to readable demo names.
3. Map hashed categories to readable demo categories where possible.
4. Create display prices from price buckets.
5. Add generated or placeholder images.
6. Add `image_source` and `is_demo_ready` fields.
7. Add app copy explaining that names/images are reconstructed for demonstration.

### Recommended files

```text
src/catalog.py
data/coveo_product_catalog_demo.csv
```

### Exit criteria

- The app can display product cards with readable names, categories, prices, and images.
- The app clearly states that this is a demo layer over anonymized source data.

## Phase 6: Streamlit Multi-page Refactor

### Purpose

Turn the current app into a product experience.

### Tasks

1. Choose implementation style:
   - Streamlit `pages/` directory, or
   - Sidebar navigation inside `src/app.py`.
2. Build pages:
   - Overview.
   - Dataset & Insights.
   - Training & Validation.
   - Marketplace Demo.
   - Impact & Limitations.
3. Move reusable UI into helper modules.
4. Add cached data loading.
5. Add cached model loading.
6. Add visualizations with Plotly or Streamlit native charts.
7. Add polished product cards.

### Recommended files

```text
src/app.py
src/pages/
src/app_components.py
src/visualization.py
```

### Exit criteria

- The app is navigable as a multi-page experience.
- Each page has a clear purpose.
- The marketplace demo is visually distinct from the analytical pages.

## Phase 7: Marketplace Demo Polish

### Purpose

Make the demo the strongest part of the project.

### Tasks

1. Add session scenario selector.
2. Add session context cards.
3. Add top recommendation grid.
4. Add product images.
5. Add score labels and explanations.
6. Add optional basket simulation.
7. Add comparison between scenarios.
8. Add fallback behavior for missing images or missing product metadata.

### Exit criteria

- A viewer can choose a session scenario and immediately understand why products are recommended.
- Product cards look close to a marketplace experience.
- Recommendations vary across session contexts.

## Phase 8: Final Documentation and Story

### Purpose

Make the final project self-explanatory and defensible.

### Tasks

1. Update `README.md`.
2. Add a concise project summary.
3. Document how to train models.
4. Document how to run the app.
5. Explain dataset decision and limitations.
6. Explain final model decision.
7. Add screenshots if useful.
8. Keep context docs aligned with code.

### Exit criteria

- A new reader understands the project without reading all code.
- The README no longer reads like a generic student template.

## Suggested Implementation Order

The safest sequence is:

1. Download/place Coveo dataset.
2. Audit browsing, search, and product metadata.
3. Parse sessions and define session cutoffs.
4. Generate candidates and labels.
5. Build session/product/search features.
6. Implement ranking metrics.
7. Implement popularity, recent-session, co-visitation, and co-cart baselines.
8. Train supervised rankers.
9. Build reconstructed demo catalog.
10. Refactor Streamlit into multi-page app.
11. Build marketplace demo.
12. Update README and final story.

## Priority Matrix

| Priority | Work item | Why |
| --- | --- | --- |
| P0 | Coveo data acquisition and audit | Needed for all later work |
| P0 | Session parsing and truncation | Required for realistic recommendation |
| P0 | Ranking metrics | Required for recommender evaluation |
| P0 | Popularity, co-visitation, and co-cart baselines | Required for honest comparison |
| P1 | Session/search/content features | Improves model quality and explanations |
| P1 | Reconstructed demo catalog | Required for credible product cards |
| P1 | Marketplace page | Key final presentation |
| P1 | Product images/placeholders | Key UX improvement |
| P2 | Matrix factorization or sequence model | Strengthens recommender story |
| P2 | Basket simulation | Nice product polish |
| P2 | Calibration | Needed only if UI claims probabilities |

## Risks and Mitigations

### Risk: dataset is anonymized and lacks raw storefront images

Mitigation:

- Add reconstructed demo catalog table.
- Use generated or placeholder category images.
- Clearly document image and name reconstruction in the app.

### Risk: Coveo data is heavy for local iteration

Mitigation:

- Start with a representative subset.
- Keep preprocessing cached.
- Scale from sample to full dataset progressively.
- Separate offline scoring from Streamlit display.

### Risk: full-catalog scoring is slow in Streamlit

Mitigation:

- Precompute recommendations.
- Cache per-session results.
- Limit live scoring to candidate sets.

### Risk: scope becomes too large

Mitigation:

- Ship minimum credible v2 first.
- Keep deep learning and real-time systems as future work.

## Minimum Credible V2 Release

If time becomes constrained, the release should still include:

1. Dataset audit and enrichment table.
2. Session-truncation validation.
3. Popularity and co-visitation baselines.
4. One strong supervised session-product ranker.
5. Precision@10, Recall@10, NDCG@10.
6. Multi-page Streamlit app.
7. Marketplace demo with reconstructed product cards and explanations.

## Final Target

The final deliverable should make this statement defensible:

> This project demonstrates a realistic session-based recommendation engine trained on anonymized e-commerce behavior from Coveo, evaluated with recommender-specific metrics and presented through an interactive marketplace-style demo layer.
