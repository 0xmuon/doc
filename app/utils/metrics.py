"""in memory totals.logs are one request,this is every request since startup."""

stats: dict[str, dict] = {}


def record_request(method: str, route: str, status: int, duration_ms: float) -> None:
    """count by the route template,so /products/1 and /products/2 share one row."""
    row = stats.setdefault(f"{method} {route}", {"requests": 0, "errors": 0, "total_ms": 0.0})
    row["requests"] += 1
    if status >= 500:
        row["errors"] += 1
    row["total_ms"] += duration_ms


def metrics_report() -> dict:
    return {
        route: {
            "requests": row["requests"],
            "error_rate": round(row["errors"] / row["requests"], 3),
            "avg_ms": round(row["total_ms"] / row["requests"], 1),
        }
        for route, row in stats.items()
    }


def reset_metrics() -> None:
    stats.clear()
