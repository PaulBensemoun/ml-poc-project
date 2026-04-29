# Data Strategy

## Cleaning Rules
- Remove rows with missing Customer ID
- Remove rows with missing Description or StockCode
- Keep only Quantity > 0
- Keep only Price > 0
- Convert InvoiceDate to datetime
- Convert Customer ID to string

## Modeling Approach

We build a binary classification dataset:

Each row represents:
(Customer ID, Product)

Target:
- 1 if the customer bought the product
- 0 if the customer did not buy the product

## Feature Ideas

### Customer features
- total_spend
- total_quantity
- number_of_transactions
- recency (days since last purchase)

### Product features
- product_popularity (number of purchases)
- average_price

### Interaction
- customer-product frequency (if exists)

## Negative Sampling
- Randomly sample products not purchased by each customer
- Keep dataset balanced
