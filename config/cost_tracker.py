import threading
import logging

logger = logging.getLogger(__name__)

# per-token costs
PRICING = {
    "gpt-5": {
        "input": 1.25 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
    "gpt-5-search-api": {
        "input": 1.25 / 1_000_000,
        "output": 10.00 / 1_000_000,
        "per_search": 10.00 / 1_000,
    },
    "gpt-4.1-mini": {
        "input": 0.40 / 1_000_000,
        "output": 1.60 / 1_000_000,
    },
}

SERPAPI_COST_PER_CALL = 275.00 / 30_000


class CostTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.openai = {
                model: {"input_tokens": 0, "output_tokens": 0, "calls": 0}
                for model in PRICING
            }
            self.serpapi_calls = 0

    def track_openai(self, model, usage):
        with self._lock:
            bucket = self.openai.get(model)
            if bucket:
                bucket["input_tokens"] += usage.prompt_tokens
                bucket["output_tokens"] += usage.completion_tokens
                bucket["calls"] += 1

    def track_serpapi(self):
        with self._lock:
            self.serpapi_calls += 1

    def _model_cost(self, model, data):
        p = PRICING[model]
        cost = data["input_tokens"] * p["input"] + data["output_tokens"] * p["output"]
        if "per_search" in p:
            cost += data["calls"] * p["per_search"]
        return cost

    def print_summary(self):
        with self._lock:
            total = 0.0
            lines = ["\n===== COST SUMMARY ====="]

            for model, data in self.openai.items():
                if data["calls"] == 0:
                    continue
                cost = self._model_cost(model, data)
                total += cost
                lines.append(f"\n  {model}:")
                lines.append(f"    Calls:          {data['calls']}")
                lines.append(f"    Input tokens:   {data['input_tokens']:,}")
                lines.append(f"    Output tokens:  {data['output_tokens']:,}")
                lines.append(f"    Cost:           ${cost:.4f}")

            serpapi_cost = self.serpapi_calls * SERPAPI_COST_PER_CALL
            total += serpapi_cost
            lines.append(f"\n  SerpAPI:")
            lines.append(f"    Calls:          {self.serpapi_calls}")
            lines.append(f"    Cost:           ${serpapi_cost:.4f}")

            lines.append(f"\n  TOTAL: ${total:.4f}")
            lines.append("========================\n")
            logger.info("\n".join(lines))


tracker = CostTracker()