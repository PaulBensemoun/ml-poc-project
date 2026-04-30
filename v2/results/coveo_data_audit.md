# Coveo Data Audit

## Files

- Browsing: `v2/data/coveo/raw/browsing_train.csv`
- Search: `v2/data/coveo/raw/search_train.csv`
- Content: `v2/data/coveo/raw/sku_to_content.csv`

## Browsing Events

- Rows: 36,079,307
- Unique sessions: 4,934,699
- Unique products: 57,483
- Product event rows: 10,431,611
- Sessions with detail: 3,260,353
- Sessions with add: 214,684
- Sessions with purchase: 53,209
- Sessions with remove: 57,441
- Session length summary: {'min': 1, 'p25': 2, 'median': 3, 'p75': 8, 'p90': 17, 'p95': 27, 'max': 206}

### Product Action Counts

- <empty>: 25,647,696
- detail: 9,707,890
- add: 329,557
- remove: 316,316
- purchase: 77,848

## Search Events

- Rows: 819,516
- Unique sessions: 550,100
- Rows with result products: 602,754
- Rows with clicked products: 179,495

## Product Content

- Rows: 66,386
- Unique products: 66,386
- Rows with description vector: 31,950
- Rows with image vector: 28,370

### Price Bucket Counts

- <empty>: 34,348
- 4.0: 3,409
- 3.0: 3,350
- 9.0: 3,238
- 10.0: 3,201
- 1.0: 3,198
- 7.0: 3,191
- 8.0: 3,183
- 2.0: 3,103
- 5.0: 3,086
- 6.0: 3,079

## Initial Decision Notes

- Use browsing events as the first modeling backbone.
- Use search events for hard negatives and search-context features.
- Use product content metadata for category, price, text-vector, and image-vector features.
- If full-data iteration is slow, start with a representative session sample and scale later.
