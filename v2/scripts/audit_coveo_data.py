from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "coveo" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"


def _top(counter: Counter[str], n: int = 15) -> list[dict[str, int | str]]:
    return [{"value": key, "count": count} for key, count in counter.most_common(n)]


def _empty(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _read_csv_rows(path: Path):
    with path.open(newline="", encoding="utf-8", errors="replace") as file_handle:
        reader = csv.DictReader(file_handle)
        yield reader.fieldnames or []
        for row in reader:
            yield row


def audit_browsing(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    rows_iter = _read_csv_rows(path)
    columns = next(rows_iter)

    event_type_counts: Counter[str] = Counter()
    product_action_counts: Counter[str] = Counter()
    missing_counts: Counter[str] = Counter()
    sessions: set[str] = set()
    products: set[str] = set()
    session_lengths: dict[str, int] = defaultdict(int)
    session_flags: dict[str, int] = defaultdict(int)
    product_event_rows = 0
    timestamp_min: int | None = None
    timestamp_max: int | None = None

    action_bits = {"detail": 1, "add": 2, "purchase": 4, "remove": 8}

    row_count = 0
    for row in rows_iter:
        row_count += 1
        if max_rows is not None and row_count > max_rows:
            break

        session_id = row.get("session_id_hash", "")
        product_sku = row.get("product_sku_hash", "")
        event_type = row.get("event_type", "")
        product_action = row.get("product_action", "")
        ts_raw = row.get("server_timestamp_epoch_ms", "")

        for col in columns:
            if _empty(row.get(col)):
                missing_counts[col] += 1

        if not _empty(session_id):
            sessions.add(session_id)
            session_lengths[session_id] += 1

        if not _empty(product_sku):
            products.add(product_sku)
            product_event_rows += 1

        event_type_counts[event_type or "<empty>"] += 1
        product_action_counts[product_action or "<empty>"] += 1

        action_key = product_action.strip().lower()
        if session_id and action_key in action_bits:
            session_flags[session_id] |= action_bits[action_key]

        if ts_raw:
            try:
                ts = int(float(ts_raw))
            except ValueError:
                continue
            timestamp_min = ts if timestamp_min is None else min(timestamp_min, ts)
            timestamp_max = ts if timestamp_max is None else max(timestamp_max, ts)

    lengths = list(session_lengths.values())
    lengths.sort()

    def percentile(pct: float) -> int:
        if not lengths:
            return 0
        idx = min(len(lengths) - 1, int(round((len(lengths) - 1) * pct)))
        return lengths[idx]

    flag_values = list(session_flags.values())
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "columns": columns,
        "rows": row_count if max_rows is None else min(row_count, max_rows),
        "unique_sessions": len(sessions),
        "unique_products": len(products),
        "product_event_rows": product_event_rows,
        "timestamp_min_epoch_ms": timestamp_min,
        "timestamp_max_epoch_ms": timestamp_max,
        "event_type_counts": _top(event_type_counts),
        "product_action_counts": _top(product_action_counts),
        "missing_counts": dict(missing_counts),
        "session_length": {
            "min": lengths[0] if lengths else 0,
            "p25": percentile(0.25),
            "median": percentile(0.50),
            "p75": percentile(0.75),
            "p90": percentile(0.90),
            "p95": percentile(0.95),
            "max": lengths[-1] if lengths else 0,
        },
        "sessions_with_detail": sum(1 for flags in flag_values if flags & 1),
        "sessions_with_add": sum(1 for flags in flag_values if flags & 2),
        "sessions_with_purchase": sum(1 for flags in flag_values if flags & 4),
        "sessions_with_remove": sum(1 for flags in flag_values if flags & 8),
    }


def audit_search(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    rows_iter = _read_csv_rows(path)
    columns = next(rows_iter)

    missing_counts: Counter[str] = Counter()
    sessions: set[str] = set()
    rows_with_results = 0
    rows_with_clicks = 0
    result_count_hist: Counter[str] = Counter()
    clicked_count_hist: Counter[str] = Counter()
    timestamp_min: int | None = None
    timestamp_max: int | None = None

    row_count = 0
    for row in rows_iter:
        row_count += 1
        if max_rows is not None and row_count > max_rows:
            break

        session_id = row.get("session_id_hash", "")
        results_raw = row.get("product_skus_hash", "")
        clicked_raw = row.get("clicked_skus_hash", "")
        ts_raw = row.get("server_timestamp_epoch_ms", "")

        for col in columns:
            if _empty(row.get(col)):
                missing_counts[col] += 1

        if not _empty(session_id):
            sessions.add(session_id)

        results = [item for item in results_raw.split("|") if item] if results_raw else []
        clicked = [item for item in clicked_raw.split("|") if item] if clicked_raw else []

        if results:
            rows_with_results += 1
        if clicked:
            rows_with_clicks += 1

        result_count_hist[str(len(results))] += 1
        clicked_count_hist[str(len(clicked))] += 1

        if ts_raw:
            try:
                ts = int(float(ts_raw))
            except ValueError:
                continue
            timestamp_min = ts if timestamp_min is None else min(timestamp_min, ts)
            timestamp_max = ts if timestamp_max is None else max(timestamp_max, ts)

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "columns": columns,
        "rows": row_count if max_rows is None else min(row_count, max_rows),
        "unique_sessions": len(sessions),
        "timestamp_min_epoch_ms": timestamp_min,
        "timestamp_max_epoch_ms": timestamp_max,
        "rows_with_results": rows_with_results,
        "rows_with_clicks": rows_with_clicks,
        "result_count_histogram_top": _top(result_count_hist),
        "clicked_count_histogram_top": _top(clicked_count_hist),
        "missing_counts": dict(missing_counts),
    }


def audit_content(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    rows_iter = _read_csv_rows(path)
    columns = next(rows_iter)

    missing_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    price_bucket_counts: Counter[str] = Counter()
    products: set[str] = set()
    rows_with_description_vector = 0
    rows_with_image_vector = 0

    row_count = 0
    for row in rows_iter:
        row_count += 1
        if max_rows is not None and row_count > max_rows:
            break

        product_sku = row.get("product_sku_hash", "")
        category_hash = row.get("category_hash", "")
        price_bucket = row.get("price_bucket", "")
        description_vector = row.get("description_vector", "")
        image_vector = row.get("image_vector", "")

        for col in columns:
            if _empty(row.get(col)):
                missing_counts[col] += 1

        if not _empty(product_sku):
            products.add(product_sku)
        category_counts[category_hash or "<empty>"] += 1
        price_bucket_counts[price_bucket or "<empty>"] += 1
        if not _empty(description_vector):
            rows_with_description_vector += 1
        if not _empty(image_vector):
            rows_with_image_vector += 1

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "columns": columns,
        "rows": row_count if max_rows is None else min(row_count, max_rows),
        "unique_products": len(products),
        "rows_with_description_vector": rows_with_description_vector,
        "rows_with_image_vector": rows_with_image_vector,
        "category_counts_top": _top(category_counts),
        "price_bucket_counts": _top(price_bucket_counts, n=20),
        "missing_counts": dict(missing_counts),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    browsing = report["browsing"]
    search = report["search"]
    content = report["content"]

    lines = [
        "# Coveo Data Audit",
        "",
        "## Files",
        "",
        f"- Browsing: `{browsing['path']}`",
        f"- Search: `{search['path']}`",
        f"- Content: `{content['path']}`",
        "",
        "## Browsing Events",
        "",
        f"- Rows: {browsing['rows']:,}",
        f"- Unique sessions: {browsing['unique_sessions']:,}",
        f"- Unique products: {browsing['unique_products']:,}",
        f"- Product event rows: {browsing['product_event_rows']:,}",
        f"- Sessions with detail: {browsing['sessions_with_detail']:,}",
        f"- Sessions with add: {browsing['sessions_with_add']:,}",
        f"- Sessions with purchase: {browsing['sessions_with_purchase']:,}",
        f"- Sessions with remove: {browsing['sessions_with_remove']:,}",
        f"- Session length summary: {browsing['session_length']}",
        "",
        "### Product Action Counts",
        "",
    ]
    lines.extend(
        f"- {item['value']}: {item['count']:,}"
        for item in browsing["product_action_counts"]
    )
    lines.extend(
        [
            "",
            "## Search Events",
            "",
            f"- Rows: {search['rows']:,}",
            f"- Unique sessions: {search['unique_sessions']:,}",
            f"- Rows with result products: {search['rows_with_results']:,}",
            f"- Rows with clicked products: {search['rows_with_clicks']:,}",
            "",
            "## Product Content",
            "",
            f"- Rows: {content['rows']:,}",
            f"- Unique products: {content['unique_products']:,}",
            f"- Rows with description vector: {content['rows_with_description_vector']:,}",
            f"- Rows with image vector: {content['rows_with_image_vector']:,}",
            "",
            "### Price Bucket Counts",
            "",
        ]
    )
    lines.extend(
        f"- {item['value']}: {item['count']:,}"
        for item in content["price_bucket_counts"]
    )
    lines.extend(
        [
            "",
            "## Initial Decision Notes",
            "",
            "- Use browsing events as the first modeling backbone.",
            "- Use search events for hard negatives and search-context features.",
            "- Use product content metadata for category, price, text-vector, and image-vector features.",
            "- If full-data iteration is slow, start with a representative session sample and scale later.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Coveo SIGIR eCom data files.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()

    browsing_path = args.raw_dir / "browsing_train.csv"
    search_path = args.raw_dir / "search_train.csv"
    content_path = args.raw_dir / "sku_to_content.csv"

    missing = [path for path in [browsing_path, search_path, content_path] if not path.exists()]
    if missing:
        missing_list = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing Coveo files: {missing_list}")

    RESULTS_DIR.mkdir(exist_ok=True)
    report = {
        "browsing": audit_browsing(browsing_path, max_rows=args.max_rows),
        "search": audit_search(search_path, max_rows=args.max_rows),
        "content": audit_content(content_path, max_rows=args.max_rows),
    }

    json_path = RESULTS_DIR / "coveo_data_audit.json"
    markdown_path = RESULTS_DIR / "coveo_data_audit.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, markdown_path)

    print(f"Wrote {json_path.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {markdown_path.relative_to(PROJECT_ROOT)}")
    print(json.dumps(report, indent=2)[:4000])


if __name__ == "__main__":
    main()
