from prometheus_client import Counter, Histogram

# Business Metric: Routing Decisions
ROUTING_DECISIONS = Counter(
    "smartinbox_routing_decisions_total",
    "Total number of messages routed, by resulting action.",
    labelnames=["action"]
)

# Business Metric: Confidence Bands
CONFIDENCE_BANDS = Counter(
    "smartinbox_confidence_bands_total",
    "Number of routing decisions grouped by confidence band (e.g., high, medium, low).",
    labelnames=["band"]
)

# ML Metric: Embedding Duration
EMBEDDING_DURATION = Histogram(
    "smartinbox_embedding_duration_seconds",
    "Time spent generating ML semantic embeddings.",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Operational Metric: DLQ Entries
DLQ_ENTRIES = Counter(
    "smartinbox_dlq_entries_total",
    "Number of tasks moved to the DLQ after final retry exhaustion.",
    labelnames=["task_name"]
)
