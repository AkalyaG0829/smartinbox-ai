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

from prometheus_client.core import CounterMetricFamily
from prometheus_client import REGISTRY
import redis
from src.config.settings import settings

class RedisDLQCollector(object):
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0)
    
    def collect(self):
        c = CounterMetricFamily(
            "smartinbox_dlq_entries_total",
            "Number of tasks moved to the DLQ after final retry exhaustion.",
            labels=["task_name"]
        )
        try:
            dlq_counts = self.redis_client.hgetall("smartinbox:metrics:dlq_entries")
            for task_name, count in dlq_counts.items():
                c.add_metric([task_name], float(count))
        except Exception:
            pass # Fail gracefully if Redis is unavailable
        yield c

REGISTRY.register(RedisDLQCollector())

