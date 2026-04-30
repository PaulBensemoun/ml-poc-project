# Project Overview

## Objective
Build a machine learning proof-of-concept for a realistic session-based e-commerce recommender.

## Business Problem
How can we improve product discovery, cart conversion, and basket value by recommending the most relevant next products during a shopping session?

## Approach
We reformulate the problem as a session-based ranking task:

Given the first part of a shopping session, rank candidate products according to how likely they are to be viewed, added to cart, or purchased later in the same session.

## Dataset
Coveo SIGIR eCom 2021 is the v2 target dataset.

Core files:
- `browsing_train.csv`
- `search_train.csv`
- `sku_to_content.csv`

Key signals:
- session IDs
- timestamps
- product detail events
- add-to-cart events
- purchase events
- search interactions
- clicked and non-clicked search results
- product categories
- price buckets
- text and image content vectors

`Online Retail II` remains only as a v1 baseline reference.

## Output
- A trained session-based recommender
- Baseline comparison: popularity, recent-session, co-visitation, co-cart
- Model comparison: tabular rankers and recommender-specific baselines
- Ranking metrics: Precision@K, Recall@K, MAP@K, NDCG@K, HitRate@K
- A Streamlit app showing:
  - project objective and dataset choice
  - session behavior insights
  - model performance and final model justification
  - top product recommendations for selected session scenarios
  - a credible marketplace demo layer with reconstructed product names/images

The app must state that the visual product catalog is reconstructed for demonstration because Coveo is anonymized. The recommender logic remains grounded in real e-commerce behavior.
