# V2 Product Vision

## Executive Summary

The project should evolve from a student machine learning proof of concept into a credible e-commerce recommendation product demo.

The final product should not only prove that a model can predict whether a customer may buy a product. It should show how a real online retailer could use recommendations to increase basket size, improve personalization, support marketing actions, and make the shopping experience more relevant for each customer.

The v2 target is a multi-page interactive Streamlit application backed by a more rigorous recommender pipeline, stronger validation, clearer business storytelling, and a marketplace-like demo experience. The priority is the ML recommender itself: the visual marketplace layer is allowed to be a credible demonstration layer as long as this is stated clearly in the app.

## Product Positioning

### One-sentence pitch

An interactive session-based recommendation engine that predicts the next most relevant products from real e-commerce behavior signals such as product views, search interactions, add-to-cart events, purchases, timestamps, and product metadata.

### Business problem

E-commerce platforms often have large catalogs and many short shopping sessions where the platform must react quickly to views, searches, cart actions, and purchase intent. Without personalization, shoppers see generic recommendations and the platform misses opportunities for product discovery, upsell, cross-sell, and conversion.

The product answers:

- Which products should we recommend in this shopping session now?
- Why are these products relevant?
- Which model performs best for this recommendation problem?
- How can the system be used in a realistic e-commerce workflow?

### Business value

The expected value is not just model accuracy. The product should connect recommendations to business outcomes:

- Higher average basket value through cross-sell and upsell.
- Better conversion through personalized product ranking.
- More relevant CRM campaigns.
- Better merchandising decisions from customer and product insights.
- A reusable recommendation workflow that could be integrated into a storefront, email campaign, or checkout page.

## Target Users

### Primary audience: business stakeholders

They need to understand the value of the product quickly. The app should show clear business objectives, session scenarios, product cards, and recommendation explanations.

### Secondary audience: technical evaluators

They need to see that the data strategy, modeling approach, validation protocol, and metrics are credible. The app and documentation should make the ML process transparent without overwhelming non-technical users.

### Tertiary audience: product and marketing teams

They need to imagine how the recommender could be used operationally: homepage personalization, cart upsell, CRM targeting, segmented offers, or product discovery.

## Final Application Experience

The final Streamlit application should feel like a small product, not a notebook exported to the web.

Recommended pages:

1. **Overview**
   - Project objective.
   - Business context.
   - Original assignment constraints.
   - Final v2 ambition.
   - Main success criteria.

2. **Dataset & Business Case**
   - Dataset source and structure, with Coveo SIGIR eCom 2021 as the target ML dataset.
   - Why this dataset was chosen.
   - Cleaning, anonymization, and demo enrichment strategy.
   - Data limits and how the project mitigates them.
   - Key customer and product insights.

3. **Training & Validation**
   - Model pipeline.
   - Train/validation/test strategy.
   - Feature families.
   - Baselines and advanced models.
   - Ranking metrics and model comparison.
   - Final model choice and justification.

4. **Marketplace Demo**
   - Session scenario selector.
   - Observed behavior summary.
   - Product recommendation cards with image, price, category, score, and explanation.
   - Scenario-specific recommendation logic.
   - Optional cart or upsell simulation.

5. **Impact & Next Steps**
   - How the recommender could be deployed.
   - Expected business impact.
   - Known limits.
   - Production roadmap.

## Product Principles

### Credibility over decoration

The app should look polished, but the product story must remain technically honest. If scores are model scores rather than calibrated purchase probabilities, the UI must say so.

### ML recommender first

The main value of the project is the recommender system, not the visual catalog. The selected dataset should maximize behavioral and evaluation credibility, even if product names and images need to be reconstructed for the demo.

### Ranking over classification

A recommender is judged by whether relevant products appear near the top. The project should move from simple accuracy/F1 toward metrics such as Precision@K, Recall@K, MAP@K, and NDCG@K.

### Realistic offline validation

The model should be evaluated on a scenario close to real deployment: observe the first part of a shopping session, recommend products, and check whether the future session events contain those products.

### Explainable recommendations

Each recommendation should include a concise reason: frequently co-viewed, frequently co-carted, aligned with the current session category, present in search context, close in product-content space, or high model affinity.

### Product-like demo

The marketplace page should use product cards, images, short descriptions, badges, prices, and score explanations. It should make the ML output feel usable in a real e-commerce site, while explicitly stating that some display names and visuals are reconstructed for demonstration because the primary dataset is anonymized.

## Success Criteria

### Technical success

- The dataset decision is explicit and justified.
- The validation protocol avoids obvious leakage.
- The model comparison includes recommender metrics, not only classification metrics.
- At least one simple baseline is included, such as popularity-based recommendations.
- The selected final model is justified by both performance and product usability.

### Product success

- A non-technical viewer can understand the problem and value in under two minutes.
- The demo page looks and behaves like a small marketplace experience.
- Session scenarios show visibly different recommendations and explanations.
- The app explains what the model score means and does not overclaim probability accuracy.

### Business success

- The product narrative connects model outputs to use cases: homepage personalization, email recommendations, cart upsell, and CRM targeting.
- The app shows how recommendations could affect basket size, conversion, or retention.
- The final project feels closer to a prototype that could be pitched internally than to a basic academic assignment.

## Scope Boundaries

This is still a local proof of concept. The v2 should not pretend to include production infrastructure such as real-time event streaming, online A/B testing, feature stores, or full MLOps deployment.

However, the project should be structured so that these topics can be discussed credibly as future work.

## Recommended V2 Direction

The best direction is to migrate the recommender core from `Online Retail II` to the Coveo SIGIR eCom 2021 dataset, then use a reconstructed visual layer for the marketplace demo.

1. **Data and modeling credibility**
   - Use real session-level e-commerce behavior.
   - Exploit product detail views, add-to-cart events, purchases, searches, timestamps, categories, prices, and content embeddings.
   - Evaluate future in-session product interactions with recommender metrics.

2. **Recommendation realism**
   - Rank candidate products within a browsing session.
   - Compare against popularity, recent-session, co-visitation, co-cart, and co-purchase baselines.
   - Add clear score semantics and session-based explanations.

3. **Product experience**
   - Move to a multi-page app.
   - Build a marketplace-style demo.
   - Use reconstructed names, categories, and generated or placeholder images where needed.
   - Clearly disclose the demo layer while keeping the ML pipeline grounded in real e-commerce events.
