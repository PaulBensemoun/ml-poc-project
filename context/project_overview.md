# Project Overview

## Objective
Build a machine learning proof-of-concept to recommend the next best product to a customer in an e-commerce setting.

## Business Problem
How can we increase revenue per user and basket size by recommending the most relevant product to each customer?

## Approach
We reformulate the problem as a supervised learning task:

Predict the probability that a customer will purchase a given product.

## Dataset
Online Retail II dataset.

Columns:
- Invoice
- StockCode
- Description
- Quantity
- InvoiceDate
- Price
- Customer ID
- Country

## Output
- A trained ML model
- Model comparison (LogReg, RandomForest, XGBoost)
- A Streamlit app showing:
  - insights
  - model performance
  - top product recommendations for a selected customer
