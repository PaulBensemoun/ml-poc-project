# V2 Streamlit App Specification

## Objective

The v2 Streamlit app should become a polished interactive product demo for an e-commerce recommendation engine.

It should no longer feel like a single analytical page. It should guide the user through:

1. The business objective.
2. The dataset and project choice.
3. The model training and validation process.
4. The final recommendation demo.
5. The expected business impact.

The app must clearly state that the ML recommender is the priority. The core model uses real anonymized Coveo session behavior, while the marketplace visuals are a reconstructed demonstration layer.

## Recommended App Architecture

Use Streamlit multipage structure:

```text
src/
  app.py
  pages/
    1_Overview.py
    2_Dataset_and_Insights.py
    3_Training_and_Validation.py
    4_Marketplace_Demo.py
    5_Impact_and_Limitations.py
```

Alternative if the template constraints make this inconvenient:

- Keep `src/app.py` as the entry point.
- Use `st.navigation` if available in the installed Streamlit version.
- Or use `st.sidebar.radio` to simulate pages.

The final user experience should still feel multi-page even if the internal implementation remains in one file.

## Global UX Requirements

### Visual style

The app should use:

- Wide layout.
- Clear sidebar navigation.
- Strong page titles and short summaries.
- Product cards instead of raw tables where possible.
- Consistent badges for model, category, score, and scenario.
- Clean metric cards for business and ML KPIs.

### Tone

The writing should be business-friendly and technically honest.

Avoid:

- Overclaiming that scores are guaranteed purchase probabilities.
- Hiding dataset limitations.
- Presenting academic metrics without product interpretation.

Prefer:

- "Recommendation score".
- "Predicted affinity".
- "Top-ranked candidates".
- "Offline validation".
- "Expected business use case".

## Page 1: Overview

### Purpose

Explain the project quickly and make the ambition clear.

### Content blocks

1. Hero section:
   - Product name.
   - One-sentence value proposition.
   - Short business problem.

2. Project objective:
   - Build a session-based e-commerce recommender.
   - Recommend products from observed session behavior.
   - Increase basket size and personalization quality.

3. Assignment context:
   - This started as a machine learning POC.
   - The v2 turns it into a more realistic product prototype.

4. How the system works:
   - Product views.
   - Search interactions.
   - Add-to-cart events.
   - Purchases.
   - Product metadata and content vectors.
   - Model scoring.
   - Ranked recommendations.
   - Marketplace demo layer.

5. Success criteria:
   - Technical credibility.
   - Ranking performance.
   - Clear product experience.
   - Business value.

### Suggested components

- `st.title`
- `st.markdown`
- `st.columns` with cards for business, ML, product.
- Small architecture diagram using `st.graphviz_chart` or markdown Mermaid in docs, not necessarily in Streamlit.

## Page 2: Dataset & Insights

### Purpose

Explain why the dataset was chosen, what it contains, how it is cleaned, and what business insights it reveals.

### Content blocks

1. Dataset summary:
   - Source: Coveo SIGIR eCom 2021.
   - Session-based e-commerce behavior.
   - Browsing events.
   - Search events.
   - Product content metadata.
   - Anonymized product identifiers.

2. Data cleaning:
   - Parse browsing and search files.
   - Normalize product actions.
   - Order events by timestamp inside sessions.
   - Join product events to `sku_to_content.csv`.
   - Build observed session prefixes and future targets.

3. Dataset strengths:
   - Real e-commerce sessions.
   - Product views, add-to-cart events, and purchases.
   - Search result impressions and clicks.
   - Timestamps.
   - Categories, price buckets, text vectors, and image vectors.

4. Dataset limitations:
   - Product IDs and categories are anonymized.
   - Product names are not human-readable.
   - Product images are represented as vectors rather than raw storefront photos.
   - The visual demo needs reconstructed names and images.

5. V2 enrichment plan:
   - Add `coveo_product_catalog_demo.csv`.
   - Create readable demo categories.
   - Create generated or placeholder visuals.
   - Create demo-ready product names and descriptions.
   - Disclose this reconstruction in the app.

6. Exploratory insights:
   - Session length distribution.
   - Product action funnel.
   - Search behavior.
   - Price bucket distribution.
   - Top products by view, add, and purchase count.

### Suggested visuals

- Session length distribution.
- Event type distribution.
- Product action funnel: detail, add, purchase.
- Search usage rate.
- Price bucket distribution.
- Top products by view, add, and purchase count.

## Page 3: Training & Validation

### Purpose

Show that the recommender was trained and evaluated seriously.

### Content blocks

1. Problem formulation:
   - Recommend top products during an active shopping session.
   - Rank candidate products using model scores.
   - Evaluate whether future clicked, carted, or purchased products appear in top K.

2. Feature engineering:
   - Session sequence features.
   - Product popularity by event type.
   - Search and clicked-result features.
   - Co-visitation, co-cart, and co-purchase features.
   - Product category, price bucket, text vector, and image vector features.

3. Validation protocol:
   - Session truncation or chronological split.
   - Train on observed session context.
   - Validate/test on future session events.
   - Avoid future leakage after the cutoff.

4. Models:
   - Random baseline.
   - Popularity baseline.
   - Recent-session baseline.
   - Co-visitation baseline.
   - Co-cart baseline.
   - Logistic Regression.
   - Random Forest.
   - XGBoost.
   - Item-item collaborative or co-occurrence model.

5. Metrics:
   - Precision@5 / Precision@10.
   - Recall@5 / Recall@10.
   - NDCG@10.
   - MAP@10.
   - Coverage.
   - Existing classification metrics can remain as secondary metrics.

6. Model selection:
   - Explain why the final model was selected.
   - Balance performance, speed, explainability, and UX quality.

### Suggested visuals

- Model comparison table.
- Bar chart of ranking metrics.
- Confusion matrix only as optional secondary artifact.
- Feature importance chart for tree models.
- Baseline vs model lift chart.

### Required disclaimer

The page should explain:

> The recommender is evaluated offline. A real production deployment would require online A/B testing to measure conversion or revenue uplift.

It should also explain:

> The dataset is anonymized. The ML model uses real session behavior and product-content signals; the marketplace names and images are reconstructed for demonstration.

## Page 4: Marketplace Demo

### Purpose

Provide the most impressive part of the final project: an interactive recommendation experience that looks like a real marketplace.

## Demo User Flow

1. Choose a shopping-session scenario.
2. Read the session context.
3. See observed behavior features.
4. View recommended products as product cards.
5. Inspect why each product was recommended.
6. Optionally add a product to a mock basket.
7. See an upsell or cross-sell scenario update.

## Session Scenarios

### Scenario 1: Browse-only product discovery

Profile:

- Several product detail views.
- No cart event yet.
- Category preference visible from the session.

Recommendation angle:

- Similar products.
- Popular products in the same category.
- Products close in content-vector space.

### Scenario 2: Search-led session

Profile:

- Shopper used search.
- Some results were shown.
- One or more products may have been clicked.

Recommendation angle:

- Products from search results.
- Products similar to clicked results.
- Products likely to satisfy the query intent.

### Scenario 3: Cart intent session

Profile:

- Shopper added at least one product to cart.
- Conversion intent is stronger.
- Cross-sell and substitution are both relevant.

Recommendation angle:

- Complementary products.
- Co-cart products.
- Products frequently purchased with the cart item.

### Scenario 4: Purchase-intent session

Profile:

- Session already contains strong purchase signals.
- The system recommends final next-best products before checkout.

Recommendation angle:

- Co-purchase products.
- High-conversion candidates.
- Relevant add-ons or substitutes.

## Product Card Specification

Each recommendation should appear as a card with:

- Product image.
- Product name.
- Product category.
- Price or average historical price.
- Recommendation score.
- Badge such as `Top pick`, `Popular`, `Great price fit`, `Frequently co-purchased`.
- Short explanation.
- Optional action button: `Add to demo basket`.

### Example card content

```text
Product: Vintage Ceramic Mug
Category: Home Decor
Price bucket: Mid-range
Recommendation score: 87
Why recommended: Frequently co-visited and co-carted with products observed earlier in this session, with strong category and content-vector fit.
```

## Image Strategy

Because Coveo provides image representations rather than raw storefront images, the v2 needs an explicit demo image strategy.

Recommended hierarchy:

1. Use generated or local placeholder images by readable demo category.
2. Use curated demo images only if licensing and source are clear.
3. Use a consistent fallback image for products without a match.

The app must not imply that generated or placeholder images are original product photos.

Suggested future file:

```text
data/coveo_product_catalog_demo.csv
```

Required app behavior:

- If `image_url` exists, show it.
- Else if category placeholder exists, show that.
- Else show a neutral placeholder.

## Recommendation Explanation Strategy

Each card should include a short reason selected from available signals:

| Signal | Example explanation |
| --- | --- |
| Co-visit | Often viewed with products in the observed session |
| Co-cart | Often added to cart with products in the observed session |
| Co-purchase | Often purchased with products in the observed session |
| Search fit | Appeared in or resembles clicked search results |
| Category fit | Matches categories observed in the session |
| Price fit | Close to the session's observed price buckets |
| Content similarity | Close in text or image-vector space |

For v2, explanations can be rule-based and derived from features. They do not need to be perfect SHAP explanations, but they must be consistent with the data shown.

## Marketplace Demo Layout

Recommended layout:

```text
Sidebar:
  - Page navigation
  - Session scenario selector
  - Model selector or final model badge
  - Number of recommendations

Main:
  - Session context hero
  - Observed behavior metrics
  - Recommendation product grid
  - Explanation drawer/table
  - Optional demo basket
```

## Page 5: Impact & Limitations

### Purpose

Close the story with business value and honesty.

### Content blocks

1. Business use cases:
   - Homepage personalization.
   - Email campaigns.
   - Cart upsell.
   - CRM targeting.
   - Product discovery.

2. Expected impact:
   - Higher basket value.
   - Better click-through.
   - Better conversion.
   - More relevant recommendations.

3. Limitations:
   - Offline validation only.
   - Dataset is anonymized.
   - Product names/images are reconstructed for demo.
   - Raw product photos are not included.
   - Long-term customer identity is less central than session behavior.
   - Scores are not guaranteed probabilities unless calibrated.

4. Production roadmap:
   - Event tracking.
   - Real-time scoring.
   - A/B testing.
   - Monitoring.
   - Model retraining.

## Technical Implementation Notes

### Data loading

Expensive data preparation should be cached:

- `@st.cache_data` for cleaned data and feature tables.
- `@st.cache_resource` for model loading.

### Performance

For the demo:

- Precompute recommendation candidates where possible.
- Limit live scoring to a manageable candidate set.
- Cache per-session recommendations.
- Use full-catalog scoring offline if live performance becomes slow.

### File organization

Recommended supporting modules:

```text
src/app_components.py
src/catalog.py
src/recommendation.py
src/visualization.py
```

These can keep page files readable and avoid a single oversized `app.py`.

## Definition of Done

The app v2 is complete when:

- It has a clear multi-page structure.
- It explains the dataset decision and limitations.
- It presents ranking-based model evaluation.
- It justifies the chosen final recommender.
- The demo page shows session scenarios and product cards.
- Recommendations include scores and explanations.
- Product images or credible placeholders are integrated.
- The user can understand both the business value and technical credibility.
