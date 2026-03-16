import threading
import logging

logger = logging.getLogger(__name__)

# --- Pricing (per 1M tokens) ---
# GPT-5:               $1.25 input,  $10.00 output
# GPT-5-search-api:    $1.25 input,  $10.00 output + $10.00 per 1K web search calls (+ search content tokens at input rate)
# SerpAPI:              $275.00 per 30,000 calls/month

PRICING = {
    "gpt-5": {"input": 1.25 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-5-search-api": {"input": 1.25 / 1_000_000, "output": 10.00 / 1_000_000, "search_call": 10.00 / 1_000},
}

SERPAPI_COST_PER_CALL = 275.00 / 30_000  # ~$0.00917


class CostTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            # OpenAI tokens
            self.openai_calls = {
                "gpt-5": {"input_tokens": 0, "output_tokens": 0, "calls": 0},
                "gpt-5-search-api": {"input_tokens": 0, "output_tokens": 0, "calls": 0},
            }
            # SerpAPI calls
            self.serpapi_calls = 0

    def track_openai(self, model, usage):
        """Track an OpenAI API call. Pass response.usage directly."""
        with self._lock:
            bucket = self.openai_calls.get(model)
            if bucket:
                bucket["input_tokens"] += usage.prompt_tokens
                bucket["output_tokens"] += usage.completion_tokens
                bucket["calls"] += 1

    def track_serpapi(self):
        """Track a single SerpAPI call."""
        with self._lock:
            self.serpapi_calls += 1

    def get_summary(self):
        with self._lock:
            lines = ["\n===== COST SUMMARY ====="]
            total = 0.0

            for model, data in self.openai_calls.items():
                if data["calls"] == 0:
                    continue
                pricing = PRICING[model]
                input_cost = data["input_tokens"] * pricing["input"]
                output_cost = data["output_tokens"] * pricing["output"]
                search_cost = 0.0
                if "search_call" in pricing:
                    search_cost = data["calls"] * pricing["search_call"]
                model_total = input_cost + output_cost + search_cost

                lines.append(f"\n  {model}:")
                lines.append(f"    Calls:         {data['calls']}")
                lines.append(f"    Input tokens:  {data['input_tokens']:,}")
                lines.append(f"    Output tokens: {data['output_tokens']:,}")
                lines.append(f"    Input cost:    ${input_cost:.4f}")
                lines.append(f"    Output cost:   ${output_cost:.4f}")
                if search_cost > 0:
                    lines.append(f"    Search calls:  ${search_cost:.4f}")
                lines.append(f"    Subtotal:      ${model_total:.4f}")
                total += model_total

            serpapi_cost = self.serpapi_calls * SERPAPI_COST_PER_CALL
            lines.append(f"\n  SerpAPI:")
            lines.append(f"    Calls:         {self.serpapi_calls}")
            lines.append(f"    Cost:          ${serpapi_cost:.4f}")
            total += serpapi_cost

            lines.append(f"\n  TOTAL: ${total:.4f}")
            lines.append("========================\n")
            return "\n".join(lines)

    def print_summary(self):
        logger.info(self.get_summary())


# Single global instance — import this everywhere
tracker = CostTracker()
